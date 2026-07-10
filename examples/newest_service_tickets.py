from __future__ import annotations

import json
import os

from rentmanager_api import FileTokenStore, RentManagerClient
from rentmanager_api.workflows import (
    export_newest_service_ticket_details,
    get_newest_service_tickets as get_newest_service_tickets,
)


def _optional_int(name: str) -> int | None:
    value = os.getenv(name)
    return int(value) if value else None


def main() -> None:
    with RentManagerClient(
        corp_id=os.environ["RM_CORP_ID"],
        username=os.environ["RM_USERNAME"],
        password=os.environ["RM_PASSWORD"],
        location_id=_optional_int("RM_LOCATION_ID"),
        token_store=FileTokenStore(".rentmanager-token.json"),
    ) as client:
        manifest = export_newest_service_ticket_details(
            client,
            limit=_optional_int("RM_SERVICE_TICKET_LIMIT") or 5,
            export_root=os.getenv("RM_SERVICE_TICKET_EXPORT_ROOT"),
            max_pages=_optional_int("RM_SERVICE_TICKET_MAX_PAGES"),
        )

    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
