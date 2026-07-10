from . import models as _models
from .accounting import ACCOUNTING_MODEL_NAMES
from .applications_leasing import APPLICATIONS_LEASING_MODEL_NAMES
from .client import AsyncRentManagerClient, RentManagerClient
from .communications_documents_portals_web import COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_MODEL_NAMES
from .errors import (
    RentManagerAPIError,
    RentManagerAuthError,
    RentManagerBadRequestError,
    RentManagerConflictError,
    RentManagerNotFoundError,
    RentManagerPermissionError,
    RentManagerPreconditionError,
    RentManagerRateLimitError,
    RentManagerServerError,
    RentManagerTransportError,
)
from .maintenance_assets_inspections_service import MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_MODEL_NAMES
from .models import (
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
from .pagination import Page
from .platform_metadata import PLATFORM_METADATA_MODEL_NAMES
from .properties_owners import PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_MODEL_NAMES
from .query import QueryParams, RQL
from .reporting_surveys_memorized_templates import REPORTING_SURVEYS_MEMORIZED_TEMPLATES_MODEL_NAMES
from .reference_misc import REFERENCE_MISC_MODEL_NAMES
from .registry import EndpointConfidence, EndpointRegistry, EndpointSpec
from .token_store import FileTokenStore, InMemoryTokenStore, TokenStore
from .utilities_metering import UTILITIES_METERING_MODEL_NAMES

for _model_name in ACCOUNTING_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)
for _model_name in PLATFORM_METADATA_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)
for _model_name in APPLICATIONS_LEASING_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)
for _model_name in COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)
for _model_name in MAINTENANCE_ASSETS_INSPECTIONS_SERVICE_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)
for _model_name in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)
for _model_name in UTILITIES_METERING_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)
for _model_name in REFERENCE_MISC_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)
for _model_name in PROPERTIES_OWNERS_ASSOCIATIONS_VIOLATIONS_MODEL_NAMES:
    globals()[_model_name] = getattr(_models, _model_name)

__all__ = [
    "Amenity",
    "AsyncRentManagerClient",
    "Charge",
    "ChargeType",
    "Contact",
    "EndpointConfidence",
    "EndpointRegistry",
    "EndpointSpec",
    "FileTokenStore",
    "GLAccount",
    "HistoryItem",
    "InMemoryTokenStore",
    "Lease",
    "Location",
    "Owner",
    "OwnerCheck",
    "Page",
    "Payment",
    "Property",
    "PropertyGroup",
    "Prospect",
    "QueryParams",
    "RQL",
    "RecurringCharge",
    "RentManagerAPIError",
    "RentManagerAuthError",
    "RentManagerBadRequestError",
    "RentManagerClient",
    "RentManagerConflictError",
    "RentManagerNotFoundError",
    "RentManagerPermissionError",
    "RentManagerPreconditionError",
    "RentManagerRateLimitError",
    "RentManagerServerError",
    "RentManagerTransportError",
    "ReportWriterReport",
    "ServiceManagerCategory",
    "ServiceManagerIssue",
    "ServiceManagerPriority",
    "ServiceManagerStatus",
    "Task",
    "Tenant",
    "TokenStore",
    "Transaction",
    "Unit",
    "UnitType",
    "User",
    "UserDefinedField",
    "UserDefinedValue",
    "Vendor",
    "VendorBill",
]

__all__ = list(
    dict.fromkeys(
        [
            *__all__,
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
    )
)
