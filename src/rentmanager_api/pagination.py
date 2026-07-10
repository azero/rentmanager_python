from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Page:
    data: list[Any]
    status_code: int
    headers: dict[str, str]
    page_number: int
    page_size: int
    total_results: int | None = None
    links: dict[str, str] = field(default_factory=dict)


def parse_link_header(value: str | None) -> dict[str, str]:
    links: dict[str, str] = {}
    if not value:
        return links
    for part in value.split(","):
        section = part.strip()
        if not section or ";" not in section:
            continue
        url_part, *param_parts = section.split(";")
        url = url_part.strip()
        if url.startswith("<") and url.endswith(">"):
            url = url[1:-1]
        rel = None
        for param in param_parts:
            key, _, raw_value = param.strip().partition("=")
            if key.lower() == "rel":
                rel = raw_value.strip('"')
        if rel:
            links[rel] = url
    return links


def total_results_from_headers(headers: dict[str, str]) -> int | None:
    raw = headers.get("X-Total-Results") or headers.get("x-total-results")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None
