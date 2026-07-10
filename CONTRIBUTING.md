# Contributing

Thanks for helping improve `rentmanager_api`.

## Before you begin

- Open an issue before a large or breaking change so the approach can be discussed.
- Never include credentials, API tokens, real tenant data, exports, or other customer information in issues, fixtures,
  screenshots, commits, or logs.
- By submitting a contribution, you agree that it may be distributed under this project's PolyForm Noncommercial 1.0.0
  license and required attribution notice.

## Local setup

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Activate the virtual environment using the command appropriate for your shell.

## Checks

Run these before opening a pull request:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m build
```

Add mocked tests for every behavior change. Live tests must remain opt-in, and code that writes to a Rent Manager account
must never run in CI by default.

## Pull requests

Keep each pull request focused. Explain what changed, why it changed, the tests performed, and any API compatibility or
security considerations. Update the README and changelog when behavior visible to users changes.
