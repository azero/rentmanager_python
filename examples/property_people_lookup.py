from __future__ import annotations

from typing import Any

from rentmanager_api import RQL

try:
    from examples._shared import as_dict, as_records, build_client, env_flag, print_json, required_int
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/property_people_lookup.py`
    from _shared import as_dict, as_records, build_client, env_flag, print_json, required_int


PROPERTY_FIELDS = ["PropertyID", "Name", "ShortName", "PrimaryOwnerID", "IsActive"]
OWNER_FIELDS = ["OwnerID", "Name", "CompanyName", "FirstName", "LastName", "Email", "IsActive"]
TENANT_FIELDS = [
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
]
UNIT_FIELDS = ["UnitID", "PropertyID", "Name", "UnitNumber", "IsActive"]
LEASE_FIELDS = ["LeaseID", "TenantID", "UnitID", "PropertyID", "MoveInDate", "MoveOutDate"]


def tenant_filters_for_property(property_id: int | str, *, active_only: bool = True) -> list[str]:
    filters = [RQL.eq("PropertyID", property_id)]
    if active_only:
        filters.append(RQL.eq("IsActive", True))
    return filters


def lease_filters_for_property(property_id: int | str) -> list[str]:
    return [RQL.eq("PropertyID", property_id)]


def lookup_property_people(
    client: Any,
    property_id: int | str,
    *,
    active_only: bool = True,
    include_leases: bool = True,
    page_size: int = 1000,
) -> dict[str, Any]:
    property_row = as_dict(client.properties.get(property_id, fields=PROPERTY_FIELDS))
    primary_owner_id = property_row.get("PrimaryOwnerID") if isinstance(property_row, dict) else None
    owner = as_dict(client.owners.get(primary_owner_id, fields=OWNER_FIELDS)) if primary_owner_id is not None else None
    tenants = as_records(
        client.tenants.list(
            fields=TENANT_FIELDS,
            filters=tenant_filters_for_property(property_id, active_only=active_only),
            page_size=page_size,
        )
    )
    units = as_records(client.properties.units(property_id, fields=UNIT_FIELDS))
    leases = (
        as_records(
            client.leases.list(
                fields=LEASE_FIELDS,
                filters=lease_filters_for_property(property_id),
                page_size=page_size,
            )
        )
        if include_leases
        else []
    )

    return {
        "property_id": property_id,
        "property": property_row,
        "owner": owner,
        "tenants": tenants,
        "units": units,
        "leases": leases,
    }


def main() -> None:
    property_id = required_int("RM_EXAMPLE_PROPERTY_ID")
    active_only = not env_flag("RM_EXAMPLE_INCLUDE_INACTIVE")
    include_leases = not env_flag("RM_EXAMPLE_SKIP_LEASES")

    with build_client() as client:
        result = lookup_property_people(
            client,
            property_id,
            active_only=active_only,
            include_leases=include_leases,
        )
    print_json(result)


if __name__ == "__main__":
    main()
