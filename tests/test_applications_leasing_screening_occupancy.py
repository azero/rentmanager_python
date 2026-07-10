import json

import httpx
import pytest

import rentmanager_api
import rentmanager_api.models as models
from rentmanager_api.applications_leasing import APPLICATIONS_LEASING_RESOURCE_SPECS
from rentmanager_api import InMemoryTokenStore, RentManagerClient
from rentmanager_api.registry import EndpointRegistry
from rentmanager_api.resources import core as resource_core
from resource_spec_helpers import specs_from_resource_specs


def make_path_client():
    calls = []

    def handler(request):
        if request.url.path == "/Authentication/AuthorizeUser":
            return httpx.Response(200, json="token")
        body = json.loads(request.content.decode("utf-8")) if request.content else None
        calls.append(
            {
                "method": request.method,
                "path": request.url.path,
                "params": dict(request.url.params),
                "json": body,
            }
        )
        return httpx.Response(200, json=[])

    client = RentManagerClient(
        corp_id="sampleco",
        username="user",
        password="pass",
        transport=httpx.MockTransport(handler),
        token_store=InMemoryTokenStore(),
        max_retries=0,
    )
    return client, calls


APPLICATIONS_LEASING_SPECS = specs_from_resource_specs(APPLICATIONS_LEASING_RESOURCE_SPECS)


@pytest.mark.parametrize("spec", APPLICATIONS_LEASING_SPECS, ids=lambda spec: spec["name"])
def test_applications_leasing_models_are_permissive_and_include_sample_fields(spec):
    model = getattr(models, spec["model_name"])

    for field in spec["fields"]:
        assert field in model.model_fields

    payload = {spec["fields"][0]: 123} if spec["fields"] else {}
    instance = model.model_validate({**payload, "UnexpectedField": "kept"})
    assert getattr(instance, "UnexpectedField") == "kept"


@pytest.mark.parametrize("spec", APPLICATIONS_LEASING_SPECS, ids=lambda spec: spec["name"])
def test_applications_leasing_resources_are_attached_with_expected_path_and_model(spec):
    resource_class = getattr(resource_core, spec["resource_class"])
    model = getattr(models, spec["model_name"])
    client, _calls = make_path_client()

    resource = getattr(client, spec["client_attr"])

    assert isinstance(resource, resource_class)
    assert resource.path == spec["name"]
    assert resource.model is model


@pytest.mark.parametrize("spec", APPLICATIONS_LEASING_SPECS, ids=lambda spec: spec["name"])
def test_applications_leasing_resource_methods_are_non_destructive_mock_calls(spec):
    client, calls = make_path_client()
    resource = getattr(client, spec["client_attr"])
    endpoint_paths = set(spec["endpoints"])

    expected_calls = []
    if ("GET", f"/{spec['name']}") in endpoint_paths:
        resource.list()
        expected_calls.append(("GET", f"/{spec['name']}", None))
    if ("GET", f"/{spec['name']}/{{id}}") in endpoint_paths:
        resource.get(123)
        expected_calls.append(("GET", f"/{spec['name']}/123", None))
    if ("POST", f"/{spec['name']}") in endpoint_paths:
        resource.create([{}])
        expected_calls.append(("POST", f"/{spec['name']}", [{}]))
    if ("DELETE", f"/{spec['name']}") in endpoint_paths:
        resource.delete(ids=[123])
        expected_calls.append(("DELETE", f"/{spec['name']}", [123]))
    if ("DELETE", f"/{spec['name']}/{{id}}") in endpoint_paths:
        resource.delete(123)
        expected_calls.append(("DELETE", f"/{spec['name']}/123", None))

    assert [(call["method"], call["path"], call["json"]) for call in calls] == expected_calls
    assert all(call["params"] == {} for call in calls)


def test_applications_leasing_registry_includes_all_live_help_endpoints():
    registry_paths = {(endpoint.method, endpoint.path) for endpoint in EndpointRegistry.default()}
    missing_paths = [
        (spec["name"], method, path)
        for spec in APPLICATIONS_LEASING_SPECS
        for method, path in spec["endpoints"]
        if (method, path) not in registry_paths
    ]

    assert missing_paths == []


def test_applications_leasing_models_are_top_level_exports():
    for spec in APPLICATIONS_LEASING_SPECS:
        assert getattr(rentmanager_api, spec["model_name"]) is getattr(models, spec["model_name"])
        assert spec["model_name"] in rentmanager_api.__all__
