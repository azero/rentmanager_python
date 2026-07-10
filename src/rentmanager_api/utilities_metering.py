from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


UtilitiesMeteringOperation = Literal["list", "get", "create", "delete_many", "delete_one"]


@dataclass(frozen=True, slots=True)
class UtilitiesMeteringResourceSpec:
    path: str
    client_attr: str
    model_name: str
    fields: tuple[str, ...]
    operations: tuple[UtilitiesMeteringOperation, ...]

    @property
    def resource_class_name(self) -> str:
        return f"{self.path}Resource"


def _fields(value: str) -> tuple[str, ...]:
    return tuple(value.split()) if value else ()


CRUD_OPERATIONS: tuple[UtilitiesMeteringOperation, ...] = (
    "list",
    "get",
    "create",
    "delete_many",
    "delete_one",
)
READ_CREATE_OPERATIONS: tuple[UtilitiesMeteringOperation, ...] = ("list", "get", "create")


UTILITIES_METERING_RESOURCE_SPECS = (
    UtilitiesMeteringResourceSpec(
        path="MasterMeters",
        client_attr="master_meters",
        model_name="MasterMeter",
        fields=_fields(
            "MasterMeterID UtilityID PropertyID VendorID ExpenseAccountGLAccountID MeterNumber IsActive CreateDate "
            "CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypePlusCalculations",
        client_attr="meter_type_plus_calculations",
        model_name="MeterTypePlusCalculation",
        fields=_fields(
            "MeterTypePlusCalculationID MeterTypeID VariableName Calculation Round Description SortOrder MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypePlusRates",
        client_attr="meter_type_plus_rates",
        model_name="MeterTypePlusRate",
        fields=_fields(
            "MeterTypePlusRateID MeterTypePlusRateVariableID Date StandardRate LowIncomeRate Description CreateUserID "
            "CreateDate UpdateUserID UpdateDate ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypePlusRateVariables",
        client_attr="meter_type_plus_rate_variables",
        model_name="MeterTypePlusRateVariable",
        fields=_fields("MeterTypePlusRateVariableID MeterTypeID Name MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypePlusStatementFields",
        client_attr="meter_type_plus_statement_fields",
        model_name="MeterTypePlusStatementField",
        fields=_fields("MeterTypePlusStatementFieldID MeterTypeID Description Title Value SortOrder MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypes",
        client_attr="meter_types",
        model_name="MeterType",
        fields=_fields(
            "MeterTypeID Name ShortName IsMUPlus MinimumCharge FlatFee IsPerDay IsGraduated ConversionFormula "
            "IsRangeEqual BaseRate BaseLine ExcessRate StatementPosition Comments CreateUserID CreateDate "
            "UpdateUserID UpdateDate MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypesPlus",
        client_attr="meter_types_plus",
        model_name="MeterTypesPlu",
        fields=_fields("MeterTypeID Name ShortName"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypesStandard",
        client_attr="meter_types_standard",
        model_name="MeterTypesStandard",
        fields=_fields("MeterTypeID Name ShortName"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypeStandardCalculations",
        client_attr="meter_type_standard_calculations",
        model_name="MeterTypeStandardCalculation",
        fields=_fields("MeterTypeStandardCalculationID MeterTypeID Level Calculation MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="MeterTypeStandardVariables",
        client_attr="meter_type_standard_variables",
        model_name="MeterTypeStandardVariable",
        fields=_fields("MeterTypeStandardVariableID MeterTypeID Name Value SortOrder MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="Utilities",
        client_attr="utilities",
        model_name="Utility",
        fields=_fields("UtilityID Name"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilitiesAutomationSchedules",
        client_attr="utilities_automation_schedules",
        model_name="UtilitiesAutomationSchedule",
        fields=_fields(
            "UtilitiesAutomationScheduleID Name IsActive StartDate EndDate RunDay PostingDay NotificationEmail "
            "IncludeDetails CreateDate UpdateDate IsUseCurrentReadingDay IsPostZeroCharges IsCreateInvoices "
            "InvoiceComment TransactionMemo PropertyGroupID LastRunDate NextRunDate CreateUserID UpdateUserID "
            "ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityConsumptionGroupMeterTypes",
        client_attr="utility_consumption_group_meter_types",
        model_name="UtilityConsumptionGroupMeterType",
        fields=_fields("UtilityConsumptionGroupMeterTypeID UtilityConsumptionGroupID UtilityMeterID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityConsumptionGroupRanges",
        client_attr="utility_consumption_group_ranges",
        model_name="UtilityConsumptionGroupRange",
        fields=_fields(
            "UtilityConsumptionGroupRangeID UtilityConsumptionGroupID Name LowValue HighValue ExpressThemeColorID "
            "HexValue IsException ExceptionDescription IsRequireExceptionImage IsRequireExceptionComment "
            "ConsumptionUnitStatus IsZeroConsumption IsNegativeConsumption MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityConsumptionGroups",
        client_attr="utility_consumption_groups",
        model_name="UtilityConsumptionGroup",
        fields=_fields(
            "UtilityConsumptionGroupID Name UtilityTypeID ConsumptionRangeUoM IsVacantOccupiedSplit "
            "IsShowNegativeConsumption IsShowZeroConsumption MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityMeterLinkedReadings",
        client_attr="utility_meter_linked_readings",
        model_name="UtilityMeterLinkedReading",
        fields=_fields(
            "UtilityMeterLinkedReadingID UtilityReadingID IsUseDefaultMeterType MeterNumber IsLowIncome ClassCode "
            "CurrentReading CurrentReadingDate PreviousReading PreviousReadingDate RZone ReadingType "
            "UtilityReadingFileMapID ReadingUoM IsPending ReadingDueDate CreateUserID CreateDate UpdateUserID "
            "UpdateDate ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityMeterReadingHistory",
        client_attr="utility_meter_reading_history",
        model_name="UtilityMeterReadingHistory",
        fields=_fields("UtilityMeterReadingHistoryID UtilityID MeterNumber"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityMeterReadings",
        client_attr="utility_meter_readings",
        model_name="UtilityMeterReading",
        fields=_fields(
            "UtilityMeterReadingID UtilityID MeterTypeID UseDefaultMeterType PropertyID UnitID MeterNumber Route "
            "IsLowIncome ClassCode CurrentReading CurrentReadingDate PreviousReading PreviousReadingDate BillingYear "
            "RZone Other Other2 Other3 Other4 Other5 Comments UtilityReadingFileMapID ReadingUoM "
            "ServiceManagerIssueID IsPending ReadingDueDate ExceptionReasonID ConditionalApproverNote "
            "FinalApproverNote ReviewerUserID ConditionalApproverUserID FinalApproverUserID ConsumptionRange "
            "ConsumptionRangeThemeColorID ConsumptionRangeHex CreateDate UpdateDate ConcurrencyID CreateUserID"
        ),
        operations=READ_CREATE_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityMeters",
        client_attr="utility_meters",
        model_name="UtilityMeter",
        fields=_fields(
            "UtilityMeterID Name ShortName IsUtilityMeterPlus MinimumCharge FlatFee IsPerDay IsGraduated "
            "ConversionFormula IsRangeEqual BaseRate BaseLine ExcessRate StatementPosition Comments UtilityTypeID "
            "DefaultUoM BillingUoM IsAutoConvertMeterUoMToBillingUoM CreateDate UpdateDate CreateUserID "
            "UpdateUserID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityReadingFileMapFiles",
        client_attr="utility_reading_file_map_files",
        model_name="UtilityReadingFileMapFile",
        fields=_fields("UtilityReadingFileMapFileID UtilityReadingFileMapID FileID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityReadingFileMaps",
        client_attr="utility_reading_file_maps",
        model_name="UtilityReadingFileMap",
        fields=_fields("UtilityReadingFileMapID UtilityMeterID UtilityConsumptionGroupRangeID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityReadingsFileFormats",
        client_attr="utility_readings_file_formats",
        model_name="UtilityReadingsFileFormat",
        fields=_fields(
            "UtilityReadingsFileFormatID CreateUserID UpdateUserID ConcurrencyID Name IsExcludeFirstLine "
            "IsFixedLengthField FixedLengthRecordTerminator RecordLength FieldDelimiter TextQualifier CreateDate "
            "UpdateDate MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityReadingsHistories",
        client_attr="utility_readings_histories",
        model_name="UtilityReadingsHistory",
        fields=_fields(
            "UtilityReadingsHistoryID UtilityID MeterNumber Route EntityID UtilityMeterID UtilityReadingFileMapID "
            "ReadingUoM BillingUoM IsLowIncome ClassCode CurrentReading CurrentReadingDate PreviousReading "
            "PreviousReadingDate BillingYear Consumption AdjustedConsumption ChargeAmount PostDate AccountID "
            "ChargeID PostingID RZone Other Other2 Other3 Other4 Other5 Comments SubEntityID ExceptionReason "
            "ReviewerUserID ConditionalApproverNote FinalApproverNote ConditionalApproverUserID FinalApproverUserID "
            "ConsumptionRange ConsumptionRangeThemeColorID ConsumptionRangeHex"
        ),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityTypes",
        client_attr="utility_types",
        model_name="UtilityType",
        fields=_fields("UtilityTypeID Name MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityTypeUnitOfMeasures",
        client_attr="utility_type_unit_of_measures",
        model_name="UtilityTypeUnitOfMeasure",
        fields=_fields("UtilityTypeUnitOfMeasureID UtilityTypeID UtilityUnitOfMeasureID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityUnitOfMeasureConversions",
        client_attr="utility_unit_of_measure_conversions",
        model_name="UtilityUnitOfMeasureConversion",
        fields=_fields("UtilityUnitOfMeasureConversionID ReadingUoM BillingUoM Multiplier MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    UtilitiesMeteringResourceSpec(
        path="UtilityUnitOfMeasures",
        client_attr="utility_unit_of_measures",
        model_name="UtilityUnitOfMeasure",
        fields=_fields("UtilityUnitOfMeasureID Name MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
)


UTILITIES_METERING_MODEL_NAMES = tuple(dict.fromkeys(spec.model_name for spec in UTILITIES_METERING_RESOURCE_SPECS))
UTILITIES_METERING_RESOURCE_CLASS_NAMES = tuple(spec.resource_class_name for spec in UTILITIES_METERING_RESOURCE_SPECS)


__all__ = [
    "UTILITIES_METERING_MODEL_NAMES",
    "UTILITIES_METERING_RESOURCE_CLASS_NAMES",
    "UTILITIES_METERING_RESOURCE_SPECS",
    "UtilitiesMeteringOperation",
    "UtilitiesMeteringResourceSpec",
]
