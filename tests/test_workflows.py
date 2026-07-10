import httpx

from rentmanager_api import InMemoryTokenStore, RentManagerClient
from rentmanager_api.workflows import lookup_by_email


def test_lookup_by_email_scans_core_entities_and_contacts():
    payloads = {
        "/Owners": [{"OwnerID": 1, "Name": "Owner", "Email": "owner@example.com"}],
        "/Tenants": [{"TenantID": 2, "Name": "Tenant", "Email": "other@example.com"}],
        "/Prospects": [{"ProspectID": 3, "Name": "Prospect", "Email": None}],
        "/Vendors": [{"VendorID": 4, "Name": "Vendor", "Email": "vendor@example.com"}],
        "/Contacts": [{"ContactID": 9, "ParentType": "Tenant", "ParentID": 2, "Email": "target@example.com"}],
    }

    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="token")
        return httpx.Response(200, json=payloads[request.url.path])

    client = RentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=InMemoryTokenStore(),
        max_retries=0,
    )

    result = lookup_by_email(client, "target@example.com")

    assert result["sender_email"] == "target@example.com"
    assert result["total_matches"] == 1
    assert result["matches"][0]["entity"] == "Contact"
    assert result["matches"][0]["record"]["ContactID"] == 9
