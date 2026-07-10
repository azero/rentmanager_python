from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, create_model

from .accounting import ACCOUNTING_MODEL_NAMES, ACCOUNTING_RESOURCE_SPECS
from .applications_leasing import APPLICATIONS_LEASING_MODEL_NAMES, APPLICATIONS_LEASING_RESOURCE_SPECS
from .communications_documents_portals_web import (
    COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_MODEL_NAMES,
    COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS,
)
from .maintenance_assets_inspections_service import (
    MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_MODEL_NAMES,
    MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS,
)
from .platform_metadata import PLATFORM_METADATA_MODEL_NAMES, PLATFORM_METADATA_RESOURCE_SPECS
from .properties_owners import (
    PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_MODEL_NAMES,
    PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_RESOURCE_SPECS,
)
from .reporting_surveys_memorized_templates import (
    REPORTING_SURVEYS_MEMORIZED_TEMPLATES_MODEL_NAMES,
    REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS,
)
from .reference_misc import REFERENCE_MISC_MODEL_NAMES, REFERENCE_MISC_RESOURCE_SPECS
from .utilities_metering import UTILITIES_METERING_MODEL_NAMES, UTILITIES_METERING_RESOURCE_SPECS


class RMBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    ApiUri: str | None = None
    APIURI: str | None = None
    ID: int | None = None
    Id: int | None = None
    CreateDate: str | None = None
    DateCreated: str | None = None
    UpdateDate: str | None = None
    DateUpdated: str | None = None


class Owner(RMBaseModel):
    OwnerID: int | None = None
    Name: str | None = None
    CompanyName: str | None = None
    FirstName: str | None = None
    LastName: str | None = None
    Email: str | None = None
    IsActive: bool | None = None


class Tenant(RMBaseModel):
    TenantID: int | None = None
    TenantDisplayID: int | str | None = None
    Name: str | None = None
    FirstName: str | None = None
    LastName: str | None = None
    Email: str | None = None
    PropertyID: int | None = None
    UnitID: int | None = None
    IsActive: bool | None = None
    CurrentBalance: float | None = None


class Prospect(RMBaseModel):
    ProspectID: int | None = None
    Name: str | None = None
    FirstName: str | None = None
    LastName: str | None = None
    Email: str | None = None
    IsActive: bool | None = None


class Vendor(RMBaseModel):
    VendorID: int | None = None
    Name: str | None = None
    CompanyName: str | None = None
    Email: str | None = None
    IsActive: bool | None = None


class Property(RMBaseModel):
    PropertyID: int | None = None
    Name: str | None = None
    ShortName: str | None = None
    PrimaryOwnerID: int | None = None
    IsActive: bool | None = None


class Contact(RMBaseModel):
    ContactID: int | None = None
    ParentType: str | None = None
    ParentID: int | None = None
    Name: str | None = None
    FirstName: str | None = None
    LastName: str | None = None
    Email: str | None = None


class Task(RMBaseModel):
    TaskID: int | None = None
    Title: str | None = None
    TenantID: int | None = None
    DueDate: str | None = None


class Unit(RMBaseModel):
    UnitID: int | None = None
    PropertyID: int | None = None
    Name: str | None = None
    UnitNumber: str | None = None
    IsActive: bool | None = None


class Lease(RMBaseModel):
    LeaseID: int | None = None
    TenantID: int | None = None
    UnitID: int | None = None
    PropertyID: int | None = None
    MoveInDate: str | None = None
    MoveOutDate: str | None = None


class User(RMBaseModel):
    UserID: int | None = None
    Username: str | None = None
    Name: str | None = None
    FirstName: str | None = None
    LastName: str | None = None
    IsActive: bool | None = None


class Location(RMBaseModel):
    LocationID: int | None = None
    Name: str | None = None


class PropertyGroup(RMBaseModel):
    PropertyGroupID: int | None = None
    Name: str | None = None


class Amenity(RMBaseModel):
    AmenityID: int | None = None
    UnitAmenityID: int | None = None
    Name: str | None = None
    Text: str | None = None
    Selected: bool | None = None


class GLAccount(RMBaseModel):
    GLAccountID: int | None = None
    Name: str | None = None
    AccountNumber: str | None = None


class ChargeType(RMBaseModel):
    ChargeTypeID: int | None = None
    Name: str | None = None


class UnitType(RMBaseModel):
    UnitTypeID: int | None = None
    Name: str | None = None


class Transaction(RMBaseModel):
    TransactionID: int | None = None
    TenantID: int | None = None
    Amount: float | None = None
    TransactionDate: str | None = None
    Comment: str | None = None


class HistoryItem(RMBaseModel):
    HistoryID: int | None = None
    HistoryType: str | None = None
    HistoryDate: str | None = None
    Note: str | None = None
    NoteText: str | None = None


class OwnerCheck(RMBaseModel):
    OwnerCheckID: int | None = None
    OwnerID: int | None = None
    PropertyID: int | None = None
    ActualAmount: float | None = None
    OriginalAmount: float | None = None
    CheckDate: str | None = None


class Payment(RMBaseModel):
    PaymentID: int | None = None
    Amount: float | None = None
    TransactionDate: str | None = None
    PropertyID: int | None = None


class Charge(RMBaseModel):
    ChargeID: int | None = None
    Amount: float | None = None
    TransactionDate: str | None = None
    PropertyID: int | None = None


class RecurringCharge(RMBaseModel):
    RecurringChargeID: int | None = None
    TenantID: int | None = None
    ChargeTypeID: int | None = None
    Amount: float | None = None


class UserDefinedField(RMBaseModel):
    UserDefinedFieldID: int | None = None
    Name: str | None = None
    DataType: str | None = None


class UserDefinedValue(RMBaseModel):
    UserDefinedValueID: int | None = None
    UserDefinedFieldID: int | None = None
    ParentID: int | None = None
    Value: Any = None


class VendorBill(RMBaseModel):
    BillID: int | None = None
    VendorID: int | None = None
    Amount: float | None = None
    BillDate: str | None = None


class ServiceManagerStatus(RMBaseModel):
    ServiceManagerStatusID: int | None = None
    Name: str | None = None
    Description: str | None = None
    SortOrder: int | None = None
    Color: str | None = None


class ServiceManagerCategory(RMBaseModel):
    ServiceManagerCategoryID: int | None = None
    Name: str | None = None
    Description: str | None = None


class ServiceManagerPriority(RMBaseModel):
    ServiceManagerPriorityID: int | None = None
    Name: str | None = None
    Description: str | None = None
    SortOrder: int | None = None
    Color: str | None = None
    IsActive: bool | None = None


class ServiceManagerIssue(RMBaseModel):
    ServiceManagerIssueID: int | None = None
    IssueID: int | None = None
    TicketID: int | None = None
    Title: str | None = None
    Description: str | None = None
    IsClosed: bool | None = None
    PropertyID: int | None = None
    UnitID: int | None = None
    TenantID: int | None = None
    VendorID: int | None = None
    StatusID: int | None = None
    CategoryID: int | None = None
    PriorityID: int | None = None
    LineItems: list[dict[str, Any]] | None = None


class ReportWriterReport(RMBaseModel):
    ReportWriterReportID: int | None = None
    Name: str | None = None
    Rows: list[dict[str, Any]] | None = None


def _install_accounting_models() -> None:
    for spec in ACCOUNTING_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


def _install_platform_metadata_models() -> None:
    for spec in PLATFORM_METADATA_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


def _install_applications_leasing_models() -> None:
    for spec in APPLICATIONS_LEASING_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


def _install_communications_documents_portals_web_models() -> None:
    for spec in COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


def _install_maintenance_assets_inspections_service_models() -> None:
    for spec in MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


def _install_reporting_surveys_memorized_templates_models() -> None:
    for spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


def _install_utilities_metering_models() -> None:
    for spec in UTILITIES_METERING_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


def _install_reference_misc_models() -> None:
    for spec in REFERENCE_MISC_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


def _install_properties_owners_associations_violations_models() -> None:
    for spec in PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_RESOURCE_SPECS:
        base_model = globals().get(spec.model_name, RMBaseModel)
        existing_fields = set(getattr(base_model, "model_fields", ()))
        missing_fields = {
            field_name: (Any | None, None) for field_name in spec.fields if field_name not in existing_fields
        }
        if not missing_fields and spec.model_name in globals():
            continue

        model = create_model(spec.model_name, __base__=base_model, **missing_fields)
        model.__module__ = __name__
        globals()[spec.model_name] = model


_install_accounting_models()
_install_platform_metadata_models()
_install_applications_leasing_models()
_install_communications_documents_portals_web_models()
_install_maintenance_assets_inspections_service_models()
_install_reporting_surveys_memorized_templates_models()
_install_utilities_metering_models()
_install_reference_misc_models()
_install_properties_owners_associations_violations_models()

__all__ = [
    "RMBaseModel",
    "Owner",
    "Tenant",
    "Prospect",
    "Vendor",
    "Property",
    "Contact",
    "Task",
    "Unit",
    "Lease",
    "User",
    "Location",
    "PropertyGroup",
    "Amenity",
    "GLAccount",
    "ChargeType",
    "UnitType",
    "Transaction",
    "HistoryItem",
    "OwnerCheck",
    "Payment",
    "Charge",
    "RecurringCharge",
    "UserDefinedField",
    "UserDefinedValue",
    "VendorBill",
    "ServiceManagerStatus",
    "ServiceManagerCategory",
    "ServiceManagerPriority",
    "ServiceManagerIssue",
    "ReportWriterReport",
    *ACCOUNTING_MODEL_NAMES,
    *PLATFORM_METADATA_MODEL_NAMES,
    *APPLICATIONS_LEASING_MODEL_NAMES,
    *COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_MODEL_NAMES,
    *MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_MODEL_NAMES,
    *REPORTING_SURVEYS_MEMORIZED_TEMPLATES_MODEL_NAMES,
    *UTILITIES_METERING_MODEL_NAMES,
    *REFERENCE_MISC_MODEL_NAMES,
    *PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_MODEL_NAMES,
]
