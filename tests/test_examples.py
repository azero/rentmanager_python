from rentmanager_api import Page
from examples.newest_service_tickets import get_newest_service_tickets


class RecordingResource:
    def __init__(self, rows=None, item=None):
        self.rows = rows or []
        self.item = item if item is not None else {}
        self.calls = []

    def list(self, **query):
        self.calls.append(("list", query))
        return self.rows

    def get(self, item_id, **query):
        self.calls.append(("get", item_id, query))
        return self.item


class RecordingPropertiesResource(RecordingResource):
    def __init__(self, rows=None, item=None, units=None):
        super().__init__(rows=rows, item=item)
        self.unit_rows = units or []

    def units(self, property_id, **query):
        self.calls.append(("units", property_id, query))
        return self.unit_rows


class RecordingTenantsResource(RecordingResource):
    def __init__(
        self,
        rows=None,
        item=None,
        contacts=None,
        leases=None,
        addresses=None,
        transactions=None,
        recurring_charges=None,
        user_defined_values=None,
        history=None,
    ):
        super().__init__(rows=rows, item=item)
        self.contact_rows = contacts or []
        self.lease_rows = leases or []
        self.address_rows = addresses or []
        self.transaction_rows = transactions or []
        self.recurring_charge_rows = recurring_charges or []
        self.user_defined_value_rows = user_defined_values or []
        self.history_rows = history or []

    def contacts(self, tenant_id, **query):
        self.calls.append(("contacts", tenant_id, query))
        return self.contact_rows

    def leases(self, tenant_id, **query):
        self.calls.append(("leases", tenant_id, query))
        return self.lease_rows

    def addresses(self, tenant_id, **query):
        self.calls.append(("addresses", tenant_id, query))
        return self.address_rows

    def transactions(self, tenant_id, **query):
        self.calls.append(("transactions", tenant_id, query))
        return self.transaction_rows

    def recurring_charges(self, tenant_id, **query):
        self.calls.append(("recurring_charges", tenant_id, query))
        return self.recurring_charge_rows

    def user_defined_values(self, tenant_id, **query):
        self.calls.append(("user_defined_values", tenant_id, query))
        return self.user_defined_value_rows

    def history(self, tenant_id, **query):
        self.calls.append(("history", tenant_id, query))
        return self.history_rows


class SequencedResource:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def list(self, **query):
        self.calls.append(("list", query))
        if self.responses:
            return self.responses.pop(0)
        return []


class FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def iter_pages(self, endpoint, **query):
        self.calls.append((endpoint, query))
        yield from self.pages


def test_get_newest_service_tickets_sorts_created_dates_across_pages():
    client = FakeClient(
        [
            Page(
                data=[
                    {"ServiceManagerIssueID": 1, "Title": "older", "CreateDate": "2026-04-22T09:00:00"},
                    {"ServiceManagerIssueID": 2, "Title": "newest", "CreateDate": "2026-04-24T09:00:00"},
                ],
                status_code=200,
                headers={},
                page_number=1,
                page_size=2,
                total_results=None,
                links={"next": "page=2"},
            ),
            Page(
                data=[
                    {"ServiceManagerIssueID": 3, "Title": "middle", "DateCreated": "2026-04-23T09:00:00"},
                    {"ServiceManagerIssueID": 4, "Title": "undated"},
                ],
                status_code=200,
                headers={},
                page_number=2,
                page_size=2,
                total_results=None,
                links={},
            ),
        ]
    )

    tickets = get_newest_service_tickets(client, limit=3, page_size=2)

    assert [ticket["Title"] for ticket in tickets] == ["newest", "middle", "older"]
    assert client.calls == [
        (
            "ServiceManagerIssues",
            {
                "fields": [
                    "ServiceManagerIssueID",
                    "IssueID",
                    "TicketID",
                    "Title",
                    "IsClosed",
                    "StatusID",
                    "CategoryID",
                    "CreateDate",
                    "DateCreated",
                    "IssueDate",
                    "UpdateDate",
                ],
                "page_size": 2,
                "max_pages": None,
            },
        )
    ]


def test_shared_helpers_parse_env_and_normalize_records(monkeypatch):
    from pydantic import BaseModel

    from examples._shared import as_records, optional_int, required_int

    class Row(BaseModel):
        RowID: int
        Name: str

    monkeypatch.setenv("RM_EXAMPLE_LIMIT", "12")
    monkeypatch.setenv("RM_EXAMPLE_REQUIRED_ID", "99")

    assert optional_int("RM_EXAMPLE_LIMIT") == 12
    assert optional_int("RM_EXAMPLE_MISSING", default=5) == 5
    assert required_int("RM_EXAMPLE_REQUIRED_ID") == 99
    assert as_records([Row(RowID=1, Name="Ada"), {"RowID": 2, "Name": "Lin"}]) == [
        {"RowID": 1, "Name": "Ada"},
        {"RowID": 2, "Name": "Lin"},
    ]


def test_shared_helpers_load_env_file_without_overriding_shell_values(tmp_path, monkeypatch):
    import os

    from examples._shared import load_env_file, optional_int

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# Rent Manager example credentials",
                "RM_CORP_ID=sampleco",
                'RM_USERNAME="api-user"',
                "RM_PASSWORD='secret value'",
                "export RM_LOCATION_ID=3",
                "RM_KEEP_EXISTING=from-file",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("RM_CORP_ID", raising=False)
    monkeypatch.delenv("RM_USERNAME", raising=False)
    monkeypatch.delenv("RM_PASSWORD", raising=False)
    monkeypatch.delenv("RM_LOCATION_ID", raising=False)
    monkeypatch.setenv("RM_KEEP_EXISTING", "from-shell")

    loaded = load_env_file(env_file)

    assert loaded == {
        "RM_CORP_ID": "sampleco",
        "RM_USERNAME": "api-user",
        "RM_PASSWORD": "secret value",
        "RM_LOCATION_ID": "3",
    }
    assert "RM_KEEP_EXISTING" not in loaded
    assert optional_int("RM_LOCATION_ID") == 3
    assert os.environ["RM_KEEP_EXISTING"] == "from-shell"


def test_build_client_loads_default_env_file(tmp_path, monkeypatch):
    from examples._shared import build_client

    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "RM_CORP_ID=sampleco",
                "RM_USERNAME=api-user",
                "RM_PASSWORD=secret",
                "RM_LOCATION_ID=5",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    for name in ("RM_CORP_ID", "RM_USERNAME", "RM_PASSWORD", "RM_LOCATION_ID"):
        monkeypatch.delenv(name, raising=False)

    client = build_client(token_path=str(tmp_path / "token.json"))

    assert client.corp_id == "sampleco"
    assert client.username == "api-user"
    assert client.password == "secret"
    assert client.location_id == 5
    client.close()


def test_property_people_lookup_builds_expected_property_queries():
    from examples.property_people_lookup import lookup_property_people, tenant_filters_for_property

    client = type("Client", (), {})()
    client.properties = RecordingPropertiesResource(
        item={"PropertyID": 7, "Name": "Main", "PrimaryOwnerID": 42},
        units=[{"UnitID": 3, "PropertyID": 7, "Name": "101"}],
    )
    client.owners = RecordingResource(item={"OwnerID": 42, "Name": "Owner"})
    client.tenants = RecordingResource(rows=[{"TenantID": 11, "PropertyID": 7, "IsActive": True}])
    client.leases = RecordingResource(rows=[{"LeaseID": 22, "PropertyID": 7, "TenantID": 11}])

    result = lookup_property_people(client, 7)

    assert tenant_filters_for_property(7) == ["PropertyID,eq,7", "IsActive,eq,true"]
    assert result["property"]["PropertyID"] == 7
    assert result["owner"]["OwnerID"] == 42
    assert result["tenants"][0]["TenantID"] == 11
    assert client.properties.calls[0][0] == "get"
    assert client.properties.calls[1][0] == "units"
    assert client.tenants.calls[0] == (
        "list",
        {
            "fields": [
                "TenantID",
                "TenantDisplayID",
                "Name",
                "FirstName",
                "LastName",
                "Email",
                "PropertyID",
                "UnitID",
                "IsActive",
                "CurrentBalance",
            ],
            "filters": ["PropertyID,eq,7", "IsActive,eq,true"],
            "page_size": 1000,
        },
    )


def test_owner_property_lookup_filters_properties_by_primary_owner():
    from examples.owner_property_lookup import lookup_owner_properties, property_filters_for_owner

    client = type("Client", (), {})()
    client.owners = RecordingResource(item={"OwnerID": 42, "Name": "Owner"})
    client.properties = RecordingResource(rows=[{"PropertyID": 7, "Name": "Main", "PrimaryOwnerID": 42}])

    result = lookup_owner_properties(client, 42, active_only=False)

    assert property_filters_for_owner(42, active_only=False) == ["PrimaryOwnerID,eq,42"]
    assert result["owner"]["OwnerID"] == 42
    assert result["properties"][0]["PrimaryOwnerID"] == 42
    assert client.properties.calls[0][1]["filters"] == ["PrimaryOwnerID,eq,42"]


def test_text_conversation_helpers_build_filters_and_outgoing_payload():
    from examples.text_conversations import (
        build_outgoing_text_payload,
        build_text_broadcast_batch_payload,
        conversation_filters,
        outgoing_text_filters,
    )

    assert conversation_filters(parent_type="Tenant", parent_id=11, phone_number="555") == [
        "ParentType,eq,Tenant",
        "ParentID,eq,11",
        "ExternalPhoneNumber,ct,555",
    ]
    assert outgoing_text_filters(parent_type="Tenant", parent_id=11, phone_number="555") == [
        "ParentType,eq,Tenant",
        "ParentID,eq,11",
        "PhoneNumber,ct,555",
    ]
    assert build_outgoing_text_payload(
        phone_number="+15551234567",
        message="Hello from the example",
        parent_type="Tenant",
        parent_id=11,
        history_category_id=5,
    ) == {
        "PhoneNumber": "+15551234567",
        "Message": "Hello from the example",
        "IsMMS": False,
        "ParentType": "Tenant",
        "ParentID": 11,
        "HistoryCategoryID": 5,
    }
    assert build_text_broadcast_batch_payload(
        phone_number="+15551234567",
        message="Hello from the example",
        parent_type="Tenant",
        parent_id=11,
        recipient_name="Ada Tenant",
        history_category_id=5,
    ) == {
        "MessageName": "Tenant text - Ada Tenant",
        "MessageDescription": "Sent from rentmanager_api.",
        "IsScheduledNow": True,
        "NDTBroadcastBatchDetails": [
            {
                "Name": "Ada Tenant",
                "PhoneNumber": "+15551234567",
                "ParentType": "Tenant",
                "ParentID": 11,
                "MessageText": "Hello from the example",
                "HistoryNote": "Hello from the example",
                "HistoryCategoryID": 5,
            }
        ],
    }


def test_read_text_conversations_queries_conversations_and_texts():
    from examples.text_conversations import read_text_conversations

    client = type("Client", (), {})()
    client.text_messaging_conversations = RecordingResource(
        rows=[{"ExternalPhoneNumber": "+15551234567", "ParentType": "Tenant", "ParentID": 11}]
    )
    client.outgoing_texts = RecordingResource(rows=[{"OutgoingTextID": 4, "ParentID": 11}])

    result = read_text_conversations(client, parent_type="Tenant", parent_id=11, limit=10)

    assert result["conversations"][0]["ParentID"] == 11
    assert result["outgoing_texts"][0]["OutgoingTextID"] == 4
    assert client.text_messaging_conversations.calls[0][1]["filters"] == [
        "ParentType,eq,Tenant",
        "ParentID,eq,11",
    ]
    assert client.outgoing_texts.calls[0][1]["page_size"] == 10


def test_tenant_text_sender_searches_tenants_and_discovers_text_numbers():
    from examples.tenant_text_sender import search_tenant_text_candidates

    client = type("Client", (), {})()
    client.tenants = RecordingTenantsResource(
        rows=[
            {"TenantID": 11, "Name": "Ada Tenant", "TenantDisplayID": "A11"},
            {"Name": None, "TenantDisplayID": None},
        ],
        contacts=[{"ContactID": 5, "Name": "Ada", "CellPhone": "(555) 123-4567"}],
    )
    client.text_messaging_conversations = RecordingResource(
        rows=[{"ExternalPhoneNumber": "+15559876543", "ParentType": "Tenant", "ParentID": 11}]
    )

    result = search_tenant_text_candidates(client, "Ada", page_size=5)

    assert result["query"] == "Ada"
    assert result["matches"][0]["tenant"]["TenantID"] == 11
    assert result["matches"][0]["display_name"] == "Ada Tenant"
    assert result["matches"][0]["phone_options"] == [
        {"phone_number": "+15559876543", "source": "conversation"},
        {"phone_number": "(555) 123-4567", "source": "contact:5"},
    ]
    assert len(result["matches"]) == 1
    assert client.tenants.calls[0][1]["filters"] == ["Name,ct,Ada"]
    assert client.text_messaging_conversations.calls[0][1]["filters"] == [
        "ParentType,eq,Tenant",
        "ParentID,eq,11",
    ]


def test_tenant_text_sender_parser_does_not_prefill_phone_or_message_from_shared_example_env(monkeypatch, tmp_path):
    from examples.tenant_text_sender import _parser

    monkeypatch.setenv("RM_ENV_FILE", str(tmp_path / "missing.env"))
    monkeypatch.setenv("RM_EXAMPLE_PHONE_NUMBER", "+15551234567")
    monkeypatch.setenv("RM_EXAMPLE_TEXT_MESSAGE", "Hello from rentmanager_api.")

    args = _parser().parse_args(["Ada"])

    assert args.phone_number is None
    assert args.message is None


def test_tenant_text_sender_sends_text_broadcast_batch_to_selected_tenant():
    from examples.tenant_text_sender import send_text_to_tenant

    class RecordingTextClient:
        def __init__(self):
            self.calls = []

        def post(self, endpoint, *, json=None, params=None):
            self.calls.append(("post", endpoint, json, params))
            payload = json[0]
            return [{"NDTTextBroadcastBatchID": 99, **payload}]

    client = RecordingTextClient()

    result = send_text_to_tenant(
        client,
        tenant={"TenantID": 11, "Name": "Ada Tenant"},
        phone_number="5559876543",
        message="Your maintenance request is scheduled.",
        history_category_id=7,
    )

    assert result["created_text_broadcast_batch"][0]["NDTTextBroadcastBatchID"] == 99
    assert client.calls == [
        (
            "post",
            "NDTTextBroadcastBatches",
            [
                {
                    "MessageName": "Tenant text - Ada Tenant",
                    "MessageDescription": "Sent from rentmanager_api.",
                    "IsScheduledNow": True,
                    "NDTBroadcastBatchDetails": [
                        {
                            "Name": "Ada Tenant",
                            "PhoneNumber": "5559876543",
                            "ParentType": "Tenant",
                            "ParentID": 11,
                            "MessageText": "Your maintenance request is scheduled.",
                            "HistoryNote": "Your maintenance request is scheduled.",
                            "HistoryCategoryID": 7,
                        }
                    ],
                }
            ],
            {"embeds": "NDTBroadcastBatchDetails"},
        )
    ]


def test_tenant_text_sender_interactive_flow_selects_tenant_and_sends_message():
    from examples.tenant_text_sender import run_interactive

    class RecordingTextClient:
        def __init__(self):
            self.tenants = RecordingTenantsResource(
                rows=[{"TenantID": 11, "Name": "Ada Tenant", "TenantDisplayID": "A11"}],
            )
            self.text_messaging_conversations = RecordingResource(
                rows=[{"ExternalPhoneNumber": "+15559876543", "ParentType": "Tenant", "ParentID": 11}]
            )
            self.calls = []

        def post(self, endpoint, *, json=None, params=None):
            self.calls.append(("post", endpoint, json, params))
            payload = json[0]
            return [{"NDTTextBroadcastBatchID": 100, **payload}]

    client = RecordingTextClient()
    inputs = iter(["1", "Your maintenance request is scheduled.", "y"])

    result = run_interactive(client, name="Ada", input_func=lambda _prompt: next(inputs))

    assert result["created_text_broadcast_batch"][0]["NDTTextBroadcastBatchID"] == 100
    detail = client.calls[0][2][0]["NDTBroadcastBatchDetails"][0]
    assert detail["ParentType"] == "Tenant"
    assert detail["ParentID"] == 11
    assert detail["PhoneNumber"] == "+15559876543"
    assert detail["MessageText"] == "Your maintenance request is scheduled."


def test_query_cookbook_demonstrates_generic_list_get_and_pagination():
    from examples.query_cookbook import (
        generic_contains_search,
        list_active_tenants,
        paged_rows,
        tenant_with_embeds,
    )

    class CookbookClient:
        def __init__(self):
            self.tenants = RecordingResource(rows=[{"TenantID": 1}], item={"TenantID": 1})
            self.generic_calls = []

        def get(self, endpoint, **query):
            self.generic_calls.append((endpoint, query))
            return [{"ID": 1, "Name": "needle"}]

        def iter_pages(self, endpoint, **query):
            self.generic_calls.append((endpoint, query))
            yield Page(
                data=[{"ID": 1}],
                status_code=200,
                headers={},
                page_number=1,
                page_size=query["page_size"],
                total_results=None,
                links={},
            )

    client = CookbookClient()

    assert list_active_tenants(client)[0]["TenantID"] == 1
    assert tenant_with_embeds(client, 1)["TenantID"] == 1
    assert generic_contains_search(client, "Owners", "Name", "Smith")[0]["Name"] == "needle"
    assert paged_rows(client, "Owners", page_size=50) == [{"ID": 1}]
    assert client.tenants.calls[0][1]["filters"] == ["IsActive,eq,true"]
    assert client.tenants.calls[1][2]["embeds"] == ["Contacts", "Leases"]
    assert client.generic_calls[0] == (
        "Owners",
        {"fields": ["ID", "Name"], "filters": ["Name,ct,Smith"], "page_size": 100},
    )


def test_tenant_snapshot_collects_related_records_with_optional_history():
    from examples.tenant_snapshot import lookup_tenant_snapshot

    client = type("Client", (), {})()
    client.tenants = RecordingTenantsResource(
        item={"TenantID": 11, "Name": "Tenant"},
        contacts=[{"ContactID": 1, "Email": "tenant@example.com"}],
        leases=[{"LeaseID": 2, "TenantID": 11}],
        addresses=[{"Address": "100 Main"}],
        transactions=[{"TransactionID": 3, "TenantID": 11}],
        recurring_charges=[{"RecurringChargeID": 4, "TenantID": 11}],
        user_defined_values=[{"UserDefinedValueID": 5, "TenantID": 11}],
        history=[{"HistoryID": 6, "TenantID": 11}],
    )

    result = lookup_tenant_snapshot(client, 11, include_history=True, page_size=50)

    assert result["tenant"]["TenantID"] == 11
    assert result["contacts"][0]["ContactID"] == 1
    assert result["transactions"][0]["TransactionID"] == 3
    assert result["history"][0]["HistoryID"] == 6
    assert client.tenants.calls == [
        ("get", 11, {"fields": ["TenantID", "TenantDisplayID", "Name", "Email", "PropertyID", "UnitID", "IsActive"]}),
        ("contacts", 11, {"page_size": 50}),
        ("leases", 11, {"page_size": 50}),
        ("addresses", 11, {}),
        ("transactions", 11, {"page_size": 50}),
        ("recurring_charges", 11, {"page_size": 50}),
        ("user_defined_values", 11, {"page_size": 50}),
        ("history", 11, {"page_size": 50}),
    ]


def test_email_lookup_example_summarizes_matches():
    from examples.email_lookup import summarize_matches

    result = summarize_matches(
        {
            "sender_email": "target@example.com",
            "total_matches": 2,
            "matches": [
                {"entity": "Tenant", "identity": {"TenantID": 11, "Name": "Tenant"}, "record": {"ignored": True}},
                {"entity": "Owner", "identity": {"OwnerID": 42, "Name": "Owner"}, "record": {"ignored": True}},
            ],
        }
    )

    assert result == {
        "sender_email": "target@example.com",
        "total_matches": 2,
        "matches": [
            {"entity": "Tenant", "TenantID": 11, "Name": "Tenant"},
            {"entity": "Owner", "OwnerID": 42, "Name": "Owner"},
        ],
    }


def test_name_id_lookup_searches_selected_resource_fields_and_dedupes():
    from examples.name_id_lookup import normalize_search_types, search_filters_for_field, search_ids_by_name

    client = type("Client", (), {})()
    client.properties = SequencedResource(
        [
            [{"PropertyID": 7, "Name": "Main House", "ShortName": "Main", "PrimaryOwnerID": 42}],
            [{"PropertyID": 7, "Name": "Main House", "ShortName": "Main", "PrimaryOwnerID": 42}],
        ]
    )

    result = search_ids_by_name(client, "Main", search_types=["property"], page_size=25)

    assert normalize_search_types("property") == ["property"]
    assert search_filters_for_field("Name", "Main") == ["Name,ct,Main"]
    assert result == {
        "query": "Main",
        "search_types": ["property"],
        "matches": [
            {
                "type": "property",
                "id_field": "PropertyID",
                "id": 7,
                "name": "Main House",
                "PropertyID": 7,
                "ShortName": "Main",
                "PrimaryOwnerID": 42,
            }
        ],
    }
    assert client.properties.calls == [
        (
            "list",
            {
                "fields": ["PropertyID", "Name", "ShortName", "PrimaryOwnerID", "IsActive"],
                "filters": ["Name,ct,Main"],
                "page_size": 25,
            },
        ),
        (
            "list",
            {
                "fields": ["PropertyID", "Name", "ShortName", "PrimaryOwnerID", "IsActive"],
                "filters": ["ShortName,ct,Main"],
                "page_size": 25,
            },
        ),
    ]


def test_name_id_lookup_searches_all_supported_types():
    from examples.name_id_lookup import search_ids_by_name

    client = type("Client", (), {})()
    client.tenants = SequencedResource(
        [
            [{"TenantID": 11, "Name": "Ada Tenant", "PropertyID": 7, "UnitID": 3}],
            [],
            [],
            [],
        ]
    )
    client.properties = SequencedResource([[], []])
    client.owners = SequencedResource(
        [
            [{"OwnerID": 42, "Name": "Ada Owner", "Email": "owner@example.com"}],
            [],
            [],
            [],
        ]
    )

    result = search_ids_by_name(client, "Ada", search_types=["all"], page_size=10)

    assert [match["type"] for match in result["matches"]] == ["tenant", "owner"]
    assert result["matches"][0]["id"] == 11
    assert result["matches"][1]["id"] == 42


def test_name_id_lookup_skips_bad_request_search_fields():
    from rentmanager_api.errors import RentManagerBadRequestError

    from examples.name_id_lookup import NameSearchSpec, _search_one_type

    class BadRequestAfterFirstField:
        def __init__(self):
            self.calls = []

        def list(self, **query):
            self.calls.append(query)
            if len(self.calls) == 1:
                return [{"TenantID": 11, "Name": "Andrew Burton"}]
            raise RentManagerBadRequestError("The request is invalid.")

    client = type("Client", (), {})()
    client.tenants = BadRequestAfterFirstField()
    spec = NameSearchSpec(
        search_type="tenant",
        resource_attr="tenants",
        id_field="TenantID",
        search_fields=("Name", "TenantDisplayID"),
        fields=("TenantID", "Name", "TenantDisplayID"),
        name_fields=("Name", "TenantDisplayID"),
        summary_fields=("TenantID", "TenantDisplayID"),
    )

    assert _search_one_type(client, "Andrew Burton", spec, page_size=25) == [
        {
            "type": "tenant",
            "id_field": "TenantID",
            "id": 11,
            "name": "Andrew Burton",
            "TenantID": 11,
        }
    ]
