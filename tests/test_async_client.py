import httpx
import pytest

from rentmanager_api import AsyncRentManagerClient, InMemoryTokenStore, RentManagerNotFoundError


@pytest.mark.asyncio
async def test_async_client_authenticates_and_lists_resources():
    seen = []

    async def handler(request):
        seen.append((request.method, request.url.path, request.headers.get("X-RM12Api-ApiToken")))
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="async-token")
        return httpx.Response(200, json=[{"PropertyID": 11, "Name": "Main"}])

    client = AsyncRentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=InMemoryTokenStore(),
        max_retries=0,
    )

    properties = await client.properties.list()
    await client.aclose()

    assert properties[0].PropertyID == 11
    assert seen == [
        ("POST", "/Authentication/AuthorizeUser", None),
        ("GET", "/Properties", "async-token"),
    ]


@pytest.mark.asyncio
async def test_async_iter_pages_yields_all_pages():
    async def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="async-token")
        page_number = int(request.url.params["pagenumber"])
        headers = {
            "Link": '<https://sampleco.api.rentmanager.com/Owners?pagenumber=2&pagesize=1>; rel="next"'
            if page_number == 1
            else "",
            "X-Total-Results": "2",
        }
        return httpx.Response(200, json=[{"OwnerID": page_number}], headers=headers)

    client = AsyncRentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=InMemoryTokenStore(),
        max_retries=0,
    )

    pages = []
    async for page in client.iter_pages("Owners", page_size=1):
        pages.append(page)
    await client.aclose()

    assert [page.data[0]["OwnerID"] for page in pages] == [1, 2]


@pytest.mark.asyncio
async def test_async_download_bytes_authenticates_and_returns_raw_content():
    seen = []

    async def handler(request):
        seen.append((request.method, request.url.path, request.headers.get("X-RM12Api-ApiToken")))
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="async-token")
        return httpx.Response(200, content=b"async-pdf-bytes")

    client = AsyncRentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=InMemoryTokenStore(),
        max_retries=0,
    )

    content = await client.download_bytes("Files/45")
    await client.aclose()

    assert content == b"async-pdf-bytes"
    assert seen == [
        ("POST", "/Authentication/AuthorizeUser", None),
        ("GET", "/Files/45", "async-token"),
    ]


@pytest.mark.asyncio
async def test_async_download_bytes_uses_error_mapping():
    async def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="async-token")
        return httpx.Response(404, json={"DeveloperMessage": "Missing async file"})

    client = AsyncRentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=InMemoryTokenStore(),
        max_retries=0,
    )

    with pytest.raises(RentManagerNotFoundError) as exc:
        await client.download_bytes("Files/404")
    await client.aclose()

    assert exc.value.developer_message == "Missing async file"
