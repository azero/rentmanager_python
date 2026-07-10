from __future__ import annotations

import asyncio
import json as jsonlib
import time
from collections.abc import AsyncIterator, Iterator, Mapping
from typing import Any

import httpx

from .errors import RentManagerTransportError, error_from_response
from .pagination import Page, parse_link_header, total_results_from_headers
from .query import QueryParams, query_params_from_kwargs
from .resources import attach_resources
from .token_store import InMemoryTokenStore, TokenStore

RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


class _ClientMixin:
    base_url: str
    corp_id: str
    username: str
    password: str
    location_id: int | None
    token_store: TokenStore
    max_retries: int
    retry_backoff_seconds: float
    _token: str | None

    @staticmethod
    def json_dumps(payload: Any) -> str:
        return jsonlib.dumps(payload, separators=(",", ":"), ensure_ascii=True)

    def _endpoint_path(self, endpoint: str) -> str:
        return "/" + str(endpoint).strip("/")

    def _auth_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"Username": self.username, "Password": self.password}
        if self.location_id is not None:
            payload["LocationID"] = self.location_id
        return payload

    def _set_token(self, token: str) -> None:
        self._token = token
        self.token_store.save(token)

    def _clear_token(self) -> None:
        self._token = None
        self.token_store.clear()

    def _decode_response(self, response: httpx.Response) -> Any:
        if response.status_code == 204 or not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return response.text

    def _merge_params(self, params: Mapping[str, Any] | None, query: Mapping[str, Any]) -> dict[str, Any]:
        merged = dict(params or {})
        if query:
            merged.update(query_params_from_kwargs(query))
        return merged

    def _page_from_response(
        self,
        response: httpx.Response,
        *,
        page_number: int,
        page_size: int,
    ) -> Page:
        data = self._decode_response(response)
        rows = data if isinstance(data, list) else [data]
        headers = dict(response.headers)
        return Page(
            data=rows,
            status_code=response.status_code,
            headers=headers,
            page_number=page_number,
            page_size=page_size,
            total_results=total_results_from_headers(headers),
            links=parse_link_header(response.headers.get("Link")),
        )


class RentManagerClient(_ClientMixin):
    def __init__(
        self,
        corp_id: str,
        username: str,
        password: str,
        *,
        location_id: int | None = None,
        base_url: str | None = None,
        timeout: float = 15.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.4,
        token_store: TokenStore | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.corp_id = corp_id
        self.username = username
        self.password = password
        self.location_id = location_id
        self.base_url = (base_url or f"https://{corp_id}.api.rentmanager.com").rstrip("/")
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self.token_store = token_store or InMemoryTokenStore()
        self._token: str | None = None
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        attach_resources(self)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RentManagerClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def authenticate(self, *, force: bool = False) -> str:
        if not force:
            cached = self._token or self.token_store.load()
            if cached:
                self._token = cached
                return cached

        response = self._request_raw(
            "POST",
            "Authentication/AuthorizeUser",
            auth=False,
            json=self._auth_payload(),
        )
        payload = self._decode_response(response)
        token = payload.get("Token") if isinstance(payload, dict) else payload
        if not isinstance(token, str) or not token.strip():
            raise RentManagerTransportError("Authentication response did not contain an API token.")
        self._set_token(token)
        return token

    def authorize_token(self, token: str) -> Any:
        return self.request("POST", "Authentication/AuthorizeToken", auth=False, params={"token": token})

    def change_location(self, location_id: int) -> Any:
        result = self.post("Authentication/ChangeLocation", params={"locationID": location_id})
        self.location_id = location_id
        return result

    def _ensure_token(self) -> None:
        if self._token:
            return
        cached = self.token_store.load()
        if cached:
            self._token = cached
            return
        self.authenticate(force=True)

    def _headers(self, headers: Mapping[str, str] | None, auth: bool) -> dict[str, str]:
        merged = dict(headers or {})
        if auth and self._token:
            merged["X-RM12Api-ApiToken"] = self._token
        return merged

    def _send_once(self, method: str, endpoint: str, *, auth: bool, **kwargs: Any) -> httpx.Response:
        if auth:
            self._ensure_token()
        headers = self._headers(kwargs.pop("headers", None), auth)
        return self._client.request(method, self._endpoint_path(endpoint), headers=headers, **kwargs)

    def _request_raw(
        self,
        method: str,
        endpoint: str,
        *,
        auth: bool = True,
        retry_auth: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        attempts = self.max_retries + 1
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = self._send_once(method, endpoint, auth=auth, **kwargs)
            except httpx.TransportError as exc:
                last_error = exc
                if attempt >= attempts:
                    raise RentManagerTransportError(str(exc)) from exc
                time.sleep(self.retry_backoff_seconds * attempt)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < attempts:
                time.sleep(self.retry_backoff_seconds * attempt)
                continue

            if response.status_code == 401 and auth and retry_auth:
                self._clear_token()
                self.authenticate(force=True)
                return self._request_raw(method, endpoint, auth=auth, retry_auth=False, **kwargs)

            if response.is_error:
                raise error_from_response(response)
            return response

        raise RentManagerTransportError(str(last_error or "Request failed."))

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        auth: bool = True,
        headers: Mapping[str, str] | None = None,
        **query: Any,
    ) -> Any:
        merged_params = self._merge_params(params, query)
        response = self._request_raw(
            method,
            endpoint,
            auth=auth,
            params=merged_params or None,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )
        return self._decode_response(response)

    def get(self, endpoint: str, *, params: Mapping[str, Any] | None = None, **query: Any) -> Any:
        return self.request("GET", endpoint, params=params, **query)

    def download_bytes(self, endpoint: str, *, params: Mapping[str, Any] | None = None, **query: Any) -> bytes:
        merged_params = self._merge_params(params, query)
        response = self._request_raw("GET", endpoint, params=merged_params or None)
        return response.content

    def post(
        self,
        endpoint: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        **query: Any,
    ) -> Any:
        return self.request("POST", endpoint, params=params, json=json, **query)

    def delete(
        self,
        endpoint: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        **query: Any,
    ) -> Any:
        return self.request("DELETE", endpoint, params=params, json=json, **query)

    def action(self, endpoint: str, payload: Any = None, **query: Any) -> Any:
        return self.post(endpoint, json=payload, **query)

    def post_multipart(
        self,
        endpoint: str,
        *,
        files: Any,
        data: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        return self.request("POST", endpoint, params=params, files=files, data=data)

    def paginate(
        self,
        endpoint: str,
        *,
        page_number: int = 1,
        page_size: int = 1000,
        params: Mapping[str, Any] | None = None,
        **query: Any,
    ) -> Page:
        merged = self._merge_params(params, query)
        merged.update(QueryParams(page_number=page_number, page_size=page_size).to_params())
        response = self._request_raw("GET", endpoint, params=merged)
        return self._page_from_response(response, page_number=page_number, page_size=page_size)

    def iter_pages(
        self,
        endpoint: str,
        *,
        page_size: int = 1000,
        start_page: int = 1,
        max_pages: int | None = None,
        **query: Any,
    ) -> Iterator[Page]:
        page_number = start_page
        yielded = 0
        while True:
            page = self.paginate(endpoint, page_number=page_number, page_size=page_size, **query)
            yield page
            yielded += 1
            if max_pages is not None and yielded >= max_pages:
                break
            if "next" not in page.links:
                break
            page_number += 1


class AsyncRentManagerClient(_ClientMixin):
    def __init__(
        self,
        corp_id: str,
        username: str,
        password: str,
        *,
        location_id: int | None = None,
        base_url: str | None = None,
        timeout: float = 15.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.4,
        token_store: TokenStore | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.corp_id = corp_id
        self.username = username
        self.password = password
        self.location_id = location_id
        self.base_url = (base_url or f"https://{corp_id}.api.rentmanager.com").rstrip("/")
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self.token_store = token_store or InMemoryTokenStore()
        self._token: str | None = None
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        attach_resources(self)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncRentManagerClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()

    async def authenticate(self, *, force: bool = False) -> str:
        if not force:
            cached = self._token or self.token_store.load()
            if cached:
                self._token = cached
                return cached

        response = await self._request_raw(
            "POST",
            "Authentication/AuthorizeUser",
            auth=False,
            json=self._auth_payload(),
        )
        payload = self._decode_response(response)
        token = payload.get("Token") if isinstance(payload, dict) else payload
        if not isinstance(token, str) or not token.strip():
            raise RentManagerTransportError("Authentication response did not contain an API token.")
        self._set_token(token)
        return token

    async def authorize_token(self, token: str) -> Any:
        return await self.request("POST", "Authentication/AuthorizeToken", auth=False, params={"token": token})

    async def change_location(self, location_id: int) -> Any:
        result = await self.post("Authentication/ChangeLocation", params={"locationID": location_id})
        self.location_id = location_id
        return result

    async def _ensure_token(self) -> None:
        if self._token:
            return
        cached = self.token_store.load()
        if cached:
            self._token = cached
            return
        await self.authenticate(force=True)

    def _headers(self, headers: Mapping[str, str] | None, auth: bool) -> dict[str, str]:
        merged = dict(headers or {})
        if auth and self._token:
            merged["X-RM12Api-ApiToken"] = self._token
        return merged

    async def _send_once(self, method: str, endpoint: str, *, auth: bool, **kwargs: Any) -> httpx.Response:
        if auth:
            await self._ensure_token()
        headers = self._headers(kwargs.pop("headers", None), auth)
        return await self._client.request(method, self._endpoint_path(endpoint), headers=headers, **kwargs)

    async def _request_raw(
        self,
        method: str,
        endpoint: str,
        *,
        auth: bool = True,
        retry_auth: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        attempts = self.max_retries + 1
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                response = await self._send_once(method, endpoint, auth=auth, **kwargs)
            except httpx.TransportError as exc:
                last_error = exc
                if attempt >= attempts:
                    raise RentManagerTransportError(str(exc)) from exc
                await asyncio.sleep(self.retry_backoff_seconds * attempt)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < attempts:
                await asyncio.sleep(self.retry_backoff_seconds * attempt)
                continue

            if response.status_code == 401 and auth and retry_auth:
                self._clear_token()
                await self.authenticate(force=True)
                return await self._request_raw(method, endpoint, auth=auth, retry_auth=False, **kwargs)

            if response.is_error:
                raise error_from_response(response)
            return response

        raise RentManagerTransportError(str(last_error or "Request failed."))

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        auth: bool = True,
        headers: Mapping[str, str] | None = None,
        **query: Any,
    ) -> Any:
        merged_params = self._merge_params(params, query)
        response = await self._request_raw(
            method,
            endpoint,
            auth=auth,
            params=merged_params or None,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )
        return self._decode_response(response)

    async def get(self, endpoint: str, *, params: Mapping[str, Any] | None = None, **query: Any) -> Any:
        return await self.request("GET", endpoint, params=params, **query)

    async def download_bytes(self, endpoint: str, *, params: Mapping[str, Any] | None = None, **query: Any) -> bytes:
        merged_params = self._merge_params(params, query)
        response = await self._request_raw("GET", endpoint, params=merged_params or None)
        return response.content

    async def post(
        self,
        endpoint: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        **query: Any,
    ) -> Any:
        return await self.request("POST", endpoint, params=params, json=json, **query)

    async def delete(
        self,
        endpoint: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        **query: Any,
    ) -> Any:
        return await self.request("DELETE", endpoint, params=params, json=json, **query)

    async def action(self, endpoint: str, payload: Any = None, **query: Any) -> Any:
        return await self.post(endpoint, json=payload, **query)

    async def post_multipart(
        self,
        endpoint: str,
        *,
        files: Any,
        data: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Any:
        return await self.request("POST", endpoint, params=params, files=files, data=data)

    async def paginate(
        self,
        endpoint: str,
        *,
        page_number: int = 1,
        page_size: int = 1000,
        params: Mapping[str, Any] | None = None,
        **query: Any,
    ) -> Page:
        merged = self._merge_params(params, query)
        merged.update(QueryParams(page_number=page_number, page_size=page_size).to_params())
        response = await self._request_raw("GET", endpoint, params=merged)
        return self._page_from_response(response, page_number=page_number, page_size=page_size)

    async def iter_pages(
        self,
        endpoint: str,
        *,
        page_size: int = 1000,
        start_page: int = 1,
        max_pages: int | None = None,
        **query: Any,
    ) -> AsyncIterator[Page]:
        page_number = start_page
        yielded = 0
        while True:
            page = await self.paginate(endpoint, page_number=page_number, page_size=page_size, **query)
            yield page
            yielded += 1
            if max_pages is not None and yielded >= max_pages:
                break
            if "next" not in page.links:
                break
            page_number += 1
