from __future__ import annotations

from typing import Any

from rentmanager_api import RQL

try:
    from examples._shared import as_dict, as_records, build_client, env_flag, print_json, required_int
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/owner_property_lookup.py`
    from _shared import as_dict, as_records, build_client, env_flag, print_json, required_int


OWNER_FIELDS = ["OwnerID", "Name", "CompanyName", "FirstName", "LastName", "Email", "IsActive"]
PROPERTY_FIELDS = ["PropertyID", "Name", "ShortName", "PrimaryOwnerID", "IsActive"]


def property_filters_for_owner(owner_id: int | str, *, active_only: bool = True) -> list[str]:
    filters = [RQL.eq("PrimaryOwnerID", owner_id)]
    if active_only:
        filters.append(RQL.eq("IsActive", True))
    return filters


def lookup_owner_properties(
    client: Any,
    owner_id: int | str,
    *,
    active_only: bool = True,
    include_owner: bool = True,
    page_size: int = 1000,
) -> dict[str, Any]:
    owner = as_dict(client.owners.get(owner_id, fields=OWNER_FIELDS)) if include_owner else None
    properties = as_records(
        client.properties.list(
            fields=PROPERTY_FIELDS,
            filters=property_filters_for_owner(owner_id, active_only=active_only),
            page_size=page_size,
        )
    )
    return {
        "owner_id": owner_id,
        "owner": owner,
        "properties": properties,
    }


def main() -> None:
    owner_id = required_int("RM_EXAMPLE_OWNER_ID")
    active_only = not env_flag("RM_EXAMPLE_INCLUDE_INACTIVE")

    with build_client() as client:
        result = lookup_owner_properties(client, owner_id, active_only=active_only)
    print_json(result)


if __name__ == "__main__":
    main()
