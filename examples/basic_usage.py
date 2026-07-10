from __future__ import annotations

from _shared import build_client
from rentmanager_api import RQL


def main() -> None:
    with build_client() as client:
        tenants = client.tenants.list(
            fields=["TenantID", "Name"],
            filters=[RQL.eq("IsActive", True)],
            page_size=100,
        )
        for tenant in tenants:
            print(tenant.TenantID, tenant.Name)


if __name__ == "__main__":
    main()
