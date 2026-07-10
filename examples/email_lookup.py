from __future__ import annotations

import os
from typing import Any

from rentmanager_api.workflows import lookup_by_email

try:
    from examples._shared import build_client, env_flag, print_json
except ModuleNotFoundError:  # pragma: no cover - supports `python examples/email_lookup.py`
    from _shared import build_client, env_flag, print_json


def summarize_matches(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "sender_email": result.get("sender_email"),
        "total_matches": result.get("total_matches", 0),
        "matches": [
            {"entity": match.get("entity"), **(match.get("identity") or {})} for match in result.get("matches", [])
        ],
    }


def lookup_email(
    client: Any, email: str, *, include_contacts: bool = True, summary_only: bool = False
) -> dict[str, Any]:
    result = lookup_by_email(client, email, include_contacts=include_contacts)
    return summarize_matches(result) if summary_only else result


def main() -> None:
    email = os.environ["RM_EXAMPLE_EMAIL"]
    include_contacts = not env_flag("RM_EXAMPLE_SKIP_CONTACTS")
    summary_only = env_flag("RM_EXAMPLE_SUMMARY_ONLY", default=True)

    with build_client() as client:
        result = lookup_email(
            client,
            email,
            include_contacts=include_contacts,
            summary_only=summary_only,
        )
    print_json(result)


if __name__ == "__main__":
    main()
