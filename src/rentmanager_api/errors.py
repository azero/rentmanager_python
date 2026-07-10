from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(slots=True)
class ErrorModel:
    developer_message: str | None = None
    user_message: str | None = None
    message: str | None = None
    details: Any = None


class RentManagerAPIError(Exception):
    """Base exception for Rent Manager API failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        method: str | None = None,
        url: str | None = None,
        details: Any = None,
        developer_message: str | None = None,
        user_message: str | None = None,
        response_headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.method = method
        self.url = url
        self.details = details
        self.developer_message = developer_message
        self.user_message = user_message
        self.response_headers = response_headers or {}


class RentManagerBadRequestError(RentManagerAPIError):
    pass


class RentManagerAuthError(RentManagerAPIError):
    pass


class RentManagerPermissionError(RentManagerAPIError):
    pass


class RentManagerNotFoundError(RentManagerAPIError):
    pass


class RentManagerConflictError(RentManagerAPIError):
    pass


class RentManagerPreconditionError(RentManagerAPIError):
    pass


class RentManagerRateLimitError(RentManagerAPIError):
    pass


class RentManagerServerError(RentManagerAPIError):
    pass


class RentManagerTransportError(RentManagerAPIError):
    pass


STATUS_ERROR_MAP: dict[int, type[RentManagerAPIError]] = {
    400: RentManagerBadRequestError,
    401: RentManagerAuthError,
    403: RentManagerPermissionError,
    404: RentManagerNotFoundError,
    409: RentManagerConflictError,
    412: RentManagerPreconditionError,
    429: RentManagerRateLimitError,
}


def parse_error_model(response: httpx.Response) -> ErrorModel:
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return ErrorModel(message=text or response.reason_phrase)

    if not isinstance(payload, dict):
        return ErrorModel(message=str(payload))

    nested = payload.get("error") if isinstance(payload.get("error"), dict) else payload
    return ErrorModel(
        developer_message=nested.get("DeveloperMessage") or nested.get("developerMessage"),
        user_message=nested.get("UserMessage") or nested.get("userMessage"),
        message=nested.get("Message") or nested.get("message") or nested.get("error"),
        details=payload,
    )


def error_from_response(response: httpx.Response) -> RentManagerAPIError:
    error_model = parse_error_model(response)
    error_cls = STATUS_ERROR_MAP.get(response.status_code)
    if error_cls is None:
        error_cls = RentManagerServerError if response.status_code >= 500 else RentManagerAPIError

    request = response.request
    message = (
        error_model.developer_message
        or error_model.user_message
        or error_model.message
        or response.reason_phrase
        or f"Rent Manager API request failed with status {response.status_code}"
    )
    return error_cls(
        message,
        status_code=response.status_code,
        method=request.method if request else None,
        url=str(request.url) if request else None,
        details=error_model.details,
        developer_message=error_model.developer_message,
        user_message=error_model.user_message,
        response_headers=dict(response.headers),
    )
