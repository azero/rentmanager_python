from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from rentmanager_api.errors import RentManagerBadRequestError

from examples.landscaping_ticket_workflow import (
    WorkflowError,
    normalize_text,
    parse_price,
    payload_money,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" 2212   Feldman Ave ", "2212 feldman ave"),
        ("CRES Property MANAGEMENT", "cres property management"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_text_collapses_case_and_whitespace(raw, expected):
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("125", Decimal("125.00")),
        ("125.5", Decimal("125.50")),
        ("$1,250.75", Decimal("1250.75")),
    ],
)
def test_parse_price_accepts_currency_like_values(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "0", "-1", "$0.00"])
def test_parse_price_rejects_invalid_or_non_positive_values(raw):
    with pytest.raises(WorkflowError):
        parse_price(raw)


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (Decimal("125.00"), 125),
        (Decimal("125.50"), 125.5),
    ],
)
def test_payload_money_returns_json_serializable_numbers(amount, expected):
    assert payload_money(amount) == expected


from examples.landscaping_ticket_workflow import (
    FIXED_LOOKUPS,
    LookupCache,
    find_record_by_name,
    resolve_fixed_lookups,
)


class RecordingResource:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def list(self, **query):
        self.calls.append(query)
        return list(self.rows)


class BadFieldThenGoodResource:
    def __init__(self):
        self.calls = []

    def list(self, **query):
        self.calls.append(query)
        if query["filters"] == ["Username,ct,Andrew Burton"]:
            raise RentManagerBadRequestError("The request is invalid.")
        return [{"UserID": 7, "Name": "Andrew Burton", "Username": "example-user"}]


def test_lookup_cache_reads_and_writes_ids(tmp_path):
    cache_path = tmp_path / "lookup-cache.json"
    cache = LookupCache.load(cache_path)
    cache.set_entry(
        "status.completed",
        {
            "resource": "service_manager.statuses",
            "name": "Completed",
            "id_field": "ServiceManagerStatusID",
            "id": 3,
        },
    )
    cache.save()

    loaded = LookupCache.load(cache_path)

    assert loaded.get_id("status.completed") == 3


def test_find_record_by_name_skips_bad_request_fields():
    resource = BadFieldThenGoodResource()

    record = find_record_by_name(
        resource,
        display_name="Andrew Burton",
        id_field="UserID",
        name_fields=("Username", "Name"),
        fields=("UserID", "Username", "Name"),
        page_size=25,
    )

    assert record["UserID"] == 7
    assert resource.calls == [
        {"fields": ["UserID", "Username", "Name"], "filters": ["Username,ct,Andrew Burton"], "page_size": 25},
        {"fields": ["UserID", "Username", "Name"], "filters": ["Name,ct,Andrew Burton"], "page_size": 25},
    ]


def test_resolve_fixed_lookups_uses_cache_without_querying(tmp_path):
    cache = LookupCache.load(tmp_path / "lookup-cache.json")
    for lookup in FIXED_LOOKUPS:
        cache.set_entry(
            lookup.key,
            {
                "resource": lookup.resource_path,
                "name": lookup.display_name,
                "id_field": lookup.id_field,
                "id": 99,
            },
        )
    cache.save()
    client = type("Client", (), {})()

    resolved = resolve_fixed_lookups(client, cache=cache, refresh_cache=False, page_size=25)

    assert set(resolved) == {lookup.key for lookup in FIXED_LOOKUPS}
    assert all(value == 99 for value in resolved.values())


def test_resolve_fixed_lookups_queries_and_caches_missing_values(tmp_path):
    client = type("Client", (), {})()
    client.service_manager = type(
        "ServiceManager",
        (),
        {
            "categories": RecordingResource([{"ServiceManagerCategoryID": 1, "Name": "Property Wide"}]),
            "priorities": RecordingResource([{"ServiceManagerPriorityID": 2, "Name": "Low"}]),
            "statuses": RecordingResource([{"ServiceManagerStatusID": 3, "Name": "Completed"}]),
        },
    )()
    client.users = RecordingResource([{"UserID": 4, "Name": "Andrew Burton"}])
    client.vendors = RecordingResource([{"VendorID": 5, "Name": "Cres Property Management"}])
    client.inventory_items = RecordingResource([{"InventoryItemID": 6, "Name": "Landscaping"}])
    cache = LookupCache.load(tmp_path / "lookup-cache.json")

    resolved = resolve_fixed_lookups(client, cache=cache, refresh_cache=False, page_size=25)

    assert resolved == {
        "category.property_wide": 1,
        "priority.low": 2,
        "status.completed": 3,
        "user.andrew_burton": 4,
        "vendor.cres_property_management": 5,
        "item.landscaping": 6,
    }
    assert LookupCache.load(cache.path).get_id("item.landscaping") == 6


def test_find_record_by_name_raises_for_missing_exact_match():
    resource = RecordingResource([{"VendorID": 5, "Name": "Cres PM"}])

    with pytest.raises(WorkflowError, match="Cres Property Management"):
        find_record_by_name(
            resource,
            display_name="Cres Property Management",
            id_field="VendorID",
            name_fields=("Name",),
            fields=("VendorID", "Name"),
            page_size=25,
        )


def test_find_record_by_name_can_match_configured_alias():
    resource = RecordingResource([{"ServiceManagerStatusID": 5, "Name": "Complete"}])

    record = find_record_by_name(
        resource,
        display_name="Completed",
        search_names=("Completed", "Complete"),
        id_field="ServiceManagerStatusID",
        name_fields=("Name",),
        fields=("ServiceManagerStatusID", "Name"),
        page_size=25,
    )

    assert record["ServiceManagerStatusID"] == 5
    assert resource.calls == [
        {"fields": ["ServiceManagerStatusID", "Name"], "filters": ["Name,ct,Completed"], "page_size": 25},
        {"fields": ["ServiceManagerStatusID", "Name"], "filters": ["Name,ct,Complete"], "page_size": 25},
    ]


from examples.landscaping_ticket_workflow import (
    choose_property,
    property_display_address,
    resolve_property,
    search_property_candidates,
)


def test_property_display_address_prefers_street_fields():
    row = {
        "PropertyID": 10,
        "Name": "Feldman Rental",
        "ShortName": "Feldman",
        "StreetAddress": "2212 Feldman Ave",
    }

    assert property_display_address(row, fallback="entered") == "2212 Feldman Ave"


def test_choose_property_returns_single_exact_match_without_prompting():
    prompts = []
    rows = [
        {"PropertyID": 10, "Name": "2212 Feldman Ave"},
        {"PropertyID": 11, "Name": "2212 Feldman Ave Rear"},
    ]

    selected = choose_property(
        " 2212 feldman ave ",
        rows,
        input_func=lambda prompt: prompts.append(prompt) or "1",
        output_func=lambda line: None,
    )

    assert selected["PropertyID"] == 10
    assert prompts == []


def test_choose_property_prompts_when_multiple_partial_matches():
    printed = []
    rows = [
        {"PropertyID": 10, "Name": "2212 Feldman Ave"},
        {"PropertyID": 11, "Name": "2214 Feldman Ave"},
    ]

    selected = choose_property(
        "Feldman Ave",
        rows,
        input_func=lambda prompt: "2",
        output_func=printed.append,
    )

    assert selected["PropertyID"] == 11
    assert "1. 2212 Feldman Ave (PropertyID: 10)" in printed
    assert "2. 2214 Feldman Ave (PropertyID: 11)" in printed


def test_choose_property_raises_when_no_candidates():
    with pytest.raises(WorkflowError, match="No property matches"):
        choose_property("2212 Feldman Ave", [], input_func=lambda prompt: "1", output_func=lambda line: None)


def test_search_property_candidates_dedupes_and_skips_bad_fields():
    class PropertyResource:
        def __init__(self):
            self.calls = []

        def list(self, **query):
            self.calls.append(query)
            if query["filters"][0].startswith("StreetAddress,"):
                raise RentManagerBadRequestError("The request is invalid.")
            if query["filters"][0].startswith("Name,"):
                return [{"PropertyID": 10, "Name": "2212 Feldman Ave"}]
            if query["filters"][0].startswith("ShortName,"):
                return [{"PropertyID": 10, "Name": "2212 Feldman Ave"}]
            return []

    client = type("Client", (), {"properties": PropertyResource()})()

    rows = search_property_candidates(client, "2212 Feldman Ave", page_size=25)

    assert rows == [{"PropertyID": 10, "Name": "2212 Feldman Ave"}]


def test_resolve_property_searches_then_selects():
    client = type(
        "Client",
        (),
        {"properties": RecordingResource([{"PropertyID": 10, "Name": "2212 Feldman Ave"}])},
    )()

    selected = resolve_property(
        client,
        "2212 Feldman Ave",
        page_size=25,
        input_func=lambda prompt: "1",
        output_func=lambda line: None,
    )

    assert selected["PropertyID"] == 10


from examples.landscaping_ticket_workflow import (
    approval_allows_create,
    build_ticket_payload,
    create_landscaping_ticket,
    ticket_summary_lines,
)


def test_build_ticket_payload_sets_required_landscaping_fields():
    payload = build_ticket_payload(
        property_record={"PropertyID": 10, "StreetAddress": "2212 Feldman Ave", "Name": "Feldman Rental"},
        fixed_ids={
            "category.property_wide": 1,
            "priority.low": 2,
            "status.completed": 3,
            "user.andrew_burton": 4,
            "vendor.cres_property_management": 5,
            "item.landscaping": 6,
        },
        price=Decimal("125.50"),
        today=date(2026, 4, 30),
        closed_at=datetime(2026, 4, 30, 15, 45, 30),
        entered_address="2212 Feldman Ave",
    )

    assert payload == {
        "Title": "2212 Feldman Ave - Landscaping",
        "Description": "Landscaping 2026-04-30",
        "DueDate": "2026-04-30",
        "AssignedOpenDate": "2026-04-30T15:45:30",
        "CloseDate": "2026-04-30T15:45:30",
        "AssignedCloseDate": "2026-04-30T15:45:30",
        "IsClosed": True,
        "PropertyID": 10,
        "CategoryID": 1,
        "PriorityID": 2,
        "StatusID": 3,
        "AssignedToUserID": 4,
        "VendorID": 5,
        "LineItems": [
            {
                "InventoryItemID": 6,
                "Description": "Landscaping 2026-04-30",
                "Quantity": 1,
                "Cost": 125.5,
                "Price": 125.5,
            }
        ],
    }


def test_ticket_summary_lines_include_write_preview():
    lines = ticket_summary_lines(
        {
            "Title": "2212 Feldman Ave - Landscaping",
            "DueDate": "2026-04-30",
            "PropertyID": 10,
            "LineItems": [{"Cost": 125, "Price": 125}],
        }
    )

    assert lines == [
        "Title: 2212 Feldman Ave - Landscaping",
        "PropertyID: 10",
        "DueDate: 2026-04-30",
        "Cost: 125",
        "Sale Price: 125",
    ]


def test_approval_allows_create_when_auto_approved_without_prompting():
    prompts = []

    assert approval_allows_create(auto_approve=True, input_func=lambda prompt: prompts.append(prompt) or "n") is True
    assert prompts == []


@pytest.mark.parametrize(("answer", "expected"), [("y", True), ("yes", True), ("", False), ("n", False)])
def test_approval_prompt_defaults_to_no(answer, expected):
    assert approval_allows_create(auto_approve=False, input_func=lambda prompt: answer) is expected


def test_create_landscaping_ticket_calls_service_manager_issues_create():
    class Issues:
        def __init__(self):
            self.calls = []
            self.link_calls = []

        def create(self, payload):
            self.calls.append(payload)
            return [{"ServiceManagerIssueID": 77, **payload}]

        def link_property(self, issue_id, property_id):
            self.link_calls.append((issue_id, property_id))
            return {}

    class WorkOrders:
        def __init__(self):
            self.calls = []

        def create(self, payload):
            self.calls.append(payload)
            return [{"ServiceManagerIssueWorkOrderID": 99, **payload}]

    client = type("Client", (), {})()
    client.service_manager = type("ServiceManager", (), {"issues": Issues()})()
    client.service_manager_issue_work_orders = WorkOrders()
    payload = {
        "Title": "2212 Feldman Ave - Landscaping",
        "PropertyID": 10,
        "VendorID": 5,
        "LineItems": [
            {"InventoryItemID": 6, "Description": "Landscaping", "Quantity": 1, "Cost": 60.75, "Price": 60.75}
        ],
    }

    result = create_landscaping_ticket(client, payload)

    assert result["issue"][0]["ServiceManagerIssueID"] == 77
    assert result["work_orders"][0]["ServiceManagerIssueWorkOrderID"] == 99
    assert client.service_manager.issues.calls == [
        {"Title": "2212 Feldman Ave - Landscaping", "PropertyID": 10, "VendorID": 5}
    ]
    assert client.service_manager.issues.link_calls == [(77, 10)]
    assert client.service_manager_issue_work_orders.calls == [
        {
            "ServiceManagerIssueID": 77,
            "PropertyID": 10,
            "VendorID": 5,
            "PayeeAccountID": 5,
            "InventoryItemID": 6,
            "Description": "Landscaping",
            "Quantity": 1,
            "Cost": 60.75,
            "Price": 60.75,
        }
    ]


from examples.landscaping_ticket_workflow import build_parser, run_workflow


class FakeIssues:
    def __init__(self):
        self.created = []
        self.linked_properties = []

    def create(self, payload):
        self.created.append(payload)
        return [{"ServiceManagerIssueID": 88, **payload}]

    def link_property(self, issue_id, property_id):
        self.linked_properties.append((issue_id, property_id))
        return {}


class FakeWorkOrders:
    def __init__(self):
        self.created = []

    def create(self, payload):
        self.created.append(payload)
        return [{"ServiceManagerIssueWorkOrderID": 188, **payload}]


class FakeWorkflowClient:
    def __init__(self):
        self.properties = RecordingResource([{"PropertyID": 10, "Name": "2212 Feldman Ave"}])
        self.service_manager = type(
            "ServiceManager",
            (),
            {
                "categories": RecordingResource([{"ServiceManagerCategoryID": 1, "Name": "Property Wide"}]),
                "priorities": RecordingResource([{"ServiceManagerPriorityID": 2, "Name": "Low"}]),
                "statuses": RecordingResource([{"ServiceManagerStatusID": 3, "Name": "Completed"}]),
                "issues": FakeIssues(),
            },
        )()
        self.users = RecordingResource([{"UserID": 4, "Name": "Andrew Burton"}])
        self.vendors = RecordingResource([{"VendorID": 5, "Name": "Cres Property Management"}])
        self.inventory_items = RecordingResource([{"InventoryItemID": 6, "Name": "Landscaping"}])
        self.service_manager_issue_work_orders = FakeWorkOrders()


def test_build_parser_accepts_address_price_and_auto_approve_alias():
    args = build_parser().parse_args(["2212 Feldman Ave", "125", "--auto-approve"])

    assert args.address == "2212 Feldman Ave"
    assert args.price == "125"
    assert args.auto_approve is True


def test_build_parser_accepts_optional_address_price_and_yes_alias():
    args = build_parser().parse_args(["--address", "2212 Feldman Ave", "--price", "125", "--yes"])

    assert args.address_option == "2212 Feldman Ave"
    assert args.price_option == "125"
    assert args.yes is True


def test_run_workflow_creates_ticket_when_auto_approved(tmp_path):
    printed = []
    client = FakeWorkflowClient()

    result = run_workflow(
        client,
        address="2212 Feldman Ave",
        price_text="125",
        cache_path=tmp_path / "lookup-cache.json",
        refresh_cache=False,
        auto_approve=True,
        page_size=25,
        today=date(2026, 4, 30),
        input_func=lambda prompt: "n",
        output_func=printed.append,
    )

    assert result["issue"][0]["ServiceManagerIssueID"] == 88
    assert result["work_orders"][0]["ServiceManagerIssueWorkOrderID"] == 188
    assert client.service_manager.issues.created[0]["Title"] == "2212 Feldman Ave - Landscaping"
    assert client.service_manager.issues.linked_properties == [(88, 10)]
    assert "Title: 2212 Feldman Ave - Landscaping" in printed


def test_run_workflow_stops_when_approval_declines(tmp_path):
    client = FakeWorkflowClient()

    with pytest.raises(WorkflowError, match="declined"):
        run_workflow(
            client,
            address="2212 Feldman Ave",
            price_text="125",
            cache_path=tmp_path / "lookup-cache.json",
            refresh_cache=False,
            auto_approve=False,
            page_size=25,
            today=date(2026, 4, 30),
            input_func=lambda prompt: "n",
            output_func=lambda line: None,
        )

    assert client.service_manager.issues.created == []
