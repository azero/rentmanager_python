from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable

from rentmanager_api import RQL
from rentmanager_api.errors import RentManagerBadRequestError

try:
    from examples._shared import as_records, build_client, optional_int, print_json
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/landscaping_ticket_workflow.py`
    from _shared import as_records, build_client, optional_int, print_json


DEFAULT_CACHE_PATH = ".rentmanager-landscaping-cache.json"
MONEY_CENTS = Decimal("0.01")
WHITESPACE_RE = re.compile(r"\s+")


class WorkflowError(RuntimeError):
    pass


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return WHITESPACE_RE.sub(" ", text.strip().lower())


def parse_price(value: Any) -> Decimal:
    text = "" if value is None else str(value).strip()
    text = text.replace("$", "").replace(",", "")
    if not text:
        raise WorkflowError("Enter a landscaping price greater than zero.")
    try:
        amount = Decimal(text).quantize(MONEY_CENTS, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise WorkflowError(f"Invalid landscaping price: {value!r}.") from exc
    if amount <= 0:
        raise WorkflowError("Enter a landscaping price greater than zero.")
    return amount


def payload_money(amount: Decimal) -> int | float:
    if amount == amount.to_integral_value():
        return int(amount)
    return float(amount)


@dataclass(frozen=True, slots=True)
class FixedLookup:
    key: str
    resource_path: str
    display_name: str
    id_field: str
    name_fields: tuple[str, ...]
    fields: tuple[str, ...]
    search_names: tuple[str, ...] = ()


FIXED_LOOKUPS: tuple[FixedLookup, ...] = (
    FixedLookup(
        key="category.property_wide",
        resource_path="service_manager.categories",
        display_name="Property Wide",
        id_field="ServiceManagerCategoryID",
        name_fields=("Name",),
        fields=("ServiceManagerCategoryID", "Name", "Description"),
    ),
    FixedLookup(
        key="priority.low",
        resource_path="service_manager.priorities",
        display_name="Low",
        id_field="ServiceManagerPriorityID",
        name_fields=("Name",),
        fields=("ServiceManagerPriorityID", "Name", "Description", "IsActive"),
    ),
    FixedLookup(
        key="status.completed",
        resource_path="service_manager.statuses",
        display_name="Completed",
        id_field="ServiceManagerStatusID",
        name_fields=("Name",),
        fields=("ServiceManagerStatusID", "Name", "Description"),
        search_names=("Completed", "Complete"),
    ),
    FixedLookup(
        key="user.andrew_burton",
        resource_path="users",
        display_name="Andrew Burton",
        id_field="UserID",
        name_fields=("Username", "Name", "FirstName", "LastName"),
        fields=("UserID", "Username", "Name", "FirstName", "LastName", "IsActive"),
    ),
    FixedLookup(
        key="vendor.cres_property_management",
        resource_path="vendors",
        display_name="Cres Property Management",
        id_field="VendorID",
        name_fields=("Name", "CompanyName"),
        fields=("VendorID", "Name", "CompanyName", "IsActive"),
    ),
    FixedLookup(
        key="item.landscaping",
        resource_path="inventory_items",
        display_name="Landscaping",
        id_field="InventoryItemID",
        name_fields=("Name",),
        fields=("InventoryItemID", "Name", "Description"),
    ),
)


class LookupCache:
    def __init__(self, path: str | os.PathLike[str], data: dict[str, Any] | None = None) -> None:
        self.path = Path(path)
        self.data = data or {"lookups": {}}
        self.data.setdefault("lookups", {})

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> "LookupCache":
        cache_path = Path(path)
        if not cache_path.exists():
            return cls(cache_path)
        return cls(cache_path, json.loads(cache_path.read_text(encoding="utf-8")))

    def get_id(self, key: str) -> int | None:
        entry = self.data.get("lookups", {}).get(key)
        if not isinstance(entry, dict):
            return None
        value = entry.get("id")
        if isinstance(value, bool) or value is None:
            return None
        try:
            parsed = int(str(value).strip())
        except ValueError:
            return None
        return parsed if parsed > 0 else None

    def set_entry(self, key: str, entry: dict[str, Any]) -> None:
        self.data.setdefault("lookups", {})[key] = entry

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")


def get_nested_attr(root: Any, dotted_path: str) -> Any:
    value = root
    for part in dotted_path.split("."):
        value = getattr(value, part)
    return value


def find_record_by_name(
    resource: Any,
    *,
    display_name: str,
    search_names: tuple[str, ...] = (),
    id_field: str,
    name_fields: tuple[str, ...],
    fields: tuple[str, ...],
    page_size: int,
) -> dict[str, Any]:
    search_values = search_names or (display_name,)
    expected_names = {normalize_text(name) for name in search_values}
    matches: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for search_value in search_values:
        for name_field in name_fields:
            try:
                rows = as_records(
                    resource.list(
                        fields=list(fields),
                        filters=[RQL.ct(name_field, search_value)],
                        page_size=page_size,
                    )
                )
            except RentManagerBadRequestError:
                continue
            for row in rows:
                row_id = row.get(id_field)
                dedupe_key = str(row_id) if row_id is not None else repr(sorted(row.items()))
                if dedupe_key in seen_ids:
                    continue
                seen_ids.add(dedupe_key)
                matches.append(row)

    exact_matches = [
        row
        for row in matches
        if any(normalize_text(row.get(name_field)) in expected_names for name_field in name_fields)
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise WorkflowError(f"Multiple exact matches found for {display_name!r}.")
    raise WorkflowError(f"Unable to find {display_name!r} in {getattr(resource, 'path', 'resource')}.")


def resolve_fixed_lookups(
    client: Any,
    *,
    cache: LookupCache,
    refresh_cache: bool,
    page_size: int,
) -> dict[str, int]:
    resolved: dict[str, int] = {}
    cache_changed = False
    for lookup in FIXED_LOOKUPS:
        cached_id = None if refresh_cache else cache.get_id(lookup.key)
        if cached_id is not None:
            resolved[lookup.key] = cached_id
            continue

        resource = get_nested_attr(client, lookup.resource_path)
        record = find_record_by_name(
            resource,
            display_name=lookup.display_name,
            search_names=lookup.search_names,
            id_field=lookup.id_field,
            name_fields=lookup.name_fields,
            fields=lookup.fields,
            page_size=page_size,
        )
        record_id = record.get(lookup.id_field)
        if isinstance(record_id, bool) or record_id is None:
            raise WorkflowError(f"Resolved {lookup.display_name!r} without {lookup.id_field}.")
        resolved_id = int(record_id)
        resolved[lookup.key] = resolved_id
        cache.set_entry(
            lookup.key,
            {
                "resource": lookup.resource_path,
                "name": lookup.display_name,
                "id_field": lookup.id_field,
                "id": resolved_id,
            },
        )
        cache_changed = True

    if cache_changed:
        cache.save()
    return resolved


PROPERTY_ID_FIELD = "PropertyID"
PROPERTY_FIELDS = [
    "PropertyID",
    "Name",
    "ShortName",
    "StreetAddress",
    "Address",
    "Address1",
    "PropertyAddress",
    "IsActive",
]
ADDRESS_SEARCH_FIELDS = ("StreetAddress", "Address", "Address1", "PropertyAddress", "Name", "ShortName")
PROPERTY_DISPLAY_FIELDS = ("StreetAddress", "Address", "Address1", "PropertyAddress", "Name", "ShortName")


def property_display_address(row: dict[str, Any], *, fallback: str) -> str:
    for field in PROPERTY_DISPLAY_FIELDS:
        value = row.get(field)
        if value not in (None, ""):
            return str(value).strip()
    return fallback.strip()


def property_identity_values(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for field in PROPERTY_DISPLAY_FIELDS:
        value = row.get(field)
        if value not in (None, ""):
            values.append(str(value))
    return values


def _property_rows_for_field(client: Any, field: str, address: str, *, page_size: int) -> list[dict[str, Any]]:
    query = {"filters": [RQL.ct(field, address)], "page_size": page_size}
    try:
        return as_records(client.properties.list(fields=PROPERTY_FIELDS, **query))
    except RentManagerBadRequestError:
        try:
            return as_records(client.properties.list(**query))
        except RentManagerBadRequestError:
            return []


def search_property_candidates(client: Any, address: str, *, page_size: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for field in ADDRESS_SEARCH_FIELDS:
        rows = _property_rows_for_field(client, field, address, page_size=page_size)
        for row in rows:
            row_id = row.get(PROPERTY_ID_FIELD)
            dedupe_key = str(row_id) if row_id is not None else repr(sorted(row.items()))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            candidates.append(row)
    return candidates


def choose_property(
    address: str,
    candidates: list[dict[str, Any]],
    *,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> dict[str, Any]:
    if not candidates:
        raise WorkflowError(f"No property matches found for {address!r}.")

    expected = normalize_text(address)
    exact_matches = [
        row for row in candidates if any(normalize_text(value) == expected for value in property_identity_values(row))
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]

    options = exact_matches if exact_matches else candidates
    for index, row in enumerate(options, start=1):
        display = property_display_address(row, fallback=address)
        output_func(f"{index}. {display} (PropertyID: {row.get(PROPERTY_ID_FIELD)})")

    raw_choice = input_func("Select property number: ").strip()
    try:
        choice = int(raw_choice)
    except ValueError as exc:
        raise WorkflowError(f"Invalid property selection: {raw_choice!r}.") from exc
    if choice < 1 or choice > len(options):
        raise WorkflowError(f"Property selection must be between 1 and {len(options)}.")
    return options[choice - 1]


def resolve_property(
    client: Any,
    address: str,
    *,
    page_size: int,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
) -> dict[str, Any]:
    candidates = search_property_candidates(client, address, page_size=page_size)
    return choose_property(address, candidates, input_func=input_func, output_func=output_func)


def required_id(row: dict[str, Any], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or value is None:
        raise WorkflowError(f"Selected record is missing {field}.")
    parsed = int(value)
    if parsed <= 0:
        raise WorkflowError(f"Selected record has invalid {field}: {value!r}.")
    return parsed


def build_ticket_payload(
    *,
    property_record: dict[str, Any],
    fixed_ids: dict[str, int],
    price: Decimal,
    today: date,
    closed_at: datetime | None = None,
    entered_address: str,
) -> dict[str, Any]:
    current_date = today.isoformat()
    close_datetime = (closed_at or datetime.now()).replace(microsecond=0).isoformat()
    street_address = property_display_address(property_record, fallback=entered_address)
    amount = payload_money(price)
    return {
        "Title": f"{street_address} - Landscaping",
        "Description": f"Landscaping {current_date}",
        "DueDate": current_date,
        "AssignedOpenDate": close_datetime,
        "CloseDate": close_datetime,
        "AssignedCloseDate": close_datetime,
        "IsClosed": True,
        "PropertyID": required_id(property_record, PROPERTY_ID_FIELD),
        "CategoryID": fixed_ids["category.property_wide"],
        "PriorityID": fixed_ids["priority.low"],
        "StatusID": fixed_ids["status.completed"],
        "AssignedToUserID": fixed_ids["user.andrew_burton"],
        "VendorID": fixed_ids["vendor.cres_property_management"],
        "LineItems": [
            {
                "InventoryItemID": fixed_ids["item.landscaping"],
                "Description": f"Landscaping {current_date}",
                "Quantity": 1,
                "Cost": amount,
                "Price": amount,
            }
        ],
    }


def ticket_summary_lines(payload: dict[str, Any]) -> list[str]:
    line_item = payload.get("LineItems", [{}])[0]
    return [
        f"Title: {payload.get('Title')}",
        f"PropertyID: {payload.get('PropertyID')}",
        f"DueDate: {payload.get('DueDate')}",
        f"Cost: {line_item.get('Cost')}",
        f"Sale Price: {line_item.get('Price')}",
    ]


def approval_allows_create(*, auto_approve: bool, input_func: Callable[[str], str]) -> bool:
    if auto_approve:
        return True
    answer = normalize_text(input_func("Create this landscaping ticket? [y/N]: "))
    return answer in {"y", "yes"}


def first_record(value: Any) -> dict[str, Any]:
    rows = as_records(value)
    if not rows:
        raise WorkflowError("Rent Manager response did not include a created record.")
    row = rows[0]
    if not isinstance(row, dict):
        raise WorkflowError("Rent Manager response did not include a created record.")
    return row


def issue_id_from_response(value: Any) -> int:
    row = first_record(value)
    for field in ("ServiceManagerIssueID", "IssueID", "TicketID", "ID", "Id"):
        raw_id = row.get(field)
        if raw_id is None or isinstance(raw_id, bool):
            continue
        parsed = int(raw_id)
        if parsed > 0:
            return parsed
    raise WorkflowError("Created ticket response did not include a service issue ID.")


def build_work_order_payload(
    *,
    issue_id: int,
    property_id: int,
    vendor_id: int | None,
    line_item: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "ServiceManagerIssueID": issue_id,
        "PropertyID": property_id,
    }
    if vendor_id is not None:
        payload["VendorID"] = vendor_id
        payload["PayeeAccountID"] = vendor_id
    payload.update(line_item)
    return payload


def create_landscaping_ticket(client: Any, payload: dict[str, Any]) -> Any:
    issue_payload = {key: value for key, value in payload.items() if key != "LineItems"}
    created_issue = client.service_manager.issues.create(issue_payload)
    issue_id = issue_id_from_response(created_issue)
    property_id = required_id(payload, PROPERTY_ID_FIELD)
    linked_property = client.service_manager.issues.link_property(issue_id, property_id)

    work_orders: list[dict[str, Any]] = []
    for line_item in payload.get("LineItems", []):
        work_order_payload = build_work_order_payload(
            issue_id=issue_id,
            property_id=property_id,
            vendor_id=payload.get("VendorID"),
            line_item=line_item,
        )
        work_orders.extend(as_records(client.service_manager_issue_work_orders.create(work_order_payload)))

    return {
        "issue": as_records(created_issue),
        "linked_property": linked_property,
        "work_orders": work_orders,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a completed landscaping service ticket for a property.")
    parser.add_argument("address", nargs="?", help="Property street address to verify.")
    parser.add_argument("price", nargs="?", help="Landscaping cost and sale price.")
    parser.add_argument("--address", dest="address_option", help="Property street address to verify.")
    parser.add_argument("--price", dest="price_option", help="Landscaping cost and sale price.")
    parser.add_argument("--yes", action="store_true", help="Create without the approval prompt.")
    parser.add_argument("--auto-approve", action="store_true", help="Create without the approval prompt.")
    parser.add_argument("--refresh-cache", action="store_true", help="Refresh cached Rent Manager setup IDs.")
    parser.add_argument(
        "--cache-path",
        default=os.getenv("RM_LANDSCAPING_CACHE_PATH", DEFAULT_CACHE_PATH),
        help="Path to the fixed lookup cache JSON file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=optional_int("RM_EXAMPLE_LIMIT", default=25) or 25,
        help="Page size for property and setup lookups.",
    )
    return parser


def run_workflow(
    client: Any,
    *,
    address: str,
    price_text: str,
    cache_path: str | os.PathLike[str],
    refresh_cache: bool,
    auto_approve: bool,
    page_size: int,
    today: date | None = None,
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], None] = print,
) -> Any:
    clean_address = address.strip()
    if not clean_address:
        raise WorkflowError("Enter a property street address.")

    price = parse_price(price_text)
    selected_property = resolve_property(
        client,
        clean_address,
        page_size=page_size,
        input_func=input_func,
        output_func=output_func,
    )
    cache = LookupCache.load(cache_path)
    fixed_ids = resolve_fixed_lookups(
        client,
        cache=cache,
        refresh_cache=refresh_cache,
        page_size=page_size,
    )
    payload = build_ticket_payload(
        property_record=selected_property,
        fixed_ids=fixed_ids,
        price=price,
        today=today or date.today(),
        entered_address=clean_address,
    )

    for line in ticket_summary_lines(payload):
        output_func(line)
    if not approval_allows_create(auto_approve=auto_approve, input_func=input_func):
        raise WorkflowError("Ticket creation declined.")
    return create_landscaping_ticket(client, payload)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    address = args.address_option or args.address
    price_text = args.price_option or args.price
    if not address:
        address = input("Property street address: ").strip()
    if not price_text:
        price_text = input("Landscaping price: ").strip()

    with build_client() as client:
        result = run_workflow(
            client,
            address=address,
            price_text=price_text,
            cache_path=args.cache_path,
            refresh_cache=args.refresh_cache,
            auto_approve=args.yes or args.auto_approve,
            page_size=args.limit,
        )
    print_json(result)


if __name__ == "__main__":
    main()
