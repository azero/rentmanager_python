from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterable, Mapping

RQL_OPERATORS = {
    "eq",
    "ne",
    "in",
    "ni",
    "ct",
    "sw",
    "ew",
    "lt",
    "le",
    "gt",
    "ge",
    "bt",
    "gtn",
    "gen",
    "ltn",
    "len",
    "hv",
}


def _format_rql_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return "null"
    return str(value)


class RQL:
    @staticmethod
    def filter(field: str, operator: str, value: Any = "") -> str:
        if operator not in RQL_OPERATORS:
            allowed = ", ".join(sorted(RQL_OPERATORS))
            raise ValueError(f"Unsupported RQL operator {operator!r}. Allowed: {allowed}")
        if not field or not isinstance(field, str):
            raise ValueError("RQL field must be a non-empty string.")
        if isinstance(value, (list, tuple, set)):
            formatted = "(" + ",".join(_format_rql_value(item) for item in value) + ")"
        else:
            formatted = _format_rql_value(value)
        return f"{field},{operator},{formatted}"

    @staticmethod
    def eq(field: str, value: Any) -> str:
        return RQL.filter(field, "eq", value)

    @staticmethod
    def ne(field: str, value: Any) -> str:
        return RQL.filter(field, "ne", value)

    @staticmethod
    def in_(field: str, value: Iterable[Any]) -> str:
        return RQL.filter(field, "in", list(value))

    @staticmethod
    def ni(field: str, value: Iterable[Any]) -> str:
        return RQL.filter(field, "ni", list(value))

    @staticmethod
    def ct(field: str, value: Any) -> str:
        return RQL.filter(field, "ct", value)

    @staticmethod
    def sw(field: str, value: Any) -> str:
        return RQL.filter(field, "sw", value)

    @staticmethod
    def ew(field: str, value: Any) -> str:
        return RQL.filter(field, "ew", value)

    @staticmethod
    def lt(field: str, value: Any) -> str:
        return RQL.filter(field, "lt", value)

    @staticmethod
    def le(field: str, value: Any) -> str:
        return RQL.filter(field, "le", value)

    @staticmethod
    def gt(field: str, value: Any) -> str:
        return RQL.filter(field, "gt", value)

    @staticmethod
    def ge(field: str, value: Any) -> str:
        return RQL.filter(field, "ge", value)

    @staticmethod
    def bt(field: str, start: Any, end: Any) -> str:
        return RQL.filter(field, "bt", [start, end])

    @staticmethod
    def gtn(field: str, value: Any) -> str:
        return RQL.filter(field, "gtn", value)

    @staticmethod
    def gen(field: str, value: Any) -> str:
        return RQL.filter(field, "gen", value)

    @staticmethod
    def ltn(field: str, value: Any) -> str:
        return RQL.filter(field, "ltn", value)

    @staticmethod
    def len(field: str, value: Any) -> str:
        return RQL.filter(field, "len", value)

    @staticmethod
    def hv(field: str, value: Any = "") -> str:
        return RQL.filter(field, "hv", value)


def _as_csv(value: str | Iterable[str] | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return ",".join(str(item) for item in value)


def _as_filter_list(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


@dataclass(slots=True)
class QueryParams:
    fields: str | Iterable[str] | None = None
    embed: str | Iterable[str] | None = None
    embeds: str | Iterable[str] | None = None
    filter: str | Iterable[str] | None = None
    filters: str | Iterable[str] | None = None
    page_number: int | None = None
    page_size: int | None = None
    no_content: bool | None = None
    order_by: str | Iterable[str] | None = None
    save_options: Mapping[str, bool] | Iterable[str] | str | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def to_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {}
        fields = _as_csv(self.fields)
        if fields:
            params["fields"] = fields

        embeds = [item for item in (_as_csv(self.embed), _as_csv(self.embeds)) if item]
        if embeds:
            params["embed"] = ",".join(embeds)

        filters = _as_filter_list(self.filter) + _as_filter_list(self.filters)
        if filters:
            params["filters"] = ";".join(filters)

        if self.page_number is not None:
            params["pagenumber"] = int(self.page_number)
        if self.page_size is not None:
            params["pagesize"] = int(self.page_size)
        if self.no_content is not None:
            params["nocontent"] = "true" if self.no_content else "false"

        order_by = _as_csv(self.order_by)
        if order_by:
            params["orderby"] = order_by

        save_options = self._format_save_options()
        if save_options:
            params["SaveOptions"] = save_options

        params.update(dict(self.extra))
        return params

    def _format_save_options(self) -> str | None:
        if self.save_options is None:
            return None
        if isinstance(self.save_options, str):
            return self.save_options
        if isinstance(self.save_options, Mapping):
            return ";".join(f"{key},{'true' if value else 'false'}" for key, value in self.save_options.items())
        return ";".join(str(item) for item in self.save_options)


def query_params_from_kwargs(kwargs: Mapping[str, Any]) -> dict[str, Any]:
    values = dict(kwargs)
    known = {
        "fields": values.pop("fields", None),
        "embed": values.pop("embed", None),
        "embeds": values.pop("embeds", None),
        "filter": values.pop("filter", None),
        "filters": values.pop("filters", None),
        "page_number": values.pop("page_number", values.pop("pagenumber", None)),
        "page_size": values.pop("page_size", values.pop("pagesize", None)),
        "no_content": values.pop("no_content", values.pop("nocontent", None)),
        "order_by": values.pop("order_by", values.pop("orderby", None)),
        "save_options": values.pop("save_options", values.pop("SaveOptions", None)),
        "extra": values,
    }
    return QueryParams(**known).to_params()
