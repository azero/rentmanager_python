import json
import httpx
import pytest

from rentmanager_api import (
    FileTokenStore,
    InMemoryTokenStore,
    Page,
    RentManagerClient,
    RentManagerNotFoundError,
    RQL,
)


def make_client(handler, token_store=None):
    return RentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        location_id=7,
        transport=httpx.MockTransport(handler),
        token_store=token_store or InMemoryTokenStore(),
        max_retries=0,
    )


def json_response(status_code, payload, headers=None):
    return httpx.Response(status_code, json=payload, headers=headers or {})


def test_client_authenticates_and_sends_token_header():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path, request.headers.get("X-RM12Api-ApiToken")))
        if request.url.path == "/Authentication/AuthorizeUser":
            assert json.loads(request.read()) == {"Username": "user", "Password": "pass", "LocationID": 7}
            return json_response(200, "token-123")
        return json_response(200, [{"TenantID": 1, "Name": "Ada"}])

    client = make_client(handler)

    tenants = client.tenants.list(fields=["TenantID", "Name"])

    assert tenants[0].TenantID == 1
    assert seen == [
        ("POST", "/Authentication/AuthorizeUser", None),
        ("GET", "/Tenants", "token-123"),
    ]


def test_client_reauthenticates_once_after_401():
    token_responses = iter(["old-token", "new-token"])
    tenant_attempts = []

    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, next(token_responses))
        tenant_attempts.append(request.headers.get("X-RM12Api-ApiToken"))
        if len(tenant_attempts) == 1:
            return json_response(401, {"DeveloperMessage": "expired"})
        return json_response(200, [{"TenantID": 2}])

    client = make_client(handler)

    assert client.tenants.list()[0].TenantID == 2
    assert tenant_attempts == ["old-token", "new-token"]


def test_cached_token_is_reused_without_auth_request():
    seen_paths = []
    store = InMemoryTokenStore("cached-token")

    def handler(request):
        seen_paths.append(request.url.path)
        assert request.headers["X-RM12Api-ApiToken"] == "cached-token"
        return json_response(200, [{"OwnerID": 3}])

    client = make_client(handler, token_store=store)

    assert client.owners.list()[0].OwnerID == 3
    assert seen_paths == ["/Owners"]


def test_error_mapping_raises_not_found_with_error_model():
    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        return json_response(
            404,
            {"DeveloperMessage": "Record not found", "UserMessage": "Missing tenant"},
        )

    client = make_client(handler)

    with pytest.raises(RentManagerNotFoundError) as exc:
        client.tenants.get(999)

    assert exc.value.status_code == 404
    assert exc.value.developer_message == "Record not found"
    assert exc.value.user_message == "Missing tenant"


def test_paginate_and_iter_pages_use_headers_and_query_params():
    calls = []

    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        calls.append(dict(request.url.params))
        page_number = int(request.url.params["pagenumber"])
        headers = {
            "X-Total-Results": "3",
            "Link": '<https://sampleco.api.rentmanager.com/Tenants?pagenumber=2&pagesize=2>; rel="next"'
            if page_number == 1
            else "",
        }
        rows = [{"TenantID": 1}, {"TenantID": 2}] if page_number == 1 else [{"TenantID": 3}]
        return json_response(200, rows, headers=headers)

    client = make_client(handler)

    first = client.paginate("Tenants", page_number=1, page_size=2, filters=RQL.eq("IsActive", True))
    pages = list(client.iter_pages("Tenants", page_size=2, filters=RQL.eq("IsActive", True)))

    assert isinstance(first, Page)
    assert first.total_results == 3
    assert first.links["next"].endswith("pagenumber=2&pagesize=2")
    assert [row["TenantID"] for page in pages for row in page.data] == [1, 2, 3]
    assert calls == [
        {"filters": "IsActive,eq,true", "pagenumber": "1", "pagesize": "2"},
        {"filters": "IsActive,eq,true", "pagenumber": "1", "pagesize": "2"},
        {"filters": "IsActive,eq,true", "pagenumber": "2", "pagesize": "2"},
    ]


def test_file_token_store_round_trip(tmp_path):
    store = FileTokenStore(tmp_path / "token.json")

    store.save("abc")

    assert store.load() == "abc"
    store.clear()
    assert store.load() is None


def test_download_bytes_authenticates_and_returns_raw_content():
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path, request.headers.get("X-RM12Api-ApiToken")))
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        return httpx.Response(200, content=b"pdf-bytes", headers={"Content-Type": "application/pdf"})

    client = make_client(handler)

    content = client.download_bytes("Files/44")

    assert content == b"pdf-bytes"
    assert seen == [
        ("POST", "/Authentication/AuthorizeUser", None),
        ("GET", "/Files/44", "token-123"),
    ]


def test_download_bytes_uses_error_mapping():
    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        return json_response(404, {"DeveloperMessage": "Missing file"})

    client = make_client(handler)

    with pytest.raises(RentManagerNotFoundError) as exc:
        client.download_bytes("Files/404")

    assert exc.value.developer_message == "Missing file"
