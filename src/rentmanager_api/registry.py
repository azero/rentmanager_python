from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Literal, get_args

from .accounting import ACCOUNTING_RESOURCE_SPECS, AccountingResourceSpec
from .applications_leasing import APPLICATIONS_LEASING_RESOURCE_SPECS, ApplicationsLeasingResourceSpec
from .communications_documents_portals_web import (
    COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS,
    CommunicationsDocumentsPortalsWebResourceSpec,
)
from .maintenance_assets_inspections_service import (
    MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS,
    MaintenanceAssetsInspectionsServiceResourceSpec,
)
from .platform_metadata import PLATFORM_METADATA_RESOURCE_SPECS, PlatformMetadataResourceSpec
from .properties_owners import (
    PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_RESOURCE_SPECS,
    PropertiesOwnersAssociationsViolationsResourceSpec,
)
from .reporting_surveys_memorized_templates import (
    REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS,
    ReportingSurveysMemorizedTemplatesResourceSpec,
)
from .reference_misc import REFERENCE_MISC_RESOURCE_SPECS, ReferenceMiscResourceSpec
from .utilities_metering import UTILITIES_METERING_RESOURCE_SPECS, UtilitiesMeteringResourceSpec


EndpointConfidence = Literal["documented", "prior_art", "field_discovered", "live_help_catalog"]
VALID_CONFIDENCE_VALUES = frozenset(get_args(EndpointConfidence))


@dataclass(frozen=True, slots=True)
class EndpointSpec:
    method: str
    path: str
    model: str | None
    confidence: EndpointConfidence
    source: str

    def __post_init__(self) -> None:
        if self.confidence not in VALID_CONFIDENCE_VALUES:
            allowed = ", ".join(sorted(VALID_CONFIDENCE_VALUES))
            raise ValueError(f"EndpointSpec confidence must be one of: {allowed}")


class EndpointRegistry:
    def __init__(self, endpoints: Iterable[EndpointSpec]) -> None:
        self._endpoints = tuple(endpoints)

    def __iter__(self):
        return iter(self._endpoints)

    def coverage_report(self) -> list[dict[str, str | None]]:
        return [asdict(endpoint) for endpoint in self._endpoints]

    @classmethod
    def default(cls) -> "EndpointRegistry":
        return cls(DEFAULT_ENDPOINTS)


def _spec(
    method: str,
    path: str,
    model: str | None,
    confidence: EndpointConfidence,
    source: str,
) -> EndpointSpec:
    return EndpointSpec(method=method, path=path, model=model, confidence=confidence, source=source)


def _accounting_specs_for_resource(spec: AccountingResourceSpec) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    endpoints = []
    for operation in spec.operations:
        if operation == "list":
            endpoints.append(_spec("GET", f"/{spec.path}", spec.model_name, "live_help_catalog", source))
        elif operation == "get":
            endpoints.append(_spec("GET", f"/{spec.path}/{{id}}", spec.model_name, "live_help_catalog", source))
        elif operation == "create":
            endpoints.append(_spec("POST", f"/{spec.path}", spec.model_name, "live_help_catalog", source))
        elif operation == "delete_many":
            endpoints.append(_spec("DELETE", f"/{spec.path}", "dict", "live_help_catalog", source))
        elif operation == "delete_one":
            endpoints.append(_spec("DELETE", f"/{spec.path}/{{id}}", "dict", "live_help_catalog", source))
    return endpoints


def _accounting_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in ACCOUNTING_RESOURCE_SPECS
        for endpoint in _accounting_specs_for_resource(resource_spec)
    ]


def _platform_metadata_specs_for_resource(spec: PlatformMetadataResourceSpec) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    return [
        _spec(
            method,
            path,
            "dict" if method == "DELETE" else spec.model_name,
            "live_help_catalog",
            source,
        )
        for method, path in spec.endpoints
    ]


def _platform_metadata_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in PLATFORM_METADATA_RESOURCE_SPECS
        for endpoint in _platform_metadata_specs_for_resource(resource_spec)
    ]


def _applications_leasing_specs_for_resource(spec: ApplicationsLeasingResourceSpec) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    return [
        _spec(
            method,
            path,
            "dict" if method == "DELETE" else spec.model_name,
            "live_help_catalog",
            source,
        )
        for method, path in spec.endpoints
    ]


def _applications_leasing_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in APPLICATIONS_LEASING_RESOURCE_SPECS
        for endpoint in _applications_leasing_specs_for_resource(resource_spec)
    ]


def _communications_documents_portals_web_specs_for_resource(
    spec: CommunicationsDocumentsPortalsWebResourceSpec,
) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    endpoints = []
    for operation in spec.operations:
        if operation == "list":
            endpoints.append(_spec("GET", f"/{spec.path}", spec.model_name, "live_help_catalog", source))
        elif operation == "get":
            endpoints.append(_spec("GET", f"/{spec.path}/{{id}}", spec.model_name, "live_help_catalog", source))
        elif operation == "create":
            endpoints.append(_spec("POST", f"/{spec.path}", spec.model_name, "live_help_catalog", source))
        elif operation == "delete_many":
            endpoints.append(_spec("DELETE", f"/{spec.path}", "dict", "live_help_catalog", source))
        elif operation == "delete_one":
            endpoints.append(_spec("DELETE", f"/{spec.path}/{{id}}", "dict", "live_help_catalog", source))
    return endpoints


def _communications_documents_portals_web_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS
        for endpoint in _communications_documents_portals_web_specs_for_resource(resource_spec)
    ]


def _maintenance_assets_inspections_service_specs_for_resource(
    spec: MaintenanceAssetsInspectionsServiceResourceSpec,
) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    return [
        _spec(
            method,
            path,
            "dict" if method == "DELETE" else spec.model_name,
            "live_help_catalog",
            source,
        )
        for method, path in spec.endpoints
    ]


def _maintenance_assets_inspections_service_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS
        for endpoint in _maintenance_assets_inspections_service_specs_for_resource(resource_spec)
    ]


def _reporting_surveys_memorized_templates_specs_for_resource(
    spec: ReportingSurveysMemorizedTemplatesResourceSpec,
) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    endpoints = []
    for operation in spec.operations:
        if operation == "list":
            endpoints.append(_spec("GET", f"/{spec.path}", spec.model_name, "live_help_catalog", source))
        elif operation == "get":
            endpoints.append(_spec("GET", f"/{spec.path}/{{id}}", spec.model_name, "live_help_catalog", source))
        elif operation == "create":
            endpoints.append(_spec("POST", f"/{spec.path}", spec.model_name, "live_help_catalog", source))
        elif operation == "delete_many":
            endpoints.append(_spec("DELETE", f"/{spec.path}", "dict", "live_help_catalog", source))
        elif operation == "delete_one":
            endpoints.append(_spec("DELETE", f"/{spec.path}/{{id}}", "dict", "live_help_catalog", source))
    return endpoints


def _reporting_surveys_memorized_templates_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS
        for endpoint in _reporting_surveys_memorized_templates_specs_for_resource(resource_spec)
    ]


def _utilities_metering_specs_for_resource(spec: UtilitiesMeteringResourceSpec) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    endpoints = []
    for operation in spec.operations:
        if operation == "list":
            endpoints.append(_spec("GET", f"/{spec.path}", spec.model_name, "live_help_catalog", source))
        elif operation == "get":
            endpoints.append(_spec("GET", f"/{spec.path}/{{id}}", spec.model_name, "live_help_catalog", source))
        elif operation == "create":
            endpoints.append(_spec("POST", f"/{spec.path}", spec.model_name, "live_help_catalog", source))
        elif operation == "delete_many":
            endpoints.append(_spec("DELETE", f"/{spec.path}", "dict", "live_help_catalog", source))
        elif operation == "delete_one":
            endpoints.append(_spec("DELETE", f"/{spec.path}/{{id}}", "dict", "live_help_catalog", source))
    return endpoints


def _utilities_metering_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in UTILITIES_METERING_RESOURCE_SPECS
        for endpoint in _utilities_metering_specs_for_resource(resource_spec)
    ]


def _reference_misc_specs_for_resource(spec: ReferenceMiscResourceSpec) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    return [
        _spec(
            method,
            path,
            "dict" if method == "DELETE" else spec.model_name,
            "live_help_catalog",
            source,
        )
        for method, path in spec.endpoints
    ]


def _reference_misc_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in REFERENCE_MISC_RESOURCE_SPECS
        for endpoint in _reference_misc_specs_for_resource(resource_spec)
    ]


def _properties_owners_associations_violations_specs_for_resource(
    spec: PropertiesOwnersAssociationsViolationsResourceSpec,
) -> list[EndpointSpec]:
    source = "authenticated WAPI12 Help catalog"
    return [
        _spec(
            method,
            path,
            "dict" if method == "DELETE" else spec.model_name,
            "live_help_catalog",
            source,
        )
        for method, path in spec.endpoints
    ]


def _properties_owners_associations_violations_endpoint_specs() -> list[EndpointSpec]:
    return [
        endpoint
        for resource_spec in PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_RESOURCE_SPECS
        for endpoint in _properties_owners_associations_violations_specs_for_resource(resource_spec)
    ]


DEFAULT_ENDPOINTS = [
    _spec("POST", "/Authentication/AuthorizeUser", "str", "documented", "Rent Manager WAPI12 overview"),
    _spec("POST", "/Authentication/AuthorizeToken", "dict", "prior_art", "TopShelfRobot JS client"),
    _spec("POST", "/Authentication/ChangeLocation", "dict", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Owners", "Owner", "field_discovered", "local example"),
    _spec("GET", "/Owners/{id}", "Owner", "field_discovered", "local example"),
    _spec("GET", "/Owners/{id}/History", "HistoryItem", "field_discovered", "local example"),
    _spec("GET", "/Owners/{id}/OwnerChecks", "OwnerCheck", "field_discovered", "local example"),
    _spec("GET", "/Owners/{id}/Payments", "Payment", "field_discovered", "local example"),
    _spec("GET", "/Owners/{id}/Charges", "Charge", "field_discovered", "local example"),
    _spec("GET", "/Owners/{id}/Contact", "Contact", "field_discovered", "local example"),
    _spec("GET", "/Tenants", "Tenant", "field_discovered", "local example"),
    _spec("GET", "/Tenants/{id}", "Tenant", "field_discovered", "local example"),
    _spec("GET", "/Tenants/{id}/Transactions", "Transaction", "field_discovered", "local example"),
    _spec("GET", "/Tenants/{id}/History", "HistoryItem", "field_discovered", "local example"),
    _spec("GET", "/Tenants/{id}/Contacts", "Contact", "field_discovered", "local example"),
    _spec("GET", "/Tenants/{id}/Leases", "Lease", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Tenants/{id}/RecurringCharges", "RecurringCharge", "prior_art", "TopShelfRobot JS client"),
    _spec("POST", "/Tenants/{id}/RecurringCharges", "RecurringCharge", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Tenants/{id}/UserDefinedValues", "UserDefinedValue", "prior_art", "TopShelfRobot JS client"),
    _spec("POST", "/Tenants/{id}/UserDefinedValues", "UserDefinedValue", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Tenants/{id}/UserDefinedFields", "UserDefinedField", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Tenants/{id}/Addresses", "dict", "prior_art", "TopShelfRobot JS client"),
    _spec("POST", "/Tenants/{id}/UploadUserDefinedValueAttachment", "dict", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Prospects", "Prospect", "field_discovered", "local example"),
    _spec("GET", "/Prospects/{id}", "Prospect", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/Prospects/{id}/History", "HistoryItem", "field_discovered", "local example"),
    _spec("GET", "/Prospects/{id}/Contacts", "Contact", "field_discovered", "local example"),
    _spec("GET", "/Vendors", "Vendor", "field_discovered", "local example"),
    _spec("GET", "/Vendors/{id}", "Vendor", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/Vendors/{id}/History", "HistoryItem", "field_discovered", "local example"),
    _spec("GET", "/Vendors/{id}/Transactions", "Transaction", "field_discovered", "local example"),
    _spec("GET", "/Vendors/{id}/Contacts", "Contact", "field_discovered", "local example"),
    _spec("GET", "/Vendors/{id}/Bills", "VendorBill", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Properties", "Property", "field_discovered", "local example"),
    _spec("GET", "/Properties/{id}", "Property", "field_discovered", "local example"),
    _spec("GET", "/Properties/{id}/Units", "Unit", "field_discovered", "local example"),
    _spec("GET", "/Contacts", "Contact", "field_discovered", "local example"),
    _spec("GET", "/Contacts/{id}", "Contact", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/Tasks", "Task", "field_discovered", "local example"),
    _spec("GET", "/Tasks/{id}", "Task", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/Units", "Unit", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Units/{id}", "Unit", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("POST", "/Units", "Unit", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Units/{id}/Leases", "Lease", "field_discovered", "local example"),
    _spec("GET", "/Units/{id}/UserDefinedValues", "UserDefinedValue", "prior_art", "TopShelfRobot JS client"),
    _spec("POST", "/Units/{id}/LinkAmenities", "dict", "prior_art", "TopShelfRobot JS client"),
    _spec("DELETE", "/Units/{id}/UnLinkAmenities", "dict", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Leases", "Lease", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Leases/{id}", "Lease", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/Users", "User", "field_discovered", "local example"),
    _spec("GET", "/Users/{id}", "User", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/Users/CurrentUser", "User", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Locations", "Location", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Locations/{id}", "Location", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/PropertyGroups", "PropertyGroup", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/PropertyGroups/{id}", "PropertyGroup", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/Amenities", "Amenity", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/Amenities/{id}", "Amenity", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/GLAccounts", "GLAccount", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/GLAccounts/{id}", "GLAccount", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/ChargeTypes", "ChargeType", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/ChargeTypes/{id}", "ChargeType", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/UnitTypes", "UnitType", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/UnitTypes/{id}", "UnitType", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/RecurringCharges", "RecurringCharge", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/RecurringCharges/{id}", "RecurringCharge", "live_help_catalog", "authenticated WAPI12 Help catalog"),
    _spec("GET", "/ServiceManagerIssues", "ServiceManagerIssue", "field_discovered", "local example"),
    _spec("GET", "/ServiceManagerIssues/{id}", "ServiceManagerIssue", "field_discovered", "local example"),
    _spec("POST", "/ServiceManagerIssues", "ServiceManagerIssue", "field_discovered", "local example"),
    _spec("POST", "/ServiceManagerIssues/{id}", "ServiceManagerIssue", "documented", "Rent Manager WAPI12 overview"),
    _spec("DELETE", "/ServiceManagerIssues/{id}", "dict", "prior_art", "TopShelfRobot JS client"),
    _spec("POST", "/ServiceManagerIssues/{id}/LinkProperty", "dict", "field_discovered", "local example"),
    _spec("POST", "/ServiceManagerIssues/{id}/LinkUnit", "dict", "prior_art", "TopShelfRobot JS client"),
    _spec("GET", "/ServiceManagerIssues/{id}/History", "HistoryItem", "field_discovered", "local example"),
    _spec("POST", "/ServiceManagerIssues/{id}/History", "HistoryItem", "field_discovered", "local example"),
    _spec("GET", "/ServiceManagerIssues/{id}/Properties", "Property", "field_discovered", "local example"),
    _spec("GET", "/ServiceManagerIssues/{id}/Attachments", "dict", "field_discovered", "local example"),
    _spec("POST", "/ServiceManagerIssues/{id}/Attachments", "dict", "field_discovered", "local example"),
    _spec("POST", "/ServiceManagerIssues/{id}/UploadSignatureFile", "dict", "field_discovered", "local example"),
    _spec("GET", "/ServiceManagerIssues/{id}/LineItems", "dict", "field_discovered", "local example"),
    _spec("POST", "/ServiceManagerIssues/{id}/LineItems", "dict", "field_discovered", "local example"),
    _spec(
        "GET",
        "/ServiceManagerIssues/{id}/UserDefinedValues",
        "UserDefinedValue",
        "prior_art",
        "TopShelfRobot JS client",
    ),
    _spec(
        "POST",
        "/ServiceManagerIssues/{id}/UserDefinedValues",
        "UserDefinedValue",
        "prior_art",
        "TopShelfRobot JS client",
    ),
    _spec(
        "GET",
        "/ServiceManagerIssues/{id}/UserDefinedFields",
        "UserDefinedField",
        "prior_art",
        "TopShelfRobot JS client",
    ),
    _spec("GET", "/ServiceManagerStatuses", "ServiceManagerStatus", "field_discovered", "local example"),
    _spec(
        "GET",
        "/ServiceManagerStatuses/{id}",
        "ServiceManagerStatus",
        "live_help_catalog",
        "authenticated WAPI12 Help catalog",
    ),
    _spec("GET", "/ServiceManagerCategories", "ServiceManagerCategory", "field_discovered", "local example"),
    _spec(
        "GET",
        "/ServiceManagerCategories/{id}",
        "ServiceManagerCategory",
        "live_help_catalog",
        "authenticated WAPI12 Help catalog",
    ),
    _spec("GET", "/ServiceManagerPriorities", "ServiceManagerPriority", "field_discovered", "live WAPI probe"),
    _spec("GET", "/ServiceManagerPriorities/{id}", "ServiceManagerPriority", "field_discovered", "live WAPI probe"),
    _spec("GET", "/ReportWriterReports", "ReportWriterReport", "field_discovered", "local example"),
    _spec(
        "GET",
        "/ReportWriterReports/{id}",
        "ReportWriterReport",
        "live_help_catalog",
        "authenticated WAPI12 Help catalog",
    ),
    _spec(
        "GET",
        "/ReportWriterReports/{id}/RunReportWriterReport",
        "ReportWriterReport",
        "field_discovered",
        "local example",
    ),
    _spec("POST", "/RecurringCharges/PostRecurringCharges", "dict", "documented", "Rent Manager WAPI12 overview"),
    *_platform_metadata_endpoint_specs(),
    *_accounting_endpoint_specs(),
    *_applications_leasing_endpoint_specs(),
    *_communications_documents_portals_web_endpoint_specs(),
    *_maintenance_assets_inspections_service_endpoint_specs(),
    *_reporting_surveys_memorized_templates_endpoint_specs(),
    *_utilities_metering_endpoint_specs(),
    *_reference_misc_endpoint_specs(),
    *_properties_owners_associations_violations_endpoint_specs(),
]
