from __future__ import annotations

import os
from typing import Any

from rentmanager_api import RQL

try:
    from examples._shared import as_dict, as_records, build_client, optional_int, print_json
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/query_cookbook.py`
    from _shared import as_dict, as_records, build_client, optional_int, print_json


TENANT_FIELDS = ["TenantID", "TenantDisplayID", "Name", "Email", "PropertyID", "UnitID", "IsActive"]
GENERIC_NAME_FIELDS = ["ID", "Name"]


def list_active_tenants(client: Any, *, page_size: int = 100) -> list[dict[str, Any]]:
    return as_records(
        client.tenants.list(
            fields=TENANT_FIELDS,
            filters=[RQL.eq("IsActive", True)],
            page_size=page_size,
            order_by=["Name"],
        )
    )


def tenant_with_embeds(client: Any, tenant_id: int | str) -> dict[str, Any]:
    return as_dict(client.tenants.get(tenant_id, embeds=["Contacts", "Leases"]))


def generic_contains_search(
    client: Any,
    endpoint: str,
    field: str,
    value: str,
    *,
    fields: list[str] | None = None,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    return as_records(
        client.get(
            endpoint,
            fields=fields or GENERIC_NAME_FIELDS,
            filters=[RQL.ct(field, value)],
            page_size=page_size,
        )
    )


def generic_id_search(
    client: Any,
    endpoint: str,
    field: str,
    values: list[int | str],
    *,
    fields: list[str] | None = None,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    return as_records(
        client.get(
            endpoint,
            fields=fields or GENERIC_NAME_FIELDS,
            filters=[RQL.in_(field, values)],
            page_size=page_size,
        )
    )


def rows_with_value(
    client: Any,
    endpoint: str,
    field: str,
    *,
    fields: list[str] | None = None,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    return as_records(
        client.get(
            endpoint,
            fields=fields or GENERIC_NAME_FIELDS,
            filters=[RQL.hv(field)],
            page_size=page_size,
        )
    )


def paged_rows(
    client: Any,
    endpoint: str,
    *,
    fields: list[str] | None = None,
    filters: list[str] | None = None,
    page_size: int = 1000,
    max_pages: int | None = 3,
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {"page_size": page_size, "max_pages": max_pages}
    if fields:
        query["fields"] = fields
    if filters:
        query["filters"] = filters

    rows: list[dict[str, Any]] = []
    for page in client.iter_pages(endpoint, **query):
        rows.extend(as_records(page.data))
    return rows


def newest_rows(
    client: Any,
    endpoint: str,
    date_field: str,
    *,
    fields: list[str] | None = None,
    page_size: int = 25,
) -> list[dict[str, Any]]:
    query: dict[str, Any] = {"page_size": page_size, "order_by": [f"{date_field} DESC"]}
    if fields:
        query["fields"] = fields
    return as_records(client.get(endpoint, **query))


def main() -> None:
    endpoint = os.getenv("RM_EXAMPLE_ENDPOINT", "Owners")
    search_field = os.getenv("RM_EXAMPLE_SEARCH_FIELD", "Name")
    search_value = os.getenv("RM_EXAMPLE_SEARCH_VALUE", "Smith")
    tenant_id = optional_int("RM_EXAMPLE_TENANT_ID")

    with build_client() as client:
        result: dict[str, Any] = {
            "active_tenants": list_active_tenants(client, page_size=optional_int("RM_EXAMPLE_LIMIT", 10) or 10),
            "generic_contains_search": generic_contains_search(client, endpoint, search_field, search_value),
            "paged_owner_rows": paged_rows(client, "Owners", fields=["OwnerID", "Name"], max_pages=1),
        }
        if tenant_id is not None:
            result["tenant_with_embeds"] = tenant_with_embeds(client, tenant_id)

    print_json(result)


if __name__ == "__main__":
    main()
