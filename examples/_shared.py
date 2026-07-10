from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from rentmanager_api import AsyncRentManagerClient, FileTokenStore, RentManagerClient


def _env_paths() -> list[Path]:
    explicit_path = os.getenv("RM_ENV_FILE")
    if explicit_path:
        return [Path(explicit_path).expanduser()]

    paths = [Path.cwd() / ".env", Path(__file__).resolve().parents[1] / ".env"]
    unique_paths: list[Path] = []
    for path in paths:
        if path not in unique_paths:
            unique_paths.append(path)
    return unique_paths


def _unquote_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_env_file(path: str | os.PathLike[str] = ".env", *, override: bool = False) -> dict[str, str]:
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return {}

    loaded: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or (key in os.environ and not override):
            continue

        loaded_value = _unquote_env_value(value)
        os.environ[key] = loaded_value
        loaded[key] = loaded_value
    return loaded


def load_default_env_files() -> dict[str, str]:
    loaded: dict[str, str] = {}
    for path in _env_paths():
        loaded.update(load_env_file(path))
    return loaded


def optional_int(name: str, default: int | None = None) -> int | None:
    load_default_env_files()
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def required_int(name: str) -> int:
    value = optional_int(name)
    if value is None:
        raise RuntimeError(f"Set {name} to run this example.")
    return value


def env_flag(name: str, default: bool = False) -> bool:
    load_default_env_files()
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def as_dict(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return as_dict(value.model_dump(mode="json"))
    if isinstance(value, list):
        return [as_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: as_dict(item) for key, item in value.items()}
    return value


def as_records(rows: Any) -> list[dict[str, Any]]:
    if rows is None:
        return []
    if not isinstance(rows, list):
        rows = [rows]
    return [as_dict(row) for row in rows]


def print_json(payload: Any) -> None:
    print(json.dumps(as_dict(payload), indent=2, sort_keys=True, default=str))


def build_client(*, token_path: str = ".rentmanager-token.json") -> RentManagerClient:
    load_default_env_files()
    return RentManagerClient(
        corp_id=os.environ["RM_CORP_ID"],
        username=os.environ["RM_USERNAME"],
        password=os.environ["RM_PASSWORD"],
        location_id=optional_int("RM_LOCATION_ID"),
        token_store=FileTokenStore(token_path),
    )


def build_async_client(*, token_path: str = ".rentmanager-token.json") -> AsyncRentManagerClient:
    load_default_env_files()
    return AsyncRentManagerClient(
        corp_id=os.environ["RM_CORP_ID"],
        username=os.environ["RM_USERNAME"],
        password=os.environ["RM_PASSWORD"],
        location_id=optional_int("RM_LOCATION_ID"),
        token_store=FileTokenStore(token_path),
    )
