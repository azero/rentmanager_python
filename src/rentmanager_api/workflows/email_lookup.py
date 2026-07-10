from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def _as_dict(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [_as_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: _as_dict(item) for key, item in value.items()}
    return value


def _contains_email(value: Any, target_email: str) -> bool:
    value = _as_dict(value)
    if value is None:
        return False
    if isinstance(value, str):
        return target_email in value.lower()
    if isinstance(value, list):
        return any(_contains_email(item, target_email) for item in value)
    if isinstance(value, dict):
        return any(_contains_email(item, target_email) for item in value.values())
    return False


def _identity(record: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "ID",
        "ContactID",
        "ParentType",
        "ParentID",
        "TenantID",
        "ProspectID",
        "OwnerID",
        "VendorID",
        "Name",
        "CompanyName",
        "FirstName",
        "LastName",
        "Status",
        "IsActive",
    ]
    return {key: record.get(key) for key in keys if key in record}


def _match(entity: str, record: Any) -> dict[str, Any]:
    row = _as_dict(record)
    return {
        "entity": entity,
        "identity": _identity(row),
        "record": row,
    }


def _dedupe(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for match in matches:
        record = match.get("record") or {}
        key = None
        for id_key in ("ContactID", "OwnerID", "TenantID", "ProspectID", "VendorID", "ID"):
            if record.get(id_key) is not None:
                key = f"{match['entity']}:{id_key}:{record[id_key]}"
                break
        if key is None:
            key = repr(sorted(record.items()))
        if key in seen:
            continue
        seen.add(key)
        output.append(match)
    return output


def lookup_by_email(client: Any, email: str, *, include_contacts: bool = True) -> dict[str, Any]:
    target = (email or "").strip().lower()
    if not target:
        return {"sender_email": email, "total_matches": 0, "matches": []}

    fetchers = [
        ("Owner", client.owners.list),
        ("Tenant", client.tenants.list),
        ("Prospect", client.prospects.list),
        ("Vendor", client.vendors.list),
    ]
    if include_contacts:
        fetchers.append(("Contact", client.contacts.list))

    matches: list[dict[str, Any]] = []
    for entity, fetch in fetchers:
        rows = fetch()
        for row in rows or []:
            if _contains_email(row, target):
                matches.append(_match(entity, row))

    matches = _dedupe(matches)
    return {"sender_email": email, "total_matches": len(matches), "matches": matches}
