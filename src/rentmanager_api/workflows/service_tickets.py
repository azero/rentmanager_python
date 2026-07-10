from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ..errors import RentManagerAPIError
from ..query import RQL

SERVICE_TICKET_FIELDS = [
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
]

ISSUE_DETAIL_FIELDS = [
    "ServiceManagerIssueID",
    "Title",
    "Description",
    "Resolution",
    "CustomerDescription",
    "NoteText",
    "CategoryID",
    "Category",
    "StatusID",
    "Status",
    "PriorityID",
    "Priority",
    "PayeeAccountID",
    "PayeeAccount",
    "VendorID",
    "Vendor",
    "AssignedToUserID",
    "AssignedToUser",
    "CreateUserID",
    "CreateUser",
    "UpdateUserID",
    "UpdateUser",
    "PropertyID",
    "Property",
    "UnitID",
    "Unit",
    "TenantID",
    "Tenant",
    "History",
    "Properties",
    "WorkOrders",
    "ServiceManagerIssueWorkOrders",
    "LineItems",
    "ServiceLineItems",
    "Items",
    "Attachments",
    "Files",
    "Documents",
    "UserDefinedValues",
    "UserDefinedFields",
    "AssignedOpenDate",
    "DueDate",
    "IsRead",
    "CreateDate",
    "UpdateDate",
    "Age",
]

ISSUE_DETAIL_EMBEDS = [
    "Category",
    "Status",
    "Priority",
    "PayeeAccount",
    "Vendor",
    "AssignedToUser",
    "CreateUser",
    "UpdateUser",
    "Property",
    "Unit",
    "Tenant",
    "History",
    "Properties",
    "WorkOrders",
    "ServiceManagerIssueWorkOrders",
    "LineItems",
    "ServiceLineItems",
    "Items",
    "Attachments",
    "Files",
    "Documents",
    "UserDefinedValues",
    "UserDefinedFields",
]

DETAIL_ENDPOINTS = {
    "history": "ServiceManagerIssues/{ticket_id}/History",
    "properties": "ServiceManagerIssues/{ticket_id}/Properties",
    "line_items": "ServiceManagerIssues/{ticket_id}/LineItems",
    "attachments": "ServiceManagerIssues/{ticket_id}/Attachments",
    "files": "ServiceManagerIssues/{ticket_id}/Files",
    "documents": "ServiceManagerIssues/{ticket_id}/Documents",
    "user_defined_values": "ServiceManagerIssues/{ticket_id}/UserDefinedValues",
    "user_defined_fields": "ServiceManagerIssues/{ticket_id}/UserDefinedFields",
}

WORK_ORDER_FIELDS = [
    "ServiceManagerIssueWorkOrderID",
    "WorkOrderID",
    "ServiceManagerIssueID",
    "HasInvoiceLink",
    "InvoiceID",
    "InvoiceDetailID",
    "HasVendorBillLink",
    "VendorBillID",
    "HasOwnerBillLink",
    "OwnerBillID",
    "PayeeAccountID",
    "PropertyID",
    "UnitID",
    "TenantID",
    "VendorID",
    "OwnerID",
    "AccountID",
    "JobID",
    "Description",
    "Quantity",
    "Cost",
    "Price",
    "InventoryItemID",
    "HasPurchaseOrderLink",
    "PurchaseOrderID",
    "SmartReceiptID",
    "QuickBillID",
    "CreateDate",
    "CreateUserID",
    "UpdateDate",
    "UpdateUserID",
    "MetaTag",
]

WORK_ORDER_EMBEDS = [
    "PayeeAccount",
    "Property",
    "Unit",
    "Tenant",
    "Vendor",
    "Owner",
    "Job",
    "InventoryItem",
]

DEFAULT_DOWNLOAD_ENDPOINT_TEMPLATES = [
    "ServiceManagerIssues/{ticket_id}/Attachments/{file_id}",
    "ServiceManagerIssues/{ticket_id}/Files/{file_id}",
    "ServiceManagerIssues/{ticket_id}/Documents/{file_id}",
    "Files/{file_id}",
    "Documents/{file_id}",
]

FILE_ID_KEYS = (
    "FileID",
    "FileId",
    "fileID",
    "fileId",
    "AttachmentID",
    "AttachmentId",
    "DocumentID",
    "DocumentId",
    "ID",
    "Id",
)

FILENAME_KEYS = ("FileName", "Filename", "Name", "DocumentName", "Title")
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def parse_ticket_datetime(value: Any) -> datetime:
    if value in (None, ""):
        return datetime.min.replace(tzinfo=timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def ticket_created_at(ticket: dict[str, Any]) -> datetime:
    return max(
        parse_ticket_datetime(ticket.get("CreateDate")),
        parse_ticket_datetime(ticket.get("DateCreated")),
        parse_ticket_datetime(ticket.get("IssueDate")),
    )


def get_newest_service_tickets(
    client: Any,
    *,
    limit: int = 5,
    page_size: int = 1000,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    tickets: list[dict[str, Any]] = []
    for page in client.iter_pages(
        "ServiceManagerIssues",
        fields=SERVICE_TICKET_FIELDS,
        page_size=page_size,
        max_pages=max_pages,
    ):
        tickets.extend(_as_dict(row) for row in page.data if isinstance(_as_dict(row), dict))

    return sorted(tickets, key=ticket_created_at, reverse=True)[: max(0, int(limit))]


def get_service_ticket_details(
    client: Any,
    issue_id: int | str,
    *,
    export_dir: str | Path | None = None,
    download_attachments: bool = True,
) -> dict[str, Any]:
    ticket_id = str(issue_id).strip()
    ticket_dir = Path(export_dir) if export_dir is not None else None
    errors: list[dict[str, Any]] = []
    unavailable_endpoints: list[dict[str, Any]] = []
    details: dict[str, Any] = {
        "ticket_id": _parse_int(ticket_id) or ticket_id,
        "issue": None,
        "history": [],
        "properties": [],
        "work_orders": [],
        "line_items": [],
        "attachments": [],
        "files": [],
        "documents": [],
        "user_defined_values": [],
        "user_defined_fields": [],
        "related": {},
        "billing_rows": [],
        "billing_summary": _billing_summary([]),
        "billing_documents": _empty_billing_documents(),
        "downloads": [],
        "errors": errors,
        "unavailable_endpoints": unavailable_endpoints,
    }

    issue_endpoint = f"ServiceManagerIssues/{ticket_id}"
    issue_payload = _safe_get(
        client,
        issue_endpoint,
        errors,
        params={
            "fields": ",".join(ISSUE_DETAIL_FIELDS),
            "embed": ",".join(ISSUE_DETAIL_EMBEDS),
        },
    )
    if issue_payload is None:
        issue_payload = _safe_get(client, issue_endpoint, errors)
    details["issue"] = issue_payload

    for key, template in DETAIL_ENDPOINTS.items():
        endpoint = template.format(ticket_id=ticket_id)
        details[key] = _safe_get(
            client,
            endpoint,
            errors,
            unavailable_endpoints=unavailable_endpoints,
            default=[],
        )
        details[key] = _collection_payload(details[key])

    details["work_orders"] = _collection_list(
        _safe_get(
            client,
            "ServiceManagerIssueWorkOrders",
            errors,
            unavailable_endpoints=unavailable_endpoints,
            default=[],
            params={
                "filters": RQL.eq("ServiceManagerIssueID", _parse_int(ticket_id) or ticket_id),
                "fields": ",".join(WORK_ORDER_FIELDS),
                "embed": ",".join(WORK_ORDER_EMBEDS),
            },
        )
    )

    _apply_embedded_issue_details(details)
    _resolve_related_resources(client, details, errors, unavailable_endpoints)
    _apply_billing_overview(client, details, errors, unavailable_endpoints)

    if download_attachments and ticket_dir is not None:
        attachments_dir = ticket_dir / "attachments"
        attachment_rows = _attachment_rows(details)
        for row in attachment_rows:
            details["downloads"].append(_download_attachment(client, ticket_id, row, attachments_dir))

    if ticket_dir is not None:
        ticket_dir.mkdir(parents=True, exist_ok=True)
        _write_json(ticket_dir / "details.json", details)

    return details


def export_newest_service_ticket_details(
    client: Any,
    *,
    limit: int = 5,
    export_root: str | Path | None = None,
    page_size: int = 1000,
    max_pages: int | None = None,
) -> dict[str, Any]:
    tickets = get_newest_service_tickets(client, limit=limit, page_size=page_size, max_pages=max_pages)
    root = Path(export_root or "service-ticket-exports")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    export_dir = root / f"{timestamp}-newest-{max(0, int(limit))}"
    export_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "exported_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "export_dir": str(export_dir),
        "ticket_count": 0,
        "tickets": [],
    }

    for ticket in tickets:
        ticket_id = _extract_ticket_id(ticket)
        if ticket_id is None:
            manifest["tickets"].append(
                {
                    "ticket_id": None,
                    "source_ticket": ticket,
                    "details": None,
                    "details_path": None,
                    "download_count": 0,
                    "error_count": 1,
                    "errors": [{"endpoint": "ServiceManagerIssues", "error": "Unable to determine ticket id."}],
                }
            )
            continue

        ticket_dir = export_dir / f"ticket-{ticket_id}"
        details = get_service_ticket_details(client, ticket_id, export_dir=ticket_dir, download_attachments=True)
        downloads = [item for item in details.get("downloads", []) if isinstance(item, dict) and item.get("ok")]
        errors = [item for item in details.get("errors", []) if isinstance(item, dict)]
        failed_downloads = [
            item for item in details.get("downloads", []) if isinstance(item, dict) and not item.get("ok")
        ]
        unavailable = [item for item in details.get("unavailable_endpoints", []) if isinstance(item, dict)]
        summary = {
            "ticket_id": ticket_id,
            "title": ticket.get("Title"),
            "created_at": ticket_created_at(ticket).isoformat(),
            "details_path": str(ticket_dir / "details.json"),
            "download_count": len(downloads),
            "error_count": len(errors) + len(failed_downloads),
            "unavailable_endpoint_count": len(unavailable),
            "details": details,
        }
        manifest["tickets"].append(summary)

    manifest["ticket_count"] = len(manifest["tickets"])
    _write_json(export_dir / "manifest.json", manifest)
    return manifest


def _safe_get(
    client: Any,
    endpoint: str,
    errors: list[dict[str, Any]],
    *,
    params: dict[str, Any] | None = None,
    unavailable_endpoints: list[dict[str, Any]] | None = None,
    default: Any = None,
) -> Any:
    try:
        return _jsonable(client.get(endpoint, params=params))
    except RentManagerAPIError as exc:
        if unavailable_endpoints is not None and _is_unsupported_endpoint(exc):
            unavailable_endpoints.append(_error_record(endpoint, exc))
            return default
        errors.append(_error_record(endpoint, exc))
        return default


def _apply_embedded_issue_details(details: dict[str, Any]) -> None:
    issue = details.get("issue")
    if not isinstance(issue, dict):
        return
    embedded_keys = {
        "work_orders": ("WorkOrders", "ServiceManagerIssueWorkOrders", "IssueWorkOrders"),
        "line_items": ("LineItems", "ServiceLineItems", "Items"),
        "attachments": ("Attachments", "Attachment", "IssueAttachments"),
        "files": ("Files", "IssueFiles"),
        "documents": ("Documents", "IssueDocuments"),
        "user_defined_values": ("UserDefinedValues",),
        "user_defined_fields": ("UserDefinedFields",),
    }
    for detail_key, issue_keys in embedded_keys.items():
        if details.get(detail_key):
            continue
        for issue_key in issue_keys:
            embedded = issue.get(issue_key)
            if embedded:
                details[detail_key] = _collection_list(embedded) if detail_key == "work_orders" else _jsonable(embedded)
                break


def _collection_payload(value: Any) -> list[Any] | dict[str, Any]:
    if value is None or value == {}:
        return []
    if isinstance(value, list):
        return value
    return value


def _collection_list(value: Any) -> list[Any]:
    value = _collection_payload(_jsonable(value))
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _resolve_related_resources(
    client: Any,
    details: dict[str, Any],
    errors: list[dict[str, Any]],
    unavailable_endpoints: list[dict[str, Any]],
) -> None:
    issue = details.get("issue")
    if not isinstance(issue, dict):
        return
    related_specs = [
        ("status", "StatusID", "ServiceManagerStatuses/{id}"),
        ("category", "CategoryID", "ServiceManagerCategories/{id}"),
        ("priority", "PriorityID", "ServiceManagerPriorities/{id}"),
        ("vendor", "VendorID", "Vendors/{id}"),
        ("assigned_to_user", "AssignedToUserID", "Users/{id}"),
        ("create_user", "CreateUserID", "Users/{id}"),
        ("update_user", "UpdateUserID", "Users/{id}"),
        ("property", "PropertyID", "Properties/{id}"),
        ("unit", "UnitID", "Units/{id}"),
        ("tenant", "TenantID", "Tenants/{id}"),
    ]
    cache: dict[str, Any] = {}
    related = details.setdefault("related", {})
    for name, id_key, template in related_specs:
        item_id = _parse_id(issue.get(id_key))
        if item_id is None:
            continue
        endpoint = template.format(id=item_id)
        if endpoint not in cache:
            cache[endpoint] = _safe_get(
                client,
                endpoint,
                errors,
                unavailable_endpoints=unavailable_endpoints,
            )
        if cache[endpoint] is not None:
            related[name] = cache[endpoint]

    owner_id = (
        _parse_id(issue.get("OwnerID"))
        or _parse_id(issue.get("PrimaryOwnerID"))
        or _first_collection_int(details.get("properties"), "PrimaryOwnerID")
    )
    if owner_id is not None:
        endpoint = f"Owners/{owner_id}"
        if endpoint not in cache:
            cache[endpoint] = _safe_get(
                client,
                endpoint,
                errors,
                unavailable_endpoints=unavailable_endpoints,
            )
        if cache[endpoint] is not None:
            related["owner"] = cache[endpoint]


def _apply_billing_overview(
    client: Any,
    details: dict[str, Any],
    errors: list[dict[str, Any]],
    unavailable_endpoints: list[dict[str, Any]],
) -> None:
    billing_rows = _billing_rows(details)
    details["billing_rows"] = billing_rows
    details["billing_summary"] = _billing_summary(billing_rows)
    details["billing_documents"] = _resolve_billing_documents(
        client,
        billing_rows,
        errors,
        unavailable_endpoints,
    )


def _billing_rows(details: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    work_orders = details.get("work_orders")
    if isinstance(work_orders, list):
        rows.extend(
            _billing_row("work_order", index, row, details)
            for index, row in enumerate(work_orders)
            if isinstance(row, dict)
        )

    line_items = details.get("line_items")
    if not rows and isinstance(line_items, list):
        rows.extend(
            _billing_row("line_item", index, row, details)
            for index, row in enumerate(line_items)
            if isinstance(row, dict)
        )
    return rows


def _billing_row(source: str, index: int, row: dict[str, Any], details: dict[str, Any]) -> dict[str, Any]:
    issue = details.get("issue") if isinstance(details.get("issue"), dict) else {}
    related = details.get("related") if isinstance(details.get("related"), dict) else {}
    owner = related.get("owner") if isinstance(related.get("owner"), dict) else {}
    billing_type = _billing_type(row)
    bill_to_type = _bill_to_type(row, issue, billing_type)
    tenant_id = _parse_id(row.get("TenantID")) or _parse_id(issue.get("TenantID"))
    vendor_id = _parse_id(row.get("VendorID")) or _parse_id(issue.get("VendorID"))
    owner_id = _parse_id(row.get("OwnerID")) or _parse_id(issue.get("OwnerID")) or _parse_id(owner.get("OwnerID"))
    return {
        "source": source,
        "source_index": index,
        "billing_type": billing_type,
        "bill_to_type": bill_to_type,
        "bill_to_id": _bill_to_id(row, bill_to_type, tenant_id, vendor_id, owner_id),
        "service_manager_issue_work_order_id": _parse_id(row.get("ServiceManagerIssueWorkOrderID")),
        "work_order_id": _parse_id(row.get("WorkOrderID")),
        "service_manager_issue_id": _parse_id(row.get("ServiceManagerIssueID"))
        or _parse_id(issue.get("ServiceManagerIssueID")),
        "description": row.get("Description"),
        "quantity": _parse_number(row.get("Quantity")),
        "cost": _parse_number(row.get("Cost")),
        "price": _parse_number(row.get("Price")),
        "payee_account_id": _parse_id(row.get("PayeeAccountID")),
        "tenant_id": tenant_id,
        "vendor_id": vendor_id,
        "owner_id": owner_id,
        "property_id": _parse_id(row.get("PropertyID")) or _parse_id(issue.get("PropertyID")),
        "unit_id": _parse_id(row.get("UnitID")) or _parse_id(issue.get("UnitID")),
        "job_id": _parse_id(row.get("JobID")),
        "inventory_item_id": _parse_id(row.get("InventoryItemID")),
        "invoice_id": _parse_id(row.get("InvoiceID")),
        "invoice_detail_id": _parse_id(row.get("InvoiceDetailID")),
        "vendor_bill_id": _parse_id(row.get("VendorBillID")),
        "owner_bill_id": _parse_id(row.get("OwnerBillID")),
        "purchase_order_id": _parse_id(row.get("PurchaseOrderID")),
        "quick_bill_id": _parse_id(row.get("QuickBillID")),
        "smart_receipt_id": _parse_id(row.get("SmartReceiptID")),
        "raw": _jsonable(row),
    }


def _billing_type(row: dict[str, Any]) -> str:
    if (
        _truthy(row.get("HasInvoiceLink"))
        or _parse_id(row.get("InvoiceID")) is not None
        or _parse_id(row.get("InvoiceDetailID")) is not None
    ):
        return "tenant_invoice"
    if _truthy(row.get("HasVendorBillLink")) or _parse_id(row.get("VendorBillID")) is not None:
        return "vendor_bill"
    if _truthy(row.get("HasOwnerBillLink")) or _parse_id(row.get("OwnerBillID")) is not None:
        return "owner_bill"
    if _truthy(row.get("HasPurchaseOrderLink")) or _parse_id(row.get("PurchaseOrderID")) is not None:
        return "purchase_order"
    if _parse_id(row.get("QuickBillID")) is not None:
        return "quick_bill"
    if _parse_id(row.get("SmartReceiptID")) is not None:
        return "smart_receipt"
    return "unbilled"


def _bill_to_type(row: dict[str, Any], issue: dict[str, Any], billing_type: str) -> str:
    if billing_type == "tenant_invoice":
        if _parse_id(row.get("TenantID")) is not None or _parse_id(issue.get("TenantID")) is not None:
            return "tenant"
        return "account"
    if billing_type == "vendor_bill":
        return "vendor"
    if billing_type == "owner_bill":
        return "owner"
    if billing_type == "purchase_order":
        if (
            _parse_id(row.get("VendorID")) is not None
            or _parse_id(issue.get("VendorID")) is not None
            or _parse_id(row.get("PayeeAccountID")) is not None
        ):
            return "vendor"
        return "purchase_order"
    if billing_type in {"quick_bill", "smart_receipt"}:
        return "payee"
    return "unbilled"


def _bill_to_id(
    row: dict[str, Any],
    bill_to_type: str,
    tenant_id: int | None,
    vendor_id: int | None,
    owner_id: int | None,
) -> int | None:
    if bill_to_type == "tenant":
        return tenant_id or _parse_id(row.get("AccountID"))
    if bill_to_type == "vendor":
        return vendor_id or _parse_id(row.get("PayeeAccountID"))
    if bill_to_type == "owner":
        return owner_id or _parse_id(row.get("PayeeAccountID"))
    if bill_to_type == "account":
        return _parse_id(row.get("AccountID"))
    if bill_to_type == "payee":
        return _parse_id(row.get("PayeeAccountID"))
    return None


def _billing_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    billing_types = Counter(row.get("billing_type") or "unknown" for row in rows)
    bill_to_types = Counter(row.get("bill_to_type") or "unknown" for row in rows)
    return {
        "row_count": len(rows),
        "total_cost": _sum_numeric(row.get("cost") for row in rows),
        "total_price": _sum_numeric(row.get("price") for row in rows),
        "billing_type_counts": dict(billing_types),
        "bill_to_type_counts": dict(bill_to_types),
        "unbilled_count": billing_types.get("unbilled", 0),
    }


def _resolve_billing_documents(
    client: Any,
    billing_rows: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    unavailable_endpoints: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    documents = _empty_billing_documents()
    cache: dict[str, Any] = {}
    document_specs = [
        ("invoices", "invoice_id", "Invoices/{id}"),
        ("vendor_bills", "vendor_bill_id", "Bills/{id}"),
        ("owner_bills", "owner_bill_id", "Bills/{id}"),
        ("purchase_orders", "purchase_order_id", "PurchaseOrders/{id}"),
    ]
    for row in billing_rows:
        for group, id_key, template in document_specs:
            item_id = _parse_id(row.get(id_key))
            if item_id is None:
                continue
            endpoint = template.format(id=item_id)
            if endpoint not in cache:
                cache[endpoint] = _safe_get(
                    client,
                    endpoint,
                    errors,
                    unavailable_endpoints=unavailable_endpoints,
                )
            if cache[endpoint] is not None:
                documents[group][str(item_id)] = cache[endpoint]
    return documents


def _empty_billing_documents() -> dict[str, dict[str, Any]]:
    return {
        "invoices": {},
        "vendor_bills": {},
        "owner_bills": {},
        "purchase_orders": {},
    }


def _parse_number(value: Any) -> int | float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        return None
    if parsed == parsed.to_integral_value():
        return int(parsed)
    return float(parsed)


def _sum_numeric(values: Any) -> int | float:
    total = Decimal("0")
    has_fraction = False
    for value in values:
        if value is None or isinstance(value, bool):
            continue
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            continue
        total += number
        has_fraction = has_fraction or number != number.to_integral_value()
    if has_fraction or total != total.to_integral_value():
        return float(total)
    return int(total)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "y", "1"}
    return bool(value)


def _first_collection_int(value: Any, key: str) -> int | None:
    rows = _collection_list(value)
    for row in rows:
        if isinstance(row, dict):
            parsed = _parse_id(row.get(key))
            if parsed is not None:
                return parsed
    return None


def _download_attachment(client: Any, ticket_id: str, row: dict[str, Any], attachments_dir: Path) -> dict[str, Any]:
    file_id = _extract_file_id(row)
    filename = _attachment_filename(row, file_id)
    attempts: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "ok": False,
        "file_id": file_id,
        "filename": filename,
        "path": None,
        "metadata": row,
        "attempts": attempts,
    }
    if file_id is None:
        attempts.append({"endpoint": None, "ok": False, "status_code": None, "error": "Missing file id."})
        return result

    for template in _download_endpoint_templates():
        endpoint = template.format(ticket_id=ticket_id, file_id=file_id)
        try:
            content = client.download_bytes(endpoint)
        except RentManagerAPIError as exc:
            attempts.append(_error_record(endpoint, exc) | {"ok": False})
            continue

        attachments_dir.mkdir(parents=True, exist_ok=True)
        path = _unique_path(attachments_dir, filename)
        path.write_bytes(content)
        attempts.append({"endpoint": endpoint, "ok": True, "status_code": 200, "error": None})
        result.update({"ok": True, "path": str(path), "endpoint": endpoint, "size": len(content)})
        return result

    return result


def _download_endpoint_templates() -> list[str]:
    raw = str(os.getenv("RM_TICKET_DOWNLOAD_ENDPOINT_TEMPLATES") or "").strip()
    if raw:
        templates = [item.strip() for item in raw.split(",") if item.strip()]
        if templates:
            return templates
    return list(DEFAULT_DOWNLOAD_ENDPOINT_TEMPLATES)


def _attachment_rows(details: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("attachments", "files", "documents"):
        value = details.get(key)
        if isinstance(value, list):
            rows.extend(_as_dict(item) for item in value if isinstance(_as_dict(item), dict))
        elif isinstance(value, dict):
            rows.append(value)
    return rows


def _attachment_filename(row: dict[str, Any], file_id: int | None) -> str:
    for key in FILENAME_KEYS:
        value = str(row.get(key) or "").strip()
        if value:
            return _sanitize_filename(value)
    suffix = str(file_id) if file_id is not None else "unknown"
    return f"ticket-file-{suffix}"


def _sanitize_filename(value: str) -> str:
    name = value.replace("\\", "/").split("/")[-1].strip()
    name = INVALID_FILENAME_CHARS.sub("_", name).strip(" .")
    return name or "attachment"


def _unique_path(directory: Path, filename: str) -> Path:
    stem = Path(filename).stem or "attachment"
    suffix = Path(filename).suffix
    candidate = directory / filename
    counter = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{counter}{suffix}"
        counter += 1
    resolved_dir = directory.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_dir not in resolved_candidate.parents and resolved_candidate != resolved_dir:
        raise ValueError(f"Refusing to write outside export directory: {candidate}")
    return candidate


def _extract_ticket_id(value: Any) -> int | None:
    row = _as_dict(value)
    if isinstance(row, list):
        for item in row:
            parsed = _extract_ticket_id(item)
            if parsed is not None:
                return parsed
    if isinstance(row, dict):
        for key in ("ServiceManagerIssueID", "IssueID", "TicketID", "ID", "Id"):
            parsed = _parse_int(row.get(key))
            if parsed is not None:
                return parsed
    return _parse_int(row)


def _extract_file_id(value: Any) -> int | None:
    row = _as_dict(value)
    if isinstance(row, dict):
        for key in FILE_ID_KEYS:
            parsed = _parse_int(row.get(key))
            if parsed is not None:
                return parsed
        for nested in row.values():
            parsed = _extract_file_id(nested)
            if parsed is not None:
                return parsed
    elif isinstance(row, list):
        for item in row:
            parsed = _extract_file_id(item)
            if parsed is not None:
                return parsed
    return _parse_int(row)


def _parse_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _parse_id(value: Any) -> int | None:
    parsed = _parse_int(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed


def _as_dict(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    return value


def _jsonable(value: Any) -> Any:
    value = _as_dict(value)
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _error_record(endpoint: str | None, exc: RentManagerAPIError) -> dict[str, Any]:
    return {
        "endpoint": endpoint,
        "status_code": exc.status_code,
        "error": str(exc),
        "developer_message": exc.developer_message,
        "user_message": exc.user_message,
    }


def _is_unsupported_endpoint(exc: RentManagerAPIError) -> bool:
    message = " ".join(
        str(part or "")
        for part in (
            exc.developer_message,
            exc.user_message,
            str(exc),
        )
    ).lower()
    return exc.status_code == 404 and "no http resource was found" in message


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def create_service_ticket(
    client: Any,
    *,
    title: str,
    description: str,
    property_id: int | None = None,
    unit_id: int | None = None,
    tenant_id: int | None = None,
    vendor_id: int | None = None,
    status_id: int | None = None,
    category_id: int | None = None,
    line_items: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> Any:
    payload: dict[str, Any] = {
        "Title": title,
        "Description": description,
        "IsClosed": False,
    }
    optional_values = {
        "PropertyID": property_id,
        "UnitID": unit_id,
        "TenantID": tenant_id,
        "VendorID": vendor_id,
        "StatusID": status_id,
        "CategoryID": category_id,
    }
    payload.update({key: value for key, value in optional_values.items() if value is not None})
    if line_items:
        payload["LineItems"] = line_items
    if extra:
        payload.update(extra)
    return client.service_manager.issues.create(payload)


def update_ticket_line_items(
    client: Any,
    *,
    issue_id: int,
    line_items: list[dict[str, Any]],
    note: str | None = None,
) -> Any:
    payload: dict[str, Any] = {"LineItems": line_items}
    if note:
        payload["NoteText"] = note
    return client.service_manager.issues.update(issue_id, payload)
