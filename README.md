# rentmanager_api

[![CI](https://github.com/azero/rentmanager_python/actions/workflows/ci.yml/badge.svg)](https://github.com/azero/rentmanager_python/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](https://www.python.org/downloads/)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue.svg)](LICENSE)

A typed synchronous and asynchronous Python SDK for Rent Manager WAPI12. It combines convenient resource
namespaces with a generic request interface, so applications can use modeled endpoints today without losing access to
new or less common endpoints.

> [!IMPORTANT]
> This is an independent, community-maintained project. It is not affiliated with, endorsed by, or supported by
> Rent Manager or London Computer Systems. You need your own authorized Rent Manager WAPI12 account and must follow
> the provider's terms and your organization's data-handling requirements.

## Features

- Synchronous and asynchronous clients built on `httpx`
- Typed Pydantic models and resource namespaces across accounting, leasing, maintenance, communications, reporting,
  utilities, properties, owners, and platform metadata
- RQL filter helpers, field selection, embedding, pagination, and page iteration
- Structured authentication, transport, rate-limit, and API errors
- Configurable in-memory or file-backed authentication token storage
- Generic endpoint and action methods for API surface not yet modeled
- Optional helpers for service-ticket and email-lookup workflows
- Mock-based test suite; live tests and write operations are opt-in

## Requirements

- Python 3.10 or newer
- Rent Manager WAPI12 credentials and API access

## Installation

Until a package is published to PyPI, install directly from GitHub:

```bash
python -m pip install "git+https://github.com/azero/rentmanager_python.git"
```

For local development:

```bash
git clone https://github.com/azero/rentmanager_python.git
cd rentmanager_python
python -m venv .venv
```

Activate the virtual environment, then install the project and development tools:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Quick start

```python
from rentmanager_api import RQL, RentManagerClient

with RentManagerClient(
    corp_id="your-corp-id",
    username="your-api-user",
    password="your-api-password",
    location_id=1,
) as client:
    tenants = client.tenants.list(
        fields=["TenantID", "Name"],
        filters=[RQL.eq("IsActive", True)],
        page_size=100,
    )

    for tenant in tenants:
        print(tenant.TenantID, tenant.Name)
```

The default API base URL is `https://<corp-id>.api.rentmanager.com`. Pass `base_url=` when your environment uses a
different endpoint.

### Async client

```python
import asyncio

from rentmanager_api import AsyncRentManagerClient


async def main() -> None:
    async with AsyncRentManagerClient(
        "your-corp-id",
        "your-api-user",
        "your-api-password",
        location_id=1,
    ) as client:
        properties = await client.properties.list(page_size=100)
        print(properties)


asyncio.run(main())
```

### Generic endpoint access

Use the generic interface when a resource is not modeled yet:

```python
rows = client.get("CustomResource", filters="Name,ct,Smith")
result = client.action(
    "RecurringCharges/PostRecurringCharges",
    {"PostDate": "2026-07-09"},
)
```

### Token storage

Clients use memory-only token storage by default. To reuse an API token between runs, explicitly provide a file store:

```python
from rentmanager_api import FileTokenStore, RentManagerClient

client = RentManagerClient(
    "your-corp-id",
    "your-api-user",
    "your-api-password",
    token_store=FileTokenStore(".rentmanager-token.json"),
)
```

Token files matching `.rentmanager-*.json` are ignored by Git. Never commit credentials, API tokens, `.env` files, or
real customer data.

## Examples

Copy the safe template and fill in only the values needed by the example you want to run:

```bash
cp .env.example .env
python examples/basic_usage.py
```

On PowerShell, use `Copy-Item .env.example .env`. Environment variables override values in `.env`; set `RM_ENV_FILE`
to load another file. Useful examples include:

```bash
python examples/name_id_lookup.py --type all "Smith"
python examples/tenant_text_sender.py "Smith"
python examples/landscaping_ticket_workflow.py "123 Example Street" 125.00
```

Some examples perform writes or send messages. Review their confirmation output and source before running them against
a live account. Opt-in flags such as `--auto-approve` should only be used when the target IDs and payload are verified.

## Endpoint coverage

The WAPI overview describes the API conventions but does not provide a complete public endpoint and model catalog. This
SDK therefore ships known typed resources plus a registry and generic caller:

```python
from rentmanager_api import EndpointRegistry

for endpoint in EndpointRegistry.default().coverage_report():
    print(endpoint["method"], endpoint["path"], endpoint["confidence"])
```

Generated resources use a PascalCase model, a `<Name>Resource` resource class, and a snake_case client attribute.
Standard resources inherit `list`, `get`, `create`, `update`, `delete`, `paginate`, and `iter_pages`. Custom methods are
reserved for action endpoints or special payloads.

## Development

Run the same checks used by CI:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m build
```

Tests use mocked transports unless explicitly marked for live execution. Live write/delete tests remain disabled unless
`RM_LIVE_WRITE_TESTS` is enabled. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow and
[SECURITY.md](SECURITY.md) for private vulnerability reporting.

## License

This project is source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE). You may use, modify, and
redistribute it for permitted noncommercial purposes, provided the license and required attribution notice remain with
copies. Commercial use or inclusion in a commercial product is not permitted without a separate license from the
copyright holder.
