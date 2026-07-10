from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CommunicationsDocumentsPortalsWebOperation = Literal["list", "get", "create", "delete_many", "delete_one"]


@dataclass(frozen=True, slots=True)
class CommunicationsDocumentsPortalsWebResourceSpec:
    path: str
    client_attr: str
    model_name: str
    fields: tuple[str, ...]
    operations: tuple[CommunicationsDocumentsPortalsWebOperation, ...]

    @property
    def resource_class_name(self) -> str:
        return f"{self.path}Resource"


def _fields(value: str) -> tuple[str, ...]:
    return tuple(value.split()) if value else ()


CRUD_OPERATIONS: tuple[CommunicationsDocumentsPortalsWebOperation, ...] = (
    "list",
    "get",
    "create",
    "delete_many",
    "delete_one",
)
READ_ONLY_OPERATIONS: tuple[CommunicationsDocumentsPortalsWebOperation, ...] = ("list", "get")
LIST_ONLY_OPERATIONS: tuple[CommunicationsDocumentsPortalsWebOperation, ...] = ("list",)


COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS = (
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="AutomatedNotificationEventSetupEvictionWorkflowStages",
        client_attr="automated_notification_event_setup_eviction_workflow_stages",
        model_name="AutomatedNotificationEventSetupEvictionWorkflowStage",
        fields=_fields(
            "AutomatedNotificationEventSetupEvictionWorkflowStageID AutomatedNotificationEventSetupID "
            "EvictionWorkflowStageID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="AutomatedNotificationEventSetupInspectorTypes",
        client_attr="automated_notification_event_setup_inspector_types",
        model_name="AutomatedNotificationEventSetupInspectorType",
        fields=_fields("NotificationEventSetupInspectorTypeID NotificationEventSetupID InspectorTypeID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="AutomatedNotificationEventSetupRenewalStatuss",
        client_attr="automated_notification_event_setup_renewal_statuses",
        model_name="AutomatedNotificationEventSetupRenewalStatus",
        fields=_fields(
            "AutomatedNotificationEventSetupRenewalStatusID AutomatedNotificationEventSetupID RenewalStatusID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="AutomatedNotificationEventSetups",
        client_attr="automated_notification_event_setups",
        model_name="AutomatedNotificationEventSetup",
        fields=_fields(
            "AutomatedNotificationEventSetupID IsSystemDefaultSetup IsActive IsIncludeProspectMoveIn ExcludeIfMoveOut "
            "IsRenewalAccepted IsSendReminderDailyUntilPaidOrCancelled SurveyExpirationDays "
            "IsArchitecturalRequestApproved ArchitecturalRequestStatuses Days IsAddHistory FromName FromEmailAddress "
            "Subject Message AppendWebChatQueueMessageToEmail SMSMessage AppendWebChatQueueMessageToSMS "
            "LetterTemplateID ServiceBasedMessageSendTime ServiceBasedMessageSendTimeTimeZone "
            "ServiceBasedMessageSendTimeIsDaylightSavingTime ServiceBasedLastRunTime IsExcludeReservedProspect "
            "CreateDate CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="AutomatedNotificationSetups",
        client_attr="automated_notification_setups",
        model_name="AutomatedNotificationSetup",
        fields=_fields(
            "AutomatedNotificationEventSetupID IsSystemDefaultSetup IsActive IsIncludeProspectMoveIn ExcludeIfMoveOut "
            "IsRenewalAccepted IsSendReminderDailyUntilPaidOrCancelled SurveyExpirationDays "
            "IsArchitecturalRequestApproved ArchitecturalRequestStatuses Days IsAddHistory FromName FromEmailAddress "
            "Subject Message AppendWebChatQueueMessageToEmail SMSMessage AppendWebChatQueueMessageToSMS "
            "LetterTemplateID ServiceBasedMessageSendTime ServiceBasedMessageSendTimeTimeZone "
            "ServiceBasedMessageSendTimeIsDaylightSavingTime ServiceBasedLastRunTime IsExcludeReservedProspect "
            "CreateDate CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="AutomatedNotificationTypeGroups",
        client_attr="automated_notification_type_groups",
        model_name="AutomatedNotificationTypeGroup",
        fields=_fields("AutomatedNotificationTypeGroupID Name Description SortOrder MetaTag"),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="AutomatedNotificationTypes",
        client_attr="automated_notification_types",
        model_name="AutomatedNotificationType",
        fields=_fields(
            "AutomatedNotificationTypeID Name Description TreeViewDescription IsService IsStandaloneAvailable "
            "IsHidden AutomatedNotificationTypeGroupID MetaTag"
        ),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="BlueMoonSignableDocuments",
        client_attr="blue_moon_signable_documents",
        model_name="BlueMoonSignableDocument",
        fields=_fields(
            "BlueMoonSignableDocumentID BlueMoonESignatureID LeaseAttachmentID HistoryID DateInitiated ExpirationDate "
            "RepresentativeName RepresentativePhone RepresentativeEmail InitiatedByUserID DateCompleted "
            "CompletedByUserID CreateDate CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="CustomForms",
        client_attr="custom_forms",
        model_name="CustomForm",
        fields=_fields(
            "CustomFormID Name Description IsSystemReport IsVPOReady IsXiForm IsConvertedFromXIForm IsTypeDefault "
            "IsTypeSystemDefault IsSuppressPageNumbers IsSuppressPageFooter CreateDate CreateUserID UpdateDate "
            "UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="DocumentPackets",
        client_attr="document_packets",
        model_name="DocumentPacket",
        fields=_fields("DocumentPacketID Name Description"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="EmailChains",
        client_attr="email_chains",
        model_name="EmailChain",
        fields=_fields("EmailChainID IsPrivate SentUserID ChainGuid MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="Emails",
        client_attr="emails",
        model_name="Email",
        fields=(),
        operations=LIST_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="EmailSentFolders",
        client_attr="email_sent_folders",
        model_name="EmailSentFolder",
        fields=_fields(
            "EmailSentFolderID FolderName FolderLevel ParentEmailSentFolderID UpdateDate ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="EmailSentItems",
        client_attr="email_sent_items",
        model_name="EmailSentItem",
        fields=_fields(
            "EmailSentItemID FromAddress Subject EmailSentDate MessageBody DisplayName IsSentIndividually IsOutgoing "
            "UserID CreateUserID IsHTML EmailSentFolderID EmailChainID EntityKeyID EntityTypeID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="LetterTemplateFolders",
        client_attr="letter_template_folders",
        model_name="LetterTemplateFolder",
        fields=_fields(
            "LetterTemplateFolderID Name CreateDate CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="LetterTemplateLetterTemplateFolders",
        client_attr="letter_template_letter_template_folders",
        model_name="LetterTemplateLetterTemplateFolder",
        fields=_fields("LetterTemplateLetterTemplateFolderID LetterTemplateID LetterTemplateFolderID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="LetterTemplates",
        client_attr="letter_templates",
        model_name="LetterTemplate",
        fields=_fields(
            "LetterTemplateID Name Description IsOnRightClickMenu IsOnLetterMenu MaximumSignerCount "
            "RequiresCompanyRepresentativeSignatures"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="NDTBroadcastLists",
        client_attr="ndt_broadcast_lists",
        model_name="NDTBroadcastList",
        fields=_fields(
            "NDTBroadcastListID ListName CreateDate CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="NDTPhoneBroadcastBatches",
        client_attr="ndt_phone_broadcast_batches",
        model_name="NDTPhoneBroadcastBatche",
        fields=_fields(
            "NDTPhoneBroadcastBatchID BroadcastType NDTBroadcastResponseBatchID MessageName MessageDescription "
            "PhoneRecordingID IsScheduledNow ScheduledDate IsCancelled CreateUserID CreateDate MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="NDTPhoneBroadcasts",
        client_attr="ndt_phone_broadcasts",
        model_name="NDTPhoneBroadcast",
        fields=_fields("NDTPhoneBroadcastID RecordingName PhoneRecordingID Description MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="NDTTextBroadcastBatches",
        client_attr="ndt_text_broadcast_batches",
        model_name="NDTTextBroadcastBatche",
        fields=_fields(
            "NDTTextBroadcastBatchID BroadcastType NDTBroadcastResponseBatchID MessageName MessageDescription "
            "IsScheduledNow ScheduledDate IsCancelled CreateUserID CreateDate MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="NDTTextBroadcasts",
        client_attr="ndt_text_broadcasts",
        model_name="NDTTextBroadcast",
        fields=_fields(
            "NDTTextBroadcastID Name Description MessageText CreateDate CreateUserID UpdateDate UpdateUserID "
            "ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="Notes",
        client_attr="notes",
        model_name="Note",
        fields=_fields("NoteID Name Description"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="OutgoingTexts",
        client_attr="outgoing_texts",
        model_name="OutgoingText",
        fields=_fields(
            "OutgoingTextID NDTBroadcastBatchID PhoneNumber Message ParentID ParentType SentUserID SentDate IsMMS "
            "SegmentCount LocationID MainLocationOutgoingTextID SendingPhoneNumberString HistoryCategoryID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="PhoneBroadcastRecordings",
        client_attr="phone_broadcast_recordings",
        model_name="PhoneBroadcastRecording",
        fields=_fields("PhoneBroadcastRecordingID RecordingName FileID Description MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="PhoneNumbers",
        client_attr="phone_numbers",
        model_name="PhoneNumber",
        fields=_fields("PhoneNumber"),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="PublishedTWAReports",
        client_attr="published_twa_reports",
        model_name="PublishedTWAReport",
        fields=_fields(
            "PublishedTWAReportID TWAReportTemplateID PropertyID PublishDate IsActiveCommitteeMembersOnly "
            "IsCurrentBoardMembersOnly ExpirationDateResolved DisplayName DisplayNameResolved CreateDate CreateUserID "
            "UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="RMResidentPushNotificationTokens",
        client_attr="rm_resident_push_notification_tokens",
        model_name="RMResidentPushNotificationToken",
        fields=_fields(
            "RMResidentPushNotificationTokenID WebUserID Token GroupNotificationKey GroupNotificationKeyName DeviceID "
            "DeviceType RegistrationDate CreateDate CreateUser UpdateDate UpdateUser ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="RMVoIPCallHistory",
        client_attr="rm_vo_ip_call_history",
        model_name="RMVoIPCallHistory",
        fields=_fields(
            "RMVoIPCallHistoryID RMVoIPMainLocationCallHistoryID LocationID ParentID UserIDTo UserIDFrom CallTo "
            "CallFrom DialedPhoneNumber IsOutbound IsContactMade HistoryCategoryID LeadSourceID "
            "OwnerProspectLeadSourceID StartTime EndTime StartTimeUTC Notes CallerID ChannelID RMVoIPFileName MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="SignableDocumentPackets",
        client_attr="signable_document_packets",
        model_name="SignableDocumentPacket",
        fields=_fields(
            "SignableDocumentPacketID Name AccountID CompletedDate VoidedDate CreateDate CreateUserID UpdateDate "
            "UpdateUserID TotalSignerCount CompletedSignerCount ExpirationDate Comment MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="SignableDocuments",
        client_attr="signable_documents",
        model_name="SignableDocument",
        fields=_fields(
            "SignableDocumentID Name PageCount SignableDocumentPacketID OriginalFileID CurrentFileID IsLandscape "
            "CreateDate CreateUserID UpdateDate UpdateUserID SignerCount MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="SignablePDFTemplates",
        client_attr="signable_pdf_templates",
        model_name="SignablePDFTemplate",
        fields=_fields("Name Description"),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="Signatures",
        client_attr="signatures",
        model_name="Signature",
        fields=_fields(
            "SignatureID Name Description FileID CreateUserID CreateDate UpdateUserID UpdateDate ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="TextMessagingConversations",
        client_attr="text_messaging_conversations",
        model_name="TextMessagingConversation",
        fields=_fields("ExternalPhoneNumber ParentType ParentID LastTextDate MetaTag"),
        operations=LIST_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="TextNumbers",
        client_attr="text_numbers",
        model_name="TextNumber",
        fields=_fields(
            "TextNumberID TextNumber IsForBroadcast IsSystemDefault IsActive Name Description StrippedTextNumber "
            "SortOrder MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="TextTemplateFolders",
        client_attr="text_template_folders",
        model_name="TextTemplateFolder",
        fields=_fields("TextTemplateFolderID Name SortOrder CreateDate CreateUserID UpdateDate UpdateUserID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="TextTemplates",
        client_attr="text_templates",
        model_name="TextTemplate",
        fields=_fields(
            "TextTemplateID Name Description MessageText TextTemplateFolderID HistoryCategoryID SortOrder CreateDate "
            "CreateUserID UpdateDate UpdateUserID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="TWADisabledProperties",
        client_attr="twa_disabled_properties",
        model_name="TWADisabledProperty",
        fields=_fields("TWADisabledPropertyID PropertyID PropertyGroupID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="TWAReportTemplates",
        client_attr="twa_report_templates",
        model_name="TWAReportTemplate",
        fields=_fields(
            "TWAReportTemplateID PropertyID DisplayName IsActiveCommitteeMembersOnly IsCurrentBoardMembersOnly "
            "IsExpirePublishedReport ExpireAfterNumber ExpireAfterPeriodType FirstRunDate IsRecurring "
            "RecurrenceEndDate NextPublishDate IsActive CreateDate CreateUserID UpdateDate UpdateUserID "
            "ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="VirtualPostOfficeJobs",
        client_attr="virtual_post_office_jobs",
        model_name="VirtualPostOfficeJob",
        fields=_fields("VirtualPostOfficeJobID CreateDate CreateUserID Fee Status MetaTag"),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="WebChatConversationItems",
        client_attr="web_chat_conversation_items",
        model_name="WebChatConversationItem",
        fields=_fields(
            "WebChatConversationItemID WebChatConversationID CreateDate CreateUserID UTCCreateDate Message HasImages "
            "UpdateDate IsSystemMessage MetaTag"
        ),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="WebChatConversations",
        client_attr="web_chat_conversations",
        model_name="WebChatConversation",
        fields=_fields(
            "WebChatConversationID CreateDate UTCCreateDate InteractiveStartDate UTCInteractiveStartDate AgentUserID "
            "IsOfflineQuestion WebChatQueueID SortOrder Comment Notes Name EmailAddress PhoneNumber PropertyName "
            "UnitName AccountNumber EndDate UTCEndDate TimeOutDate UTCTimeOutDate WaitTime IsTimedOut IsTransferred "
            "IsClientActive HubGroupName Duration CreateUserID UpdateUserID UpdateDate MetaTag"
        ),
        operations=READ_ONLY_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="WebChatQueues",
        client_attr="web_chat_queues",
        model_name="WebChatQueue",
        fields=_fields("WebChatQueueID Name"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="WebhookDetails",
        client_attr="webhook_details",
        model_name="WebhookDetail",
        fields=_fields(
            "WebhookDetailID URL PartnerProductID CreateDate CreateUserID UpdateDate UpdateUserID ConcurrencyID MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="WebMessageBoardPosts",
        client_attr="web_message_board_posts",
        model_name="WebMessageBoardPost",
        fields=_fields("WebMessageBoardPostID PostText PostDate PostParentID IsApproved ApprovalUserID MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="WebPageCustomizations",
        client_attr="web_page_customizations",
        model_name="WebPageCustomization",
        fields=_fields("WebPagesCustomizationID Title CustomMessage CustomMenu Singular Plural MetaTag"),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="WebUserAccounts",
        client_attr="web_user_accounts",
        model_name="WebUserAccount",
        fields=_fields(
            "WebUserAccountID WebUserID AccountID DisplayID Nickname IsDefault IsEnabled CreateDate UpdateDate MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
    CommunicationsDocumentsPortalsWebResourceSpec(
        path="WebUsers",
        client_attr="web_users",
        model_name="WebUser",
        fields=_fields(
            "WebUserID UserName UserNameIsVerified EmailAddress IsVerifiedEmail FirstName LastName Name "
            "LastSuccessfulLogin LastFailedLogin LastLogout LastLockout FailedLogins IsPasswordReset CreateDate "
            "CreateUserID UpdateDate UpdateUserID ConcurrencyID IsOptInCreditReporting IsShowNameAddressInDirectory "
            "IsShowPhoneNumberInDirectory IsShowEmailAddressInDirectory PaymentLockoutTime OverridePaymentLockoutTime "
            "CreditReportingID ViewedOWAWhatsNew TAToken MetaTag"
        ),
        operations=CRUD_OPERATIONS,
    ),
)


COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_MODEL_NAMES = tuple(
    dict.fromkeys(spec.model_name for spec in COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS)
)
COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_CLASS_NAMES = tuple(
    spec.resource_class_name for spec in COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS
)


__all__ = [
    "COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_MODEL_NAMES",
    "COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_CLASS_NAMES",
    "COMMUNICATIONS_DOCUMENTS_PORTALS_WEB_RESOURCE_SPECS",
    "CommunicationsDocumentsPortalsWebOperation",
    "CommunicationsDocumentsPortalsWebResourceSpec",
]
