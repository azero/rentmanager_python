from __future__ import annotations

import os

from rentmanager_api import RentManagerClient
from rentmanager_api.workflows import create_service_ticket


def main() -> None:
    client = RentManagerClient(
        corp_id=os.environ["RM_CORP_ID"],
        username=os.environ["RM_USERNAME"],
        password=os.environ["RM_PASSWORD"],
        location_id=int(os.environ["RM_LOCATION_ID"]) if os.getenv("RM_LOCATION_ID") else None,
    )
    issue = create_service_ticket(
        client,
        title="Vendor service request",
        description="Created from rentmanager_api example.",
        property_id=int(os.environ["RM_EXAMPLE_PROPERTY_ID"]),
        line_items=[{"Description": "Review invoice", "Quantity": 1}],
    )
    print(issue)


if __name__ == "__main__":
    main()
