import json

import httpx
import pytest

from rentmanager_api import EndpointRegistry, EndpointSpec, InMemoryTokenStore, RentManagerClient
from rentmanager_api.communications_documents_portals_web import (
    COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS,
)
from rentmanager_api.maintenance_assets_inspections_service import (
    MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS,
)
from rentmanager_api.reporting_surveys_memorized_templates import (
    REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS,
)
from rentmanager_api.utilities_metering import UTILITIES_METERING_RESOURCE_SPECS


LIVE_HELP_COLLECTION_AND_ITEM_RESOURCES = {
    "Amenities",
    "ChargeTypes",
    "Contacts",
    "GLAccounts",
    "Leases",
    "Locations",
    "Owners",
    "Properties",
    "PropertyGroups",
    "Prospects",
    "RecurringCharges",
    "ReportWriterReports",
    "ServiceManagerCategories",
    "ServiceManagerIssues",
    "ServiceManagerPriorities",
    "ServiceManagerStatuses",
    "Tasks",
    "Tenants",
    "Units",
    "UnitTypes",
    "Users",
    "Vendors",
    *(spec.path for spec in COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS if "get" in spec.operations),
    *(spec.path for spec in MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS),
    *(
        spec.path
        for spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS
        if {"list", "get"}.issubset(set(spec.operations))
    ),
    *(spec.path for spec in UTILITIES_METERING_RESOURCE_SPECS if {"list", "get"}.issubset(set(spec.operations))),
}


ALLOWED_CONFIDENCE_VALUES = {"documented", "prior_art", "field_discovered", "live_help_catalog"}


def make_path_client():
    calls = []

    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="token")
        body = json.loads(request.content.decode("utf-8")) if request.content else None
        calls.append(
            {
                "method": request.method,
                "path": request.url.path,
                "params": dict(request.url.params),
                "json": body,
            }
        )
        return httpx.Response(200, json=[])

    client = RentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=InMemoryTokenStore(),
        max_retries=0,
    )
    return client, calls


def resolve_attr(obj, attr_path):
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def assert_inherited_resource_call(case):
    client_attr, method_name, expected_path, payload_or_params = case
    client, calls = make_path_client()
    resource = resolve_attr(client, client_attr)
    expected_json = None

    if method_name == "list":
        resource.list()
        expected_method = "GET"
    elif method_name == "get":
        resource.get(payload_or_params)
        expected_method = "GET"
    elif method_name == "create":
        resource.create(payload_or_params)
        expected_method = "POST"
        expected_json = payload_or_params
    elif method_name == "update":
        resource.update(payload_or_params["id"], payload_or_params["payload"])
        expected_method = "POST"
        expected_json = payload_or_params["payload"]
    elif method_name == "delete" and isinstance(payload_or_params, dict) and "ids" in payload_or_params:
        resource.delete(ids=payload_or_params["ids"])
        expected_method = "DELETE"
        expected_json = payload_or_params["ids"]
    elif method_name == "delete":
        resource.delete(payload_or_params)
        expected_method = "DELETE"
    else:
        raise AssertionError(f"Unsupported resource method in test table: {method_name}")

    assert calls == [
        {
            "method": expected_method,
            "path": expected_path,
            "params": {},
            "json": expected_json,
        }
    ]


def test_seeded_resource_methods_call_expected_paths():
    client, calls = make_path_client()

    client.contacts.list()
    client.tenants.transactions(12)
    client.tenants.recurring_charges(12)
    client.tenants.addresses(12)
    client.owners.owner_checks(3)
    client.vendors.bills(4)
    client.units.link_amenities(5, [8, 9])
    client.service_manager.issues.link_property(10, 77)
    client.service_manager.issues.history(10)
    client.service_manager.priorities.get(5)
    client.report_writer_reports.run(218)
    client.recurring_charges.post_recurring_charges({"PostDate": "2026-04-23"})

    assert [(call["method"], call["path"], call["params"]) for call in calls] == [
        ("GET", "/Contacts", {}),
        ("GET", "/Tenants/12/Transactions", {}),
        ("GET", "/Tenants/12/RecurringCharges", {}),
        ("GET", "/Tenants/12/Addresses", {}),
        ("GET", "/Owners/3/OwnerChecks", {}),
        ("GET", "/Vendors/4/Bills", {}),
        ("POST", "/Units/5/LinkAmenities", {}),
        ("POST", "/ServiceManagerIssues/10/LinkProperty", {"propertyID": "77"}),
        ("GET", "/ServiceManagerIssues/10/History", {}),
        ("GET", "/ServiceManagerPriorities/5", {}),
        ("GET", "/ReportWriterReports/218/RunReportWriterReport", {}),
        ("POST", "/RecurringCharges/PostRecurringCharges", {}),
    ]


@pytest.mark.parametrize(
    "case",
    [
        ("contacts", "list", "/Contacts", None),
        ("contacts", "get", "/Contacts/123", 123),
        ("contacts", "create", "/Contacts", [{"Name": "Ada"}]),
        ("contacts", "update", "/Contacts/123", {"id": 123, "payload": [{"Name": "Ada Updated"}]}),
        ("contacts", "delete", "/Contacts", {"ids": [123]}),
        ("contacts", "delete", "/Contacts/123", 123),
        ("service_manager.priorities", "get", "/ServiceManagerPriorities/123", 123),
    ],
)
def test_inherited_resource_methods_call_expected_paths(case):
    assert_inherited_resource_call(case)


def test_registry_reports_seeded_endpoint_coverage():
    report = EndpointRegistry.default().coverage_report()
    paths = {(item["method"], item["path"]) for item in report}

    assert ("GET", "/Tenants/{id}/Transactions") in paths
    assert ("POST", "/ServiceManagerIssues/{id}/LinkProperty") in paths
    assert ("GET", "/ServiceManagerPriorities") in paths
    assert ("GET", "/ServiceManagerPriorities/{id}") in paths
    assert ("GET", "/ReportWriterReports/{id}/RunReportWriterReport") in paths
    assert ("POST", "/RecurringCharges/PostRecurringCharges") in paths
    assert all(item["confidence"] in ALLOWED_CONFIDENCE_VALUES for item in report)


def test_endpoint_spec_supports_live_help_catalog_confidence():
    spec = EndpointSpec(
        method="GET",
        path="/ExampleResources",
        model="ExampleResource",
        confidence="live_help_catalog",
        source="authenticated WAPI12 Help catalog",
    )

    report = EndpointRegistry([spec]).coverage_report()

    assert report[0]["confidence"] == "live_help_catalog"


def test_endpoint_spec_rejects_unknown_confidence():
    with pytest.raises(ValueError, match="confidence"):
        EndpointSpec(
            method="GET",
            path="/ExampleResources",
            model="ExampleResource",
            confidence="guessed",
            source="test",
        )


@pytest.mark.parametrize("resource", sorted(LIVE_HELP_COLLECTION_AND_ITEM_RESOURCES))
def test_registry_has_live_help_collection_and_item_gets_for_first_class_resources(resource):
    paths = {(endpoint.method, endpoint.path) for endpoint in EndpointRegistry.default()}

    assert ("GET", f"/{resource}") in paths
    assert ("GET", f"/{resource}/{{id}}") in paths
