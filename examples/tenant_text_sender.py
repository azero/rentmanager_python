from __future__ import annotations

import argparse
import os
from collections.abc import Callable
from typing import Any

from rentmanager_api import RQL
from rentmanager_api.errors import RentManagerBadRequestError

try:
    from examples._shared import (
        as_records,
        build_client,
        env_flag,
        load_default_env_files,
        optional_int,
        print_json,
    )
    from examples.text_conversations import CONVERSATION_FIELDS, conversation_filters, send_text_message
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/tenant_text_sender.py`
    from _shared import as_records, build_client, env_flag, load_default_env_files, optional_int, print_json
    from text_conversations import CONVERSATION_FIELDS, conversation_filters, send_text_message


TENANT_SEARCH_FIELDS = ("Name", "FirstName", "LastName", "TenantDisplayID")
TENANT_FIELDS = (
    "TenantID",
    "TenantDisplayID",
    "Name",
    "FirstName",
    "LastName",
    "Email",
    "PropertyID",
    "UnitID",
    "IsActive",
)
PHONE_FIELD_CANDIDATES = (
    "PhoneNumber",
    "Phone",
    "CellPhone",
    "CellPhoneNumber",
    "MobilePhone",
    "MobilePhoneNumber",
    "HomePhone",
    "HomePhoneNumber",
    "WorkPhone",
    "WorkPhoneNumber",
    "OtherPhone",
    "OtherPhoneNumber",
    "TextNumber",
    "TextPhoneNumber",
)


def _display_name(row: dict[str, Any]) -> str:
    if row.get("Name"):
        return str(row["Name"])

    first = str(row.get("FirstName") or "").strip()
    last = str(row.get("LastName") or "").strip()
    full_name = " ".join(part for part in (first, last) if part)
    if full_name:
        return full_name

    if row.get("TenantDisplayID"):
        return str(row["TenantDisplayID"])
    if row.get("TenantID") is not None:
        return f"Tenant {row['TenantID']}"
    return "Unknown tenant"


def _tenant_dedupe_key(row: dict[str, Any]) -> str:
    tenant_id = row.get("TenantID") or row.get("ID")
    if tenant_id is not None:
        return f"tenant:{tenant_id}"
    return repr(sorted(row.items()))


def _phone_dedupe_key(phone_number: str) -> str:
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    return digits or phone_number.strip().lower()


def _phone_source(row: dict[str, Any], default: str) -> str:
    contact_id = row.get("ContactID")
    if contact_id not in (None, ""):
        return f"contact:{contact_id}"
    return default


def _looks_like_phone_field(field_name: str) -> bool:
    lowered = field_name.lower()
    if lowered.endswith("id"):
        return False
    return "phone" in lowered or lowered in {"textnumber", "textphonenumber"}


def _iter_phone_values(row: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    seen_fields: set[str] = set()

    for field_name in PHONE_FIELD_CANDIDATES:
        seen_fields.add(field_name)
        if field_name in row:
            values.append(row[field_name])

    for field_name, value in row.items():
        if field_name in seen_fields:
            continue
        if _looks_like_phone_field(field_name):
            values.append(value)
    return values


def _add_phone_option(
    options: list[dict[str, str]],
    seen: set[str],
    phone_number: Any,
    source: str,
) -> None:
    phone_text = "" if phone_number is None else str(phone_number).strip()
    if not phone_text:
        return

    key = _phone_dedupe_key(phone_text)
    if key in seen:
        return

    seen.add(key)
    options.append({"phone_number": phone_text, "source": source})


def search_tenants_by_name(client: Any, name: str, *, page_size: int = 25) -> list[dict[str, Any]]:
    query = (name or "").strip()
    if not query:
        raise ValueError("Enter a tenant name to search.")

    matches: list[dict[str, Any]] = []
    seen: set[str] = set()
    for field_name in TENANT_SEARCH_FIELDS:
        try:
            rows = as_records(
                client.tenants.list(
                    fields=list(TENANT_FIELDS),
                    filters=[RQL.ct(field_name, query)],
                    page_size=page_size,
                )
            )
        except RentManagerBadRequestError:
            continue

        for row in rows:
            if row.get("TenantID") is None and row.get("ID") is None:
                continue
            key = _tenant_dedupe_key(row)
            if key in seen:
                continue
            seen.add(key)
            matches.append(row)

    return matches


def tenant_phone_options(
    client: Any,
    tenant: dict[str, Any],
    *,
    conversation_limit: int = 10,
    contact_limit: int = 50,
) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    seen: set[str] = set()

    for value in _iter_phone_values(tenant):
        _add_phone_option(options, seen, value, "tenant")

    tenant_id = tenant.get("TenantID")
    if tenant_id is None:
        return options

    try:
        conversations = as_records(
            client.text_messaging_conversations.list(
                fields=CONVERSATION_FIELDS,
                filters=conversation_filters(parent_type="Tenant", parent_id=tenant_id),
                page_size=conversation_limit,
                order_by=["LastTextDate DESC"],
            )
        )
    except (AttributeError, RentManagerBadRequestError):
        conversations = []

    for conversation in conversations:
        _add_phone_option(options, seen, conversation.get("ExternalPhoneNumber"), "conversation")

    try:
        contacts = as_records(client.tenants.contacts(tenant_id, page_size=contact_limit))
    except (AttributeError, RentManagerBadRequestError):
        contacts = []

    for contact in contacts:
        source = _phone_source(contact, "contact")
        for value in _iter_phone_values(contact):
            _add_phone_option(options, seen, value, source)

    return options


def search_tenant_text_candidates(client: Any, name: str, *, page_size: int = 25) -> dict[str, Any]:
    query = (name or "").strip()
    tenants = search_tenants_by_name(client, query, page_size=page_size)
    return {
        "query": query,
        "matches": [
            {
                "tenant": tenant,
                "tenant_id": tenant.get("TenantID"),
                "display_name": _display_name(tenant),
                "phone_options": tenant_phone_options(client, tenant),
            }
            for tenant in tenants
        ],
    }


def send_text_to_tenant(
    client: Any,
    *,
    tenant: dict[str, Any],
    phone_number: str,
    message: str,
    history_category_id: int | str | None = None,
    is_mms: bool = False,
) -> dict[str, Any]:
    if is_mms:
        raise ValueError("MMS sending is not supported by this single-tenant text sender.")

    tenant_id = tenant.get("TenantID") or tenant.get("ID")
    if tenant_id is None:
        raise ValueError("Selected tenant does not include a TenantID.")

    created = send_text_message(
        client,
        phone_number=phone_number,
        message=message,
        parent_type="Tenant",
        parent_id=tenant_id,
        recipient_name=_display_name(tenant),
        history_category_id=history_category_id,
    )
    return {
        "tenant": tenant,
        "phone_number": phone_number,
        "created_text_broadcast_batch": created,
    }


def _choice_prompt(
    prompt: str,
    *,
    max_choice: int,
    input_func: Callable[[str], str] = input,
) -> int:
    while True:
        raw = input_func(prompt).strip()
        if raw.lower() in {"q", "quit", "exit"}:
            raise SystemExit("Cancelled.")
        try:
            choice = int(raw)
        except ValueError:
            print(f"Enter a number from 1 to {max_choice}, or q to cancel.")
            continue
        if 1 <= choice <= max_choice:
            return choice
        print(f"Enter a number from 1 to {max_choice}, or q to cancel.")


def _print_tenant_options(matches: list[dict[str, Any]]) -> None:
    for index, match in enumerate(matches, start=1):
        tenant = match["tenant"]
        bits = [
            f"TenantID={tenant.get('TenantID')}",
            f"DisplayID={tenant.get('TenantDisplayID')}",
            f"PropertyID={tenant.get('PropertyID')}",
            f"UnitID={tenant.get('UnitID')}",
            f"Active={tenant.get('IsActive')}",
        ]
        phones = ", ".join(f"{option['phone_number']} ({option['source']})" for option in match["phone_options"])
        if not phones:
            phones = "no phone numbers found"
        print(f"{index}. {match['display_name']} | {' | '.join(bits)} | {phones}")


def _choose_phone_number(
    match: dict[str, Any],
    *,
    phone_number: str | None = None,
    input_func: Callable[[str], str] = input,
) -> str:
    if phone_number:
        return phone_number.strip()

    options = match["phone_options"]
    if len(options) == 1:
        return options[0]["phone_number"]

    if options:
        print("Phone options:")
        for index, option in enumerate(options, start=1):
            print(f"{index}. {option['phone_number']} ({option['source']})")
        choice = _choice_prompt("Choose phone number: ", max_choice=len(options), input_func=input_func)
        return options[choice - 1]["phone_number"]

    return input_func("No phone number was found. Enter phone number to text: ").strip()


def run_interactive(
    client: Any,
    *,
    name: str,
    message: str | None = None,
    phone_number: str | None = None,
    page_size: int = 25,
    history_category_id: int | None = None,
    is_mms: bool = False,
    auto_confirm: bool = False,
    input_func: Callable[[str], str] = input,
) -> dict[str, Any]:
    result = search_tenant_text_candidates(client, name, page_size=page_size)
    matches = result["matches"]
    if not matches:
        raise RuntimeError(f"No tenants found for {result['query']!r}.")

    _print_tenant_options(matches)
    tenant_choice = _choice_prompt("Choose tenant: ", max_choice=len(matches), input_func=input_func)
    selected = matches[tenant_choice - 1]
    selected_phone_number = _choose_phone_number(selected, phone_number=phone_number, input_func=input_func)
    if not selected_phone_number:
        raise ValueError("phone_number is required.")

    text_message = message or input_func("Text message to send: ").strip()
    if not text_message:
        raise ValueError("message is required.")

    print()
    print(f"Tenant: {selected['display_name']} (TenantID={selected['tenant_id']})")
    print(f"Phone: {selected_phone_number}")
    print(f"Message: {text_message}")
    if not auto_confirm:
        answer = input_func("Send this text? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            return {
                "cancelled": True,
                "tenant": selected["tenant"],
                "phone_number": selected_phone_number,
            }

    return send_text_to_tenant(
        client,
        tenant=selected["tenant"],
        phone_number=selected_phone_number,
        message=text_message,
        history_category_id=history_category_id,
        is_mms=is_mms,
    )


def _parser() -> argparse.ArgumentParser:
    load_default_env_files()
    parser = argparse.ArgumentParser(description="Search for a tenant, choose a phone number, and send a text.")
    parser.add_argument("name", nargs="?", help="Tenant name or partial tenant name to search.")
    parser.add_argument(
        "--message",
        help="Text message to send. Prompts when omitted.",
    )
    parser.add_argument(
        "--phone-number",
        help="Override discovered tenant phone numbers. Otherwise the selected tenant's discovered number is used.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=optional_int("RM_EXAMPLE_LIMIT", default=25) or 25,
        help="Tenant page size for each name field search.",
    )
    parser.add_argument(
        "--history-category-id",
        type=int,
        default=optional_int("RM_EXAMPLE_HISTORY_CATEGORY_ID"),
        help="Optional HistoryCategoryID to attach to the outgoing text.",
    )
    parser.add_argument(
        "--mms",
        action="store_true",
        default=env_flag("RM_EXAMPLE_IS_MMS"),
        help="Mark the outgoing text as MMS.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=env_flag("RM_EXAMPLE_SEND_TEXT"),
        help="Send after tenant/message selection without a final confirmation prompt.",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    name = args.name or os.getenv("RM_EXAMPLE_SEARCH_NAME")
    if not name:
        name = input("Tenant name to search: ").strip()

    with build_client() as client:
        result = run_interactive(
            client,
            name=name,
            message=args.message,
            phone_number=args.phone_number,
            page_size=args.limit,
            history_category_id=args.history_category_id,
            is_mms=args.mms,
            auto_confirm=args.yes,
        )
    print_json(result)


if __name__ == "__main__":
    main()
