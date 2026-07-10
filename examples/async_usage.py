from __future__ import annotations

import asyncio
from _shared import build_async_client


async def main() -> None:
    async with build_async_client() as client:
        properties = await client.properties.list(page_size=100)
        for property_row in properties:
            print(property_row.PropertyID, property_row.Name)


if __name__ == "__main__":
    asyncio.run(main())
