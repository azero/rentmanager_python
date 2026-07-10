from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest
from pydantic import BaseModel

import rentmanager_api.models as rm_models
from rentmanager_api import (
    AsyncRentManagerClient,
    FileTokenStore,
    InMemoryTokenStore,
    QueryParams,
    RQL,
    RentManagerClient,
    RentManagerNotFoundError,
    RentManagerTransportError,
)
from rentmanager_api.errors import (
    RentManagerAPIError,
    RentManagerAuthError,
    RentManagerServerError,
    error_from_response,
    parse_error_model,
)
from rentmanager_api.pagination import parse_link_header, total_results_from_headers
from rentmanager_api.resources.core import Resource
from rentmanager_api.workflows import lookup_by_email
from rentmanager_api.workflows import service_tickets as ticket_workflow


def make_sync_client(handler, *, token_store=None, max_retries=0, retry_backoff_seconds=0):
    return RentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=token_store or InMemoryTokenStore(),
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )


def make_async_client(handler, *, token_store=None, max_retries=0, retry_backoff_seconds=0):
    return AsyncRentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=token_store or InMemoryTokenStore(),
        max_retries=max_retries,
        retry_backoff_seconds=retry_backoff_seconds,
    )


def test_client_context_manager_closes_and_authentication_validation():
    closed = False

    def handler(request):
        return httpx.Response(200, json={"not": "a token"})

    client = make_sync_client(handler)
    original_close = client._client.close

    def close():
        nonlocal closed
        closed = True
        original_close()

    client._client.close = close
    with pytest.raises(RentManagerTransportError, match="API token"):
        client.authenticate(force=True)
    with client as active_client:
        assert active_client is client

    assert closed is True


def test_client_auth_helpers_and_plain_text_decoding():
    seen = []

    def handler(request):
        body = request.content.decode("utf-8") if request.content else ""
        seen.append((request.method, request.url.path, dict(request.url.params), body))
        if request.url.path == "/Authentication/AuthorizeToken":
            return httpx.Response(200, text="authorized")
        if request.url.path == "/Authentication/ChangeLocation":
            return httpx.Response(204)
        if request.url.path == "/Raw/Text":
            return httpx.Response(200, text="plain text")
        if request.url.path == "/Actions/Run":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/Uploads":
            return httpx.Response(200, json={"uploaded": True})
        return httpx.Response(404, json={"DeveloperMessage": request.url.path})

    client = make_sync_client(handler, token_store=InMemoryTokenStore("cached-token"))

    assert client.authorize_token("external-token") == "authorized"
    assert client.change_location(12) == {}
    assert client.location_id == 12
    assert client.get("/Raw/Text") == "plain text"
    assert client.action("Actions/Run", {"Run": True}) == {"ok": True}
    assert client.post_multipart("Uploads", files={"file": ("a.txt", b"a")}) == {"uploaded": True}
    assert seen[0] == ("POST", "/Authentication/AuthorizeToken", {"token": "external-token"}, "")
    assert seen[1][2] == {"locationID": "12"}


def test_client_retries_transport_and_status_failures():
    transport_attempts = 0

    def flaky_transport(request):
        nonlocal transport_attempts
        transport_attempts += 1
        if transport_attempts == 1:
            raise httpx.ConnectError("temporary outage", request=request)
        return httpx.Response(200, json="token-after-retry")

    client = make_sync_client(flaky_transport, max_retries=1)

    assert client.authenticate(force=True) == "token-after-retry"

    status_attempts = 0

    def flaky_status(request):
        nonlocal status_attempts
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="token")
        status_attempts += 1
        if status_attempts == 1:
            return httpx.Response(503, json={"DeveloperMessage": "busy"})
        return httpx.Response(200, json=[{"TenantID": 1}])

    client = make_sync_client(flaky_status, max_retries=1)

    assert client.tenants.list()[0].TenantID == 1
    assert status_attempts == 2


def test_client_cached_authenticate_iter_pages_limit_and_no_attempt_guard():
    client = make_sync_client(lambda request: httpx.Response(500), token_store=InMemoryTokenStore("cached-token"))
    assert client.authenticate() == "cached-token"

    page_calls = []

    def paged(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="token")
        page_calls.append(dict(request.url.params))
        return httpx.Response(
            200,
            json=[{"OwnerID": int(request.url.params["pagenumber"])}],
            headers={"Link": '<https://sampleco.api.rentmanager.com/Owners?pagenumber=2>; rel="next"'},
        )

    client = make_sync_client(paged)
    pages = list(client.iter_pages("Owners", page_size=1, max_pages=1))
    assert [page.data[0]["OwnerID"] for page in pages] == [1]
    assert page_calls == [{"pagenumber": "1", "pagesize": "1"}]

    client.max_retries = -1
    with pytest.raises(RentManagerTransportError, match="Request failed"):
        client._request_raw("GET", "NeverSent")


def test_client_transport_error_after_retries_raises_transport_error():
    def handler(request):
        raise httpx.ConnectError("offline", request=request)

    client = make_sync_client(handler, max_retries=1)

    with pytest.raises(RentManagerTransportError, match="offline"):
        client.authenticate(force=True)


@pytest.mark.asyncio
async def test_async_client_context_auth_helpers_reauth_and_retry():
    token_responses = iter(["old-token", "new-token"])
    tenant_attempts = []

    async def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json=next(token_responses))
        if request.url.path == "/Authentication/AuthorizeToken":
            return httpx.Response(200, text="async-authorized")
        if request.url.path == "/Authentication/ChangeLocation":
            return httpx.Response(204)
        tenant_attempts.append(request.headers.get("X-RM12Api-ApiToken"))
        if len(tenant_attempts) == 1:
            return httpx.Response(401, json={"DeveloperMessage": "expired"})
        return httpx.Response(200, json=[{"TenantID": 2}])

    client = make_async_client(handler)
    async with client as active_client:
        assert active_client is client
        assert await client.authorize_token("external-token") == "async-authorized"
        assert await client.change_location(22) == {}
        tenants = await client.tenants.list()

    assert client.location_id == 22
    assert tenants[0].TenantID == 2
    assert tenant_attempts == ["old-token", "new-token"]


@pytest.mark.asyncio
async def test_async_client_cached_token_methods_and_error_branches():
    seen = []

    async def handler(request):
        seen.append((request.method, request.url.path, request.headers.get("X-RM12Api-ApiToken")))
        if request.url.path == "/Raw/Text":
            return httpx.Response(200, text="async text")
        if request.url.path == "/Items":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/Uploads":
            return httpx.Response(200, json={"uploaded": True})
        return httpx.Response(404, json={"DeveloperMessage": "missing"})

    client = make_async_client(handler, token_store=InMemoryTokenStore("cached-token"))

    assert await client.get("Raw/Text") == "async text"
    assert await client.post("Items", json={"x": 1}) == {"ok": True}
    assert await client.delete("Items", json=[1]) == {"ok": True}
    assert await client.action("Items", {"x": 2}) == {"ok": True}
    assert await client.post_multipart("Uploads", files={"file": ("a.txt", b"a")}) == {"uploaded": True}
    with pytest.raises(RentManagerNotFoundError):
        await client.get("Missing")
    await client.aclose()

    assert all(token == "cached-token" for _, _, token in seen)


@pytest.mark.asyncio
async def test_async_client_retries_and_reports_transport_error():
    attempts = 0

    async def flaky(request):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("temporary async outage", request=request)
        return httpx.Response(200, json="async-token")

    client = make_async_client(flaky, max_retries=1)

    assert await client.authenticate(force=True) == "async-token"
    await client.aclose()

    async def always_fails(request):
        raise httpx.ConnectError("async offline", request=request)

    client = make_async_client(always_fails, max_retries=1)

    with pytest.raises(RentManagerTransportError, match="async offline"):
        await client.authenticate(force=True)
    await client.aclose()


@pytest.mark.asyncio
async def test_async_client_cached_authenticate_retry_status_and_no_attempt_guard():
    client = make_async_client(lambda request: httpx.Response(500), token_store=InMemoryTokenStore("async-cached"))
    assert await client.authenticate() == "async-cached"
    await client.aclose()

    attempts = 0

    async def flaky_status(request):
        nonlocal attempts
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="token")
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, json={"DeveloperMessage": "busy"})
        return httpx.Response(200, json=[{"TenantID": 3}])

    client = make_async_client(flaky_status, max_retries=1)
    tenants = await client.tenants.list()
    assert tenants[0].TenantID == 3
    assert attempts == 2

    client.max_retries = -1
    with pytest.raises(RentManagerTransportError, match="Request failed"):
        await client._request_raw("GET", "NeverSent")
    await client.aclose()


@pytest.mark.asyncio
async def test_async_client_rejects_missing_auth_token_and_stops_iter_pages_at_limit():
    def bad_auth(request):
        return httpx.Response(200, json={"Token": ""})

    client = make_async_client(bad_auth)
    with pytest.raises(RentManagerTransportError, match="API token"):
        await client.authenticate(force=True)
    await client.aclose()

    async def paged(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="token")
        return httpx.Response(
            200,
            json=[{"OwnerID": int(request.url.params["pagenumber"])}],
            headers={"Link": '<https://sampleco.api.rentmanager.com/Owners?pagenumber=2>; rel="next"'},
        )

    client = make_async_client(paged)
    pages = []
    async for page in client.iter_pages("Owners", page_size=1, max_pages=1):
        pages.append(page)
    await client.aclose()

    assert [page.data[0]["OwnerID"] for page in pages] == [1]


def test_query_helpers_cover_aliases_errors_and_save_option_shapes():
    assert RQL.ne("Name", "Ada") == "Name,ne,Ada"
    assert RQL.ni("TenantID", [1, 2]) == "TenantID,ni,(1,2)"
    assert RQL.sw("Name", "A") == "Name,sw,A"
    assert RQL.ew("Name", "z") == "Name,ew,z"
    assert RQL.le("Amount", 10) == "Amount,le,10"
    assert RQL.gt("Amount", 10) == "Amount,gt,10"
    assert RQL.bt("Amount", 1, 3) == "Amount,bt,(1,3)"
    assert RQL.gtn("ClosedDate", None) == "ClosedDate,gtn,null"
    assert RQL.gen("Amount", 1) == "Amount,gen,1"
    assert RQL.ltn("ClosedDate", None) == "ClosedDate,ltn,null"
    assert RQL.len("Amount", 1) == "Amount,len,1"
    assert RQL.hv("CustomField") == "CustomField,hv,"
    assert (
        QueryParams(fields="Name", save_options="ValidateOnly,true").to_params()["SaveOptions"] == "ValidateOnly,true"
    )
    assert QueryParams(save_options=["ValidateOnly,true", "SkipAutomation,false"]).to_params()["SaveOptions"] == (
        "ValidateOnly,true;SkipAutomation,false"
    )

    with pytest.raises(ValueError, match="Unsupported RQL operator"):
        RQL.filter("Name", "bad", "Ada")
    with pytest.raises(ValueError, match="non-empty string"):
        RQL.eq("", "Ada")


def test_pagination_and_token_store_edge_cases(tmp_path):
    links = parse_link_header(
        '<https://example.test/a?page=2>; rel="next", <https://example.test/a?page=5>; rel="last", bad-section'
    )
    assert links == {
        "next": "https://example.test/a?page=2",
        "last": "https://example.test/a?page=5",
    }
    assert total_results_from_headers({"x-total-results": "41"}) == 41
    assert total_results_from_headers({"X-Total-Results": "many"}) is None

    store = FileTokenStore(tmp_path / "missing" / "token.json")
    assert store.load() is None
    store.path.parent.mkdir(parents=True)
    store.path.write_text("{bad json", encoding="utf-8")
    assert store.load() is None
    store.path.write_text('{"token": "   "}', encoding="utf-8")
    assert store.load() is None
    store.clear()
    store.clear()


def test_error_model_parses_text_non_dict_nested_and_status_mapping():
    text_response = httpx.Response(500, text="server exploded", request=httpx.Request("GET", "https://x.test"))
    assert parse_error_model(text_response).message == "server exploded"
    assert isinstance(error_from_response(text_response), RentManagerServerError)

    scalar_response = httpx.Response(418, json=["bad"], request=httpx.Request("POST", "https://x.test/things"))
    scalar_error = error_from_response(scalar_response)
    assert isinstance(scalar_error, RentManagerAPIError)
    assert scalar_error.method == "POST"
    assert scalar_error.url == "https://x.test/things"
    assert str(scalar_error) == "['bad']"

    nested_response = httpx.Response(
        401,
        json={"error": {"message": "nested auth failure"}},
        request=httpx.Request("GET", "https://x.test/private"),
    )
    nested_error = error_from_response(nested_response)
    assert isinstance(nested_error, RentManagerAuthError)
    assert str(nested_error) == "nested auth failure"


class Widget(BaseModel):
    WidgetID: int | None = None


@pytest.mark.asyncio
async def test_resource_coercion_child_methods_and_async_awaitables():
    class FakeAsyncClient:
        def __init__(self):
            self.calls = []

        async def get(self, path, **query):
            self.calls.append(("GET", path, query))
            return {"WidgetID": 1}

        async def post(self, path, json=None, **query):
            self.calls.append(("POST", path, json, query))
            return [{"WidgetID": 2}]

        def paginate(self, path, **query):
            self.calls.append(("PAGINATE", path, query))
            return "page"

        def iter_pages(self, path, **query):
            self.calls.append(("ITER", path, query))
            return iter(["page"])

    fake = FakeAsyncClient()
    resource = Resource(fake, path="Widgets", model=Widget)

    assert await resource.list(filter="WidgetID,eq,1") == Widget(WidgetID=1)
    assert await resource.create({"WidgetID": 2}) == [Widget(WidgetID=2)]
    assert resource.paginate(page_size=10) == "page"
    assert list(resource.iter_pages(page_size=10)) == ["page"]

    raw_resource = Resource(fake, path="RawWidgets", model=None)
    assert await raw_resource.list() == {"WidgetID": 1}
    assert resource._coerce("raw", Widget) == "raw"


def test_seeded_resource_child_methods_cover_expected_paths():
    calls = []

    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="token")
        calls.append((request.method, request.url.path, dict(request.url.params)))
        return httpx.Response(200, json=[{"ID": 1, "Name": "ok"}])

    client = make_sync_client(handler)

    client.owners.history(1)
    client.owners.payments(1)
    client.owners.charges(1)
    client.owners.contact(1)
    client.tenants.history(2)
    client.tenants.contacts(2)
    client.tenants.leases(2)
    client.tenants.create_recurring_charge(2, {"Amount": 1})
    client.tenants.user_defined_values(2)
    client.tenants.update_user_defined_values(2, [{"Value": "x"}])
    client.tenants.user_defined_fields(2)
    client.tenants.upload_user_defined_value_attachment(2, 9, b"file", "note.txt", Note="hello")
    client.prospects.history(3)
    client.prospects.contacts(3)
    client.vendors.history(4)
    client.vendors.transactions(4)
    client.vendors.contacts(4)
    client.properties.units(5)
    client.units.leases(6)
    client.units.user_defined_values(6)
    client.units.unlink_amenities(6, 88)
    client.users.current_user()
    client.service_manager.issues.link_unit(7, 66)
    client.service_manager.issues.add_history(7, {"Note": "called"})
    client.service_manager.issues.properties(7)
    client.service_manager.issues.attachments(7)
    client.service_manager.issues.files(7)
    client.service_manager.issues.documents(7)
    client.service_manager.issues.line_items(7)
    client.service_manager.issues.add_line_items(7, [{"Description": "labor"}])
    client.service_manager.issues.user_defined_values(7)
    client.service_manager.issues.update_user_defined_values(7, [{"Value": "x"}])
    client.service_manager.issues.user_defined_fields(7)
    client.service_manager.issues.upload_attachment(7, files={"file": ("a.txt", b"a")})
    client.service_manager.issues.upload_signature_file(7, files={"file": ("sig.png", b"s")})

    paths = [path for _, path, _ in calls]
    assert "/Owners/1/History" in paths
    assert "/Tenants/2/UploadUserDefinedValueAttachment" in paths
    assert "/Units/6/UnLinkAmenities" in paths
    assert "/Users/CurrentUser" in paths
    assert "/ServiceManagerIssues/7/UploadSignatureFile" in paths
    assert ("POST", "/ServiceManagerIssues/7/LinkUnit", {"unitID": "66"}) in calls


def test_email_lookup_empty_nested_model_and_dedupe_fallback():
    class EmailRecord(BaseModel):
        Name: str
        Nested: dict[str, object]

    assert lookup_by_email(object(), "") == {"sender_email": "", "total_matches": 0, "matches": []}

    class FakeResource:
        def __init__(self, rows):
            self.rows = rows

        def list(self):
            return self.rows

    class FakeClient:
        owners = FakeResource([EmailRecord(Name="Ada", Nested={"Emails": ["TARGET@example.com"]})])
        tenants = FakeResource([{"Name": "No id", "Email": "target@example.com"}])
        prospects = FakeResource([{"Name": "No id", "Email": "target@example.com"}])
        vendors = FakeResource([])
        contacts = FakeResource([{"ContactID": 5, "Email": "target@example.com"}])

    result = lookup_by_email(FakeClient(), "target@example.com", include_contacts=False)

    assert result["total_matches"] == 2
    assert result["matches"][0]["identity"] == {"Name": "Ada"}
    assert result["matches"][1]["record"]["Name"] == "No id"


def test_email_lookup_nested_dict_and_list_helpers():
    class FakeResource:
        def __init__(self, rows):
            self.rows = rows

        def list(self):
            return self.rows

    class FakeClient:
        owners = FakeResource([])
        tenants = FakeResource([])
        prospects = FakeResource([{"Name": "Nested", "Contacts": [{"Email": "target@example.com"}]}])
        vendors = FakeResource([])
        contacts = FakeResource([])

    result = lookup_by_email(FakeClient(), "target@example.com")

    assert result["total_matches"] == 1
    assert result["matches"][0]["entity"] == "Prospect"


def test_models_installers_cover_existing_model_skip_branches():
    rm_models._install_accounting_models()
    rm_models._install_applications_leasing_models()

    assert rm_models.ChargeType.model_fields["ChargeTypeID"]
    assert rm_models.Screening.model_fields["ScreeningID"]


def test_ticket_datetime_and_export_edge_cases(tmp_path, monkeypatch):
    assert ticket_workflow.parse_ticket_datetime(None) == datetime.min.replace(tzinfo=timezone.utc)
    assert ticket_workflow.parse_ticket_datetime("") == datetime.min.replace(tzinfo=timezone.utc)
    aware = datetime(2026, 4, 25, tzinfo=timezone.utc)
    assert ticket_workflow.parse_ticket_datetime(aware) is aware
    assert ticket_workflow.parse_ticket_datetime("not a date") == datetime.min.replace(tzinfo=timezone.utc)
    assert ticket_workflow.parse_ticket_datetime("2026-04-25T01:02:03Z").tzinfo is not None
    assert (
        ticket_workflow.get_newest_service_tickets(type("C", (), {"iter_pages": lambda *a, **k: []})(), limit=-1) == []
    )
    assert ticket_workflow._extract_ticket_id([{"ID": 81}]) == 81

    class ExportClient:
        def iter_pages(self, *args, **kwargs):
            yield type(
                "PageLike",
                (),
                {
                    "data": [
                        {"ID": 81, "CreateDate": "2026-04-23T09:00:00"},
                        {"Title": "missing id", "CreateDate": "2026-04-24T09:00:00"},
                    ]
                },
            )()

        def get(self, endpoint, params=None):
            if endpoint == "ServiceManagerIssues/81":
                return {
                    "ServiceManagerIssueID": 81,
                    "Title": "Nested id",
                    "PropertyID": "bad",
                    "UnitID": True,
                    "TenantID": 4,
                    "Attachments": [{"Name": "no-id.pdf"}],
                }
            if endpoint == "Tenants/4":
                return {"TenantID": 4}
            return []

        def download_bytes(self, endpoint):
            raise AssertionError(endpoint)

    monkeypatch.delenv("RM_TICKET_DOWNLOAD_ENDPOINT_TEMPLATES", raising=False)
    manifest = ticket_workflow.export_newest_service_ticket_details(ExportClient(), limit=2, export_root=tmp_path)

    assert manifest["ticket_count"] == 2
    ticket_with_id = next(ticket for ticket in manifest["tickets"] if ticket["ticket_id"] == 81)
    ticket_without_id = next(ticket for ticket in manifest["tickets"] if ticket["ticket_id"] is None)
    assert ticket_with_id["details"]["downloads"][0]["attempts"][0]["error"] == "Missing file id."
    assert ticket_without_id["errors"][0]["error"] == "Unable to determine ticket id."


def test_ticket_detail_fallback_non_dict_issue_and_collection_shapes(tmp_path):
    class ModelLike:
        def model_dump(self, exclude_none=True):
            return {"FileID": 91, "FileName": "model.pdf"}

    class DetailClient:
        def __init__(self):
            self.calls = []

        def get(self, endpoint, params=None):
            self.calls.append((endpoint, params))
            if endpoint == "ServiceManagerIssues/91" and params is not None:
                return None
            if endpoint == "ServiceManagerIssues/91":
                return "plain issue"
            if endpoint == "ServiceManagerIssues/91/Attachments":
                return {"FileID": 92, "FileName": "dict.pdf"}
            return []

        def download_bytes(self, endpoint):
            return b"file"

    details = ticket_workflow.get_service_ticket_details(
        DetailClient(),
        91,
        export_dir=tmp_path / "ticket-91",
        download_attachments=False,
    )

    assert details["issue"] == "plain issue"
    assert details["attachments"] == {"FileID": 92, "FileName": "dict.pdf"}
    assert ticket_workflow._attachment_rows({"attachments": ModelLike(), "files": {"FileID": 93}}) == [{"FileID": 93}]
    assert ticket_workflow._jsonable(ModelLike()) == {"FileID": 91, "FileName": "model.pdf"}
    assert (tmp_path / "ticket-91" / "details.json").exists()


def test_ticket_attachment_helpers_nested_ids_filenames_and_path_safety(tmp_path, monkeypatch):
    monkeypatch.setenv("RM_TICKET_DOWNLOAD_ENDPOINT_TEMPLATES", "Files/{file_id},Documents/{file_id}")
    assert ticket_workflow._download_endpoint_templates() == ["Files/{file_id}", "Documents/{file_id}"]
    assert ticket_workflow._extract_file_id({"nested": [{"DocumentId": "77"}]}) == 77
    assert ticket_workflow._extract_file_id(["bad", {"Id": 78}]) == 78
    assert ticket_workflow._attachment_filename({"Title": "bad:name?.pdf"}, None) == "bad_name_.pdf"
    assert ticket_workflow._attachment_filename({}, 79) == "ticket-file-79"
    assert ticket_workflow._attachment_filename({}, None) == "ticket-file-unknown"

    directory = tmp_path / "attachments"
    directory.mkdir()
    (directory / "invoice.pdf").write_text("exists", encoding="utf-8")
    assert ticket_workflow._unique_path(directory, "invoice.pdf").name == "invoice-2.pdf"
    with pytest.raises(ValueError, match="outside export directory"):
        ticket_workflow._unique_path(directory, "../escape.txt")


def test_ticket_create_and_update_helpers_build_payloads():
    class Issues:
        def __init__(self):
            self.calls = []

        def create(self, payload):
            self.calls.append(("create", payload))
            return payload

        def update(self, issue_id, payload):
            self.calls.append(("update", issue_id, payload))
            return payload

    class Client:
        def __init__(self):
            self.service_manager = type("ServiceManager", (), {"issues": Issues()})()

    client = Client()

    created = ticket_workflow.create_service_ticket(
        client,
        title="Broken sink",
        description="Leaks",
        property_id=1,
        unit_id=2,
        tenant_id=3,
        vendor_id=4,
        status_id=5,
        category_id=6,
        line_items=[{"Description": "Labor"}],
        extra={"Custom": "yes"},
    )
    updated = ticket_workflow.update_ticket_line_items(
        client,
        issue_id=99,
        line_items=[{"Description": "Parts"}],
        note="approved",
    )

    assert created["IsClosed"] is False
    assert created["PropertyID"] == 1
    assert created["LineItems"] == [{"Description": "Labor"}]
    assert created["Custom"] == "yes"
    assert updated == {"LineItems": [{"Description": "Parts"}], "NoteText": "approved"}
