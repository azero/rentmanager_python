from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Any

from rentmanager_api import RQL
from rentmanager_api.errors import RentManagerBadRequestError

try:
    from examples._shared import as_records, build_client, optional_int, print_json
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/name_id_lookup.py`
    from _shared import as_records, build_client, optional_int, print_json


@dataclass(frozen=True, slots=True)
class NameSearchSpec:
    search_type: str
    resource_attr: str
    id_field: str
    search_fields: tuple[str, ...]
    fields: tuple[str, ...]
    name_fields: tuple[str, ...]
    summary_fields: tuple[str, ...]


SEARCH_SPECS: dict[str, NameSearchSpec] = {
    "tenant": NameSearchSpec(
        search_type="tenant",
        resource_attr="tenants",
        id_field="TenantID",
        search_fields=("Name", "FirstName", "LastName"),
        fields=(
            "TenantID",
            "TenantDisplayID",
            "Name",
            "FirstName",
            "LastName",
            "Email",
            "PropertyID",
            "UnitID",
            "IsActive",
        ),
        name_fields=("Name", "FirstName", "LastName", "TenantDisplayID"),
        summary_fields=("TenantID", "TenantDisplayID", "PropertyID", "UnitID", "Email", "IsActive"),
    ),
    "property": NameSearchSpec(
        search_type="property",
        resource_attr="properties",
        id_field="PropertyID",
        search_fields=("Name", "ShortName"),
        fields=("PropertyID", "Name", "ShortName", "PrimaryOwnerID", "IsActive"),
        name_fields=("Name", "ShortName"),
        summary_fields=("PropertyID", "ShortName", "PrimaryOwnerID", "IsActive"),
    ),
    "owner": NameSearchSpec(
        search_type="owner",
        resource_attr="owners",
        id_field="OwnerID",
        search_fields=("Name", "CompanyName", "FirstName", "LastName"),
        fields=("OwnerID", "Name", "CompanyName", "FirstName", "LastName", "Email", "IsActive"),
        name_fields=("Name", "CompanyName", "FirstName", "LastName"),
        summary_fields=("OwnerID", "CompanyName", "Email", "IsActive"),
    ),
}


def search_filters_for_field(field: str, name: str) -> list[str]:
    return [RQL.ct(field, name)]


def normalize_search_types(search_types: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if search_types is None:
        return ["tenant", "property", "owner"]
    if isinstance(search_types, str):
        raw_types = [search_types]
    else:
        raw_types = list(search_types)

    normalized: list[str] = []
    for raw_search_type in raw_types:
        search_type = str(raw_search_type).strip().lower()
        if not search_type:
            continue
        if search_type == "all":
            for supported_type in ("tenant", "property", "owner"):
                if supported_type not in normalized:
                    normalized.append(supported_type)
            continue
        if search_type not in SEARCH_SPECS:
            supported = ", ".join(["all", *SEARCH_SPECS])
            raise ValueError(f"Unsupported search type {raw_search_type!r}. Use one of: {supported}.")
        if search_type not in normalized:
            normalized.append(search_type)
    return normalized or ["tenant", "property", "owner"]


def _first_present(row: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for field in fields:
        value = row.get(field)
        if value not in (None, ""):
            return value
    return None


def _summarize_match(search_type: str, spec: NameSearchSpec, row: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "type": search_type,
        "id_field": spec.id_field,
        "id": row.get(spec.id_field),
        "name": _first_present(row, spec.name_fields),
    }
    for field in spec.summary_fields:
        if field in row:
            summary[field] = row.get(field)
    return summary


def _search_one_type(
    client: Any,
    name: str,
    spec: NameSearchSpec,
    *,
    page_size: int,
) -> list[dict[str, Any]]:
    resource = getattr(client, spec.resource_attr)
    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for field in spec.search_fields:
        try:
            rows = as_records(
                resource.list(
                    fields=list(spec.fields),
                    filters=search_filters_for_field(field, name),
                    page_size=page_size,
                )
            )
        except RentManagerBadRequestError:
            continue
        for row in rows:
            row_id = row.get(spec.id_field)
            dedupe_key = f"{spec.search_type}:{row_id}" if row_id is not None else repr(sorted(row.items()))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            matches.append(_summarize_match(spec.search_type, spec, row))
    return matches


def search_ids_by_name(
    client: Any,
    name: str,
    *,
    search_types: str | list[str] | tuple[str, ...] | None = None,
    page_size: int = 25,
) -> dict[str, Any]:
    query = (name or "").strip()
    if not query:
        raise ValueError("Enter a tenant, property, or owner name to search.")

    normalized_types = normalize_search_types(search_types)
    matches: list[dict[str, Any]] = []
    for search_type in normalized_types:
        matches.extend(_search_one_type(client, query, SEARCH_SPECS[search_type], page_size=page_size))

    return {
        "query": query,
        "search_types": normalized_types,
        "matches": matches,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search tenant, property, and owner names and print matching IDs.")
    parser.add_argument("name", nargs="?", help="Partial tenant, property, or owner name to search.")
    parser.add_argument(
        "--type",
        dest="search_type",
        choices=["all", "tenant", "property", "owner"],
        default=os.getenv("RM_EXAMPLE_SEARCH_TYPE", "all"),
        help="Which kind of record to search. Defaults to all.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=optional_int("RM_EXAMPLE_LIMIT", default=25) or 25,
        help="Page size for each field search.",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    name = args.name or os.getenv("RM_EXAMPLE_SEARCH_NAME")
    if not name:
        name = input("Tenant, property, or owner name to search: ").strip()

    with build_client() as client:
        result = search_ids_by_name(
            client,
            name,
            search_types=args.search_type,
            page_size=args.limit,
        )
    print_json(result)


if __name__ == "__main__":
    main()
