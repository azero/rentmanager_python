from __future__ import annotations

from typing import Any, Iterable


def specs_from_resource_specs(resource_specs: Iterable[Any]) -> list[dict[str, Any]]:
    return [_spec_to_case(spec) for spec in resource_specs]


def _spec_to_case(spec: Any) -> dict[str, Any]:
    endpoints = getattr(spec, "endpoints", None)
    if endpoints is None:
        endpoints = tuple(_endpoint_from_operation(spec.path, operation) for operation in spec.operations)

    return {
        "name": spec.path,
        "client_attr": spec.client_attr,
        "resource_class": spec.resource_class_name,
        "model_name": spec.model_name,
        "fields": list(spec.fields),
        "endpoints": list(endpoints),
    }


def _endpoint_from_operation(path: str, operation: str) -> tuple[str, str]:
    if operation == "list":
        return ("GET", f"/{path}")
    if operation == "get":
        return ("GET", f"/{path}/{{id}}")
    if operation == "create":
        return ("POST", f"/{path}")
    if operation == "delete_many":
        return ("DELETE", f"/{path}")
    if operation == "delete_one":
        return ("DELETE", f"/{path}/{{id}}")
    raise ValueError(f"Unsupported generated resource operation: {operation}")
