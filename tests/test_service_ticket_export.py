from pathlib import Path

import httpx

from rentmanager_api import InMemoryTokenStore, Page, RentManagerClient
from rentmanager_api.workflows import export_newest_service_ticket_details, get_newest_service_tickets


class FakePagedClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def iter_pages(self, endpoint, **query):
        self.calls.append((endpoint, query))
        yield from self.pages


def make_client(handler):
    return RentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=InMemoryTokenStore(),
        max_retries=0,
    )


def json_response(status_code, payload, headers=None):
    return httpx.Response(status_code, json=payload, headers=headers or {})


def test_get_newest_service_tickets_sorts_created_dates_across_pages():
    client = FakePagedClient(
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
                    {"ServiceManagerIssueID": 4, "Title": "issue date", "IssueDate": "2026-04-23T10:00:00"},
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

    assert [ticket["Title"] for ticket in tickets] == ["newest", "issue date", "middle"]
    assert client.calls[0][0] == "ServiceManagerIssues"
    assert client.calls[0][1]["page_size"] == 2


def test_export_newest_service_ticket_details_writes_manifest_details_and_files(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "RM_TICKET_DOWNLOAD_ENDPOINT_TEMPLATES",
        "ServiceManagerIssues/{ticket_id}/Attachments/{file_id},ServiceManagerIssues/{ticket_id}/Files/{file_id}",
    )
    seen_paths = []

    def handler(request):
        seen_paths.append(request.url.path)
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        if request.url.path == "/ServiceManagerIssues":
            return json_response(
                200,
                [
                    {"ServiceManagerIssueID": 10, "Title": "First", "CreateDate": "2026-04-24T09:00:00"},
                    {"ServiceManagerIssueID": 11, "Title": "Second", "DateCreated": "2026-04-23T09:00:00"},
                ],
            )
        if request.url.path == "/ServiceManagerIssues/10":
            return json_response(200, {"ServiceManagerIssueID": 10, "Title": "First detail"})
        if request.url.path == "/ServiceManagerIssues/11":
            return json_response(200, {"ServiceManagerIssueID": 11, "Title": "Second detail"})
        if request.url.path.endswith("/History"):
            return json_response(200, [{"HistoryID": 1, "Note": "called"}])
        if request.url.path.endswith("/Properties"):
            return json_response(200, [{"PropertyID": 99, "Name": "Main"}])
        if request.url.path.endswith("/LineItems"):
            return json_response(200, [{"Description": "Labor"}])
        if request.url.path.endswith("/Attachments") and request.url.path != "/ServiceManagerIssues/10/Attachments/501":
            return json_response(
                200,
                [
                    {"FileID": 500, "FileName": "../invoice.pdf"},
                    {"FileID": 501, "FileName": "invoice.pdf"},
                ]
                if request.url.path == "/ServiceManagerIssues/10/Attachments"
                else [],
            )
        if request.url.path.endswith("/Files"):
            return json_response(200, [])
        if request.url.path.endswith("/Documents"):
            return json_response(200, [])
        if request.url.path.endswith("/UserDefinedValues"):
            return json_response(200, [{"UserDefinedValueID": 7, "Value": "Gate code"}])
        if request.url.path.endswith("/UserDefinedFields"):
            return json_response(200, [{"UserDefinedFieldID": 8, "Name": "Access"}])
        if request.url.path == "/ServiceManagerIssues/10/Attachments/500":
            return httpx.Response(200, content=b"first-pdf")
        if request.url.path == "/ServiceManagerIssues/10/Attachments/501":
            return json_response(404, {"DeveloperMessage": "wrong attachment route"})
        if request.url.path == "/ServiceManagerIssues/10/Files/501":
            return httpx.Response(200, content=b"second-pdf")
        return json_response(404, {"DeveloperMessage": f"Unexpected {request.url.path}"})

    client = make_client(handler)

    manifest = export_newest_service_ticket_details(client, limit=2, export_root=tmp_path, page_size=2)

    export_dir = Path(manifest["export_dir"])
    assert (export_dir / "manifest.json").exists()
    assert (export_dir / "ticket-10" / "details.json").exists()
    assert (export_dir / "ticket-10" / "attachments" / "invoice.pdf").read_bytes() == b"first-pdf"
    assert (export_dir / "ticket-10" / "attachments" / "invoice-2.pdf").read_bytes() == b"second-pdf"
    assert manifest["ticket_count"] == 2
    assert manifest["tickets"][0]["ticket_id"] == 10
    assert "/ServiceManagerIssues/10/History" in seen_paths
    assert "/ServiceManagerIssues/10/Attachments/500" in seen_paths
    assert "/ServiceManagerIssues/10/Files/501" in seen_paths


def test_export_records_optional_endpoint_and_download_failures(tmp_path, monkeypatch):
    monkeypatch.setenv("RM_TICKET_DOWNLOAD_ENDPOINT_TEMPLATES", "Files/{file_id}")

    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        if request.url.path == "/ServiceManagerIssues":
            return json_response(200, [{"ServiceManagerIssueID": 20, "Title": "Only", "CreateDate": "2026-04-24"}])
        if request.url.path == "/ServiceManagerIssues/20":
            return json_response(200, {"ServiceManagerIssueID": 20, "Title": "Only detail"})
        if request.url.path == "/ServiceManagerIssues/20/Attachments":
            return json_response(200, [{"FileID": 900, "FileName": "broken.pdf"}])
        if request.url.path in {
            "/ServiceManagerIssues/20/History",
            "/ServiceManagerIssues/20/Properties",
            "/ServiceManagerIssues/20/LineItems",
            "/ServiceManagerIssues/20/Files",
            "/ServiceManagerIssues/20/Documents",
            "/ServiceManagerIssues/20/UserDefinedValues",
            "/ServiceManagerIssues/20/UserDefinedFields",
            "/Files/900",
        }:
            return json_response(404, {"DeveloperMessage": f"Missing {request.url.path}"})
        return json_response(404, {"DeveloperMessage": f"Unexpected {request.url.path}"})

    client = make_client(handler)

    manifest = export_newest_service_ticket_details(client, limit=1, export_root=tmp_path)

    ticket_summary = manifest["tickets"][0]
    details = ticket_summary["details"]
    assert ticket_summary["error_count"] >= 1
    assert details["downloads"][0]["ok"] is False
    assert any(error["endpoint"] == "ServiceManagerIssues/20/History" for error in details["errors"])
    assert details["downloads"][0]["attempts"][0]["endpoint"] == "Files/900"


def test_ticket_export_uses_documented_embed_and_resolves_known_related_resources(tmp_path):
    seen = []

    def handler(request):
        seen.append((request.url.path, dict(request.url.params)))
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        if request.url.path == "/ServiceManagerIssues":
            return json_response(200, [{"ServiceManagerIssueID": 40, "Title": "Related", "CreateDate": "2026-04-24"}])
        if request.url.path == "/ServiceManagerIssues/40":
            params = dict(request.url.params)
            assert "embed" in params
            assert "embeds" not in params
            return json_response(
                200,
                {
                    "ServiceManagerIssueID": 40,
                    "Title": "Related detail",
                    "StatusID": 2,
                    "CategoryID": 8,
                    "PriorityID": 5,
                    "VendorID": 4749,
                    "AssignedToUserID": 32,
                    "CreateUserID": 32,
                    "UpdateUserID": 33,
                    "History": [{"HistoryID": 1, "Note": "embedded"}],
                    "UserDefinedValues": [{"UserDefinedValueID": 4, "Value": "embedded"}],
                },
            )
        if request.url.path == "/ServiceManagerIssues/40/History":
            return json_response(200, [{"HistoryID": 2, "Note": "child"}])
        if request.url.path == "/ServiceManagerIssues/40/Properties":
            return json_response(200, [{"PropertyID": 1052, "Name": "Main"}])
        if request.url.path in {
            "/ServiceManagerIssues/40/LineItems",
            "/ServiceManagerIssues/40/Attachments",
            "/ServiceManagerIssues/40/Files",
            "/ServiceManagerIssues/40/Documents",
        }:
            return httpx.Response(404, text="No HTTP resource was found that matches the request URI.")
        if request.url.path == "/ServiceManagerIssues/40/UserDefinedValues":
            return json_response(200, [{"UserDefinedValueID": 5, "Value": "child"}])
        if request.url.path == "/ServiceManagerIssues/40/UserDefinedFields":
            return json_response(200, [])
        related_payloads = {
            "/ServiceManagerStatuses/2": {"ServiceManagerStatusID": 2, "Name": "New"},
            "/ServiceManagerCategories/8": {"ServiceManagerCategoryID": 8, "Name": "Property Wide"},
            "/ServiceManagerPriorities/5": {"ServiceManagerPriorityID": 5, "Name": "Low"},
            "/Vendors/4749": {"VendorID": 4749, "Name": "Vendor"},
            "/Users/32": {"UserID": 32, "Name": "Creator"},
            "/Users/33": {"UserID": 33, "Name": "Updater"},
        }
        if request.url.path in related_payloads:
            return json_response(200, related_payloads[request.url.path])
        return json_response(404, {"DeveloperMessage": f"Unexpected {request.url.path}"})

    client = make_client(handler)

    manifest = export_newest_service_ticket_details(client, limit=1, export_root=tmp_path)

    details = manifest["tickets"][0]["details"]
    assert details["related"]["status"]["Name"] == "New"
    assert details["related"]["category"]["Name"] == "Property Wide"
    assert details["related"]["priority"]["Name"] == "Low"
    assert details["related"]["vendor"]["Name"] == "Vendor"
    assert details["related"]["assigned_to_user"]["Name"] == "Creator"
    assert details["related"]["create_user"]["Name"] == "Creator"
    assert details["related"]["update_user"]["Name"] == "Updater"
    assert (
        "ServiceManagerIssues/40",
        dict(next(params for path, params in seen if path == "/ServiceManagerIssues/40")),
    ) in [(path.strip("/"), params) for path, params in seen]


def test_ticket_export_includes_work_order_billing_rows_and_linked_documents(tmp_path):
    seen = []

    def handler(request):
        seen.append((request.url.path, dict(request.url.params)))
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        if request.url.path == "/ServiceManagerIssues":
            return json_response(200, [{"ServiceManagerIssueID": 60, "Title": "Billed", "CreateDate": "2026-04-24"}])
        if request.url.path == "/ServiceManagerIssues/60":
            return json_response(
                200,
                {
                    "ServiceManagerIssueID": 60,
                    "Title": "Billed detail",
                    "TenantID": 22,
                    "VendorID": 44,
                    "PropertyID": 10,
                },
            )
        if request.url.path.startswith("/ServiceManagerIssues/60/"):
            return json_response(200, [])
        if request.url.path == "/Tenants/22":
            return json_response(200, {"TenantID": 22, "Name": "Resident"})
        if request.url.path == "/Vendors/44":
            return json_response(200, {"VendorID": 44, "Name": "Vendor"})
        if request.url.path == "/Properties/10":
            return json_response(200, {"PropertyID": 10, "Name": "Property"})
        if request.url.path == "/ServiceManagerIssueWorkOrders":
            params = dict(request.url.params)
            assert params["filters"] == "ServiceManagerIssueID,eq,60"
            return json_response(
                200,
                [
                    {
                        "ServiceManagerIssueWorkOrderID": 1,
                        "WorkOrderID": 101,
                        "ServiceManagerIssueID": 60,
                        "Description": "Tenant invoice labor",
                        "Quantity": 2,
                        "Cost": 25,
                        "Price": 80,
                        "HasInvoiceLink": True,
                        "InvoiceID": 500,
                        "InvoiceDetailID": 501,
                        "PayeeAccountID": 22,
                    },
                    {
                        "ServiceManagerIssueWorkOrderID": 2,
                        "WorkOrderID": 102,
                        "ServiceManagerIssueID": 60,
                        "Description": "Vendor bill parts",
                        "Quantity": 1,
                        "Cost": 40,
                        "Price": 0,
                        "InvoiceID": -1,
                        "InvoiceDetailID": -1,
                        "HasVendorBillLink": True,
                        "VendorBillID": 700,
                        "OwnerBillID": -1,
                        "PayeeAccountID": 44,
                    },
                    {
                        "ServiceManagerIssueWorkOrderID": 3,
                        "WorkOrderID": 103,
                        "ServiceManagerIssueID": 60,
                        "Description": "Owner bill",
                        "Quantity": 1,
                        "Cost": 15,
                        "Price": 0,
                        "HasOwnerBillLink": True,
                        "OwnerBillID": 800,
                    },
                    {
                        "ServiceManagerIssueWorkOrderID": 4,
                        "WorkOrderID": 104,
                        "ServiceManagerIssueID": 60,
                        "Description": "PO material",
                        "Quantity": 3,
                        "Cost": 10,
                        "Price": 45,
                        "HasPurchaseOrderLink": True,
                        "PurchaseOrderID": 900,
                    },
                    {
                        "ServiceManagerIssueWorkOrderID": 5,
                        "WorkOrderID": 105,
                        "ServiceManagerIssueID": 60,
                        "Description": "Not billed yet",
                        "Quantity": 1,
                        "Cost": 7,
                        "Price": 9,
                    },
                ],
            )
        linked_documents = {
            "/Invoices/500": {"InvoiceID": 500, "TotalAmount": 80},
            "/Bills/700": {"ID": 700, "Reference": "vendor bill"},
            "/Bills/800": {"ID": 800, "Reference": "owner bill"},
            "/PurchaseOrders/900": {"PurchaseOrderID": 900, "PurchaseOrderNumber": "PO-900"},
        }
        if request.url.path in linked_documents:
            return json_response(200, linked_documents[request.url.path])
        return json_response(404, {"DeveloperMessage": f"Unexpected {request.url.path}"})

    client = make_client(handler)

    manifest = export_newest_service_ticket_details(client, limit=1, export_root=tmp_path)

    details = manifest["tickets"][0]["details"]
    assert [row["Description"] for row in details["work_orders"]] == [
        "Tenant invoice labor",
        "Vendor bill parts",
        "Owner bill",
        "PO material",
        "Not billed yet",
    ]
    assert [row["billing_type"] for row in details["billing_rows"]] == [
        "tenant_invoice",
        "vendor_bill",
        "owner_bill",
        "purchase_order",
        "unbilled",
    ]
    assert details["billing_rows"][0]["bill_to_type"] == "tenant"
    assert details["billing_rows"][1]["bill_to_type"] == "vendor"
    assert details["billing_rows"][2]["bill_to_type"] == "owner"
    assert details["billing_summary"]["row_count"] == 5
    assert details["billing_summary"]["total_cost"] == 97
    assert details["billing_summary"]["total_price"] == 134
    assert details["billing_summary"]["billing_type_counts"] == {
        "tenant_invoice": 1,
        "vendor_bill": 1,
        "owner_bill": 1,
        "purchase_order": 1,
        "unbilled": 1,
    }
    assert details["billing_documents"]["invoices"]["500"]["TotalAmount"] == 80
    assert details["billing_documents"]["vendor_bills"]["700"]["Reference"] == "vendor bill"
    assert details["billing_documents"]["owner_bills"]["800"]["Reference"] == "owner bill"
    assert details["billing_documents"]["purchase_orders"]["900"]["PurchaseOrderNumber"] == "PO-900"
    assert any(path == "/ServiceManagerIssueWorkOrders" for path, _params in seen)


def test_empty_detail_collection_objects_are_normalized_to_lists(tmp_path):
    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        if request.url.path == "/ServiceManagerIssues":
            return json_response(
                200, [{"ServiceManagerIssueID": 50, "Title": "Empty collections", "CreateDate": "2026-04-24"}]
            )
        if request.url.path == "/ServiceManagerIssues/50":
            return json_response(200, {"ServiceManagerIssueID": 50, "Title": "Empty collections"})
        if request.url.path.startswith("/ServiceManagerIssues/50/"):
            return json_response(200, {})
        return json_response(404, {"DeveloperMessage": f"Unexpected {request.url.path}"})

    client = make_client(handler)

    manifest = export_newest_service_ticket_details(client, limit=1, export_root=tmp_path)

    details = manifest["tickets"][0]["details"]
    for key in (
        "history",
        "properties",
        "line_items",
        "attachments",
        "files",
        "documents",
        "user_defined_values",
        "user_defined_fields",
    ):
        assert details[key] == []


def test_unsupported_optional_child_endpoints_are_not_reported_as_ticket_errors(tmp_path):
    unsupported = (
        "No HTTP resource was found that matches the request URI "
        "'http://sampleco.api.rentmanager.com/ServiceManagerIssues/30/LineItems'."
    )

    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return json_response(200, "token-123")
        if request.url.path == "/ServiceManagerIssues":
            return json_response(200, [{"ServiceManagerIssueID": 30, "Title": "Embedded", "CreateDate": "2026-04-24"}])
        if request.url.path == "/ServiceManagerIssues/30":
            return json_response(
                200,
                {
                    "ServiceManagerIssueID": 30,
                    "Title": "Embedded detail",
                    "LineItems": [{"Description": "embedded labor"}],
                    "Attachments": [{"FileID": 300, "FileName": "embedded.pdf"}],
                },
            )
        if request.url.path in {
            "/ServiceManagerIssues/30/LineItems",
            "/ServiceManagerIssues/30/Attachments",
            "/ServiceManagerIssues/30/Files",
            "/ServiceManagerIssues/30/Documents",
        }:
            return httpx.Response(404, text=unsupported)
        if request.url.path in {
            "/ServiceManagerIssues/30/History",
            "/ServiceManagerIssues/30/Properties",
            "/ServiceManagerIssues/30/UserDefinedValues",
            "/ServiceManagerIssues/30/UserDefinedFields",
        }:
            return json_response(200, [])
        if request.url.path == "/ServiceManagerIssueWorkOrders":
            return json_response(200, [])
        if request.url.path == "/ServiceManagerIssues/30/Attachments/300":
            return httpx.Response(200, content=b"embedded-pdf")
        return json_response(404, {"DeveloperMessage": f"Unexpected {request.url.path}"})

    client = make_client(handler)

    manifest = export_newest_service_ticket_details(client, limit=1, export_root=tmp_path)

    ticket_summary = manifest["tickets"][0]
    details = ticket_summary["details"]
    assert ticket_summary["error_count"] == 0
    assert details["errors"] == []
    assert [item["endpoint"] for item in details["unavailable_endpoints"]] == [
        "ServiceManagerIssues/30/LineItems",
        "ServiceManagerIssues/30/Attachments",
        "ServiceManagerIssues/30/Files",
        "ServiceManagerIssues/30/Documents",
    ]
    assert details["line_items"] == [{"Description": "embedded labor"}]
    assert details["downloads"][0]["ok"] is True
