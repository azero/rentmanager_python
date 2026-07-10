from __future__ import annotations

import inspect
from collections.abc import Awaitable
from typing import Any

from pydantic import BaseModel

from .. import models as rm_models
from ..accounting import ACCOUNTING_RESOURCE_SPECS
from ..applications_leasing import APPLICATIONS_LEASING_RESOURCE_SPECS
from ..communications_documents_portals_web import COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS
from ..maintenance_assets_inspections_service import MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS
from ..platform_metadata import PLATFORM_METADATA_RESOURCE_SPECS
from ..properties_owners import PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_RESOURCE_SPECS
from ..reporting_surveys_memorized_templates import REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS
from ..reference_misc import REFERENCE_MISC_RESOURCE_SPECS
from ..utilities_metering import UTILITIES_METERING_RESOURCE_SPECS
from ..models import (
    Amenity,
    Charge,
    ChargeType,
    Contact,
    GLAccount,
    HistoryItem,
    Lease,
    Location,
    Owner,
    OwnerCheck,
    Payment,
    Property,
    PropertyGroup,
    Prospect,
    RecurringCharge,
    ReportWriterReport,
    ServiceManagerCategory,
    ServiceManagerIssue,
    ServiceManagerPriority,
    ServiceManagerStatus,
    Task,
    Tenant,
    Transaction,
    Unit,
    UnitType,
    User,
    UserDefinedField,
    UserDefinedValue,
    Vendor,
    VendorBill,
)

ModelType = type[BaseModel] | None


class Resource:
    path: str = ""
    model: ModelType = None

    def __init__(self, client: Any, path: str | None = None, model: ModelType = None) -> None:
        self._client = client
        if path is not None:
            self.path = path
        if model is not None:
            self.model = model

    def _coerce_maybe(self, value: Any, model: ModelType = None) -> Any:
        target_model = model if model is not None else self.model
        if inspect.isawaitable(value):
            return self._coerce_awaitable(value, target_model)
        return self._coerce(value, target_model)

    async def _coerce_awaitable(self, awaitable: Awaitable[Any], model: ModelType) -> Any:
        return self._coerce(await awaitable, model)

    def _coerce(self, value: Any, model: ModelType) -> Any:
        if model is None:
            return value
        if isinstance(value, list):
            return [model.model_validate(item) if isinstance(item, dict) else item for item in value]
        if isinstance(value, dict):
            return model.model_validate(value)
        return value

    def _get_child(self, path: str, model: ModelType = None, **query: Any) -> Any:
        return self._coerce_maybe(self._client.get(path, **query), model)

    def _post_child(self, path: str, payload: Any = None, model: ModelType = None, **query: Any) -> Any:
        return self._coerce_maybe(self._client.post(path, json=payload, **query), model)

    def list(self, **query: Any) -> Any:
        return self._coerce_maybe(self._client.get(self.path, **query))

    def get(self, item_id: int | str, **query: Any) -> Any:
        return self._coerce_maybe(self._client.get(f"{self.path}/{item_id}", **query))

    def create(self, payload: Any, **query: Any) -> Any:
        return self._coerce_maybe(self._client.post(self.path, json=payload, **query))

    def update(self, item_id: int | str, payload: Any, **query: Any) -> Any:
        return self._coerce_maybe(self._client.post(f"{self.path}/{item_id}", json=payload, **query))

    def delete(self, item_id: int | str | None = None, ids: list[int] | None = None, **query: Any) -> Any:
        if item_id is not None:
            return self._client.delete(f"{self.path}/{item_id}", **query)
        return self._client.delete(self.path, json=ids, **query)

    def paginate(self, **query: Any) -> Any:
        return self._client.paginate(self.path, **query)

    def iter_pages(self, **query: Any) -> Any:
        return self._client.iter_pages(self.path, **query)


class ContactsResource(Resource):
    path = "Contacts"
    model = Contact


class TasksResource(Resource):
    path = "Tasks"
    model = Task


class OwnersResource(Resource):
    path = "Owners"
    model = Owner

    def history(self, owner_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Owners/{owner_id}/History", HistoryItem, **query)

    def owner_checks(self, owner_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Owners/{owner_id}/OwnerChecks", OwnerCheck, **query)

    def payments(self, owner_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Owners/{owner_id}/Payments", Payment, **query)

    def charges(self, owner_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Owners/{owner_id}/Charges", Charge, **query)

    def contact(self, owner_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Owners/{owner_id}/Contact", Contact, **query)


class TenantsResource(Resource):
    path = "Tenants"
    model = Tenant

    def transactions(self, tenant_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Tenants/{tenant_id}/Transactions", Transaction, **query)

    def history(self, tenant_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Tenants/{tenant_id}/History", HistoryItem, **query)

    def contacts(self, tenant_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Tenants/{tenant_id}/Contacts", Contact, **query)

    def leases(self, tenant_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Tenants/{tenant_id}/Leases", Lease, **query)

    def recurring_charges(self, tenant_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Tenants/{tenant_id}/RecurringCharges", RecurringCharge, **query)

    def create_recurring_charge(self, tenant_id: int | str, payload: Any, **query: Any) -> Any:
        return self._post_child(f"Tenants/{tenant_id}/RecurringCharges", payload, RecurringCharge, **query)

    def user_defined_values(self, tenant_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Tenants/{tenant_id}/UserDefinedValues", UserDefinedValue, **query)

    def update_user_defined_values(self, tenant_id: int | str, payload: Any, **query: Any) -> Any:
        return self._post_child(f"Tenants/{tenant_id}/UserDefinedValues", payload, UserDefinedValue, **query)

    def user_defined_fields(self, tenant_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Tenants/{tenant_id}/UserDefinedFields", UserDefinedField, **query)

    def addresses(self, tenant_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Tenants/{tenant_id}/Addresses", None, **query)

    def upload_user_defined_value_attachment(
        self,
        tenant_id: int | str,
        udf_id: int | str,
        file: Any,
        filename: str,
        **data: Any,
    ) -> Any:
        payload = {"UserDefinedFieldID": udf_id, "ParentID": tenant_id, **data}
        files = {
            "file": (filename, file),
            "udf": (None, self._client.json_dumps(payload), "application/json"),
        }
        return self._client.post_multipart(f"Tenants/{tenant_id}/UploadUserDefinedValueAttachment", files=files)


class ProspectsResource(Resource):
    path = "Prospects"
    model = Prospect

    def history(self, prospect_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Prospects/{prospect_id}/History", HistoryItem, **query)

    def contacts(self, prospect_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Prospects/{prospect_id}/Contacts", Contact, **query)


class VendorsResource(Resource):
    path = "Vendors"
    model = Vendor

    def history(self, vendor_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Vendors/{vendor_id}/History", HistoryItem, **query)

    def transactions(self, vendor_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Vendors/{vendor_id}/Transactions", Transaction, **query)

    def contacts(self, vendor_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Vendors/{vendor_id}/Contacts", Contact, **query)

    def bills(self, vendor_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Vendors/{vendor_id}/Bills", VendorBill, **query)


class PropertiesResource(Resource):
    path = "Properties"
    model = Property

    def units(self, property_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Properties/{property_id}/Units", Unit, **query)


class UnitsResource(Resource):
    path = "Units"
    model = Unit

    def leases(self, unit_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Units/{unit_id}/Leases", Lease, **query)

    def user_defined_values(self, unit_id: int | str, **query: Any) -> Any:
        return self._get_child(f"Units/{unit_id}/UserDefinedValues", UserDefinedValue, **query)

    def link_amenities(self, unit_id: int | str, unit_amenity_ids: list[int] | int) -> Any:
        ids = unit_amenity_ids if isinstance(unit_amenity_ids, list) else [unit_amenity_ids]
        return self._client.post(f"Units/{unit_id}/LinkAmenities", json=ids)

    def unlink_amenities(self, unit_id: int | str, unit_amenity_ids: list[int] | int) -> Any:
        ids = unit_amenity_ids if isinstance(unit_amenity_ids, list) else [unit_amenity_ids]
        return self._client.delete(f"Units/{unit_id}/UnLinkAmenities", json=ids)


class LeasesResource(Resource):
    path = "Leases"
    model = Lease


class UsersResource(Resource):
    path = "Users"
    model = User

    def current_user(self, **query: Any) -> Any:
        return self._get_child("Users/CurrentUser", User, **query)


class LocationsResource(Resource):
    path = "Locations"
    model = Location


class PropertyGroupsResource(Resource):
    path = "PropertyGroups"
    model = PropertyGroup


class AmenitiesResource(Resource):
    path = "Amenities"
    model = Amenity


class GLAccountsResource(Resource):
    path = "GLAccounts"
    model = GLAccount


class ChargeTypesResource(Resource):
    path = "ChargeTypes"
    model = ChargeType


class UnitTypesResource(Resource):
    path = "UnitTypes"
    model = UnitType


class RecurringChargesResource(Resource):
    path = "RecurringCharges"
    model = RecurringCharge

    def post_recurring_charges(self, payload: Any, **query: Any) -> Any:
        return self._post_child("RecurringCharges/PostRecurringCharges", payload, None, **query)


class ReportWriterReportsResource(Resource):
    path = "ReportWriterReports"
    model = ReportWriterReport

    def run(self, report_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ReportWriterReports/{report_id}/RunReportWriterReport", None, **query)


class ServiceManagerIssuesResource(Resource):
    path = "ServiceManagerIssues"
    model = ServiceManagerIssue

    def link_property(self, issue_id: int | str, property_id: int | str) -> Any:
        return self._client.post(f"ServiceManagerIssues/{issue_id}/LinkProperty", params={"propertyID": property_id})

    def link_unit(self, issue_id: int | str, unit_id: int | str) -> Any:
        return self._client.post(f"ServiceManagerIssues/{issue_id}/LinkUnit", params={"unitID": unit_id})

    def history(self, issue_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ServiceManagerIssues/{issue_id}/History", HistoryItem, **query)

    def add_history(self, issue_id: int | str, payload: Any, **query: Any) -> Any:
        return self._post_child(f"ServiceManagerIssues/{issue_id}/History", payload, HistoryItem, **query)

    def properties(self, issue_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ServiceManagerIssues/{issue_id}/Properties", Property, **query)

    def attachments(self, issue_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ServiceManagerIssues/{issue_id}/Attachments", None, **query)

    def files(self, issue_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ServiceManagerIssues/{issue_id}/Files", None, **query)

    def documents(self, issue_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ServiceManagerIssues/{issue_id}/Documents", None, **query)

    def line_items(self, issue_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ServiceManagerIssues/{issue_id}/LineItems", None, **query)

    def add_line_items(self, issue_id: int | str, payload: Any, **query: Any) -> Any:
        return self._post_child(f"ServiceManagerIssues/{issue_id}/LineItems", payload, None, **query)

    def user_defined_values(self, issue_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ServiceManagerIssues/{issue_id}/UserDefinedValues", UserDefinedValue, **query)

    def update_user_defined_values(self, issue_id: int | str, payload: Any, **query: Any) -> Any:
        return self._post_child(
            f"ServiceManagerIssues/{issue_id}/UserDefinedValues", payload, UserDefinedValue, **query
        )

    def user_defined_fields(self, issue_id: int | str, **query: Any) -> Any:
        return self._get_child(f"ServiceManagerIssues/{issue_id}/UserDefinedFields", UserDefinedField, **query)

    def upload_attachment(self, issue_id: int | str, files: Any, data: dict[str, Any] | None = None) -> Any:
        return self._client.post_multipart(f"ServiceManagerIssues/{issue_id}/Attachments", files=files, data=data)

    def upload_signature_file(self, issue_id: int | str, files: Any, data: dict[str, Any] | None = None) -> Any:
        return self._client.post_multipart(
            f"ServiceManagerIssues/{issue_id}/UploadSignatureFile",
            files=files,
            data=data,
        )


class ServiceManagerStatusesResource(Resource):
    path = "ServiceManagerStatuses"
    model = ServiceManagerStatus


class ServiceManagerCategoriesResource(Resource):
    path = "ServiceManagerCategories"
    model = ServiceManagerCategory


class ServiceManagerPrioritiesResource(Resource):
    path = "ServiceManagerPriorities"
    model = ServiceManagerPriority


class ServiceManagerNamespace:
    def __init__(self, client: Any) -> None:
        self.issues = ServiceManagerIssuesResource(client)
        self.statuses = ServiceManagerStatusesResource(client)
        self.categories = ServiceManagerCategoriesResource(client)
        self.priorities = ServiceManagerPrioritiesResource(client)


def _install_accounting_resources() -> None:
    for spec in ACCOUNTING_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


def _install_platform_metadata_resources() -> None:
    for spec in PLATFORM_METADATA_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


def _install_applications_leasing_resources() -> None:
    for spec in APPLICATIONS_LEASING_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


def _install_communications_documents_portals_web_resources() -> None:
    for spec in COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


def _install_maintenance_assets_inspections_service_resources() -> None:
    for spec in MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


def _install_reporting_surveys_memorized_templates_resources() -> None:
    for spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


def _install_utilities_metering_resources() -> None:
    for spec in UTILITIES_METERING_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


def _install_reference_misc_resources() -> None:
    for spec in REFERENCE_MISC_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


def _install_properties_owners_associations_violations_resources() -> None:
    for spec in PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_RESOURCE_SPECS:
        resource_class = type(
            spec.resource_class_name,
            (Resource,),
            {
                "__module__": __name__,
                "path": spec.path,
                "model": getattr(rm_models, spec.model_name),
            },
        )
        globals()[spec.resource_class_name] = resource_class


_install_accounting_resources()
_install_platform_metadata_resources()
_install_applications_leasing_resources()
_install_communications_documents_portals_web_resources()
_install_maintenance_assets_inspections_service_resources()
_install_reporting_surveys_memorized_templates_resources()
_install_utilities_metering_resources()
_install_reference_misc_resources()
_install_properties_owners_associations_violations_resources()


def attach_resources(client: Any) -> None:
    client.contacts = ContactsResource(client)
    client.tasks = TasksResource(client)
    client.owners = OwnersResource(client)
    client.tenants = TenantsResource(client)
    client.prospects = ProspectsResource(client)
    client.vendors = VendorsResource(client)
    client.properties = PropertiesResource(client)
    client.units = UnitsResource(client)
    client.leases = LeasesResource(client)
    client.users = UsersResource(client)
    client.locations = LocationsResource(client)
    client.property_groups = PropertyGroupsResource(client)
    client.amenities = AmenitiesResource(client)
    client.gl_accounts = GLAccountsResource(client)
    client.charge_types = ChargeTypesResource(client)
    client.unit_types = UnitTypesResource(client)
    client.recurring_charges = RecurringChargesResource(client)
    client.report_writer_reports = ReportWriterReportsResource(client)
    client.service_manager = ServiceManagerNamespace(client)
    for spec in ACCOUNTING_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
    for spec in PLATFORM_METADATA_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
    for spec in APPLICATIONS_LEASING_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
    for spec in COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
    for spec in MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
    for spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
    for spec in UTILITIES_METERING_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
    for spec in REFERENCE_MISC_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
    for spec in PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_RESOURCE_SPECS:
        resource_class = globals()[spec.resource_class_name]
        setattr(client, spec.client_attr, resource_class(client))
