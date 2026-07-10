from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol


class TokenStore(Protocol):
    def load(self) -> str | None: ...

    def save(self, token: str) -> None: ...

    def clear(self) -> None: ...


class InMemoryTokenStore:
    def __init__(self, token: str | None = None) -> None:
        self._token = token

    def load(self) -> str | None:
        return self._token

    def save(self, token: str) -> None:
        self._token = token

    def clear(self) -> None:
        self._token = None


class FileTokenStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> str | None:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        token = payload.get("token") if isinstance(payload, dict) else None
        return token if isinstance(token, str) and token.strip() else None

    def save(self, token: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"token": token}), encoding="utf-8")

    def clear(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            return
