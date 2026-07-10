from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ReportingSurveysMemorizedTemplatesOperation = Literal["list", "get", "create", "delete_many", "delete_one"]


@dataclass(frozen=True, slots=True)
class ReportingSurveysMemorizedTemplatesResourceSpec:
    path: str
    client_attr: str
    model_name: str
    fields: tuple[str, ...]
    operations: tuple[ReportingSurveysMemorizedTemplatesOperation, ...]

    @property
    def resource_class_name(self) -> str:
        return f"{self.path}Resource"


def _fields(value: str) -> tuple[str, ...]:
    return tuple(value.split()) if value else ()


CRUD_OPERATIONS: tuple[ReportingSurveysMemorizedTemplatesOperation, ...] = (
    "list",
    "get",
    "create",
    "delete_many",
    "delete_one",
)
READ_ONLY_OPERATIONS: tuple[ReportingSurveysMemorizedTemplatesOperation, ...] = ("list", "get")


REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS = (
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="CustomReports",
        client_attr="custom_reports",
        model_name="CustomReport",
        fields=_fields(
            "CustomReportID Name ReportType Title TitleFormat SubTitle SubTitleFormat FileID BeforeReport "
            "BeforeRecord AfterRecord MarginTop MarginRight MarginBottom MarginLeft Description SortOrder "
            "IsSystem Height Width CreateDate UpdateDate CreateUserID UpdateUserID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="FilterSummary",
        client_attr="filter_summary",
        model_name="FilterSummary",
        fields=(),
        operations=("get",),
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="MemorizedComments",
        client_attr="memorized_comments",
        model_name="MemorizedComment",
        fields=_fields(
            "MemorizedCommentID Name Comment CreateDate UpdateDate CreateUserID UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="MemorizedEstimateDetails",
        client_attr="memorized_estimate_details",
        model_name="MemorizedEstimateDetail",
        fields=_fields(
            "MemorizedEstimateDetailID MemorizedEstimateID InventoryItemID Quantity MarkUp IsTaxable Description "
            "SortOrder Rate IsMarkUpPercentage Amount Total MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="MemorizedEstimates",
        client_attr="memorized_estimates",
        model_name="MemorizedEstimate",
        fields=_fields(
            "MemorizedEstimateID Reference EstimateNumber PropertyID TaxRate IsTaxable TaxTypeID Interest "
            "TotalValue MemorizedName MemorizedDescription Comments SalesRepresentativeID FromAddress CreateDate "
            "CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="MemorizedInvoices",
        client_attr="memorized_invoices",
        model_name="MemorizedInvoice",
        fields=_fields(
            "MemorizedInvoiceID PropertyID UnitID AccountID Comment IsTaxable TaxPercentage SubTotal TaxAmount "
            "TotalAmount TaxTypeID TaxChargeTypeID TermID SalesRepresentativeUserID CreateDate CreateUserID "
            "UpdateDate UpdateUserID ConcurrencyID Name Description MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="MemorizedJournals",
        client_attr="memorized_journals",
        model_name="MemorizedJournal",
        fields=_fields(
            "MemorizedJournalID Comment IsPeriodAdjustment Reference Amount CreateDate CreateUserID UpdateDate "
            "UpdateUserID ConcurrencyID IsBeginningBalance MemorizedName MemorizedDescription MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="MemorizedReports",
        client_attr="memorized_reports",
        model_name="MemorizedReport",
        fields=_fields(
            "MemorizedReportID Name ReportID IsExcludedFromMenu SortOrder CreateUserID CreateDate UpdateUserID "
            "UpdateDate ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="MemorizedTasks",
        client_attr="memorized_tasks",
        model_name="MemorizedTask",
        fields=_fields(
            "MemorizedTaskID Title Description MemorizedName MemorizedDescription ActionType DueDateDaysOffset"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="ReportBatches",
        client_attr="report_batches",
        model_name="ReportBatche",
        fields=_fields(
            "ReportBatchID Name OwnerID IsExcludedFromMenu IsScheduled OwnedByUserID CreateUserID UpdateUserID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="ReportBatchReports",
        client_attr="report_batch_reports",
        model_name="ReportBatchReport",
        fields=_fields(
            "ReportBatchReportID ReportBatchID MemorizedReportID CustomFormID CustomReportID PluginReportID "
            "SortOrder MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="Reports",
        client_attr="reports",
        model_name="Report",
        fields=_fields(
            "ReportCategoryID Name Description HideGridView IsReportPrivilegeRequired PropertyTypes MetaTag"
        ),
        operations=READ_ONLY_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="ReportSortOptions",
        client_attr="report_sort_options",
        model_name="ReportSortOption",
        fields=_fields("ReportSortOptionPrimaryKeyID SortOrder DisplayName MetaTag"),
        operations=READ_ONLY_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="ReportWriterReportColumns",
        client_attr="report_writer_report_columns",
        model_name="ReportWriterReportColumn",
        fields=_fields(
            "ReportWriterReportColumnID ReportWriterReportID ColumnOrder OrderByPrecedence IsOrderBy IsHidden "
            "HasTotal Header Formula Width ExecuteOrder TotalScript LeftSpacing Height CanGrow IsWordWrap Format "
            "HeadingFontName HeadingFontSize IsHeadingFontBold IsHeadingFontItalic ValueFontName ValueFontSize "
            "IsValueFontBold IsValueFontItalic TotalFontName TotalFontSize IsTotalFontBold IsTotalFontItalic MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="SurveyAnswers",
        client_attr="survey_answers",
        model_name="SurveyAnswer",
        fields=_fields(
            "SurveyAnswerID SurveyQuestionID SurveyResponseID AnswerValue AnswerOther CreateDate CreateUserID "
            "UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="SurveyAutomationSettings",
        client_attr="survey_automation_settings",
        model_name="SurveyAutomationSetting",
        fields=_fields("SurveyAutomationSettingID SurveyID IsActive IsSendOnCloseIfNotPreviouslySent MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="SurveyQuestions",
        client_attr="survey_questions",
        model_name="SurveyQuestion",
        fields=_fields(
            "SurveyQuestionID SurveyID Question QuestionHTML IsRequired IncludeOtherResponse LimitSelectionCount "
            "SelectionCountMax SortOrder IsActive DateInactivated CreateUserID CreateDate UpdateUserID UpdateDate "
            "ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="SurveyResponses",
        client_attr="survey_responses",
        model_name="SurveyResponse",
        fields=_fields(
            "SurveyResponseID SurveyID AccountID PropertyID ServiceManagerIssueID UpdateWebUserID FinishDate "
            "ExpirationDate EmailSentItemID CreateUserID CreateDate UpdateUserID UpdateDate ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="Surveys",
        client_attr="surveys",
        model_name="Survey",
        fields=_fields(
            "SurveyID Name DisplayName IsBoardMemberSurvey Description InternalComments PublishDate PublishUserID "
            "EndDate VoidDate VoidUserID ClosingPageText IntroductionPageText CreateUserID CreateDate UpdateUserID "
            "UpdateDate ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    ReportingSurveysMemorizedTemplatesResourceSpec(
        path="SurveySetups",
        client_attr="survey_setups",
        model_name="SurveySetup",
        fields=_fields(
            "SurveySetupID SurveyID LinkExpiryDays FromName Subject EmailMessage TextMessage ButtonColor "
            "LogoUserDefinedFieldID LogoFileID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
)

REPORTING_SURVEYS_MEMORIZED_TEMPLATES_MODEL_NAMES = tuple(
    dict.fromkeys(spec.model_name for spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS)
)
REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_CLASS_NAMES = tuple(
    spec.resource_class_name for spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS
)

__all__ = [
    "REPORTING_SURVEYS_MEMORIZED_TEMPLATES_MODEL_NAMES",
    "REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_CLASS_NAMES",
    "REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS",
    "ReportingSurveysMemorizedTemplatesOperation",
    "ReportingSurveysMemorizedTemplatesResourceSpec",
]
