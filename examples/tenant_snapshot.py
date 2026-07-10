from __future__ import annotations

from typing import Any

try:
    from examples._shared import as_dict, as_records, build_client, env_flag, optional_int, print_json, required_int
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/tenant_snapshot.py`
    from _shared import as_dict, as_records, build_client, env_flag, optional_int, print_json, required_int


TENANT_FIELDS = ["TenantID", "TenantDisplayID", "Name", "Email", "PropertyID", "UnitID", "IsActive"]


def lookup_tenant_snapshot(
    client: Any,
    tenant_id: int | str,
    *,
    include_history: bool = False,
    include_financials: bool = True,
    page_size: int = 100,
) -> dict[str, Any]:
    result = {
        "tenant_id": tenant_id,
        "tenant": as_dict(client.tenants.get(tenant_id, fields=TENANT_FIELDS)),
        "contacts": as_records(client.tenants.contacts(tenant_id, page_size=page_size)),
        "leases": as_records(client.tenants.leases(tenant_id, page_size=page_size)),
        "addresses": as_records(client.tenants.addresses(tenant_id)),
        "transactions": [],
        "recurring_charges": [],
        "user_defined_values": [],
        "history": [],
    }
    if include_financials:
        result["transactions"] = as_records(client.tenants.transactions(tenant_id, page_size=page_size))
        result["recurring_charges"] = as_records(client.tenants.recurring_charges(tenant_id, page_size=page_size))
    result["user_defined_values"] = as_records(client.tenants.user_defined_values(tenant_id, page_size=page_size))
    if include_history:
        result["history"] = as_records(client.tenants.history(tenant_id, page_size=page_size))
    return result


def main() -> None:
    tenant_id = required_int("RM_EXAMPLE_TENANT_ID")
    page_size = optional_int("RM_EXAMPLE_LIMIT", default=100) or 100

    with build_client() as client:
        result = lookup_tenant_snapshot(
            client,
            tenant_id,
            include_history=env_flag("RM_EXAMPLE_INCLUDE_HISTORY"),
            include_financials=not env_flag("RM_EXAMPLE_SKIP_FINANCIALS"),
            page_size=page_size,
        )
    print_json(result)


if __name__ == "__main__":
    main()
