from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PlatformMetadataMethod = Literal["GET", "POST", "DELETE"]
PlatformMetadataEndpoint = tuple[PlatformMetadataMethod, str]


@dataclass(frozen=True, slots=True)
class PlatformMetadataResourceSpec:
    path: str
    client_attr: str
    model_name: str
    fields: tuple[str, ...]
    endpoints: tuple[PlatformMetadataEndpoint, ...]

    @property
    def resource_class_name(self) -> str:
        return f"{self.path}Resource"


PLATFORM_METADATA_RESOURCE_SPECS = (
    PlatformMetadataResourceSpec(
        path="APIInformation",
        client_attr="api_information",
        model_name="APIInformationInfo",
        fields=(),
        endpoints=(("GET", "/APIInformation"),),
    ),
    PlatformMetadataResourceSpec(
        path="Current",
        client_attr="current",
        model_name="CurrentInfo",
        fields=(),
        endpoints=(("GET", "/Current"),),
    ),
    PlatformMetadataResourceSpec(
        path="Download",
        client_attr="download",
        model_name="DownloadTokenPayload",
        fields=(),
        endpoints=(("GET", "/Download/{token}"),),
    ),
    PlatformMetadataResourceSpec(
        path="GLAccountTypes",
        client_attr="gl_account_types",
        model_name="GLAccountType",
        fields=("Name", "ShortName", "Multiplier", "InvoiceMultiplier"),
        endpoints=(("GET", "/GLAccountTypes"), ("GET", "/GLAccountTypes/{id}")),
    ),
    PlatformMetadataResourceSpec(
        path="ImageType",
        client_attr="image_type",
        model_name="ImageType",
        fields=(
            "ImageTypeID",
            "Name",
            "Description",
            "IsLayout",
            "CreateDate",
            "CreateUserID",
            "UpdateDate",
            "UpdateUserID",
            "SortOrder",
            "NameWithMaxSize",
            "MaxImageSize",
            "MaximumImageSize",
            "IsSystemType",
            "MetaTag",
        ),
        endpoints=(
            ("GET", "/ImageType"),
            ("GET", "/ImageType/{id}"),
            ("POST", "/ImageType"),
            ("DELETE", "/ImageType"),
            ("DELETE", "/ImageType/{id}"),
        ),
    ),
    PlatformMetadataResourceSpec(
        path="ImageTypes",
        client_attr="image_types",
        model_name="ImageType",
        fields=(
            "ImageTypeID",
            "Name",
            "Description",
            "IsLayout",
            "CreateDate",
            "CreateUserID",
            "UpdateDate",
            "UpdateUserID",
            "SortOrder",
            "NameWithMaxSize",
            "MaxImageSize",
            "MaximumImageSize",
            "IsSystemType",
            "MetaTag",
        ),
        endpoints=(
            ("GET", "/ImageTypes"),
            ("GET", "/ImageTypes/{id}"),
            ("POST", "/ImageTypes"),
            ("DELETE", "/ImageTypes"),
            ("DELETE", "/ImageTypes/{id}"),
        ),
    ),
    PlatformMetadataResourceSpec(
        path="ImportTemplates",
        client_attr="import_templates",
        model_name="ImportTemplate",
        fields=(
            "ImportTemplateID",
            "Name",
            "Description",
            "ImportType",
            "CreateUserID",
            "UpdateUserID",
            "CreateDate",
            "UpdateDate",
            "SortOrder",
            "MetaTag",
        ),
        endpoints=(
            ("GET", "/ImportTemplates"),
            ("GET", "/ImportTemplates/{id}"),
            ("POST", "/ImportTemplates"),
            ("DELETE", "/ImportTemplates"),
            ("DELETE", "/ImportTemplates/{id}"),
        ),
    ),
    PlatformMetadataResourceSpec(
        path="InternalAutomation",
        client_attr="internal_automation",
        model_name="InternalAutomation",
        fields=(),
        endpoints=(("GET", "/InternalAutomation"),),
    ),
    PlatformMetadataResourceSpec(
        path="Privileges",
        client_attr="privileges",
        model_name="Privilege",
        fields=(
            "Name",
            "Description",
            "SortOrder",
            "IsHidden",
            "IsAdd",
            "IsView",
            "IsEdit",
            "IsDelete",
            "IsOn",
            "IsImplemented",
            "MetaTag",
        ),
        endpoints=(("GET", "/Privileges"), ("GET", "/Privileges/{id}")),
    ),
    PlatformMetadataResourceSpec(
        path="Roles",
        client_attr="roles",
        model_name="Role",
        fields=("RoleID", "Name"),
        endpoints=(
            ("GET", "/Roles"),
            ("GET", "/Roles/{id}"),
            ("POST", "/Roles"),
            ("DELETE", "/Roles"),
            ("DELETE", "/Roles/{id}"),
        ),
    ),
    PlatformMetadataResourceSpec(
        path="SessionInformation",
        client_attr="session_information",
        model_name="SessionInformationInfo",
        fields=(),
        endpoints=(("GET", "/SessionInformation"),),
    ),
    PlatformMetadataResourceSpec(
        path="System",
        client_attr="system",
        model_name="SystemInfo",
        fields=(),
        endpoints=(("GET", "/System"),),
    ),
    PlatformMetadataResourceSpec(
        path="SystemPreferences",
        client_attr="system_preferences",
        model_name="SystemPreference",
        fields=("Name", "Value", "MetaTag"),
        endpoints=(
            ("GET", "/SystemPreferences"),
            ("GET", "/SystemPreferences/{id}"),
            ("POST", "/SystemPreferences"),
            ("DELETE", "/SystemPreferences"),
            ("DELETE", "/SystemPreferences/{id}"),
        ),
    ),
    PlatformMetadataResourceSpec(
        path="SystemWebPreferences",
        client_attr="system_web_preferences",
        model_name="SystemWebPreference",
        fields=("Name", "Value", "MetaTag"),
        endpoints=(
            ("GET", "/SystemWebPreferences"),
            ("GET", "/SystemWebPreferences/{id}"),
            ("POST", "/SystemWebPreferences"),
            ("DELETE", "/SystemWebPreferences"),
            ("DELETE", "/SystemWebPreferences/{id}"),
        ),
    ),
    PlatformMetadataResourceSpec(
        path="UserDefinedFields",
        client_attr="user_defined_fields",
        model_name="UserDefinedField",
        fields=(
            "UserDefinedFieldID",
            "SortOrder",
            "Name",
            "IsRequired",
            "FieldType",
            "ComboList",
            "PrecisionValue",
            "DefaultValue",
        ),
        endpoints=(
            ("GET", "/UserDefinedFields"),
            ("GET", "/UserDefinedFields/{id}"),
            ("POST", "/UserDefinedFields"),
            ("DELETE", "/UserDefinedFields"),
            ("DELETE", "/UserDefinedFields/{id}"),
        ),
    ),
)

PLATFORM_METADATA_MODEL_NAMES = tuple(dict.fromkeys(spec.model_name for spec in PLATFORM_METADATA_RESOURCE_SPECS))
PLATFORM_METADATA_RESOURCE_CLASS_NAMES = tuple(spec.resource_class_name for spec in PLATFORM_METADATA_RESOURCE_SPECS)

__all__ = [
    "PLATFORM_METADATA_MODEL_NAMES",
    "PLATFORM_METADATA_RESOURCE_CLASS_NAMES",
    "PLATFORM_METADATA_RESOURCE_SPECS",
    "PlatformMetadataEndpoint",
    "PlatformMetadataMethod",
    "PlatformMetadataResourceSpec",
]
