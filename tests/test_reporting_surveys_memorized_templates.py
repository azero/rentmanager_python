import json
from typing import Any

import httpx
import pytest

import rentmanager_api
import rentmanager_api.models as models
from rentmanager_api import InMemoryTokenStore, RentManagerClient
from rentmanager_api.registry import EndpointRegistry
from rentmanager_api.reporting_surveys_memorized_templates import (
    REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS,
)
from rentmanager_api.resources import core as resource_core
from resource_spec_helpers import specs_from_resource_specs


CRUD_OPERATIONS = ("list", "get", "create", "delete_many", "delete_one")
READ_ONLY_OPERATIONS = ("list", "get")


def _fields(value: str) -> list[str]:
    return value.split() if value else []


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
    raise AssertionError(f"Unsupported operation in test contract: {operation}")


def _case(
    path: str,
    client_attr: str,
    model_name: str,
    fields: str,
    operations: tuple[str, ...] = CRUD_OPERATIONS,
) -> dict[str, Any]:
    return {
        "name": path,
        "client_attr": client_attr,
        "resource_class": f"{path}Resource",
        "model_name": model_name,
        "fields": _fields(fields),
        "endpoints": [_endpoint_from_operation(path, operation) for operation in operations],
    }


REPORTING_SURVEYS_MEMORIZED_TEMPLATES_CASES = [
    _case(
        "CustomReports",
        "custom_reports",
        "CustomReport",
        "CustomReportID Name ReportType Title TitleFormat SubTitle SubTitleFormat FileID BeforeReport "
        "BeforeRecord AfterRecord MarginTop MarginRight MarginBottom MarginLeft Description SortOrder "
        "IsSystem Height Width CreateDate UpdateDate CreateUserID UpdateUserID MetaTag",
    ),
    _case("FilterSummary", "filter_summary", "FilterSummary", "", ("get",)),
    _case(
        "MemorizedComments",
        "memorized_comments",
        "MemorizedComment",
        "MemorizedCommentID Name Comment CreateDate UpdateDate CreateUserID UpdateUserID ConcurrencyID MetaTag",
    ),
    _case(
        "MemorizedEstimateDetails",
        "memorized_estimate_details",
        "MemorizedEstimateDetail",
        "MemorizedEstimateDetailID MemorizedEstimateID InventoryItemID Quantity MarkUp IsTaxable Description "
        "SortOrder Rate IsMarkUpPercentage Amount Total MetaTag",
    ),
    _case(
        "MemorizedEstimates",
        "memorized_estimates",
        "MemorizedEstimate",
        "MemorizedEstimateID Reference EstimateNumber PropertyID TaxRate IsTaxable TaxTypeID Interest "
        "TotalValue MemorizedName MemorizedDescription Comments SalesRepresentativeID FromAddress CreateDate "
        "CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag",
    ),
    _case(
        "MemorizedInvoices",
        "memorized_invoices",
        "MemorizedInvoice",
        "MemorizedInvoiceID PropertyID UnitID AccountID Comment IsTaxable TaxPercentage SubTotal TaxAmount "
        "TotalAmount TaxTypeID TaxChargeTypeID TermID SalesRepresentativeUserID CreateDate CreateUserID "
        "UpdateDate UpdateUserID ConcurrencyID Name Description MetaTag",
    ),
    _case(
        "MemorizedJournals",
        "memorized_journals",
        "MemorizedJournal",
        "MemorizedJournalID Comment IsPeriodAdjustment Reference Amount CreateDate CreateUserID UpdateDate "
        "UpdateUserID ConcurrencyID IsBeginningBalance MemorizedName MemorizedDescription MetaTag",
    ),
    _case(
        "MemorizedReports",
        "memorized_reports",
        "MemorizedReport",
        "MemorizedReportID Name ReportID IsExcludedFromMenu SortOrder CreateUserID CreateDate UpdateUserID "
        "UpdateDate ConcurrencyID MetaTag",
    ),
    _case(
        "MemorizedTasks",
        "memorized_tasks",
        "MemorizedTask",
        "MemorizedTaskID Title Description MemorizedName MemorizedDescription ActionType DueDateDaysOffset",
    ),
    _case(
        "ReportBatches",
        "report_batches",
        "ReportBatche",
        "ReportBatchID Name OwnerID IsExcludedFromMenu IsScheduled OwnedByUserID CreateUserID UpdateUserID MetaTag",
    ),
    _case(
        "ReportBatchReports",
        "report_batch_reports",
        "ReportBatchReport",
        "ReportBatchReportID ReportBatchID MemorizedReportID CustomFormID CustomReportID PluginReportID "
        "SortOrder MetaTag",
    ),
    _case(
        "Reports",
        "reports",
        "Report",
        "ReportCategoryID Name Description HideGridView IsReportPrivilegeRequired PropertyTypes MetaTag",
        READ_ONLY_OPERATIONS,
    ),
    _case(
        "ReportSortOptions",
        "report_sort_options",
        "ReportSortOption",
        "ReportSortOptionPrimaryKeyID SortOrder DisplayName MetaTag",
        READ_ONLY_OPERATIONS,
    ),
    _case(
        "ReportWriterReportColumns",
        "report_writer_report_columns",
        "ReportWriterReportColumn",
        "ReportWriterReportColumnID ReportWriterReportID ColumnOrder OrderByPrecedence IsOrderBy IsHidden "
        "HasTotal Header Formula Width ExecuteOrder TotalScript LeftSpacing Height CanGrow IsWordWrap Format "
        "HeadingFontName HeadingFontSize IsHeadingFontBold IsHeadingFontItalic ValueFontName ValueFontSize "
        "IsValueFontBold IsValueFontItalic TotalFontName TotalFontSize IsTotalFontBold IsTotalFontItalic MetaTag",
    ),
    _case(
        "SurveyAnswers",
        "survey_answers",
        "SurveyAnswer",
        "SurveyAnswerID SurveyQuestionID SurveyResponseID AnswerValue AnswerOther CreateDate CreateUserID "
        "UpdateDate UpdateUserID ConcurrencyID MetaTag",
    ),
    _case(
        "SurveyAutomationSettings",
        "survey_automation_settings",
        "SurveyAutomationSetting",
        "SurveyAutomationSettingID SurveyID IsActive IsSendOnCloseIfNotPreviouslySent MetaTag",
    ),
    _case(
        "SurveyQuestions",
        "survey_questions",
        "SurveyQuestion",
        "SurveyQuestionID SurveyID Question QuestionHTML IsRequired IncludeOtherResponse LimitSelectionCount "
        "SelectionCountMax SortOrder IsActive DateInactivated CreateUserID CreateDate UpdateUserID UpdateDate "
        "ConcurrencyID MetaTag",
    ),
    _case(
        "SurveyResponses",
        "survey_responses",
        "SurveyResponse",
        "SurveyResponseID SurveyID AccountID PropertyID ServiceManagerIssueID UpdateWebUserID FinishDate "
        "ExpirationDate EmailSentItemID CreateUserID CreateDate UpdateUserID UpdateDate ConcurrencyID MetaTag",
    ),
    _case(
        "Surveys",
        "surveys",
        "Survey",
        "SurveyID Name DisplayName IsBoardMemberSurvey Description InternalComments PublishDate PublishUserID "
        "EndDate VoidDate VoidUserID ClosingPageText IntroductionPageText CreateUserID CreateDate UpdateUserID "
        "UpdateDate ConcurrencyID MetaTag",
    ),
    _case(
        "SurveySetups",
        "survey_setups",
        "SurveySetup",
        "SurveySetupID SurveyID LinkExpiryDays FromName Subject EmailMessage TextMessage ButtonColor "
        "LogoUserDefinedFieldID LogoFileID MetaTag",
    ),
]


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


def test_reporting_surveys_memorized_templates_specs_match_todo_contract():
    assert specs_from_resource_specs(REPORTING_SURVEYS_MEMORIZED_TEMPLATES_RESOURCE_SPECS) == (
        REPORTING_SURVEYS_MEMORIZED_TEMPLATES_CASES
    )


@pytest.mark.parametrize(
    "spec",
    REPORTING_SURVEYS_MEMORIZED_TEMPLATES_CASES,
    ids=lambda spec: spec["name"],
)
def test_reporting_surveys_memorized_templates_models_are_permissive_and_include_sample_fields(spec):
    model = getattr(models, spec["model_name"])

    for field in spec["fields"]:
        assert field in model.model_fields

    payload = {spec["fields"][0]: 123} if spec["fields"] else {}
    instance = model.model_validate({**payload, "UnexpectedField": "kept"})
    assert getattr(instance, "UnexpectedField") == "kept"


@pytest.mark.parametrize(
    "spec",
    REPORTING_SURVEYS_MEMORIZED_TEMPLATES_CASES,
    ids=lambda spec: spec["name"],
)
def test_reporting_surveys_memorized_templates_resources_are_attached_with_expected_path_and_model(spec):
    resource_class = getattr(resource_core, spec["resource_class"])
    model = getattr(models, spec["model_name"])
    client, _calls = make_path_client()

    resource = getattr(client, spec["client_attr"])

    assert isinstance(resource, resource_class)
    assert resource.path == spec["name"]
    assert resource.model is model


@pytest.mark.parametrize(
    "spec",
    REPORTING_SURVEYS_MEMORIZED_TEMPLATES_CASES,
    ids=lambda spec: spec["name"],
)
def test_reporting_surveys_memorized_templates_resource_methods_are_non_destructive_mock_calls(spec):
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


def test_reporting_surveys_memorized_templates_registry_includes_all_live_help_endpoints():
    registry_paths = {(endpoint.method, endpoint.path) for endpoint in EndpointRegistry.default()}
    missing_paths = [
        (spec["name"], method, path)
        for spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_CASES
        for method, path in spec["endpoints"]
        if (method, path) not in registry_paths
    ]

    assert missing_paths == []


def test_reporting_surveys_memorized_templates_models_are_top_level_exports():
    for spec in REPORTING_SURVEYS_MEMORIZED_TEMPLATES_CASES:
        assert getattr(rentmanager_api, spec["model_name"]) is getattr(models, spec["model_name"])
        assert spec["model_name"] in rentmanager_api.__all__
