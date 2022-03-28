"""
Type annotations for iot service type definitions.

[Open documentation](https://vemel.github.io/types_aiobotocore_docs/types_aiobotocore_iot/type_defs/)

Usage::

    ```python
    from types_aiobotocore_iot.type_defs import AbortConfigTypeDef

    data: AbortConfigTypeDef = {...}
    ```
"""
import sys
from datetime import datetime
from typing import IO, Dict, List, Mapping, Sequence, Union

from botocore.response import StreamingBody
from typing_extensions import NotRequired

from .literals import (
    ActionTypeType,
    AggregationTypeNameType,
    AuditCheckRunStatusType,
    AuditFindingSeverityType,
    AuditFrequencyType,
    AuditMitigationActionsExecutionStatusType,
    AuditMitigationActionsTaskStatusType,
    AuditTaskStatusType,
    AuditTaskTypeType,
    AuthDecisionType,
    AuthorizerStatusType,
    AutoRegistrationStatusType,
    AwsJobAbortCriteriaFailureTypeType,
    BehaviorCriteriaTypeType,
    CACertificateStatusType,
    CannedAccessControlListType,
    CertificateModeType,
    CertificateStatusType,
    ComparisonOperatorType,
    ConfidenceLevelType,
    CustomMetricTypeType,
    DayOfWeekType,
    DetectMitigationActionExecutionStatusType,
    DetectMitigationActionsTaskStatusType,
    DeviceDefenderIndexingModeType,
    DimensionValueOperatorType,
    DomainConfigurationStatusType,
    DomainTypeType,
    DynamicGroupStatusType,
    DynamoKeyTypeType,
    EventTypeType,
    FieldTypeType,
    FleetMetricUnitType,
    IndexStatusType,
    JobExecutionFailureTypeType,
    JobExecutionStatusType,
    JobStatusType,
    LogLevelType,
    LogTargetTypeType,
    MessageFormatType,
    MitigationActionTypeType,
    ModelStatusType,
    NamedShadowIndexingModeType,
    OTAUpdateStatusType,
    ProtocolType,
    ReportTypeType,
    ResourceTypeType,
    RetryableFailureTypeType,
    ServerCertificateStatusType,
    ServiceTypeType,
    StatusType,
    TargetSelectionType,
    ThingConnectivityIndexingModeType,
    ThingGroupIndexingModeType,
    ThingIndexingModeType,
    TopicRuleDestinationStatusType,
    VerificationStateType,
    ViolationEventTypeType,
)

if sys.version_info >= (3, 9):
    from typing import Literal
else:
    from typing_extensions import Literal
if sys.version_info >= (3, 9):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


__all__ = (
    "AbortConfigTypeDef",
    "AbortCriteriaTypeDef",
    "AcceptCertificateTransferRequestRequestTypeDef",
    "ActionTypeDef",
    "ActiveViolationTypeDef",
    "AddThingToBillingGroupRequestRequestTypeDef",
    "AddThingToThingGroupRequestRequestTypeDef",
    "AddThingsToThingGroupParamsTypeDef",
    "AggregationTypeTypeDef",
    "AlertTargetTypeDef",
    "AllowedTypeDef",
    "AssetPropertyTimestampTypeDef",
    "AssetPropertyValueTypeDef",
    "AssetPropertyVariantTypeDef",
    "AssociateTargetsWithJobRequestRequestTypeDef",
    "AssociateTargetsWithJobResponseTypeDef",
    "AttachPolicyRequestRequestTypeDef",
    "AttachPrincipalPolicyRequestRequestTypeDef",
    "AttachSecurityProfileRequestRequestTypeDef",
    "AttachThingPrincipalRequestRequestTypeDef",
    "AttributePayloadTypeDef",
    "AuditCheckConfigurationTypeDef",
    "AuditCheckDetailsTypeDef",
    "AuditFindingTypeDef",
    "AuditMitigationActionExecutionMetadataTypeDef",
    "AuditMitigationActionsTaskMetadataTypeDef",
    "AuditMitigationActionsTaskTargetTypeDef",
    "AuditNotificationTargetTypeDef",
    "AuditSuppressionTypeDef",
    "AuditTaskMetadataTypeDef",
    "AuthInfoTypeDef",
    "AuthResultTypeDef",
    "AuthorizerConfigTypeDef",
    "AuthorizerDescriptionTypeDef",
    "AuthorizerSummaryTypeDef",
    "AwsJobAbortConfigTypeDef",
    "AwsJobAbortCriteriaTypeDef",
    "AwsJobExecutionsRolloutConfigTypeDef",
    "AwsJobExponentialRolloutRateTypeDef",
    "AwsJobPresignedUrlConfigTypeDef",
    "AwsJobRateIncreaseCriteriaTypeDef",
    "AwsJobTimeoutConfigTypeDef",
    "BehaviorCriteriaTypeDef",
    "BehaviorModelTrainingSummaryTypeDef",
    "BehaviorTypeDef",
    "BillingGroupMetadataTypeDef",
    "BillingGroupPropertiesTypeDef",
    "BucketTypeDef",
    "BucketsAggregationTypeTypeDef",
    "CACertificateDescriptionTypeDef",
    "CACertificateTypeDef",
    "CancelAuditMitigationActionsTaskRequestRequestTypeDef",
    "CancelAuditTaskRequestRequestTypeDef",
    "CancelCertificateTransferRequestRequestTypeDef",
    "CancelDetectMitigationActionsTaskRequestRequestTypeDef",
    "CancelJobExecutionRequestRequestTypeDef",
    "CancelJobRequestRequestTypeDef",
    "CancelJobResponseTypeDef",
    "CertificateDescriptionTypeDef",
    "CertificateTypeDef",
    "CertificateValidityTypeDef",
    "CloudwatchAlarmActionTypeDef",
    "CloudwatchLogsActionTypeDef",
    "CloudwatchMetricActionTypeDef",
    "CodeSigningCertificateChainTypeDef",
    "CodeSigningSignatureTypeDef",
    "CodeSigningTypeDef",
    "ConfigurationTypeDef",
    "ConfirmTopicRuleDestinationRequestRequestTypeDef",
    "CreateAuditSuppressionRequestRequestTypeDef",
    "CreateAuthorizerRequestRequestTypeDef",
    "CreateAuthorizerResponseTypeDef",
    "CreateBillingGroupRequestRequestTypeDef",
    "CreateBillingGroupResponseTypeDef",
    "CreateCertificateFromCsrRequestRequestTypeDef",
    "CreateCertificateFromCsrResponseTypeDef",
    "CreateCustomMetricRequestRequestTypeDef",
    "CreateCustomMetricResponseTypeDef",
    "CreateDimensionRequestRequestTypeDef",
    "CreateDimensionResponseTypeDef",
    "CreateDomainConfigurationRequestRequestTypeDef",
    "CreateDomainConfigurationResponseTypeDef",
    "CreateDynamicThingGroupRequestRequestTypeDef",
    "CreateDynamicThingGroupResponseTypeDef",
    "CreateFleetMetricRequestRequestTypeDef",
    "CreateFleetMetricResponseTypeDef",
    "CreateJobRequestRequestTypeDef",
    "CreateJobResponseTypeDef",
    "CreateJobTemplateRequestRequestTypeDef",
    "CreateJobTemplateResponseTypeDef",
    "CreateKeysAndCertificateRequestRequestTypeDef",
    "CreateKeysAndCertificateResponseTypeDef",
    "CreateMitigationActionRequestRequestTypeDef",
    "CreateMitigationActionResponseTypeDef",
    "CreateOTAUpdateRequestRequestTypeDef",
    "CreateOTAUpdateResponseTypeDef",
    "CreatePolicyRequestRequestTypeDef",
    "CreatePolicyResponseTypeDef",
    "CreatePolicyVersionRequestRequestTypeDef",
    "CreatePolicyVersionResponseTypeDef",
    "CreateProvisioningClaimRequestRequestTypeDef",
    "CreateProvisioningClaimResponseTypeDef",
    "CreateProvisioningTemplateRequestRequestTypeDef",
    "CreateProvisioningTemplateResponseTypeDef",
    "CreateProvisioningTemplateVersionRequestRequestTypeDef",
    "CreateProvisioningTemplateVersionResponseTypeDef",
    "CreateRoleAliasRequestRequestTypeDef",
    "CreateRoleAliasResponseTypeDef",
    "CreateScheduledAuditRequestRequestTypeDef",
    "CreateScheduledAuditResponseTypeDef",
    "CreateSecurityProfileRequestRequestTypeDef",
    "CreateSecurityProfileResponseTypeDef",
    "CreateStreamRequestRequestTypeDef",
    "CreateStreamResponseTypeDef",
    "CreateThingGroupRequestRequestTypeDef",
    "CreateThingGroupResponseTypeDef",
    "CreateThingRequestRequestTypeDef",
    "CreateThingResponseTypeDef",
    "CreateThingTypeRequestRequestTypeDef",
    "CreateThingTypeResponseTypeDef",
    "CreateTopicRuleDestinationRequestRequestTypeDef",
    "CreateTopicRuleDestinationResponseTypeDef",
    "CreateTopicRuleRequestRequestTypeDef",
    "CustomCodeSigningTypeDef",
    "DeleteAccountAuditConfigurationRequestRequestTypeDef",
    "DeleteAuditSuppressionRequestRequestTypeDef",
    "DeleteAuthorizerRequestRequestTypeDef",
    "DeleteBillingGroupRequestRequestTypeDef",
    "DeleteCACertificateRequestRequestTypeDef",
    "DeleteCertificateRequestRequestTypeDef",
    "DeleteCustomMetricRequestRequestTypeDef",
    "DeleteDimensionRequestRequestTypeDef",
    "DeleteDomainConfigurationRequestRequestTypeDef",
    "DeleteDynamicThingGroupRequestRequestTypeDef",
    "DeleteFleetMetricRequestRequestTypeDef",
    "DeleteJobExecutionRequestRequestTypeDef",
    "DeleteJobRequestRequestTypeDef",
    "DeleteJobTemplateRequestRequestTypeDef",
    "DeleteMitigationActionRequestRequestTypeDef",
    "DeleteOTAUpdateRequestRequestTypeDef",
    "DeletePolicyRequestRequestTypeDef",
    "DeletePolicyVersionRequestRequestTypeDef",
    "DeleteProvisioningTemplateRequestRequestTypeDef",
    "DeleteProvisioningTemplateVersionRequestRequestTypeDef",
    "DeleteRoleAliasRequestRequestTypeDef",
    "DeleteScheduledAuditRequestRequestTypeDef",
    "DeleteSecurityProfileRequestRequestTypeDef",
    "DeleteStreamRequestRequestTypeDef",
    "DeleteThingGroupRequestRequestTypeDef",
    "DeleteThingRequestRequestTypeDef",
    "DeleteThingTypeRequestRequestTypeDef",
    "DeleteTopicRuleDestinationRequestRequestTypeDef",
    "DeleteTopicRuleRequestRequestTypeDef",
    "DeleteV2LoggingLevelRequestRequestTypeDef",
    "DeniedTypeDef",
    "DeprecateThingTypeRequestRequestTypeDef",
    "DescribeAccountAuditConfigurationResponseTypeDef",
    "DescribeAuditFindingRequestRequestTypeDef",
    "DescribeAuditFindingResponseTypeDef",
    "DescribeAuditMitigationActionsTaskRequestRequestTypeDef",
    "DescribeAuditMitigationActionsTaskResponseTypeDef",
    "DescribeAuditSuppressionRequestRequestTypeDef",
    "DescribeAuditSuppressionResponseTypeDef",
    "DescribeAuditTaskRequestRequestTypeDef",
    "DescribeAuditTaskResponseTypeDef",
    "DescribeAuthorizerRequestRequestTypeDef",
    "DescribeAuthorizerResponseTypeDef",
    "DescribeBillingGroupRequestRequestTypeDef",
    "DescribeBillingGroupResponseTypeDef",
    "DescribeCACertificateRequestRequestTypeDef",
    "DescribeCACertificateResponseTypeDef",
    "DescribeCertificateRequestRequestTypeDef",
    "DescribeCertificateResponseTypeDef",
    "DescribeCustomMetricRequestRequestTypeDef",
    "DescribeCustomMetricResponseTypeDef",
    "DescribeDefaultAuthorizerResponseTypeDef",
    "DescribeDetectMitigationActionsTaskRequestRequestTypeDef",
    "DescribeDetectMitigationActionsTaskResponseTypeDef",
    "DescribeDimensionRequestRequestTypeDef",
    "DescribeDimensionResponseTypeDef",
    "DescribeDomainConfigurationRequestRequestTypeDef",
    "DescribeDomainConfigurationResponseTypeDef",
    "DescribeEndpointRequestRequestTypeDef",
    "DescribeEndpointResponseTypeDef",
    "DescribeEventConfigurationsResponseTypeDef",
    "DescribeFleetMetricRequestRequestTypeDef",
    "DescribeFleetMetricResponseTypeDef",
    "DescribeIndexRequestRequestTypeDef",
    "DescribeIndexResponseTypeDef",
    "DescribeJobExecutionRequestRequestTypeDef",
    "DescribeJobExecutionResponseTypeDef",
    "DescribeJobRequestRequestTypeDef",
    "DescribeJobResponseTypeDef",
    "DescribeJobTemplateRequestRequestTypeDef",
    "DescribeJobTemplateResponseTypeDef",
    "DescribeManagedJobTemplateRequestRequestTypeDef",
    "DescribeManagedJobTemplateResponseTypeDef",
    "DescribeMitigationActionRequestRequestTypeDef",
    "DescribeMitigationActionResponseTypeDef",
    "DescribeProvisioningTemplateRequestRequestTypeDef",
    "DescribeProvisioningTemplateResponseTypeDef",
    "DescribeProvisioningTemplateVersionRequestRequestTypeDef",
    "DescribeProvisioningTemplateVersionResponseTypeDef",
    "DescribeRoleAliasRequestRequestTypeDef",
    "DescribeRoleAliasResponseTypeDef",
    "DescribeScheduledAuditRequestRequestTypeDef",
    "DescribeScheduledAuditResponseTypeDef",
    "DescribeSecurityProfileRequestRequestTypeDef",
    "DescribeSecurityProfileResponseTypeDef",
    "DescribeStreamRequestRequestTypeDef",
    "DescribeStreamResponseTypeDef",
    "DescribeThingGroupRequestRequestTypeDef",
    "DescribeThingGroupResponseTypeDef",
    "DescribeThingRegistrationTaskRequestRequestTypeDef",
    "DescribeThingRegistrationTaskResponseTypeDef",
    "DescribeThingRequestRequestTypeDef",
    "DescribeThingResponseTypeDef",
    "DescribeThingTypeRequestRequestTypeDef",
    "DescribeThingTypeResponseTypeDef",
    "DestinationTypeDef",
    "DetachPolicyRequestRequestTypeDef",
    "DetachPrincipalPolicyRequestRequestTypeDef",
    "DetachSecurityProfileRequestRequestTypeDef",
    "DetachThingPrincipalRequestRequestTypeDef",
    "DetectMitigationActionExecutionTypeDef",
    "DetectMitigationActionsTaskStatisticsTypeDef",
    "DetectMitigationActionsTaskSummaryTypeDef",
    "DetectMitigationActionsTaskTargetTypeDef",
    "DisableTopicRuleRequestRequestTypeDef",
    "DocumentParameterTypeDef",
    "DomainConfigurationSummaryTypeDef",
    "DynamoDBActionTypeDef",
    "DynamoDBv2ActionTypeDef",
    "EffectivePolicyTypeDef",
    "ElasticsearchActionTypeDef",
    "EnableIoTLoggingParamsTypeDef",
    "EnableTopicRuleRequestRequestTypeDef",
    "ErrorInfoTypeDef",
    "ExplicitDenyTypeDef",
    "ExponentialRolloutRateTypeDef",
    "FieldTypeDef",
    "FileLocationTypeDef",
    "FirehoseActionTypeDef",
    "FleetMetricNameAndArnTypeDef",
    "GetBehaviorModelTrainingSummariesRequestGetBehaviorModelTrainingSummariesPaginateTypeDef",
    "GetBehaviorModelTrainingSummariesRequestRequestTypeDef",
    "GetBehaviorModelTrainingSummariesResponseTypeDef",
    "GetBucketsAggregationRequestRequestTypeDef",
    "GetBucketsAggregationResponseTypeDef",
    "GetCardinalityRequestRequestTypeDef",
    "GetCardinalityResponseTypeDef",
    "GetEffectivePoliciesRequestRequestTypeDef",
    "GetEffectivePoliciesResponseTypeDef",
    "GetIndexingConfigurationResponseTypeDef",
    "GetJobDocumentRequestRequestTypeDef",
    "GetJobDocumentResponseTypeDef",
    "GetLoggingOptionsResponseTypeDef",
    "GetOTAUpdateRequestRequestTypeDef",
    "GetOTAUpdateResponseTypeDef",
    "GetPercentilesRequestRequestTypeDef",
    "GetPercentilesResponseTypeDef",
    "GetPolicyRequestRequestTypeDef",
    "GetPolicyResponseTypeDef",
    "GetPolicyVersionRequestRequestTypeDef",
    "GetPolicyVersionResponseTypeDef",
    "GetRegistrationCodeResponseTypeDef",
    "GetStatisticsRequestRequestTypeDef",
    "GetStatisticsResponseTypeDef",
    "GetTopicRuleDestinationRequestRequestTypeDef",
    "GetTopicRuleDestinationResponseTypeDef",
    "GetTopicRuleRequestRequestTypeDef",
    "GetTopicRuleResponseTypeDef",
    "GetV2LoggingOptionsResponseTypeDef",
    "GroupNameAndArnTypeDef",
    "HttpActionHeaderTypeDef",
    "HttpActionTypeDef",
    "HttpAuthorizationTypeDef",
    "HttpContextTypeDef",
    "HttpUrlDestinationConfigurationTypeDef",
    "HttpUrlDestinationPropertiesTypeDef",
    "HttpUrlDestinationSummaryTypeDef",
    "ImplicitDenyTypeDef",
    "IotAnalyticsActionTypeDef",
    "IotEventsActionTypeDef",
    "IotSiteWiseActionTypeDef",
    "JobExecutionStatusDetailsTypeDef",
    "JobExecutionSummaryForJobTypeDef",
    "JobExecutionSummaryForThingTypeDef",
    "JobExecutionSummaryTypeDef",
    "JobExecutionTypeDef",
    "JobExecutionsRetryConfigTypeDef",
    "JobExecutionsRolloutConfigTypeDef",
    "JobProcessDetailsTypeDef",
    "JobSummaryTypeDef",
    "JobTemplateSummaryTypeDef",
    "JobTypeDef",
    "KafkaActionTypeDef",
    "KeyPairTypeDef",
    "KinesisActionTypeDef",
    "LambdaActionTypeDef",
    "ListActiveViolationsRequestListActiveViolationsPaginateTypeDef",
    "ListActiveViolationsRequestRequestTypeDef",
    "ListActiveViolationsResponseTypeDef",
    "ListAttachedPoliciesRequestListAttachedPoliciesPaginateTypeDef",
    "ListAttachedPoliciesRequestRequestTypeDef",
    "ListAttachedPoliciesResponseTypeDef",
    "ListAuditFindingsRequestListAuditFindingsPaginateTypeDef",
    "ListAuditFindingsRequestRequestTypeDef",
    "ListAuditFindingsResponseTypeDef",
    "ListAuditMitigationActionsExecutionsRequestListAuditMitigationActionsExecutionsPaginateTypeDef",
    "ListAuditMitigationActionsExecutionsRequestRequestTypeDef",
    "ListAuditMitigationActionsExecutionsResponseTypeDef",
    "ListAuditMitigationActionsTasksRequestListAuditMitigationActionsTasksPaginateTypeDef",
    "ListAuditMitigationActionsTasksRequestRequestTypeDef",
    "ListAuditMitigationActionsTasksResponseTypeDef",
    "ListAuditSuppressionsRequestListAuditSuppressionsPaginateTypeDef",
    "ListAuditSuppressionsRequestRequestTypeDef",
    "ListAuditSuppressionsResponseTypeDef",
    "ListAuditTasksRequestListAuditTasksPaginateTypeDef",
    "ListAuditTasksRequestRequestTypeDef",
    "ListAuditTasksResponseTypeDef",
    "ListAuthorizersRequestListAuthorizersPaginateTypeDef",
    "ListAuthorizersRequestRequestTypeDef",
    "ListAuthorizersResponseTypeDef",
    "ListBillingGroupsRequestListBillingGroupsPaginateTypeDef",
    "ListBillingGroupsRequestRequestTypeDef",
    "ListBillingGroupsResponseTypeDef",
    "ListCACertificatesRequestListCACertificatesPaginateTypeDef",
    "ListCACertificatesRequestRequestTypeDef",
    "ListCACertificatesResponseTypeDef",
    "ListCertificatesByCARequestListCertificatesByCAPaginateTypeDef",
    "ListCertificatesByCARequestRequestTypeDef",
    "ListCertificatesByCAResponseTypeDef",
    "ListCertificatesRequestListCertificatesPaginateTypeDef",
    "ListCertificatesRequestRequestTypeDef",
    "ListCertificatesResponseTypeDef",
    "ListCustomMetricsRequestListCustomMetricsPaginateTypeDef",
    "ListCustomMetricsRequestRequestTypeDef",
    "ListCustomMetricsResponseTypeDef",
    "ListDetectMitigationActionsExecutionsRequestListDetectMitigationActionsExecutionsPaginateTypeDef",
    "ListDetectMitigationActionsExecutionsRequestRequestTypeDef",
    "ListDetectMitigationActionsExecutionsResponseTypeDef",
    "ListDetectMitigationActionsTasksRequestListDetectMitigationActionsTasksPaginateTypeDef",
    "ListDetectMitigationActionsTasksRequestRequestTypeDef",
    "ListDetectMitigationActionsTasksResponseTypeDef",
    "ListDimensionsRequestListDimensionsPaginateTypeDef",
    "ListDimensionsRequestRequestTypeDef",
    "ListDimensionsResponseTypeDef",
    "ListDomainConfigurationsRequestListDomainConfigurationsPaginateTypeDef",
    "ListDomainConfigurationsRequestRequestTypeDef",
    "ListDomainConfigurationsResponseTypeDef",
    "ListFleetMetricsRequestListFleetMetricsPaginateTypeDef",
    "ListFleetMetricsRequestRequestTypeDef",
    "ListFleetMetricsResponseTypeDef",
    "ListIndicesRequestListIndicesPaginateTypeDef",
    "ListIndicesRequestRequestTypeDef",
    "ListIndicesResponseTypeDef",
    "ListJobExecutionsForJobRequestListJobExecutionsForJobPaginateTypeDef",
    "ListJobExecutionsForJobRequestRequestTypeDef",
    "ListJobExecutionsForJobResponseTypeDef",
    "ListJobExecutionsForThingRequestListJobExecutionsForThingPaginateTypeDef",
    "ListJobExecutionsForThingRequestRequestTypeDef",
    "ListJobExecutionsForThingResponseTypeDef",
    "ListJobTemplatesRequestListJobTemplatesPaginateTypeDef",
    "ListJobTemplatesRequestRequestTypeDef",
    "ListJobTemplatesResponseTypeDef",
    "ListJobsRequestListJobsPaginateTypeDef",
    "ListJobsRequestRequestTypeDef",
    "ListJobsResponseTypeDef",
    "ListManagedJobTemplatesRequestRequestTypeDef",
    "ListManagedJobTemplatesResponseTypeDef",
    "ListMitigationActionsRequestListMitigationActionsPaginateTypeDef",
    "ListMitigationActionsRequestRequestTypeDef",
    "ListMitigationActionsResponseTypeDef",
    "ListOTAUpdatesRequestListOTAUpdatesPaginateTypeDef",
    "ListOTAUpdatesRequestRequestTypeDef",
    "ListOTAUpdatesResponseTypeDef",
    "ListOutgoingCertificatesRequestListOutgoingCertificatesPaginateTypeDef",
    "ListOutgoingCertificatesRequestRequestTypeDef",
    "ListOutgoingCertificatesResponseTypeDef",
    "ListPoliciesRequestListPoliciesPaginateTypeDef",
    "ListPoliciesRequestRequestTypeDef",
    "ListPoliciesResponseTypeDef",
    "ListPolicyPrincipalsRequestListPolicyPrincipalsPaginateTypeDef",
    "ListPolicyPrincipalsRequestRequestTypeDef",
    "ListPolicyPrincipalsResponseTypeDef",
    "ListPolicyVersionsRequestRequestTypeDef",
    "ListPolicyVersionsResponseTypeDef",
    "ListPrincipalPoliciesRequestListPrincipalPoliciesPaginateTypeDef",
    "ListPrincipalPoliciesRequestRequestTypeDef",
    "ListPrincipalPoliciesResponseTypeDef",
    "ListPrincipalThingsRequestListPrincipalThingsPaginateTypeDef",
    "ListPrincipalThingsRequestRequestTypeDef",
    "ListPrincipalThingsResponseTypeDef",
    "ListProvisioningTemplateVersionsRequestListProvisioningTemplateVersionsPaginateTypeDef",
    "ListProvisioningTemplateVersionsRequestRequestTypeDef",
    "ListProvisioningTemplateVersionsResponseTypeDef",
    "ListProvisioningTemplatesRequestListProvisioningTemplatesPaginateTypeDef",
    "ListProvisioningTemplatesRequestRequestTypeDef",
    "ListProvisioningTemplatesResponseTypeDef",
    "ListRoleAliasesRequestListRoleAliasesPaginateTypeDef",
    "ListRoleAliasesRequestRequestTypeDef",
    "ListRoleAliasesResponseTypeDef",
    "ListScheduledAuditsRequestListScheduledAuditsPaginateTypeDef",
    "ListScheduledAuditsRequestRequestTypeDef",
    "ListScheduledAuditsResponseTypeDef",
    "ListSecurityProfilesForTargetRequestListSecurityProfilesForTargetPaginateTypeDef",
    "ListSecurityProfilesForTargetRequestRequestTypeDef",
    "ListSecurityProfilesForTargetResponseTypeDef",
    "ListSecurityProfilesRequestListSecurityProfilesPaginateTypeDef",
    "ListSecurityProfilesRequestRequestTypeDef",
    "ListSecurityProfilesResponseTypeDef",
    "ListStreamsRequestListStreamsPaginateTypeDef",
    "ListStreamsRequestRequestTypeDef",
    "ListStreamsResponseTypeDef",
    "ListTagsForResourceRequestListTagsForResourcePaginateTypeDef",
    "ListTagsForResourceRequestRequestTypeDef",
    "ListTagsForResourceResponseTypeDef",
    "ListTargetsForPolicyRequestListTargetsForPolicyPaginateTypeDef",
    "ListTargetsForPolicyRequestRequestTypeDef",
    "ListTargetsForPolicyResponseTypeDef",
    "ListTargetsForSecurityProfileRequestListTargetsForSecurityProfilePaginateTypeDef",
    "ListTargetsForSecurityProfileRequestRequestTypeDef",
    "ListTargetsForSecurityProfileResponseTypeDef",
    "ListThingGroupsForThingRequestListThingGroupsForThingPaginateTypeDef",
    "ListThingGroupsForThingRequestRequestTypeDef",
    "ListThingGroupsForThingResponseTypeDef",
    "ListThingGroupsRequestListThingGroupsPaginateTypeDef",
    "ListThingGroupsRequestRequestTypeDef",
    "ListThingGroupsResponseTypeDef",
    "ListThingPrincipalsRequestListThingPrincipalsPaginateTypeDef",
    "ListThingPrincipalsRequestRequestTypeDef",
    "ListThingPrincipalsResponseTypeDef",
    "ListThingRegistrationTaskReportsRequestListThingRegistrationTaskReportsPaginateTypeDef",
    "ListThingRegistrationTaskReportsRequestRequestTypeDef",
    "ListThingRegistrationTaskReportsResponseTypeDef",
    "ListThingRegistrationTasksRequestListThingRegistrationTasksPaginateTypeDef",
    "ListThingRegistrationTasksRequestRequestTypeDef",
    "ListThingRegistrationTasksResponseTypeDef",
    "ListThingTypesRequestListThingTypesPaginateTypeDef",
    "ListThingTypesRequestRequestTypeDef",
    "ListThingTypesResponseTypeDef",
    "ListThingsInBillingGroupRequestListThingsInBillingGroupPaginateTypeDef",
    "ListThingsInBillingGroupRequestRequestTypeDef",
    "ListThingsInBillingGroupResponseTypeDef",
    "ListThingsInThingGroupRequestListThingsInThingGroupPaginateTypeDef",
    "ListThingsInThingGroupRequestRequestTypeDef",
    "ListThingsInThingGroupResponseTypeDef",
    "ListThingsRequestListThingsPaginateTypeDef",
    "ListThingsRequestRequestTypeDef",
    "ListThingsResponseTypeDef",
    "ListTopicRuleDestinationsRequestListTopicRuleDestinationsPaginateTypeDef",
    "ListTopicRuleDestinationsRequestRequestTypeDef",
    "ListTopicRuleDestinationsResponseTypeDef",
    "ListTopicRulesRequestListTopicRulesPaginateTypeDef",
    "ListTopicRulesRequestRequestTypeDef",
    "ListTopicRulesResponseTypeDef",
    "ListV2LoggingLevelsRequestListV2LoggingLevelsPaginateTypeDef",
    "ListV2LoggingLevelsRequestRequestTypeDef",
    "ListV2LoggingLevelsResponseTypeDef",
    "ListViolationEventsRequestListViolationEventsPaginateTypeDef",
    "ListViolationEventsRequestRequestTypeDef",
    "ListViolationEventsResponseTypeDef",
    "LogTargetConfigurationTypeDef",
    "LogTargetTypeDef",
    "LoggingOptionsPayloadTypeDef",
    "MachineLearningDetectionConfigTypeDef",
    "ManagedJobTemplateSummaryTypeDef",
    "MetricDimensionTypeDef",
    "MetricToRetainTypeDef",
    "MetricValueTypeDef",
    "MitigationActionIdentifierTypeDef",
    "MitigationActionParamsTypeDef",
    "MitigationActionTypeDef",
    "MqttContextTypeDef",
    "NonCompliantResourceTypeDef",
    "OTAUpdateFileTypeDef",
    "OTAUpdateInfoTypeDef",
    "OTAUpdateSummaryTypeDef",
    "OpenSearchActionTypeDef",
    "OutgoingCertificateTypeDef",
    "PaginatorConfigTypeDef",
    "PercentPairTypeDef",
    "PolicyTypeDef",
    "PolicyVersionIdentifierTypeDef",
    "PolicyVersionTypeDef",
    "PresignedUrlConfigTypeDef",
    "ProvisioningHookTypeDef",
    "ProvisioningTemplateSummaryTypeDef",
    "ProvisioningTemplateVersionSummaryTypeDef",
    "PublishFindingToSnsParamsTypeDef",
    "PutAssetPropertyValueEntryTypeDef",
    "PutItemInputTypeDef",
    "PutVerificationStateOnViolationRequestRequestTypeDef",
    "RateIncreaseCriteriaTypeDef",
    "RegisterCACertificateRequestRequestTypeDef",
    "RegisterCACertificateResponseTypeDef",
    "RegisterCertificateRequestRequestTypeDef",
    "RegisterCertificateResponseTypeDef",
    "RegisterCertificateWithoutCARequestRequestTypeDef",
    "RegisterCertificateWithoutCAResponseTypeDef",
    "RegisterThingRequestRequestTypeDef",
    "RegisterThingResponseTypeDef",
    "RegistrationConfigTypeDef",
    "RejectCertificateTransferRequestRequestTypeDef",
    "RelatedResourceTypeDef",
    "RemoveThingFromBillingGroupRequestRequestTypeDef",
    "RemoveThingFromThingGroupRequestRequestTypeDef",
    "ReplaceDefaultPolicyVersionParamsTypeDef",
    "ReplaceTopicRuleRequestRequestTypeDef",
    "RepublishActionTypeDef",
    "ResourceIdentifierTypeDef",
    "ResponseMetadataTypeDef",
    "RetryCriteriaTypeDef",
    "RoleAliasDescriptionTypeDef",
    "S3ActionTypeDef",
    "S3DestinationTypeDef",
    "S3LocationTypeDef",
    "SalesforceActionTypeDef",
    "ScheduledAuditMetadataTypeDef",
    "SearchIndexRequestRequestTypeDef",
    "SearchIndexResponseTypeDef",
    "SecurityProfileIdentifierTypeDef",
    "SecurityProfileTargetMappingTypeDef",
    "SecurityProfileTargetTypeDef",
    "ServerCertificateSummaryTypeDef",
    "SetDefaultAuthorizerRequestRequestTypeDef",
    "SetDefaultAuthorizerResponseTypeDef",
    "SetDefaultPolicyVersionRequestRequestTypeDef",
    "SetLoggingOptionsRequestRequestTypeDef",
    "SetV2LoggingLevelRequestRequestTypeDef",
    "SetV2LoggingOptionsRequestRequestTypeDef",
    "SigV4AuthorizationTypeDef",
    "SigningProfileParameterTypeDef",
    "SnsActionTypeDef",
    "SqsActionTypeDef",
    "StartAuditMitigationActionsTaskRequestRequestTypeDef",
    "StartAuditMitigationActionsTaskResponseTypeDef",
    "StartDetectMitigationActionsTaskRequestRequestTypeDef",
    "StartDetectMitigationActionsTaskResponseTypeDef",
    "StartOnDemandAuditTaskRequestRequestTypeDef",
    "StartOnDemandAuditTaskResponseTypeDef",
    "StartSigningJobParameterTypeDef",
    "StartThingRegistrationTaskRequestRequestTypeDef",
    "StartThingRegistrationTaskResponseTypeDef",
    "StatisticalThresholdTypeDef",
    "StatisticsTypeDef",
    "StepFunctionsActionTypeDef",
    "StopThingRegistrationTaskRequestRequestTypeDef",
    "StreamFileTypeDef",
    "StreamInfoTypeDef",
    "StreamSummaryTypeDef",
    "StreamTypeDef",
    "TagResourceRequestRequestTypeDef",
    "TagTypeDef",
    "TaskStatisticsForAuditCheckTypeDef",
    "TaskStatisticsTypeDef",
    "TermsAggregationTypeDef",
    "TestAuthorizationRequestRequestTypeDef",
    "TestAuthorizationResponseTypeDef",
    "TestInvokeAuthorizerRequestRequestTypeDef",
    "TestInvokeAuthorizerResponseTypeDef",
    "ThingAttributeTypeDef",
    "ThingConnectivityTypeDef",
    "ThingDocumentTypeDef",
    "ThingGroupDocumentTypeDef",
    "ThingGroupIndexingConfigurationTypeDef",
    "ThingGroupMetadataTypeDef",
    "ThingGroupPropertiesTypeDef",
    "ThingIndexingConfigurationTypeDef",
    "ThingTypeDefinitionTypeDef",
    "ThingTypeMetadataTypeDef",
    "ThingTypePropertiesTypeDef",
    "TimeoutConfigTypeDef",
    "TimestreamActionTypeDef",
    "TimestreamDimensionTypeDef",
    "TimestreamTimestampTypeDef",
    "TlsContextTypeDef",
    "TopicRuleDestinationConfigurationTypeDef",
    "TopicRuleDestinationSummaryTypeDef",
    "TopicRuleDestinationTypeDef",
    "TopicRuleListItemTypeDef",
    "TopicRulePayloadTypeDef",
    "TopicRuleTypeDef",
    "TransferCertificateRequestRequestTypeDef",
    "TransferCertificateResponseTypeDef",
    "TransferDataTypeDef",
    "UntagResourceRequestRequestTypeDef",
    "UpdateAccountAuditConfigurationRequestRequestTypeDef",
    "UpdateAuditSuppressionRequestRequestTypeDef",
    "UpdateAuthorizerRequestRequestTypeDef",
    "UpdateAuthorizerResponseTypeDef",
    "UpdateBillingGroupRequestRequestTypeDef",
    "UpdateBillingGroupResponseTypeDef",
    "UpdateCACertificateParamsTypeDef",
    "UpdateCACertificateRequestRequestTypeDef",
    "UpdateCertificateRequestRequestTypeDef",
    "UpdateCustomMetricRequestRequestTypeDef",
    "UpdateCustomMetricResponseTypeDef",
    "UpdateDeviceCertificateParamsTypeDef",
    "UpdateDimensionRequestRequestTypeDef",
    "UpdateDimensionResponseTypeDef",
    "UpdateDomainConfigurationRequestRequestTypeDef",
    "UpdateDomainConfigurationResponseTypeDef",
    "UpdateDynamicThingGroupRequestRequestTypeDef",
    "UpdateDynamicThingGroupResponseTypeDef",
    "UpdateEventConfigurationsRequestRequestTypeDef",
    "UpdateFleetMetricRequestRequestTypeDef",
    "UpdateIndexingConfigurationRequestRequestTypeDef",
    "UpdateJobRequestRequestTypeDef",
    "UpdateMitigationActionRequestRequestTypeDef",
    "UpdateMitigationActionResponseTypeDef",
    "UpdateProvisioningTemplateRequestRequestTypeDef",
    "UpdateRoleAliasRequestRequestTypeDef",
    "UpdateRoleAliasResponseTypeDef",
    "UpdateScheduledAuditRequestRequestTypeDef",
    "UpdateScheduledAuditResponseTypeDef",
    "UpdateSecurityProfileRequestRequestTypeDef",
    "UpdateSecurityProfileResponseTypeDef",
    "UpdateStreamRequestRequestTypeDef",
    "UpdateStreamResponseTypeDef",
    "UpdateThingGroupRequestRequestTypeDef",
    "UpdateThingGroupResponseTypeDef",
    "UpdateThingGroupsForThingRequestRequestTypeDef",
    "UpdateThingRequestRequestTypeDef",
    "UpdateTopicRuleDestinationRequestRequestTypeDef",
    "ValidateSecurityProfileBehaviorsRequestRequestTypeDef",
    "ValidateSecurityProfileBehaviorsResponseTypeDef",
    "ValidationErrorTypeDef",
    "ViolationEventAdditionalInfoTypeDef",
    "ViolationEventOccurrenceRangeTypeDef",
    "ViolationEventTypeDef",
    "VpcDestinationConfigurationTypeDef",
    "VpcDestinationPropertiesTypeDef",
    "VpcDestinationSummaryTypeDef",
)

AbortConfigTypeDef = TypedDict(
    "AbortConfigTypeDef",
    {
        "criteriaList": Sequence["AbortCriteriaTypeDef"],
    },
)

AbortCriteriaTypeDef = TypedDict(
    "AbortCriteriaTypeDef",
    {
        "failureType": JobExecutionFailureTypeType,
        "action": Literal["CANCEL"],
        "thresholdPercentage": float,
        "minNumberOfExecutedThings": int,
    },
)

AcceptCertificateTransferRequestRequestTypeDef = TypedDict(
    "AcceptCertificateTransferRequestRequestTypeDef",
    {
        "certificateId": str,
        "setAsActive": NotRequired[bool],
    },
)

ActionTypeDef = TypedDict(
    "ActionTypeDef",
    {
        "dynamoDB": NotRequired["DynamoDBActionTypeDef"],
        "dynamoDBv2": NotRequired["DynamoDBv2ActionTypeDef"],
        "lambda": NotRequired["LambdaActionTypeDef"],
        "sns": NotRequired["SnsActionTypeDef"],
        "sqs": NotRequired["SqsActionTypeDef"],
        "kinesis": NotRequired["KinesisActionTypeDef"],
        "republish": NotRequired["RepublishActionTypeDef"],
        "s3": NotRequired["S3ActionTypeDef"],
        "firehose": NotRequired["FirehoseActionTypeDef"],
        "cloudwatchMetric": NotRequired["CloudwatchMetricActionTypeDef"],
        "cloudwatchAlarm": NotRequired["CloudwatchAlarmActionTypeDef"],
        "cloudwatchLogs": NotRequired["CloudwatchLogsActionTypeDef"],
        "elasticsearch": NotRequired["ElasticsearchActionTypeDef"],
        "salesforce": NotRequired["SalesforceActionTypeDef"],
        "iotAnalytics": NotRequired["IotAnalyticsActionTypeDef"],
        "iotEvents": NotRequired["IotEventsActionTypeDef"],
        "iotSiteWise": NotRequired["IotSiteWiseActionTypeDef"],
        "stepFunctions": NotRequired["StepFunctionsActionTypeDef"],
        "timestream": NotRequired["TimestreamActionTypeDef"],
        "http": NotRequired["HttpActionTypeDef"],
        "kafka": NotRequired["KafkaActionTypeDef"],
        "openSearch": NotRequired["OpenSearchActionTypeDef"],
    },
)

ActiveViolationTypeDef = TypedDict(
    "ActiveViolationTypeDef",
    {
        "violationId": NotRequired[str],
        "thingName": NotRequired[str],
        "securityProfileName": NotRequired[str],
        "behavior": NotRequired["BehaviorTypeDef"],
        "lastViolationValue": NotRequired["MetricValueTypeDef"],
        "violationEventAdditionalInfo": NotRequired["ViolationEventAdditionalInfoTypeDef"],
        "verificationState": NotRequired[VerificationStateType],
        "verificationStateDescription": NotRequired[str],
        "lastViolationTime": NotRequired[datetime],
        "violationStartTime": NotRequired[datetime],
    },
)

AddThingToBillingGroupRequestRequestTypeDef = TypedDict(
    "AddThingToBillingGroupRequestRequestTypeDef",
    {
        "billingGroupName": NotRequired[str],
        "billingGroupArn": NotRequired[str],
        "thingName": NotRequired[str],
        "thingArn": NotRequired[str],
    },
)

AddThingToThingGroupRequestRequestTypeDef = TypedDict(
    "AddThingToThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": NotRequired[str],
        "thingGroupArn": NotRequired[str],
        "thingName": NotRequired[str],
        "thingArn": NotRequired[str],
        "overrideDynamicGroups": NotRequired[bool],
    },
)

AddThingsToThingGroupParamsTypeDef = TypedDict(
    "AddThingsToThingGroupParamsTypeDef",
    {
        "thingGroupNames": Sequence[str],
        "overrideDynamicGroups": NotRequired[bool],
    },
)

AggregationTypeTypeDef = TypedDict(
    "AggregationTypeTypeDef",
    {
        "name": AggregationTypeNameType,
        "values": NotRequired[Sequence[str]],
    },
)

AlertTargetTypeDef = TypedDict(
    "AlertTargetTypeDef",
    {
        "alertTargetArn": str,
        "roleArn": str,
    },
)

AllowedTypeDef = TypedDict(
    "AllowedTypeDef",
    {
        "policies": NotRequired[List["PolicyTypeDef"]],
    },
)

AssetPropertyTimestampTypeDef = TypedDict(
    "AssetPropertyTimestampTypeDef",
    {
        "timeInSeconds": str,
        "offsetInNanos": NotRequired[str],
    },
)

AssetPropertyValueTypeDef = TypedDict(
    "AssetPropertyValueTypeDef",
    {
        "value": "AssetPropertyVariantTypeDef",
        "timestamp": "AssetPropertyTimestampTypeDef",
        "quality": NotRequired[str],
    },
)

AssetPropertyVariantTypeDef = TypedDict(
    "AssetPropertyVariantTypeDef",
    {
        "stringValue": NotRequired[str],
        "integerValue": NotRequired[str],
        "doubleValue": NotRequired[str],
        "booleanValue": NotRequired[str],
    },
)

AssociateTargetsWithJobRequestRequestTypeDef = TypedDict(
    "AssociateTargetsWithJobRequestRequestTypeDef",
    {
        "targets": Sequence[str],
        "jobId": str,
        "comment": NotRequired[str],
        "namespaceId": NotRequired[str],
    },
)

AssociateTargetsWithJobResponseTypeDef = TypedDict(
    "AssociateTargetsWithJobResponseTypeDef",
    {
        "jobArn": str,
        "jobId": str,
        "description": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

AttachPolicyRequestRequestTypeDef = TypedDict(
    "AttachPolicyRequestRequestTypeDef",
    {
        "policyName": str,
        "target": str,
    },
)

AttachPrincipalPolicyRequestRequestTypeDef = TypedDict(
    "AttachPrincipalPolicyRequestRequestTypeDef",
    {
        "policyName": str,
        "principal": str,
    },
)

AttachSecurityProfileRequestRequestTypeDef = TypedDict(
    "AttachSecurityProfileRequestRequestTypeDef",
    {
        "securityProfileName": str,
        "securityProfileTargetArn": str,
    },
)

AttachThingPrincipalRequestRequestTypeDef = TypedDict(
    "AttachThingPrincipalRequestRequestTypeDef",
    {
        "thingName": str,
        "principal": str,
    },
)

AttributePayloadTypeDef = TypedDict(
    "AttributePayloadTypeDef",
    {
        "attributes": NotRequired[Mapping[str, str]],
        "merge": NotRequired[bool],
    },
)

AuditCheckConfigurationTypeDef = TypedDict(
    "AuditCheckConfigurationTypeDef",
    {
        "enabled": NotRequired[bool],
    },
)

AuditCheckDetailsTypeDef = TypedDict(
    "AuditCheckDetailsTypeDef",
    {
        "checkRunStatus": NotRequired[AuditCheckRunStatusType],
        "checkCompliant": NotRequired[bool],
        "totalResourcesCount": NotRequired[int],
        "nonCompliantResourcesCount": NotRequired[int],
        "suppressedNonCompliantResourcesCount": NotRequired[int],
        "errorCode": NotRequired[str],
        "message": NotRequired[str],
    },
)

AuditFindingTypeDef = TypedDict(
    "AuditFindingTypeDef",
    {
        "findingId": NotRequired[str],
        "taskId": NotRequired[str],
        "checkName": NotRequired[str],
        "taskStartTime": NotRequired[datetime],
        "findingTime": NotRequired[datetime],
        "severity": NotRequired[AuditFindingSeverityType],
        "nonCompliantResource": NotRequired["NonCompliantResourceTypeDef"],
        "relatedResources": NotRequired[List["RelatedResourceTypeDef"]],
        "reasonForNonCompliance": NotRequired[str],
        "reasonForNonComplianceCode": NotRequired[str],
        "isSuppressed": NotRequired[bool],
    },
)

AuditMitigationActionExecutionMetadataTypeDef = TypedDict(
    "AuditMitigationActionExecutionMetadataTypeDef",
    {
        "taskId": NotRequired[str],
        "findingId": NotRequired[str],
        "actionName": NotRequired[str],
        "actionId": NotRequired[str],
        "status": NotRequired[AuditMitigationActionsExecutionStatusType],
        "startTime": NotRequired[datetime],
        "endTime": NotRequired[datetime],
        "errorCode": NotRequired[str],
        "message": NotRequired[str],
    },
)

AuditMitigationActionsTaskMetadataTypeDef = TypedDict(
    "AuditMitigationActionsTaskMetadataTypeDef",
    {
        "taskId": NotRequired[str],
        "startTime": NotRequired[datetime],
        "taskStatus": NotRequired[AuditMitigationActionsTaskStatusType],
    },
)

AuditMitigationActionsTaskTargetTypeDef = TypedDict(
    "AuditMitigationActionsTaskTargetTypeDef",
    {
        "auditTaskId": NotRequired[str],
        "findingIds": NotRequired[List[str]],
        "auditCheckToReasonCodeFilter": NotRequired[Dict[str, List[str]]],
    },
)

AuditNotificationTargetTypeDef = TypedDict(
    "AuditNotificationTargetTypeDef",
    {
        "targetArn": NotRequired[str],
        "roleArn": NotRequired[str],
        "enabled": NotRequired[bool],
    },
)

AuditSuppressionTypeDef = TypedDict(
    "AuditSuppressionTypeDef",
    {
        "checkName": str,
        "resourceIdentifier": "ResourceIdentifierTypeDef",
        "expirationDate": NotRequired[datetime],
        "suppressIndefinitely": NotRequired[bool],
        "description": NotRequired[str],
    },
)

AuditTaskMetadataTypeDef = TypedDict(
    "AuditTaskMetadataTypeDef",
    {
        "taskId": NotRequired[str],
        "taskStatus": NotRequired[AuditTaskStatusType],
        "taskType": NotRequired[AuditTaskTypeType],
    },
)

AuthInfoTypeDef = TypedDict(
    "AuthInfoTypeDef",
    {
        "resources": Sequence[str],
        "actionType": NotRequired[ActionTypeType],
    },
)

AuthResultTypeDef = TypedDict(
    "AuthResultTypeDef",
    {
        "authInfo": NotRequired["AuthInfoTypeDef"],
        "allowed": NotRequired["AllowedTypeDef"],
        "denied": NotRequired["DeniedTypeDef"],
        "authDecision": NotRequired[AuthDecisionType],
        "missingContextValues": NotRequired[List[str]],
    },
)

AuthorizerConfigTypeDef = TypedDict(
    "AuthorizerConfigTypeDef",
    {
        "defaultAuthorizerName": NotRequired[str],
        "allowAuthorizerOverride": NotRequired[bool],
    },
)

AuthorizerDescriptionTypeDef = TypedDict(
    "AuthorizerDescriptionTypeDef",
    {
        "authorizerName": NotRequired[str],
        "authorizerArn": NotRequired[str],
        "authorizerFunctionArn": NotRequired[str],
        "tokenKeyName": NotRequired[str],
        "tokenSigningPublicKeys": NotRequired[Dict[str, str]],
        "status": NotRequired[AuthorizerStatusType],
        "creationDate": NotRequired[datetime],
        "lastModifiedDate": NotRequired[datetime],
        "signingDisabled": NotRequired[bool],
        "enableCachingForHttp": NotRequired[bool],
    },
)

AuthorizerSummaryTypeDef = TypedDict(
    "AuthorizerSummaryTypeDef",
    {
        "authorizerName": NotRequired[str],
        "authorizerArn": NotRequired[str],
    },
)

AwsJobAbortConfigTypeDef = TypedDict(
    "AwsJobAbortConfigTypeDef",
    {
        "abortCriteriaList": Sequence["AwsJobAbortCriteriaTypeDef"],
    },
)

AwsJobAbortCriteriaTypeDef = TypedDict(
    "AwsJobAbortCriteriaTypeDef",
    {
        "failureType": AwsJobAbortCriteriaFailureTypeType,
        "action": Literal["CANCEL"],
        "thresholdPercentage": float,
        "minNumberOfExecutedThings": int,
    },
)

AwsJobExecutionsRolloutConfigTypeDef = TypedDict(
    "AwsJobExecutionsRolloutConfigTypeDef",
    {
        "maximumPerMinute": NotRequired[int],
        "exponentialRate": NotRequired["AwsJobExponentialRolloutRateTypeDef"],
    },
)

AwsJobExponentialRolloutRateTypeDef = TypedDict(
    "AwsJobExponentialRolloutRateTypeDef",
    {
        "baseRatePerMinute": int,
        "incrementFactor": float,
        "rateIncreaseCriteria": "AwsJobRateIncreaseCriteriaTypeDef",
    },
)

AwsJobPresignedUrlConfigTypeDef = TypedDict(
    "AwsJobPresignedUrlConfigTypeDef",
    {
        "expiresInSec": NotRequired[int],
    },
)

AwsJobRateIncreaseCriteriaTypeDef = TypedDict(
    "AwsJobRateIncreaseCriteriaTypeDef",
    {
        "numberOfNotifiedThings": NotRequired[int],
        "numberOfSucceededThings": NotRequired[int],
    },
)

AwsJobTimeoutConfigTypeDef = TypedDict(
    "AwsJobTimeoutConfigTypeDef",
    {
        "inProgressTimeoutInMinutes": NotRequired[int],
    },
)

BehaviorCriteriaTypeDef = TypedDict(
    "BehaviorCriteriaTypeDef",
    {
        "comparisonOperator": NotRequired[ComparisonOperatorType],
        "value": NotRequired["MetricValueTypeDef"],
        "durationSeconds": NotRequired[int],
        "consecutiveDatapointsToAlarm": NotRequired[int],
        "consecutiveDatapointsToClear": NotRequired[int],
        "statisticalThreshold": NotRequired["StatisticalThresholdTypeDef"],
        "mlDetectionConfig": NotRequired["MachineLearningDetectionConfigTypeDef"],
    },
)

BehaviorModelTrainingSummaryTypeDef = TypedDict(
    "BehaviorModelTrainingSummaryTypeDef",
    {
        "securityProfileName": NotRequired[str],
        "behaviorName": NotRequired[str],
        "trainingDataCollectionStartDate": NotRequired[datetime],
        "modelStatus": NotRequired[ModelStatusType],
        "datapointsCollectionPercentage": NotRequired[float],
        "lastModelRefreshDate": NotRequired[datetime],
    },
)

BehaviorTypeDef = TypedDict(
    "BehaviorTypeDef",
    {
        "name": str,
        "metric": NotRequired[str],
        "metricDimension": NotRequired["MetricDimensionTypeDef"],
        "criteria": NotRequired["BehaviorCriteriaTypeDef"],
        "suppressAlerts": NotRequired[bool],
    },
)

BillingGroupMetadataTypeDef = TypedDict(
    "BillingGroupMetadataTypeDef",
    {
        "creationDate": NotRequired[datetime],
    },
)

BillingGroupPropertiesTypeDef = TypedDict(
    "BillingGroupPropertiesTypeDef",
    {
        "billingGroupDescription": NotRequired[str],
    },
)

BucketTypeDef = TypedDict(
    "BucketTypeDef",
    {
        "keyValue": NotRequired[str],
        "count": NotRequired[int],
    },
)

BucketsAggregationTypeTypeDef = TypedDict(
    "BucketsAggregationTypeTypeDef",
    {
        "termsAggregation": NotRequired["TermsAggregationTypeDef"],
    },
)

CACertificateDescriptionTypeDef = TypedDict(
    "CACertificateDescriptionTypeDef",
    {
        "certificateArn": NotRequired[str],
        "certificateId": NotRequired[str],
        "status": NotRequired[CACertificateStatusType],
        "certificatePem": NotRequired[str],
        "ownedBy": NotRequired[str],
        "creationDate": NotRequired[datetime],
        "autoRegistrationStatus": NotRequired[AutoRegistrationStatusType],
        "lastModifiedDate": NotRequired[datetime],
        "customerVersion": NotRequired[int],
        "generationId": NotRequired[str],
        "validity": NotRequired["CertificateValidityTypeDef"],
    },
)

CACertificateTypeDef = TypedDict(
    "CACertificateTypeDef",
    {
        "certificateArn": NotRequired[str],
        "certificateId": NotRequired[str],
        "status": NotRequired[CACertificateStatusType],
        "creationDate": NotRequired[datetime],
    },
)

CancelAuditMitigationActionsTaskRequestRequestTypeDef = TypedDict(
    "CancelAuditMitigationActionsTaskRequestRequestTypeDef",
    {
        "taskId": str,
    },
)

CancelAuditTaskRequestRequestTypeDef = TypedDict(
    "CancelAuditTaskRequestRequestTypeDef",
    {
        "taskId": str,
    },
)

CancelCertificateTransferRequestRequestTypeDef = TypedDict(
    "CancelCertificateTransferRequestRequestTypeDef",
    {
        "certificateId": str,
    },
)

CancelDetectMitigationActionsTaskRequestRequestTypeDef = TypedDict(
    "CancelDetectMitigationActionsTaskRequestRequestTypeDef",
    {
        "taskId": str,
    },
)

CancelJobExecutionRequestRequestTypeDef = TypedDict(
    "CancelJobExecutionRequestRequestTypeDef",
    {
        "jobId": str,
        "thingName": str,
        "force": NotRequired[bool],
        "expectedVersion": NotRequired[int],
        "statusDetails": NotRequired[Mapping[str, str]],
    },
)

CancelJobRequestRequestTypeDef = TypedDict(
    "CancelJobRequestRequestTypeDef",
    {
        "jobId": str,
        "reasonCode": NotRequired[str],
        "comment": NotRequired[str],
        "force": NotRequired[bool],
    },
)

CancelJobResponseTypeDef = TypedDict(
    "CancelJobResponseTypeDef",
    {
        "jobArn": str,
        "jobId": str,
        "description": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CertificateDescriptionTypeDef = TypedDict(
    "CertificateDescriptionTypeDef",
    {
        "certificateArn": NotRequired[str],
        "certificateId": NotRequired[str],
        "caCertificateId": NotRequired[str],
        "status": NotRequired[CertificateStatusType],
        "certificatePem": NotRequired[str],
        "ownedBy": NotRequired[str],
        "previousOwnedBy": NotRequired[str],
        "creationDate": NotRequired[datetime],
        "lastModifiedDate": NotRequired[datetime],
        "customerVersion": NotRequired[int],
        "transferData": NotRequired["TransferDataTypeDef"],
        "generationId": NotRequired[str],
        "validity": NotRequired["CertificateValidityTypeDef"],
        "certificateMode": NotRequired[CertificateModeType],
    },
)

CertificateTypeDef = TypedDict(
    "CertificateTypeDef",
    {
        "certificateArn": NotRequired[str],
        "certificateId": NotRequired[str],
        "status": NotRequired[CertificateStatusType],
        "certificateMode": NotRequired[CertificateModeType],
        "creationDate": NotRequired[datetime],
    },
)

CertificateValidityTypeDef = TypedDict(
    "CertificateValidityTypeDef",
    {
        "notBefore": NotRequired[datetime],
        "notAfter": NotRequired[datetime],
    },
)

CloudwatchAlarmActionTypeDef = TypedDict(
    "CloudwatchAlarmActionTypeDef",
    {
        "roleArn": str,
        "alarmName": str,
        "stateReason": str,
        "stateValue": str,
    },
)

CloudwatchLogsActionTypeDef = TypedDict(
    "CloudwatchLogsActionTypeDef",
    {
        "roleArn": str,
        "logGroupName": str,
    },
)

CloudwatchMetricActionTypeDef = TypedDict(
    "CloudwatchMetricActionTypeDef",
    {
        "roleArn": str,
        "metricNamespace": str,
        "metricName": str,
        "metricValue": str,
        "metricUnit": str,
        "metricTimestamp": NotRequired[str],
    },
)

CodeSigningCertificateChainTypeDef = TypedDict(
    "CodeSigningCertificateChainTypeDef",
    {
        "certificateName": NotRequired[str],
        "inlineDocument": NotRequired[str],
    },
)

CodeSigningSignatureTypeDef = TypedDict(
    "CodeSigningSignatureTypeDef",
    {
        "inlineDocument": NotRequired[Union[bytes, IO[bytes], StreamingBody]],
    },
)

CodeSigningTypeDef = TypedDict(
    "CodeSigningTypeDef",
    {
        "awsSignerJobId": NotRequired[str],
        "startSigningJobParameter": NotRequired["StartSigningJobParameterTypeDef"],
        "customCodeSigning": NotRequired["CustomCodeSigningTypeDef"],
    },
)

ConfigurationTypeDef = TypedDict(
    "ConfigurationTypeDef",
    {
        "Enabled": NotRequired[bool],
    },
)

ConfirmTopicRuleDestinationRequestRequestTypeDef = TypedDict(
    "ConfirmTopicRuleDestinationRequestRequestTypeDef",
    {
        "confirmationToken": str,
    },
)

CreateAuditSuppressionRequestRequestTypeDef = TypedDict(
    "CreateAuditSuppressionRequestRequestTypeDef",
    {
        "checkName": str,
        "resourceIdentifier": "ResourceIdentifierTypeDef",
        "clientRequestToken": str,
        "expirationDate": NotRequired[Union[datetime, str]],
        "suppressIndefinitely": NotRequired[bool],
        "description": NotRequired[str],
    },
)

CreateAuthorizerRequestRequestTypeDef = TypedDict(
    "CreateAuthorizerRequestRequestTypeDef",
    {
        "authorizerName": str,
        "authorizerFunctionArn": str,
        "tokenKeyName": NotRequired[str],
        "tokenSigningPublicKeys": NotRequired[Mapping[str, str]],
        "status": NotRequired[AuthorizerStatusType],
        "tags": NotRequired[Sequence["TagTypeDef"]],
        "signingDisabled": NotRequired[bool],
        "enableCachingForHttp": NotRequired[bool],
    },
)

CreateAuthorizerResponseTypeDef = TypedDict(
    "CreateAuthorizerResponseTypeDef",
    {
        "authorizerName": str,
        "authorizerArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateBillingGroupRequestRequestTypeDef = TypedDict(
    "CreateBillingGroupRequestRequestTypeDef",
    {
        "billingGroupName": str,
        "billingGroupProperties": NotRequired["BillingGroupPropertiesTypeDef"],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateBillingGroupResponseTypeDef = TypedDict(
    "CreateBillingGroupResponseTypeDef",
    {
        "billingGroupName": str,
        "billingGroupArn": str,
        "billingGroupId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateCertificateFromCsrRequestRequestTypeDef = TypedDict(
    "CreateCertificateFromCsrRequestRequestTypeDef",
    {
        "certificateSigningRequest": str,
        "setAsActive": NotRequired[bool],
    },
)

CreateCertificateFromCsrResponseTypeDef = TypedDict(
    "CreateCertificateFromCsrResponseTypeDef",
    {
        "certificateArn": str,
        "certificateId": str,
        "certificatePem": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateCustomMetricRequestRequestTypeDef = TypedDict(
    "CreateCustomMetricRequestRequestTypeDef",
    {
        "metricName": str,
        "metricType": CustomMetricTypeType,
        "clientRequestToken": str,
        "displayName": NotRequired[str],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateCustomMetricResponseTypeDef = TypedDict(
    "CreateCustomMetricResponseTypeDef",
    {
        "metricName": str,
        "metricArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateDimensionRequestRequestTypeDef = TypedDict(
    "CreateDimensionRequestRequestTypeDef",
    {
        "name": str,
        "type": Literal["TOPIC_FILTER"],
        "stringValues": Sequence[str],
        "clientRequestToken": str,
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateDimensionResponseTypeDef = TypedDict(
    "CreateDimensionResponseTypeDef",
    {
        "name": str,
        "arn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateDomainConfigurationRequestRequestTypeDef = TypedDict(
    "CreateDomainConfigurationRequestRequestTypeDef",
    {
        "domainConfigurationName": str,
        "domainName": NotRequired[str],
        "serverCertificateArns": NotRequired[Sequence[str]],
        "validationCertificateArn": NotRequired[str],
        "authorizerConfig": NotRequired["AuthorizerConfigTypeDef"],
        "serviceType": NotRequired[ServiceTypeType],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateDomainConfigurationResponseTypeDef = TypedDict(
    "CreateDomainConfigurationResponseTypeDef",
    {
        "domainConfigurationName": str,
        "domainConfigurationArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateDynamicThingGroupRequestRequestTypeDef = TypedDict(
    "CreateDynamicThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": str,
        "queryString": str,
        "thingGroupProperties": NotRequired["ThingGroupPropertiesTypeDef"],
        "indexName": NotRequired[str],
        "queryVersion": NotRequired[str],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateDynamicThingGroupResponseTypeDef = TypedDict(
    "CreateDynamicThingGroupResponseTypeDef",
    {
        "thingGroupName": str,
        "thingGroupArn": str,
        "thingGroupId": str,
        "indexName": str,
        "queryString": str,
        "queryVersion": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateFleetMetricRequestRequestTypeDef = TypedDict(
    "CreateFleetMetricRequestRequestTypeDef",
    {
        "metricName": str,
        "queryString": str,
        "aggregationType": "AggregationTypeTypeDef",
        "period": int,
        "aggregationField": str,
        "description": NotRequired[str],
        "queryVersion": NotRequired[str],
        "indexName": NotRequired[str],
        "unit": NotRequired[FleetMetricUnitType],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateFleetMetricResponseTypeDef = TypedDict(
    "CreateFleetMetricResponseTypeDef",
    {
        "metricName": str,
        "metricArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateJobRequestRequestTypeDef = TypedDict(
    "CreateJobRequestRequestTypeDef",
    {
        "jobId": str,
        "targets": Sequence[str],
        "documentSource": NotRequired[str],
        "document": NotRequired[str],
        "description": NotRequired[str],
        "presignedUrlConfig": NotRequired["PresignedUrlConfigTypeDef"],
        "targetSelection": NotRequired[TargetSelectionType],
        "jobExecutionsRolloutConfig": NotRequired["JobExecutionsRolloutConfigTypeDef"],
        "abortConfig": NotRequired["AbortConfigTypeDef"],
        "timeoutConfig": NotRequired["TimeoutConfigTypeDef"],
        "tags": NotRequired[Sequence["TagTypeDef"]],
        "namespaceId": NotRequired[str],
        "jobTemplateArn": NotRequired[str],
        "jobExecutionsRetryConfig": NotRequired["JobExecutionsRetryConfigTypeDef"],
        "documentParameters": NotRequired[Mapping[str, str]],
    },
)

CreateJobResponseTypeDef = TypedDict(
    "CreateJobResponseTypeDef",
    {
        "jobArn": str,
        "jobId": str,
        "description": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateJobTemplateRequestRequestTypeDef = TypedDict(
    "CreateJobTemplateRequestRequestTypeDef",
    {
        "jobTemplateId": str,
        "description": str,
        "jobArn": NotRequired[str],
        "documentSource": NotRequired[str],
        "document": NotRequired[str],
        "presignedUrlConfig": NotRequired["PresignedUrlConfigTypeDef"],
        "jobExecutionsRolloutConfig": NotRequired["JobExecutionsRolloutConfigTypeDef"],
        "abortConfig": NotRequired["AbortConfigTypeDef"],
        "timeoutConfig": NotRequired["TimeoutConfigTypeDef"],
        "tags": NotRequired[Sequence["TagTypeDef"]],
        "jobExecutionsRetryConfig": NotRequired["JobExecutionsRetryConfigTypeDef"],
    },
)

CreateJobTemplateResponseTypeDef = TypedDict(
    "CreateJobTemplateResponseTypeDef",
    {
        "jobTemplateArn": str,
        "jobTemplateId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateKeysAndCertificateRequestRequestTypeDef = TypedDict(
    "CreateKeysAndCertificateRequestRequestTypeDef",
    {
        "setAsActive": NotRequired[bool],
    },
)

CreateKeysAndCertificateResponseTypeDef = TypedDict(
    "CreateKeysAndCertificateResponseTypeDef",
    {
        "certificateArn": str,
        "certificateId": str,
        "certificatePem": str,
        "keyPair": "KeyPairTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateMitigationActionRequestRequestTypeDef = TypedDict(
    "CreateMitigationActionRequestRequestTypeDef",
    {
        "actionName": str,
        "roleArn": str,
        "actionParams": "MitigationActionParamsTypeDef",
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateMitigationActionResponseTypeDef = TypedDict(
    "CreateMitigationActionResponseTypeDef",
    {
        "actionArn": str,
        "actionId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateOTAUpdateRequestRequestTypeDef = TypedDict(
    "CreateOTAUpdateRequestRequestTypeDef",
    {
        "otaUpdateId": str,
        "targets": Sequence[str],
        "files": Sequence["OTAUpdateFileTypeDef"],
        "roleArn": str,
        "description": NotRequired[str],
        "protocols": NotRequired[Sequence[ProtocolType]],
        "targetSelection": NotRequired[TargetSelectionType],
        "awsJobExecutionsRolloutConfig": NotRequired["AwsJobExecutionsRolloutConfigTypeDef"],
        "awsJobPresignedUrlConfig": NotRequired["AwsJobPresignedUrlConfigTypeDef"],
        "awsJobAbortConfig": NotRequired["AwsJobAbortConfigTypeDef"],
        "awsJobTimeoutConfig": NotRequired["AwsJobTimeoutConfigTypeDef"],
        "additionalParameters": NotRequired[Mapping[str, str]],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateOTAUpdateResponseTypeDef = TypedDict(
    "CreateOTAUpdateResponseTypeDef",
    {
        "otaUpdateId": str,
        "awsIotJobId": str,
        "otaUpdateArn": str,
        "awsIotJobArn": str,
        "otaUpdateStatus": OTAUpdateStatusType,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreatePolicyRequestRequestTypeDef = TypedDict(
    "CreatePolicyRequestRequestTypeDef",
    {
        "policyName": str,
        "policyDocument": str,
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreatePolicyResponseTypeDef = TypedDict(
    "CreatePolicyResponseTypeDef",
    {
        "policyName": str,
        "policyArn": str,
        "policyDocument": str,
        "policyVersionId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreatePolicyVersionRequestRequestTypeDef = TypedDict(
    "CreatePolicyVersionRequestRequestTypeDef",
    {
        "policyName": str,
        "policyDocument": str,
        "setAsDefault": NotRequired[bool],
    },
)

CreatePolicyVersionResponseTypeDef = TypedDict(
    "CreatePolicyVersionResponseTypeDef",
    {
        "policyArn": str,
        "policyDocument": str,
        "policyVersionId": str,
        "isDefaultVersion": bool,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateProvisioningClaimRequestRequestTypeDef = TypedDict(
    "CreateProvisioningClaimRequestRequestTypeDef",
    {
        "templateName": str,
    },
)

CreateProvisioningClaimResponseTypeDef = TypedDict(
    "CreateProvisioningClaimResponseTypeDef",
    {
        "certificateId": str,
        "certificatePem": str,
        "keyPair": "KeyPairTypeDef",
        "expiration": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateProvisioningTemplateRequestRequestTypeDef = TypedDict(
    "CreateProvisioningTemplateRequestRequestTypeDef",
    {
        "templateName": str,
        "templateBody": str,
        "provisioningRoleArn": str,
        "description": NotRequired[str],
        "enabled": NotRequired[bool],
        "preProvisioningHook": NotRequired["ProvisioningHookTypeDef"],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateProvisioningTemplateResponseTypeDef = TypedDict(
    "CreateProvisioningTemplateResponseTypeDef",
    {
        "templateArn": str,
        "templateName": str,
        "defaultVersionId": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateProvisioningTemplateVersionRequestRequestTypeDef = TypedDict(
    "CreateProvisioningTemplateVersionRequestRequestTypeDef",
    {
        "templateName": str,
        "templateBody": str,
        "setAsDefault": NotRequired[bool],
    },
)

CreateProvisioningTemplateVersionResponseTypeDef = TypedDict(
    "CreateProvisioningTemplateVersionResponseTypeDef",
    {
        "templateArn": str,
        "templateName": str,
        "versionId": int,
        "isDefaultVersion": bool,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateRoleAliasRequestRequestTypeDef = TypedDict(
    "CreateRoleAliasRequestRequestTypeDef",
    {
        "roleAlias": str,
        "roleArn": str,
        "credentialDurationSeconds": NotRequired[int],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateRoleAliasResponseTypeDef = TypedDict(
    "CreateRoleAliasResponseTypeDef",
    {
        "roleAlias": str,
        "roleAliasArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateScheduledAuditRequestRequestTypeDef = TypedDict(
    "CreateScheduledAuditRequestRequestTypeDef",
    {
        "frequency": AuditFrequencyType,
        "targetCheckNames": Sequence[str],
        "scheduledAuditName": str,
        "dayOfMonth": NotRequired[str],
        "dayOfWeek": NotRequired[DayOfWeekType],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateScheduledAuditResponseTypeDef = TypedDict(
    "CreateScheduledAuditResponseTypeDef",
    {
        "scheduledAuditArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateSecurityProfileRequestRequestTypeDef = TypedDict(
    "CreateSecurityProfileRequestRequestTypeDef",
    {
        "securityProfileName": str,
        "securityProfileDescription": NotRequired[str],
        "behaviors": NotRequired[Sequence["BehaviorTypeDef"]],
        "alertTargets": NotRequired[Mapping[Literal["SNS"], "AlertTargetTypeDef"]],
        "additionalMetricsToRetain": NotRequired[Sequence[str]],
        "additionalMetricsToRetainV2": NotRequired[Sequence["MetricToRetainTypeDef"]],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateSecurityProfileResponseTypeDef = TypedDict(
    "CreateSecurityProfileResponseTypeDef",
    {
        "securityProfileName": str,
        "securityProfileArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateStreamRequestRequestTypeDef = TypedDict(
    "CreateStreamRequestRequestTypeDef",
    {
        "streamId": str,
        "files": Sequence["StreamFileTypeDef"],
        "roleArn": str,
        "description": NotRequired[str],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateStreamResponseTypeDef = TypedDict(
    "CreateStreamResponseTypeDef",
    {
        "streamId": str,
        "streamArn": str,
        "description": str,
        "streamVersion": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateThingGroupRequestRequestTypeDef = TypedDict(
    "CreateThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": str,
        "parentGroupName": NotRequired[str],
        "thingGroupProperties": NotRequired["ThingGroupPropertiesTypeDef"],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateThingGroupResponseTypeDef = TypedDict(
    "CreateThingGroupResponseTypeDef",
    {
        "thingGroupName": str,
        "thingGroupArn": str,
        "thingGroupId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateThingRequestRequestTypeDef = TypedDict(
    "CreateThingRequestRequestTypeDef",
    {
        "thingName": str,
        "thingTypeName": NotRequired[str],
        "attributePayload": NotRequired["AttributePayloadTypeDef"],
        "billingGroupName": NotRequired[str],
    },
)

CreateThingResponseTypeDef = TypedDict(
    "CreateThingResponseTypeDef",
    {
        "thingName": str,
        "thingArn": str,
        "thingId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateThingTypeRequestRequestTypeDef = TypedDict(
    "CreateThingTypeRequestRequestTypeDef",
    {
        "thingTypeName": str,
        "thingTypeProperties": NotRequired["ThingTypePropertiesTypeDef"],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

CreateThingTypeResponseTypeDef = TypedDict(
    "CreateThingTypeResponseTypeDef",
    {
        "thingTypeName": str,
        "thingTypeArn": str,
        "thingTypeId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateTopicRuleDestinationRequestRequestTypeDef = TypedDict(
    "CreateTopicRuleDestinationRequestRequestTypeDef",
    {
        "destinationConfiguration": "TopicRuleDestinationConfigurationTypeDef",
    },
)

CreateTopicRuleDestinationResponseTypeDef = TypedDict(
    "CreateTopicRuleDestinationResponseTypeDef",
    {
        "topicRuleDestination": "TopicRuleDestinationTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

CreateTopicRuleRequestRequestTypeDef = TypedDict(
    "CreateTopicRuleRequestRequestTypeDef",
    {
        "ruleName": str,
        "topicRulePayload": "TopicRulePayloadTypeDef",
        "tags": NotRequired[str],
    },
)

CustomCodeSigningTypeDef = TypedDict(
    "CustomCodeSigningTypeDef",
    {
        "signature": NotRequired["CodeSigningSignatureTypeDef"],
        "certificateChain": NotRequired["CodeSigningCertificateChainTypeDef"],
        "hashAlgorithm": NotRequired[str],
        "signatureAlgorithm": NotRequired[str],
    },
)

DeleteAccountAuditConfigurationRequestRequestTypeDef = TypedDict(
    "DeleteAccountAuditConfigurationRequestRequestTypeDef",
    {
        "deleteScheduledAudits": NotRequired[bool],
    },
)

DeleteAuditSuppressionRequestRequestTypeDef = TypedDict(
    "DeleteAuditSuppressionRequestRequestTypeDef",
    {
        "checkName": str,
        "resourceIdentifier": "ResourceIdentifierTypeDef",
    },
)

DeleteAuthorizerRequestRequestTypeDef = TypedDict(
    "DeleteAuthorizerRequestRequestTypeDef",
    {
        "authorizerName": str,
    },
)

DeleteBillingGroupRequestRequestTypeDef = TypedDict(
    "DeleteBillingGroupRequestRequestTypeDef",
    {
        "billingGroupName": str,
        "expectedVersion": NotRequired[int],
    },
)

DeleteCACertificateRequestRequestTypeDef = TypedDict(
    "DeleteCACertificateRequestRequestTypeDef",
    {
        "certificateId": str,
    },
)

DeleteCertificateRequestRequestTypeDef = TypedDict(
    "DeleteCertificateRequestRequestTypeDef",
    {
        "certificateId": str,
        "forceDelete": NotRequired[bool],
    },
)

DeleteCustomMetricRequestRequestTypeDef = TypedDict(
    "DeleteCustomMetricRequestRequestTypeDef",
    {
        "metricName": str,
    },
)

DeleteDimensionRequestRequestTypeDef = TypedDict(
    "DeleteDimensionRequestRequestTypeDef",
    {
        "name": str,
    },
)

DeleteDomainConfigurationRequestRequestTypeDef = TypedDict(
    "DeleteDomainConfigurationRequestRequestTypeDef",
    {
        "domainConfigurationName": str,
    },
)

DeleteDynamicThingGroupRequestRequestTypeDef = TypedDict(
    "DeleteDynamicThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": str,
        "expectedVersion": NotRequired[int],
    },
)

DeleteFleetMetricRequestRequestTypeDef = TypedDict(
    "DeleteFleetMetricRequestRequestTypeDef",
    {
        "metricName": str,
        "expectedVersion": NotRequired[int],
    },
)

DeleteJobExecutionRequestRequestTypeDef = TypedDict(
    "DeleteJobExecutionRequestRequestTypeDef",
    {
        "jobId": str,
        "thingName": str,
        "executionNumber": int,
        "force": NotRequired[bool],
        "namespaceId": NotRequired[str],
    },
)

DeleteJobRequestRequestTypeDef = TypedDict(
    "DeleteJobRequestRequestTypeDef",
    {
        "jobId": str,
        "force": NotRequired[bool],
        "namespaceId": NotRequired[str],
    },
)

DeleteJobTemplateRequestRequestTypeDef = TypedDict(
    "DeleteJobTemplateRequestRequestTypeDef",
    {
        "jobTemplateId": str,
    },
)

DeleteMitigationActionRequestRequestTypeDef = TypedDict(
    "DeleteMitigationActionRequestRequestTypeDef",
    {
        "actionName": str,
    },
)

DeleteOTAUpdateRequestRequestTypeDef = TypedDict(
    "DeleteOTAUpdateRequestRequestTypeDef",
    {
        "otaUpdateId": str,
        "deleteStream": NotRequired[bool],
        "forceDeleteAWSJob": NotRequired[bool],
    },
)

DeletePolicyRequestRequestTypeDef = TypedDict(
    "DeletePolicyRequestRequestTypeDef",
    {
        "policyName": str,
    },
)

DeletePolicyVersionRequestRequestTypeDef = TypedDict(
    "DeletePolicyVersionRequestRequestTypeDef",
    {
        "policyName": str,
        "policyVersionId": str,
    },
)

DeleteProvisioningTemplateRequestRequestTypeDef = TypedDict(
    "DeleteProvisioningTemplateRequestRequestTypeDef",
    {
        "templateName": str,
    },
)

DeleteProvisioningTemplateVersionRequestRequestTypeDef = TypedDict(
    "DeleteProvisioningTemplateVersionRequestRequestTypeDef",
    {
        "templateName": str,
        "versionId": int,
    },
)

DeleteRoleAliasRequestRequestTypeDef = TypedDict(
    "DeleteRoleAliasRequestRequestTypeDef",
    {
        "roleAlias": str,
    },
)

DeleteScheduledAuditRequestRequestTypeDef = TypedDict(
    "DeleteScheduledAuditRequestRequestTypeDef",
    {
        "scheduledAuditName": str,
    },
)

DeleteSecurityProfileRequestRequestTypeDef = TypedDict(
    "DeleteSecurityProfileRequestRequestTypeDef",
    {
        "securityProfileName": str,
        "expectedVersion": NotRequired[int],
    },
)

DeleteStreamRequestRequestTypeDef = TypedDict(
    "DeleteStreamRequestRequestTypeDef",
    {
        "streamId": str,
    },
)

DeleteThingGroupRequestRequestTypeDef = TypedDict(
    "DeleteThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": str,
        "expectedVersion": NotRequired[int],
    },
)

DeleteThingRequestRequestTypeDef = TypedDict(
    "DeleteThingRequestRequestTypeDef",
    {
        "thingName": str,
        "expectedVersion": NotRequired[int],
    },
)

DeleteThingTypeRequestRequestTypeDef = TypedDict(
    "DeleteThingTypeRequestRequestTypeDef",
    {
        "thingTypeName": str,
    },
)

DeleteTopicRuleDestinationRequestRequestTypeDef = TypedDict(
    "DeleteTopicRuleDestinationRequestRequestTypeDef",
    {
        "arn": str,
    },
)

DeleteTopicRuleRequestRequestTypeDef = TypedDict(
    "DeleteTopicRuleRequestRequestTypeDef",
    {
        "ruleName": str,
    },
)

DeleteV2LoggingLevelRequestRequestTypeDef = TypedDict(
    "DeleteV2LoggingLevelRequestRequestTypeDef",
    {
        "targetType": LogTargetTypeType,
        "targetName": str,
    },
)

DeniedTypeDef = TypedDict(
    "DeniedTypeDef",
    {
        "implicitDeny": NotRequired["ImplicitDenyTypeDef"],
        "explicitDeny": NotRequired["ExplicitDenyTypeDef"],
    },
)

DeprecateThingTypeRequestRequestTypeDef = TypedDict(
    "DeprecateThingTypeRequestRequestTypeDef",
    {
        "thingTypeName": str,
        "undoDeprecate": NotRequired[bool],
    },
)

DescribeAccountAuditConfigurationResponseTypeDef = TypedDict(
    "DescribeAccountAuditConfigurationResponseTypeDef",
    {
        "roleArn": str,
        "auditNotificationTargetConfigurations": Dict[
            Literal["SNS"], "AuditNotificationTargetTypeDef"
        ],
        "auditCheckConfigurations": Dict[str, "AuditCheckConfigurationTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeAuditFindingRequestRequestTypeDef = TypedDict(
    "DescribeAuditFindingRequestRequestTypeDef",
    {
        "findingId": str,
    },
)

DescribeAuditFindingResponseTypeDef = TypedDict(
    "DescribeAuditFindingResponseTypeDef",
    {
        "finding": "AuditFindingTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeAuditMitigationActionsTaskRequestRequestTypeDef = TypedDict(
    "DescribeAuditMitigationActionsTaskRequestRequestTypeDef",
    {
        "taskId": str,
    },
)

DescribeAuditMitigationActionsTaskResponseTypeDef = TypedDict(
    "DescribeAuditMitigationActionsTaskResponseTypeDef",
    {
        "taskStatus": AuditMitigationActionsTaskStatusType,
        "startTime": datetime,
        "endTime": datetime,
        "taskStatistics": Dict[str, "TaskStatisticsForAuditCheckTypeDef"],
        "target": "AuditMitigationActionsTaskTargetTypeDef",
        "auditCheckToActionsMapping": Dict[str, List[str]],
        "actionsDefinition": List["MitigationActionTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeAuditSuppressionRequestRequestTypeDef = TypedDict(
    "DescribeAuditSuppressionRequestRequestTypeDef",
    {
        "checkName": str,
        "resourceIdentifier": "ResourceIdentifierTypeDef",
    },
)

DescribeAuditSuppressionResponseTypeDef = TypedDict(
    "DescribeAuditSuppressionResponseTypeDef",
    {
        "checkName": str,
        "resourceIdentifier": "ResourceIdentifierTypeDef",
        "expirationDate": datetime,
        "suppressIndefinitely": bool,
        "description": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeAuditTaskRequestRequestTypeDef = TypedDict(
    "DescribeAuditTaskRequestRequestTypeDef",
    {
        "taskId": str,
    },
)

DescribeAuditTaskResponseTypeDef = TypedDict(
    "DescribeAuditTaskResponseTypeDef",
    {
        "taskStatus": AuditTaskStatusType,
        "taskType": AuditTaskTypeType,
        "taskStartTime": datetime,
        "taskStatistics": "TaskStatisticsTypeDef",
        "scheduledAuditName": str,
        "auditDetails": Dict[str, "AuditCheckDetailsTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeAuthorizerRequestRequestTypeDef = TypedDict(
    "DescribeAuthorizerRequestRequestTypeDef",
    {
        "authorizerName": str,
    },
)

DescribeAuthorizerResponseTypeDef = TypedDict(
    "DescribeAuthorizerResponseTypeDef",
    {
        "authorizerDescription": "AuthorizerDescriptionTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeBillingGroupRequestRequestTypeDef = TypedDict(
    "DescribeBillingGroupRequestRequestTypeDef",
    {
        "billingGroupName": str,
    },
)

DescribeBillingGroupResponseTypeDef = TypedDict(
    "DescribeBillingGroupResponseTypeDef",
    {
        "billingGroupName": str,
        "billingGroupId": str,
        "billingGroupArn": str,
        "version": int,
        "billingGroupProperties": "BillingGroupPropertiesTypeDef",
        "billingGroupMetadata": "BillingGroupMetadataTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeCACertificateRequestRequestTypeDef = TypedDict(
    "DescribeCACertificateRequestRequestTypeDef",
    {
        "certificateId": str,
    },
)

DescribeCACertificateResponseTypeDef = TypedDict(
    "DescribeCACertificateResponseTypeDef",
    {
        "certificateDescription": "CACertificateDescriptionTypeDef",
        "registrationConfig": "RegistrationConfigTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeCertificateRequestRequestTypeDef = TypedDict(
    "DescribeCertificateRequestRequestTypeDef",
    {
        "certificateId": str,
    },
)

DescribeCertificateResponseTypeDef = TypedDict(
    "DescribeCertificateResponseTypeDef",
    {
        "certificateDescription": "CertificateDescriptionTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeCustomMetricRequestRequestTypeDef = TypedDict(
    "DescribeCustomMetricRequestRequestTypeDef",
    {
        "metricName": str,
    },
)

DescribeCustomMetricResponseTypeDef = TypedDict(
    "DescribeCustomMetricResponseTypeDef",
    {
        "metricName": str,
        "metricArn": str,
        "metricType": CustomMetricTypeType,
        "displayName": str,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeDefaultAuthorizerResponseTypeDef = TypedDict(
    "DescribeDefaultAuthorizerResponseTypeDef",
    {
        "authorizerDescription": "AuthorizerDescriptionTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeDetectMitigationActionsTaskRequestRequestTypeDef = TypedDict(
    "DescribeDetectMitigationActionsTaskRequestRequestTypeDef",
    {
        "taskId": str,
    },
)

DescribeDetectMitigationActionsTaskResponseTypeDef = TypedDict(
    "DescribeDetectMitigationActionsTaskResponseTypeDef",
    {
        "taskSummary": "DetectMitigationActionsTaskSummaryTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeDimensionRequestRequestTypeDef = TypedDict(
    "DescribeDimensionRequestRequestTypeDef",
    {
        "name": str,
    },
)

DescribeDimensionResponseTypeDef = TypedDict(
    "DescribeDimensionResponseTypeDef",
    {
        "name": str,
        "arn": str,
        "type": Literal["TOPIC_FILTER"],
        "stringValues": List[str],
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeDomainConfigurationRequestRequestTypeDef = TypedDict(
    "DescribeDomainConfigurationRequestRequestTypeDef",
    {
        "domainConfigurationName": str,
    },
)

DescribeDomainConfigurationResponseTypeDef = TypedDict(
    "DescribeDomainConfigurationResponseTypeDef",
    {
        "domainConfigurationName": str,
        "domainConfigurationArn": str,
        "domainName": str,
        "serverCertificates": List["ServerCertificateSummaryTypeDef"],
        "authorizerConfig": "AuthorizerConfigTypeDef",
        "domainConfigurationStatus": DomainConfigurationStatusType,
        "serviceType": ServiceTypeType,
        "domainType": DomainTypeType,
        "lastStatusChangeDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeEndpointRequestRequestTypeDef = TypedDict(
    "DescribeEndpointRequestRequestTypeDef",
    {
        "endpointType": NotRequired[str],
    },
)

DescribeEndpointResponseTypeDef = TypedDict(
    "DescribeEndpointResponseTypeDef",
    {
        "endpointAddress": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeEventConfigurationsResponseTypeDef = TypedDict(
    "DescribeEventConfigurationsResponseTypeDef",
    {
        "eventConfigurations": Dict[EventTypeType, "ConfigurationTypeDef"],
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeFleetMetricRequestRequestTypeDef = TypedDict(
    "DescribeFleetMetricRequestRequestTypeDef",
    {
        "metricName": str,
    },
)

DescribeFleetMetricResponseTypeDef = TypedDict(
    "DescribeFleetMetricResponseTypeDef",
    {
        "metricName": str,
        "queryString": str,
        "aggregationType": "AggregationTypeTypeDef",
        "period": int,
        "aggregationField": str,
        "description": str,
        "queryVersion": str,
        "indexName": str,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "unit": FleetMetricUnitType,
        "version": int,
        "metricArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeIndexRequestRequestTypeDef = TypedDict(
    "DescribeIndexRequestRequestTypeDef",
    {
        "indexName": str,
    },
)

DescribeIndexResponseTypeDef = TypedDict(
    "DescribeIndexResponseTypeDef",
    {
        "indexName": str,
        "indexStatus": IndexStatusType,
        "schema": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeJobExecutionRequestRequestTypeDef = TypedDict(
    "DescribeJobExecutionRequestRequestTypeDef",
    {
        "jobId": str,
        "thingName": str,
        "executionNumber": NotRequired[int],
    },
)

DescribeJobExecutionResponseTypeDef = TypedDict(
    "DescribeJobExecutionResponseTypeDef",
    {
        "execution": "JobExecutionTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeJobRequestRequestTypeDef = TypedDict(
    "DescribeJobRequestRequestTypeDef",
    {
        "jobId": str,
    },
)

DescribeJobResponseTypeDef = TypedDict(
    "DescribeJobResponseTypeDef",
    {
        "documentSource": str,
        "job": "JobTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeJobTemplateRequestRequestTypeDef = TypedDict(
    "DescribeJobTemplateRequestRequestTypeDef",
    {
        "jobTemplateId": str,
    },
)

DescribeJobTemplateResponseTypeDef = TypedDict(
    "DescribeJobTemplateResponseTypeDef",
    {
        "jobTemplateArn": str,
        "jobTemplateId": str,
        "description": str,
        "documentSource": str,
        "document": str,
        "createdAt": datetime,
        "presignedUrlConfig": "PresignedUrlConfigTypeDef",
        "jobExecutionsRolloutConfig": "JobExecutionsRolloutConfigTypeDef",
        "abortConfig": "AbortConfigTypeDef",
        "timeoutConfig": "TimeoutConfigTypeDef",
        "jobExecutionsRetryConfig": "JobExecutionsRetryConfigTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeManagedJobTemplateRequestRequestTypeDef = TypedDict(
    "DescribeManagedJobTemplateRequestRequestTypeDef",
    {
        "templateName": str,
        "templateVersion": NotRequired[str],
    },
)

DescribeManagedJobTemplateResponseTypeDef = TypedDict(
    "DescribeManagedJobTemplateResponseTypeDef",
    {
        "templateName": str,
        "templateArn": str,
        "description": str,
        "templateVersion": str,
        "environments": List[str],
        "documentParameters": List["DocumentParameterTypeDef"],
        "document": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeMitigationActionRequestRequestTypeDef = TypedDict(
    "DescribeMitigationActionRequestRequestTypeDef",
    {
        "actionName": str,
    },
)

DescribeMitigationActionResponseTypeDef = TypedDict(
    "DescribeMitigationActionResponseTypeDef",
    {
        "actionName": str,
        "actionType": MitigationActionTypeType,
        "actionArn": str,
        "actionId": str,
        "roleArn": str,
        "actionParams": "MitigationActionParamsTypeDef",
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeProvisioningTemplateRequestRequestTypeDef = TypedDict(
    "DescribeProvisioningTemplateRequestRequestTypeDef",
    {
        "templateName": str,
    },
)

DescribeProvisioningTemplateResponseTypeDef = TypedDict(
    "DescribeProvisioningTemplateResponseTypeDef",
    {
        "templateArn": str,
        "templateName": str,
        "description": str,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "defaultVersionId": int,
        "templateBody": str,
        "enabled": bool,
        "provisioningRoleArn": str,
        "preProvisioningHook": "ProvisioningHookTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeProvisioningTemplateVersionRequestRequestTypeDef = TypedDict(
    "DescribeProvisioningTemplateVersionRequestRequestTypeDef",
    {
        "templateName": str,
        "versionId": int,
    },
)

DescribeProvisioningTemplateVersionResponseTypeDef = TypedDict(
    "DescribeProvisioningTemplateVersionResponseTypeDef",
    {
        "versionId": int,
        "creationDate": datetime,
        "templateBody": str,
        "isDefaultVersion": bool,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeRoleAliasRequestRequestTypeDef = TypedDict(
    "DescribeRoleAliasRequestRequestTypeDef",
    {
        "roleAlias": str,
    },
)

DescribeRoleAliasResponseTypeDef = TypedDict(
    "DescribeRoleAliasResponseTypeDef",
    {
        "roleAliasDescription": "RoleAliasDescriptionTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeScheduledAuditRequestRequestTypeDef = TypedDict(
    "DescribeScheduledAuditRequestRequestTypeDef",
    {
        "scheduledAuditName": str,
    },
)

DescribeScheduledAuditResponseTypeDef = TypedDict(
    "DescribeScheduledAuditResponseTypeDef",
    {
        "frequency": AuditFrequencyType,
        "dayOfMonth": str,
        "dayOfWeek": DayOfWeekType,
        "targetCheckNames": List[str],
        "scheduledAuditName": str,
        "scheduledAuditArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeSecurityProfileRequestRequestTypeDef = TypedDict(
    "DescribeSecurityProfileRequestRequestTypeDef",
    {
        "securityProfileName": str,
    },
)

DescribeSecurityProfileResponseTypeDef = TypedDict(
    "DescribeSecurityProfileResponseTypeDef",
    {
        "securityProfileName": str,
        "securityProfileArn": str,
        "securityProfileDescription": str,
        "behaviors": List["BehaviorTypeDef"],
        "alertTargets": Dict[Literal["SNS"], "AlertTargetTypeDef"],
        "additionalMetricsToRetain": List[str],
        "additionalMetricsToRetainV2": List["MetricToRetainTypeDef"],
        "version": int,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeStreamRequestRequestTypeDef = TypedDict(
    "DescribeStreamRequestRequestTypeDef",
    {
        "streamId": str,
    },
)

DescribeStreamResponseTypeDef = TypedDict(
    "DescribeStreamResponseTypeDef",
    {
        "streamInfo": "StreamInfoTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeThingGroupRequestRequestTypeDef = TypedDict(
    "DescribeThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": str,
    },
)

DescribeThingGroupResponseTypeDef = TypedDict(
    "DescribeThingGroupResponseTypeDef",
    {
        "thingGroupName": str,
        "thingGroupId": str,
        "thingGroupArn": str,
        "version": int,
        "thingGroupProperties": "ThingGroupPropertiesTypeDef",
        "thingGroupMetadata": "ThingGroupMetadataTypeDef",
        "indexName": str,
        "queryString": str,
        "queryVersion": str,
        "status": DynamicGroupStatusType,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeThingRegistrationTaskRequestRequestTypeDef = TypedDict(
    "DescribeThingRegistrationTaskRequestRequestTypeDef",
    {
        "taskId": str,
    },
)

DescribeThingRegistrationTaskResponseTypeDef = TypedDict(
    "DescribeThingRegistrationTaskResponseTypeDef",
    {
        "taskId": str,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "templateBody": str,
        "inputFileBucket": str,
        "inputFileKey": str,
        "roleArn": str,
        "status": StatusType,
        "message": str,
        "successCount": int,
        "failureCount": int,
        "percentageProgress": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeThingRequestRequestTypeDef = TypedDict(
    "DescribeThingRequestRequestTypeDef",
    {
        "thingName": str,
    },
)

DescribeThingResponseTypeDef = TypedDict(
    "DescribeThingResponseTypeDef",
    {
        "defaultClientId": str,
        "thingName": str,
        "thingId": str,
        "thingArn": str,
        "thingTypeName": str,
        "attributes": Dict[str, str],
        "version": int,
        "billingGroupName": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DescribeThingTypeRequestRequestTypeDef = TypedDict(
    "DescribeThingTypeRequestRequestTypeDef",
    {
        "thingTypeName": str,
    },
)

DescribeThingTypeResponseTypeDef = TypedDict(
    "DescribeThingTypeResponseTypeDef",
    {
        "thingTypeName": str,
        "thingTypeId": str,
        "thingTypeArn": str,
        "thingTypeProperties": "ThingTypePropertiesTypeDef",
        "thingTypeMetadata": "ThingTypeMetadataTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

DestinationTypeDef = TypedDict(
    "DestinationTypeDef",
    {
        "s3Destination": NotRequired["S3DestinationTypeDef"],
    },
)

DetachPolicyRequestRequestTypeDef = TypedDict(
    "DetachPolicyRequestRequestTypeDef",
    {
        "policyName": str,
        "target": str,
    },
)

DetachPrincipalPolicyRequestRequestTypeDef = TypedDict(
    "DetachPrincipalPolicyRequestRequestTypeDef",
    {
        "policyName": str,
        "principal": str,
    },
)

DetachSecurityProfileRequestRequestTypeDef = TypedDict(
    "DetachSecurityProfileRequestRequestTypeDef",
    {
        "securityProfileName": str,
        "securityProfileTargetArn": str,
    },
)

DetachThingPrincipalRequestRequestTypeDef = TypedDict(
    "DetachThingPrincipalRequestRequestTypeDef",
    {
        "thingName": str,
        "principal": str,
    },
)

DetectMitigationActionExecutionTypeDef = TypedDict(
    "DetectMitigationActionExecutionTypeDef",
    {
        "taskId": NotRequired[str],
        "violationId": NotRequired[str],
        "actionName": NotRequired[str],
        "thingName": NotRequired[str],
        "executionStartDate": NotRequired[datetime],
        "executionEndDate": NotRequired[datetime],
        "status": NotRequired[DetectMitigationActionExecutionStatusType],
        "errorCode": NotRequired[str],
        "message": NotRequired[str],
    },
)

DetectMitigationActionsTaskStatisticsTypeDef = TypedDict(
    "DetectMitigationActionsTaskStatisticsTypeDef",
    {
        "actionsExecuted": NotRequired[int],
        "actionsSkipped": NotRequired[int],
        "actionsFailed": NotRequired[int],
    },
)

DetectMitigationActionsTaskSummaryTypeDef = TypedDict(
    "DetectMitigationActionsTaskSummaryTypeDef",
    {
        "taskId": NotRequired[str],
        "taskStatus": NotRequired[DetectMitigationActionsTaskStatusType],
        "taskStartTime": NotRequired[datetime],
        "taskEndTime": NotRequired[datetime],
        "target": NotRequired["DetectMitigationActionsTaskTargetTypeDef"],
        "violationEventOccurrenceRange": NotRequired["ViolationEventOccurrenceRangeTypeDef"],
        "onlyActiveViolationsIncluded": NotRequired[bool],
        "suppressedAlertsIncluded": NotRequired[bool],
        "actionsDefinition": NotRequired[List["MitigationActionTypeDef"]],
        "taskStatistics": NotRequired["DetectMitigationActionsTaskStatisticsTypeDef"],
    },
)

DetectMitigationActionsTaskTargetTypeDef = TypedDict(
    "DetectMitigationActionsTaskTargetTypeDef",
    {
        "violationIds": NotRequired[List[str]],
        "securityProfileName": NotRequired[str],
        "behaviorName": NotRequired[str],
    },
)

DisableTopicRuleRequestRequestTypeDef = TypedDict(
    "DisableTopicRuleRequestRequestTypeDef",
    {
        "ruleName": str,
    },
)

DocumentParameterTypeDef = TypedDict(
    "DocumentParameterTypeDef",
    {
        "key": NotRequired[str],
        "description": NotRequired[str],
        "regex": NotRequired[str],
        "example": NotRequired[str],
        "optional": NotRequired[bool],
    },
)

DomainConfigurationSummaryTypeDef = TypedDict(
    "DomainConfigurationSummaryTypeDef",
    {
        "domainConfigurationName": NotRequired[str],
        "domainConfigurationArn": NotRequired[str],
        "serviceType": NotRequired[ServiceTypeType],
    },
)

DynamoDBActionTypeDef = TypedDict(
    "DynamoDBActionTypeDef",
    {
        "tableName": str,
        "roleArn": str,
        "hashKeyField": str,
        "hashKeyValue": str,
        "operation": NotRequired[str],
        "hashKeyType": NotRequired[DynamoKeyTypeType],
        "rangeKeyField": NotRequired[str],
        "rangeKeyValue": NotRequired[str],
        "rangeKeyType": NotRequired[DynamoKeyTypeType],
        "payloadField": NotRequired[str],
    },
)

DynamoDBv2ActionTypeDef = TypedDict(
    "DynamoDBv2ActionTypeDef",
    {
        "roleArn": str,
        "putItem": "PutItemInputTypeDef",
    },
)

EffectivePolicyTypeDef = TypedDict(
    "EffectivePolicyTypeDef",
    {
        "policyName": NotRequired[str],
        "policyArn": NotRequired[str],
        "policyDocument": NotRequired[str],
    },
)

ElasticsearchActionTypeDef = TypedDict(
    "ElasticsearchActionTypeDef",
    {
        "roleArn": str,
        "endpoint": str,
        "index": str,
        "type": str,
        "id": str,
    },
)

EnableIoTLoggingParamsTypeDef = TypedDict(
    "EnableIoTLoggingParamsTypeDef",
    {
        "roleArnForLogging": str,
        "logLevel": LogLevelType,
    },
)

EnableTopicRuleRequestRequestTypeDef = TypedDict(
    "EnableTopicRuleRequestRequestTypeDef",
    {
        "ruleName": str,
    },
)

ErrorInfoTypeDef = TypedDict(
    "ErrorInfoTypeDef",
    {
        "code": NotRequired[str],
        "message": NotRequired[str],
    },
)

ExplicitDenyTypeDef = TypedDict(
    "ExplicitDenyTypeDef",
    {
        "policies": NotRequired[List["PolicyTypeDef"]],
    },
)

ExponentialRolloutRateTypeDef = TypedDict(
    "ExponentialRolloutRateTypeDef",
    {
        "baseRatePerMinute": int,
        "incrementFactor": float,
        "rateIncreaseCriteria": "RateIncreaseCriteriaTypeDef",
    },
)

FieldTypeDef = TypedDict(
    "FieldTypeDef",
    {
        "name": NotRequired[str],
        "type": NotRequired[FieldTypeType],
    },
)

FileLocationTypeDef = TypedDict(
    "FileLocationTypeDef",
    {
        "stream": NotRequired["StreamTypeDef"],
        "s3Location": NotRequired["S3LocationTypeDef"],
    },
)

FirehoseActionTypeDef = TypedDict(
    "FirehoseActionTypeDef",
    {
        "roleArn": str,
        "deliveryStreamName": str,
        "separator": NotRequired[str],
        "batchMode": NotRequired[bool],
    },
)

FleetMetricNameAndArnTypeDef = TypedDict(
    "FleetMetricNameAndArnTypeDef",
    {
        "metricName": NotRequired[str],
        "metricArn": NotRequired[str],
    },
)

GetBehaviorModelTrainingSummariesRequestGetBehaviorModelTrainingSummariesPaginateTypeDef = (
    TypedDict(
        "GetBehaviorModelTrainingSummariesRequestGetBehaviorModelTrainingSummariesPaginateTypeDef",
        {
            "securityProfileName": NotRequired[str],
            "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
        },
    )
)

GetBehaviorModelTrainingSummariesRequestRequestTypeDef = TypedDict(
    "GetBehaviorModelTrainingSummariesRequestRequestTypeDef",
    {
        "securityProfileName": NotRequired[str],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

GetBehaviorModelTrainingSummariesResponseTypeDef = TypedDict(
    "GetBehaviorModelTrainingSummariesResponseTypeDef",
    {
        "summaries": List["BehaviorModelTrainingSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetBucketsAggregationRequestRequestTypeDef = TypedDict(
    "GetBucketsAggregationRequestRequestTypeDef",
    {
        "queryString": str,
        "aggregationField": str,
        "bucketsAggregationType": "BucketsAggregationTypeTypeDef",
        "indexName": NotRequired[str],
        "queryVersion": NotRequired[str],
    },
)

GetBucketsAggregationResponseTypeDef = TypedDict(
    "GetBucketsAggregationResponseTypeDef",
    {
        "totalCount": int,
        "buckets": List["BucketTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetCardinalityRequestRequestTypeDef = TypedDict(
    "GetCardinalityRequestRequestTypeDef",
    {
        "queryString": str,
        "indexName": NotRequired[str],
        "aggregationField": NotRequired[str],
        "queryVersion": NotRequired[str],
    },
)

GetCardinalityResponseTypeDef = TypedDict(
    "GetCardinalityResponseTypeDef",
    {
        "cardinality": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetEffectivePoliciesRequestRequestTypeDef = TypedDict(
    "GetEffectivePoliciesRequestRequestTypeDef",
    {
        "principal": NotRequired[str],
        "cognitoIdentityPoolId": NotRequired[str],
        "thingName": NotRequired[str],
    },
)

GetEffectivePoliciesResponseTypeDef = TypedDict(
    "GetEffectivePoliciesResponseTypeDef",
    {
        "effectivePolicies": List["EffectivePolicyTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetIndexingConfigurationResponseTypeDef = TypedDict(
    "GetIndexingConfigurationResponseTypeDef",
    {
        "thingIndexingConfiguration": "ThingIndexingConfigurationTypeDef",
        "thingGroupIndexingConfiguration": "ThingGroupIndexingConfigurationTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetJobDocumentRequestRequestTypeDef = TypedDict(
    "GetJobDocumentRequestRequestTypeDef",
    {
        "jobId": str,
    },
)

GetJobDocumentResponseTypeDef = TypedDict(
    "GetJobDocumentResponseTypeDef",
    {
        "document": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetLoggingOptionsResponseTypeDef = TypedDict(
    "GetLoggingOptionsResponseTypeDef",
    {
        "roleArn": str,
        "logLevel": LogLevelType,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetOTAUpdateRequestRequestTypeDef = TypedDict(
    "GetOTAUpdateRequestRequestTypeDef",
    {
        "otaUpdateId": str,
    },
)

GetOTAUpdateResponseTypeDef = TypedDict(
    "GetOTAUpdateResponseTypeDef",
    {
        "otaUpdateInfo": "OTAUpdateInfoTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetPercentilesRequestRequestTypeDef = TypedDict(
    "GetPercentilesRequestRequestTypeDef",
    {
        "queryString": str,
        "indexName": NotRequired[str],
        "aggregationField": NotRequired[str],
        "queryVersion": NotRequired[str],
        "percents": NotRequired[Sequence[float]],
    },
)

GetPercentilesResponseTypeDef = TypedDict(
    "GetPercentilesResponseTypeDef",
    {
        "percentiles": List["PercentPairTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetPolicyRequestRequestTypeDef = TypedDict(
    "GetPolicyRequestRequestTypeDef",
    {
        "policyName": str,
    },
)

GetPolicyResponseTypeDef = TypedDict(
    "GetPolicyResponseTypeDef",
    {
        "policyName": str,
        "policyArn": str,
        "policyDocument": str,
        "defaultVersionId": str,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "generationId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetPolicyVersionRequestRequestTypeDef = TypedDict(
    "GetPolicyVersionRequestRequestTypeDef",
    {
        "policyName": str,
        "policyVersionId": str,
    },
)

GetPolicyVersionResponseTypeDef = TypedDict(
    "GetPolicyVersionResponseTypeDef",
    {
        "policyArn": str,
        "policyName": str,
        "policyDocument": str,
        "policyVersionId": str,
        "isDefaultVersion": bool,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "generationId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetRegistrationCodeResponseTypeDef = TypedDict(
    "GetRegistrationCodeResponseTypeDef",
    {
        "registrationCode": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetStatisticsRequestRequestTypeDef = TypedDict(
    "GetStatisticsRequestRequestTypeDef",
    {
        "queryString": str,
        "indexName": NotRequired[str],
        "aggregationField": NotRequired[str],
        "queryVersion": NotRequired[str],
    },
)

GetStatisticsResponseTypeDef = TypedDict(
    "GetStatisticsResponseTypeDef",
    {
        "statistics": "StatisticsTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetTopicRuleDestinationRequestRequestTypeDef = TypedDict(
    "GetTopicRuleDestinationRequestRequestTypeDef",
    {
        "arn": str,
    },
)

GetTopicRuleDestinationResponseTypeDef = TypedDict(
    "GetTopicRuleDestinationResponseTypeDef",
    {
        "topicRuleDestination": "TopicRuleDestinationTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetTopicRuleRequestRequestTypeDef = TypedDict(
    "GetTopicRuleRequestRequestTypeDef",
    {
        "ruleName": str,
    },
)

GetTopicRuleResponseTypeDef = TypedDict(
    "GetTopicRuleResponseTypeDef",
    {
        "ruleArn": str,
        "rule": "TopicRuleTypeDef",
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GetV2LoggingOptionsResponseTypeDef = TypedDict(
    "GetV2LoggingOptionsResponseTypeDef",
    {
        "roleArn": str,
        "defaultLogLevel": LogLevelType,
        "disableAllLogs": bool,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

GroupNameAndArnTypeDef = TypedDict(
    "GroupNameAndArnTypeDef",
    {
        "groupName": NotRequired[str],
        "groupArn": NotRequired[str],
    },
)

HttpActionHeaderTypeDef = TypedDict(
    "HttpActionHeaderTypeDef",
    {
        "key": str,
        "value": str,
    },
)

HttpActionTypeDef = TypedDict(
    "HttpActionTypeDef",
    {
        "url": str,
        "confirmationUrl": NotRequired[str],
        "headers": NotRequired[Sequence["HttpActionHeaderTypeDef"]],
        "auth": NotRequired["HttpAuthorizationTypeDef"],
    },
)

HttpAuthorizationTypeDef = TypedDict(
    "HttpAuthorizationTypeDef",
    {
        "sigv4": NotRequired["SigV4AuthorizationTypeDef"],
    },
)

HttpContextTypeDef = TypedDict(
    "HttpContextTypeDef",
    {
        "headers": NotRequired[Mapping[str, str]],
        "queryString": NotRequired[str],
    },
)

HttpUrlDestinationConfigurationTypeDef = TypedDict(
    "HttpUrlDestinationConfigurationTypeDef",
    {
        "confirmationUrl": str,
    },
)

HttpUrlDestinationPropertiesTypeDef = TypedDict(
    "HttpUrlDestinationPropertiesTypeDef",
    {
        "confirmationUrl": NotRequired[str],
    },
)

HttpUrlDestinationSummaryTypeDef = TypedDict(
    "HttpUrlDestinationSummaryTypeDef",
    {
        "confirmationUrl": NotRequired[str],
    },
)

ImplicitDenyTypeDef = TypedDict(
    "ImplicitDenyTypeDef",
    {
        "policies": NotRequired[List["PolicyTypeDef"]],
    },
)

IotAnalyticsActionTypeDef = TypedDict(
    "IotAnalyticsActionTypeDef",
    {
        "channelArn": NotRequired[str],
        "channelName": NotRequired[str],
        "batchMode": NotRequired[bool],
        "roleArn": NotRequired[str],
    },
)

IotEventsActionTypeDef = TypedDict(
    "IotEventsActionTypeDef",
    {
        "inputName": str,
        "roleArn": str,
        "messageId": NotRequired[str],
        "batchMode": NotRequired[bool],
    },
)

IotSiteWiseActionTypeDef = TypedDict(
    "IotSiteWiseActionTypeDef",
    {
        "putAssetPropertyValueEntries": Sequence["PutAssetPropertyValueEntryTypeDef"],
        "roleArn": str,
    },
)

JobExecutionStatusDetailsTypeDef = TypedDict(
    "JobExecutionStatusDetailsTypeDef",
    {
        "detailsMap": NotRequired[Dict[str, str]],
    },
)

JobExecutionSummaryForJobTypeDef = TypedDict(
    "JobExecutionSummaryForJobTypeDef",
    {
        "thingArn": NotRequired[str],
        "jobExecutionSummary": NotRequired["JobExecutionSummaryTypeDef"],
    },
)

JobExecutionSummaryForThingTypeDef = TypedDict(
    "JobExecutionSummaryForThingTypeDef",
    {
        "jobId": NotRequired[str],
        "jobExecutionSummary": NotRequired["JobExecutionSummaryTypeDef"],
    },
)

JobExecutionSummaryTypeDef = TypedDict(
    "JobExecutionSummaryTypeDef",
    {
        "status": NotRequired[JobExecutionStatusType],
        "queuedAt": NotRequired[datetime],
        "startedAt": NotRequired[datetime],
        "lastUpdatedAt": NotRequired[datetime],
        "executionNumber": NotRequired[int],
        "retryAttempt": NotRequired[int],
    },
)

JobExecutionTypeDef = TypedDict(
    "JobExecutionTypeDef",
    {
        "jobId": NotRequired[str],
        "status": NotRequired[JobExecutionStatusType],
        "forceCanceled": NotRequired[bool],
        "statusDetails": NotRequired["JobExecutionStatusDetailsTypeDef"],
        "thingArn": NotRequired[str],
        "queuedAt": NotRequired[datetime],
        "startedAt": NotRequired[datetime],
        "lastUpdatedAt": NotRequired[datetime],
        "executionNumber": NotRequired[int],
        "versionNumber": NotRequired[int],
        "approximateSecondsBeforeTimedOut": NotRequired[int],
    },
)

JobExecutionsRetryConfigTypeDef = TypedDict(
    "JobExecutionsRetryConfigTypeDef",
    {
        "criteriaList": Sequence["RetryCriteriaTypeDef"],
    },
)

JobExecutionsRolloutConfigTypeDef = TypedDict(
    "JobExecutionsRolloutConfigTypeDef",
    {
        "maximumPerMinute": NotRequired[int],
        "exponentialRate": NotRequired["ExponentialRolloutRateTypeDef"],
    },
)

JobProcessDetailsTypeDef = TypedDict(
    "JobProcessDetailsTypeDef",
    {
        "processingTargets": NotRequired[List[str]],
        "numberOfCanceledThings": NotRequired[int],
        "numberOfSucceededThings": NotRequired[int],
        "numberOfFailedThings": NotRequired[int],
        "numberOfRejectedThings": NotRequired[int],
        "numberOfQueuedThings": NotRequired[int],
        "numberOfInProgressThings": NotRequired[int],
        "numberOfRemovedThings": NotRequired[int],
        "numberOfTimedOutThings": NotRequired[int],
    },
)

JobSummaryTypeDef = TypedDict(
    "JobSummaryTypeDef",
    {
        "jobArn": NotRequired[str],
        "jobId": NotRequired[str],
        "thingGroupId": NotRequired[str],
        "targetSelection": NotRequired[TargetSelectionType],
        "status": NotRequired[JobStatusType],
        "createdAt": NotRequired[datetime],
        "lastUpdatedAt": NotRequired[datetime],
        "completedAt": NotRequired[datetime],
    },
)

JobTemplateSummaryTypeDef = TypedDict(
    "JobTemplateSummaryTypeDef",
    {
        "jobTemplateArn": NotRequired[str],
        "jobTemplateId": NotRequired[str],
        "description": NotRequired[str],
        "createdAt": NotRequired[datetime],
    },
)

JobTypeDef = TypedDict(
    "JobTypeDef",
    {
        "jobArn": NotRequired[str],
        "jobId": NotRequired[str],
        "targetSelection": NotRequired[TargetSelectionType],
        "status": NotRequired[JobStatusType],
        "forceCanceled": NotRequired[bool],
        "reasonCode": NotRequired[str],
        "comment": NotRequired[str],
        "targets": NotRequired[List[str]],
        "description": NotRequired[str],
        "presignedUrlConfig": NotRequired["PresignedUrlConfigTypeDef"],
        "jobExecutionsRolloutConfig": NotRequired["JobExecutionsRolloutConfigTypeDef"],
        "abortConfig": NotRequired["AbortConfigTypeDef"],
        "createdAt": NotRequired[datetime],
        "lastUpdatedAt": NotRequired[datetime],
        "completedAt": NotRequired[datetime],
        "jobProcessDetails": NotRequired["JobProcessDetailsTypeDef"],
        "timeoutConfig": NotRequired["TimeoutConfigTypeDef"],
        "namespaceId": NotRequired[str],
        "jobTemplateArn": NotRequired[str],
        "jobExecutionsRetryConfig": NotRequired["JobExecutionsRetryConfigTypeDef"],
        "documentParameters": NotRequired[Dict[str, str]],
    },
)

KafkaActionTypeDef = TypedDict(
    "KafkaActionTypeDef",
    {
        "destinationArn": str,
        "topic": str,
        "clientProperties": Mapping[str, str],
        "key": NotRequired[str],
        "partition": NotRequired[str],
    },
)

KeyPairTypeDef = TypedDict(
    "KeyPairTypeDef",
    {
        "PublicKey": NotRequired[str],
        "PrivateKey": NotRequired[str],
    },
)

KinesisActionTypeDef = TypedDict(
    "KinesisActionTypeDef",
    {
        "roleArn": str,
        "streamName": str,
        "partitionKey": NotRequired[str],
    },
)

LambdaActionTypeDef = TypedDict(
    "LambdaActionTypeDef",
    {
        "functionArn": str,
    },
)

ListActiveViolationsRequestListActiveViolationsPaginateTypeDef = TypedDict(
    "ListActiveViolationsRequestListActiveViolationsPaginateTypeDef",
    {
        "thingName": NotRequired[str],
        "securityProfileName": NotRequired[str],
        "behaviorCriteriaType": NotRequired[BehaviorCriteriaTypeType],
        "listSuppressedAlerts": NotRequired[bool],
        "verificationState": NotRequired[VerificationStateType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListActiveViolationsRequestRequestTypeDef = TypedDict(
    "ListActiveViolationsRequestRequestTypeDef",
    {
        "thingName": NotRequired[str],
        "securityProfileName": NotRequired[str],
        "behaviorCriteriaType": NotRequired[BehaviorCriteriaTypeType],
        "listSuppressedAlerts": NotRequired[bool],
        "verificationState": NotRequired[VerificationStateType],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListActiveViolationsResponseTypeDef = TypedDict(
    "ListActiveViolationsResponseTypeDef",
    {
        "activeViolations": List["ActiveViolationTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListAttachedPoliciesRequestListAttachedPoliciesPaginateTypeDef = TypedDict(
    "ListAttachedPoliciesRequestListAttachedPoliciesPaginateTypeDef",
    {
        "target": str,
        "recursive": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListAttachedPoliciesRequestRequestTypeDef = TypedDict(
    "ListAttachedPoliciesRequestRequestTypeDef",
    {
        "target": str,
        "recursive": NotRequired[bool],
        "marker": NotRequired[str],
        "pageSize": NotRequired[int],
    },
)

ListAttachedPoliciesResponseTypeDef = TypedDict(
    "ListAttachedPoliciesResponseTypeDef",
    {
        "policies": List["PolicyTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListAuditFindingsRequestListAuditFindingsPaginateTypeDef = TypedDict(
    "ListAuditFindingsRequestListAuditFindingsPaginateTypeDef",
    {
        "taskId": NotRequired[str],
        "checkName": NotRequired[str],
        "resourceIdentifier": NotRequired["ResourceIdentifierTypeDef"],
        "startTime": NotRequired[Union[datetime, str]],
        "endTime": NotRequired[Union[datetime, str]],
        "listSuppressedFindings": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListAuditFindingsRequestRequestTypeDef = TypedDict(
    "ListAuditFindingsRequestRequestTypeDef",
    {
        "taskId": NotRequired[str],
        "checkName": NotRequired[str],
        "resourceIdentifier": NotRequired["ResourceIdentifierTypeDef"],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
        "startTime": NotRequired[Union[datetime, str]],
        "endTime": NotRequired[Union[datetime, str]],
        "listSuppressedFindings": NotRequired[bool],
    },
)

ListAuditFindingsResponseTypeDef = TypedDict(
    "ListAuditFindingsResponseTypeDef",
    {
        "findings": List["AuditFindingTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListAuditMitigationActionsExecutionsRequestListAuditMitigationActionsExecutionsPaginateTypeDef = TypedDict(
    "ListAuditMitigationActionsExecutionsRequestListAuditMitigationActionsExecutionsPaginateTypeDef",
    {
        "taskId": str,
        "findingId": str,
        "actionStatus": NotRequired[AuditMitigationActionsExecutionStatusType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListAuditMitigationActionsExecutionsRequestRequestTypeDef = TypedDict(
    "ListAuditMitigationActionsExecutionsRequestRequestTypeDef",
    {
        "taskId": str,
        "findingId": str,
        "actionStatus": NotRequired[AuditMitigationActionsExecutionStatusType],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListAuditMitigationActionsExecutionsResponseTypeDef = TypedDict(
    "ListAuditMitigationActionsExecutionsResponseTypeDef",
    {
        "actionsExecutions": List["AuditMitigationActionExecutionMetadataTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListAuditMitigationActionsTasksRequestListAuditMitigationActionsTasksPaginateTypeDef = TypedDict(
    "ListAuditMitigationActionsTasksRequestListAuditMitigationActionsTasksPaginateTypeDef",
    {
        "startTime": Union[datetime, str],
        "endTime": Union[datetime, str],
        "auditTaskId": NotRequired[str],
        "findingId": NotRequired[str],
        "taskStatus": NotRequired[AuditMitigationActionsTaskStatusType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListAuditMitigationActionsTasksRequestRequestTypeDef = TypedDict(
    "ListAuditMitigationActionsTasksRequestRequestTypeDef",
    {
        "startTime": Union[datetime, str],
        "endTime": Union[datetime, str],
        "auditTaskId": NotRequired[str],
        "findingId": NotRequired[str],
        "taskStatus": NotRequired[AuditMitigationActionsTaskStatusType],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListAuditMitigationActionsTasksResponseTypeDef = TypedDict(
    "ListAuditMitigationActionsTasksResponseTypeDef",
    {
        "tasks": List["AuditMitigationActionsTaskMetadataTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListAuditSuppressionsRequestListAuditSuppressionsPaginateTypeDef = TypedDict(
    "ListAuditSuppressionsRequestListAuditSuppressionsPaginateTypeDef",
    {
        "checkName": NotRequired[str],
        "resourceIdentifier": NotRequired["ResourceIdentifierTypeDef"],
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListAuditSuppressionsRequestRequestTypeDef = TypedDict(
    "ListAuditSuppressionsRequestRequestTypeDef",
    {
        "checkName": NotRequired[str],
        "resourceIdentifier": NotRequired["ResourceIdentifierTypeDef"],
        "ascendingOrder": NotRequired[bool],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListAuditSuppressionsResponseTypeDef = TypedDict(
    "ListAuditSuppressionsResponseTypeDef",
    {
        "suppressions": List["AuditSuppressionTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListAuditTasksRequestListAuditTasksPaginateTypeDef = TypedDict(
    "ListAuditTasksRequestListAuditTasksPaginateTypeDef",
    {
        "startTime": Union[datetime, str],
        "endTime": Union[datetime, str],
        "taskType": NotRequired[AuditTaskTypeType],
        "taskStatus": NotRequired[AuditTaskStatusType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListAuditTasksRequestRequestTypeDef = TypedDict(
    "ListAuditTasksRequestRequestTypeDef",
    {
        "startTime": Union[datetime, str],
        "endTime": Union[datetime, str],
        "taskType": NotRequired[AuditTaskTypeType],
        "taskStatus": NotRequired[AuditTaskStatusType],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListAuditTasksResponseTypeDef = TypedDict(
    "ListAuditTasksResponseTypeDef",
    {
        "tasks": List["AuditTaskMetadataTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListAuthorizersRequestListAuthorizersPaginateTypeDef = TypedDict(
    "ListAuthorizersRequestListAuthorizersPaginateTypeDef",
    {
        "ascendingOrder": NotRequired[bool],
        "status": NotRequired[AuthorizerStatusType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListAuthorizersRequestRequestTypeDef = TypedDict(
    "ListAuthorizersRequestRequestTypeDef",
    {
        "pageSize": NotRequired[int],
        "marker": NotRequired[str],
        "ascendingOrder": NotRequired[bool],
        "status": NotRequired[AuthorizerStatusType],
    },
)

ListAuthorizersResponseTypeDef = TypedDict(
    "ListAuthorizersResponseTypeDef",
    {
        "authorizers": List["AuthorizerSummaryTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListBillingGroupsRequestListBillingGroupsPaginateTypeDef = TypedDict(
    "ListBillingGroupsRequestListBillingGroupsPaginateTypeDef",
    {
        "namePrefixFilter": NotRequired[str],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListBillingGroupsRequestRequestTypeDef = TypedDict(
    "ListBillingGroupsRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "namePrefixFilter": NotRequired[str],
    },
)

ListBillingGroupsResponseTypeDef = TypedDict(
    "ListBillingGroupsResponseTypeDef",
    {
        "billingGroups": List["GroupNameAndArnTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListCACertificatesRequestListCACertificatesPaginateTypeDef = TypedDict(
    "ListCACertificatesRequestListCACertificatesPaginateTypeDef",
    {
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListCACertificatesRequestRequestTypeDef = TypedDict(
    "ListCACertificatesRequestRequestTypeDef",
    {
        "pageSize": NotRequired[int],
        "marker": NotRequired[str],
        "ascendingOrder": NotRequired[bool],
    },
)

ListCACertificatesResponseTypeDef = TypedDict(
    "ListCACertificatesResponseTypeDef",
    {
        "certificates": List["CACertificateTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListCertificatesByCARequestListCertificatesByCAPaginateTypeDef = TypedDict(
    "ListCertificatesByCARequestListCertificatesByCAPaginateTypeDef",
    {
        "caCertificateId": str,
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListCertificatesByCARequestRequestTypeDef = TypedDict(
    "ListCertificatesByCARequestRequestTypeDef",
    {
        "caCertificateId": str,
        "pageSize": NotRequired[int],
        "marker": NotRequired[str],
        "ascendingOrder": NotRequired[bool],
    },
)

ListCertificatesByCAResponseTypeDef = TypedDict(
    "ListCertificatesByCAResponseTypeDef",
    {
        "certificates": List["CertificateTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListCertificatesRequestListCertificatesPaginateTypeDef = TypedDict(
    "ListCertificatesRequestListCertificatesPaginateTypeDef",
    {
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListCertificatesRequestRequestTypeDef = TypedDict(
    "ListCertificatesRequestRequestTypeDef",
    {
        "pageSize": NotRequired[int],
        "marker": NotRequired[str],
        "ascendingOrder": NotRequired[bool],
    },
)

ListCertificatesResponseTypeDef = TypedDict(
    "ListCertificatesResponseTypeDef",
    {
        "certificates": List["CertificateTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListCustomMetricsRequestListCustomMetricsPaginateTypeDef = TypedDict(
    "ListCustomMetricsRequestListCustomMetricsPaginateTypeDef",
    {
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListCustomMetricsRequestRequestTypeDef = TypedDict(
    "ListCustomMetricsRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListCustomMetricsResponseTypeDef = TypedDict(
    "ListCustomMetricsResponseTypeDef",
    {
        "metricNames": List[str],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListDetectMitigationActionsExecutionsRequestListDetectMitigationActionsExecutionsPaginateTypeDef = TypedDict(
    "ListDetectMitigationActionsExecutionsRequestListDetectMitigationActionsExecutionsPaginateTypeDef",
    {
        "taskId": NotRequired[str],
        "violationId": NotRequired[str],
        "thingName": NotRequired[str],
        "startTime": NotRequired[Union[datetime, str]],
        "endTime": NotRequired[Union[datetime, str]],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListDetectMitigationActionsExecutionsRequestRequestTypeDef = TypedDict(
    "ListDetectMitigationActionsExecutionsRequestRequestTypeDef",
    {
        "taskId": NotRequired[str],
        "violationId": NotRequired[str],
        "thingName": NotRequired[str],
        "startTime": NotRequired[Union[datetime, str]],
        "endTime": NotRequired[Union[datetime, str]],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListDetectMitigationActionsExecutionsResponseTypeDef = TypedDict(
    "ListDetectMitigationActionsExecutionsResponseTypeDef",
    {
        "actionsExecutions": List["DetectMitigationActionExecutionTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListDetectMitigationActionsTasksRequestListDetectMitigationActionsTasksPaginateTypeDef = TypedDict(
    "ListDetectMitigationActionsTasksRequestListDetectMitigationActionsTasksPaginateTypeDef",
    {
        "startTime": Union[datetime, str],
        "endTime": Union[datetime, str],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListDetectMitigationActionsTasksRequestRequestTypeDef = TypedDict(
    "ListDetectMitigationActionsTasksRequestRequestTypeDef",
    {
        "startTime": Union[datetime, str],
        "endTime": Union[datetime, str],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListDetectMitigationActionsTasksResponseTypeDef = TypedDict(
    "ListDetectMitigationActionsTasksResponseTypeDef",
    {
        "tasks": List["DetectMitigationActionsTaskSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListDimensionsRequestListDimensionsPaginateTypeDef = TypedDict(
    "ListDimensionsRequestListDimensionsPaginateTypeDef",
    {
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListDimensionsRequestRequestTypeDef = TypedDict(
    "ListDimensionsRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListDimensionsResponseTypeDef = TypedDict(
    "ListDimensionsResponseTypeDef",
    {
        "dimensionNames": List[str],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListDomainConfigurationsRequestListDomainConfigurationsPaginateTypeDef = TypedDict(
    "ListDomainConfigurationsRequestListDomainConfigurationsPaginateTypeDef",
    {
        "serviceType": NotRequired[ServiceTypeType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListDomainConfigurationsRequestRequestTypeDef = TypedDict(
    "ListDomainConfigurationsRequestRequestTypeDef",
    {
        "marker": NotRequired[str],
        "pageSize": NotRequired[int],
        "serviceType": NotRequired[ServiceTypeType],
    },
)

ListDomainConfigurationsResponseTypeDef = TypedDict(
    "ListDomainConfigurationsResponseTypeDef",
    {
        "domainConfigurations": List["DomainConfigurationSummaryTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListFleetMetricsRequestListFleetMetricsPaginateTypeDef = TypedDict(
    "ListFleetMetricsRequestListFleetMetricsPaginateTypeDef",
    {
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListFleetMetricsRequestRequestTypeDef = TypedDict(
    "ListFleetMetricsRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListFleetMetricsResponseTypeDef = TypedDict(
    "ListFleetMetricsResponseTypeDef",
    {
        "fleetMetrics": List["FleetMetricNameAndArnTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListIndicesRequestListIndicesPaginateTypeDef = TypedDict(
    "ListIndicesRequestListIndicesPaginateTypeDef",
    {
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListIndicesRequestRequestTypeDef = TypedDict(
    "ListIndicesRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListIndicesResponseTypeDef = TypedDict(
    "ListIndicesResponseTypeDef",
    {
        "indexNames": List[str],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListJobExecutionsForJobRequestListJobExecutionsForJobPaginateTypeDef = TypedDict(
    "ListJobExecutionsForJobRequestListJobExecutionsForJobPaginateTypeDef",
    {
        "jobId": str,
        "status": NotRequired[JobExecutionStatusType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListJobExecutionsForJobRequestRequestTypeDef = TypedDict(
    "ListJobExecutionsForJobRequestRequestTypeDef",
    {
        "jobId": str,
        "status": NotRequired[JobExecutionStatusType],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListJobExecutionsForJobResponseTypeDef = TypedDict(
    "ListJobExecutionsForJobResponseTypeDef",
    {
        "executionSummaries": List["JobExecutionSummaryForJobTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListJobExecutionsForThingRequestListJobExecutionsForThingPaginateTypeDef = TypedDict(
    "ListJobExecutionsForThingRequestListJobExecutionsForThingPaginateTypeDef",
    {
        "thingName": str,
        "status": NotRequired[JobExecutionStatusType],
        "namespaceId": NotRequired[str],
        "jobId": NotRequired[str],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListJobExecutionsForThingRequestRequestTypeDef = TypedDict(
    "ListJobExecutionsForThingRequestRequestTypeDef",
    {
        "thingName": str,
        "status": NotRequired[JobExecutionStatusType],
        "namespaceId": NotRequired[str],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
        "jobId": NotRequired[str],
    },
)

ListJobExecutionsForThingResponseTypeDef = TypedDict(
    "ListJobExecutionsForThingResponseTypeDef",
    {
        "executionSummaries": List["JobExecutionSummaryForThingTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListJobTemplatesRequestListJobTemplatesPaginateTypeDef = TypedDict(
    "ListJobTemplatesRequestListJobTemplatesPaginateTypeDef",
    {
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListJobTemplatesRequestRequestTypeDef = TypedDict(
    "ListJobTemplatesRequestRequestTypeDef",
    {
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListJobTemplatesResponseTypeDef = TypedDict(
    "ListJobTemplatesResponseTypeDef",
    {
        "jobTemplates": List["JobTemplateSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListJobsRequestListJobsPaginateTypeDef = TypedDict(
    "ListJobsRequestListJobsPaginateTypeDef",
    {
        "status": NotRequired[JobStatusType],
        "targetSelection": NotRequired[TargetSelectionType],
        "thingGroupName": NotRequired[str],
        "thingGroupId": NotRequired[str],
        "namespaceId": NotRequired[str],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListJobsRequestRequestTypeDef = TypedDict(
    "ListJobsRequestRequestTypeDef",
    {
        "status": NotRequired[JobStatusType],
        "targetSelection": NotRequired[TargetSelectionType],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
        "thingGroupName": NotRequired[str],
        "thingGroupId": NotRequired[str],
        "namespaceId": NotRequired[str],
    },
)

ListJobsResponseTypeDef = TypedDict(
    "ListJobsResponseTypeDef",
    {
        "jobs": List["JobSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListManagedJobTemplatesRequestRequestTypeDef = TypedDict(
    "ListManagedJobTemplatesRequestRequestTypeDef",
    {
        "templateName": NotRequired[str],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListManagedJobTemplatesResponseTypeDef = TypedDict(
    "ListManagedJobTemplatesResponseTypeDef",
    {
        "managedJobTemplates": List["ManagedJobTemplateSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListMitigationActionsRequestListMitigationActionsPaginateTypeDef = TypedDict(
    "ListMitigationActionsRequestListMitigationActionsPaginateTypeDef",
    {
        "actionType": NotRequired[MitigationActionTypeType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListMitigationActionsRequestRequestTypeDef = TypedDict(
    "ListMitigationActionsRequestRequestTypeDef",
    {
        "actionType": NotRequired[MitigationActionTypeType],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListMitigationActionsResponseTypeDef = TypedDict(
    "ListMitigationActionsResponseTypeDef",
    {
        "actionIdentifiers": List["MitigationActionIdentifierTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListOTAUpdatesRequestListOTAUpdatesPaginateTypeDef = TypedDict(
    "ListOTAUpdatesRequestListOTAUpdatesPaginateTypeDef",
    {
        "otaUpdateStatus": NotRequired[OTAUpdateStatusType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListOTAUpdatesRequestRequestTypeDef = TypedDict(
    "ListOTAUpdatesRequestRequestTypeDef",
    {
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
        "otaUpdateStatus": NotRequired[OTAUpdateStatusType],
    },
)

ListOTAUpdatesResponseTypeDef = TypedDict(
    "ListOTAUpdatesResponseTypeDef",
    {
        "otaUpdates": List["OTAUpdateSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListOutgoingCertificatesRequestListOutgoingCertificatesPaginateTypeDef = TypedDict(
    "ListOutgoingCertificatesRequestListOutgoingCertificatesPaginateTypeDef",
    {
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListOutgoingCertificatesRequestRequestTypeDef = TypedDict(
    "ListOutgoingCertificatesRequestRequestTypeDef",
    {
        "pageSize": NotRequired[int],
        "marker": NotRequired[str],
        "ascendingOrder": NotRequired[bool],
    },
)

ListOutgoingCertificatesResponseTypeDef = TypedDict(
    "ListOutgoingCertificatesResponseTypeDef",
    {
        "outgoingCertificates": List["OutgoingCertificateTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListPoliciesRequestListPoliciesPaginateTypeDef = TypedDict(
    "ListPoliciesRequestListPoliciesPaginateTypeDef",
    {
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListPoliciesRequestRequestTypeDef = TypedDict(
    "ListPoliciesRequestRequestTypeDef",
    {
        "marker": NotRequired[str],
        "pageSize": NotRequired[int],
        "ascendingOrder": NotRequired[bool],
    },
)

ListPoliciesResponseTypeDef = TypedDict(
    "ListPoliciesResponseTypeDef",
    {
        "policies": List["PolicyTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListPolicyPrincipalsRequestListPolicyPrincipalsPaginateTypeDef = TypedDict(
    "ListPolicyPrincipalsRequestListPolicyPrincipalsPaginateTypeDef",
    {
        "policyName": str,
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListPolicyPrincipalsRequestRequestTypeDef = TypedDict(
    "ListPolicyPrincipalsRequestRequestTypeDef",
    {
        "policyName": str,
        "marker": NotRequired[str],
        "pageSize": NotRequired[int],
        "ascendingOrder": NotRequired[bool],
    },
)

ListPolicyPrincipalsResponseTypeDef = TypedDict(
    "ListPolicyPrincipalsResponseTypeDef",
    {
        "principals": List[str],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListPolicyVersionsRequestRequestTypeDef = TypedDict(
    "ListPolicyVersionsRequestRequestTypeDef",
    {
        "policyName": str,
    },
)

ListPolicyVersionsResponseTypeDef = TypedDict(
    "ListPolicyVersionsResponseTypeDef",
    {
        "policyVersions": List["PolicyVersionTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListPrincipalPoliciesRequestListPrincipalPoliciesPaginateTypeDef = TypedDict(
    "ListPrincipalPoliciesRequestListPrincipalPoliciesPaginateTypeDef",
    {
        "principal": str,
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListPrincipalPoliciesRequestRequestTypeDef = TypedDict(
    "ListPrincipalPoliciesRequestRequestTypeDef",
    {
        "principal": str,
        "marker": NotRequired[str],
        "pageSize": NotRequired[int],
        "ascendingOrder": NotRequired[bool],
    },
)

ListPrincipalPoliciesResponseTypeDef = TypedDict(
    "ListPrincipalPoliciesResponseTypeDef",
    {
        "policies": List["PolicyTypeDef"],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListPrincipalThingsRequestListPrincipalThingsPaginateTypeDef = TypedDict(
    "ListPrincipalThingsRequestListPrincipalThingsPaginateTypeDef",
    {
        "principal": str,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListPrincipalThingsRequestRequestTypeDef = TypedDict(
    "ListPrincipalThingsRequestRequestTypeDef",
    {
        "principal": str,
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListPrincipalThingsResponseTypeDef = TypedDict(
    "ListPrincipalThingsResponseTypeDef",
    {
        "things": List[str],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListProvisioningTemplateVersionsRequestListProvisioningTemplateVersionsPaginateTypeDef = TypedDict(
    "ListProvisioningTemplateVersionsRequestListProvisioningTemplateVersionsPaginateTypeDef",
    {
        "templateName": str,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListProvisioningTemplateVersionsRequestRequestTypeDef = TypedDict(
    "ListProvisioningTemplateVersionsRequestRequestTypeDef",
    {
        "templateName": str,
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListProvisioningTemplateVersionsResponseTypeDef = TypedDict(
    "ListProvisioningTemplateVersionsResponseTypeDef",
    {
        "versions": List["ProvisioningTemplateVersionSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListProvisioningTemplatesRequestListProvisioningTemplatesPaginateTypeDef = TypedDict(
    "ListProvisioningTemplatesRequestListProvisioningTemplatesPaginateTypeDef",
    {
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListProvisioningTemplatesRequestRequestTypeDef = TypedDict(
    "ListProvisioningTemplatesRequestRequestTypeDef",
    {
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListProvisioningTemplatesResponseTypeDef = TypedDict(
    "ListProvisioningTemplatesResponseTypeDef",
    {
        "templates": List["ProvisioningTemplateSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListRoleAliasesRequestListRoleAliasesPaginateTypeDef = TypedDict(
    "ListRoleAliasesRequestListRoleAliasesPaginateTypeDef",
    {
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListRoleAliasesRequestRequestTypeDef = TypedDict(
    "ListRoleAliasesRequestRequestTypeDef",
    {
        "pageSize": NotRequired[int],
        "marker": NotRequired[str],
        "ascendingOrder": NotRequired[bool],
    },
)

ListRoleAliasesResponseTypeDef = TypedDict(
    "ListRoleAliasesResponseTypeDef",
    {
        "roleAliases": List[str],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListScheduledAuditsRequestListScheduledAuditsPaginateTypeDef = TypedDict(
    "ListScheduledAuditsRequestListScheduledAuditsPaginateTypeDef",
    {
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListScheduledAuditsRequestRequestTypeDef = TypedDict(
    "ListScheduledAuditsRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListScheduledAuditsResponseTypeDef = TypedDict(
    "ListScheduledAuditsResponseTypeDef",
    {
        "scheduledAudits": List["ScheduledAuditMetadataTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListSecurityProfilesForTargetRequestListSecurityProfilesForTargetPaginateTypeDef = TypedDict(
    "ListSecurityProfilesForTargetRequestListSecurityProfilesForTargetPaginateTypeDef",
    {
        "securityProfileTargetArn": str,
        "recursive": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListSecurityProfilesForTargetRequestRequestTypeDef = TypedDict(
    "ListSecurityProfilesForTargetRequestRequestTypeDef",
    {
        "securityProfileTargetArn": str,
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "recursive": NotRequired[bool],
    },
)

ListSecurityProfilesForTargetResponseTypeDef = TypedDict(
    "ListSecurityProfilesForTargetResponseTypeDef",
    {
        "securityProfileTargetMappings": List["SecurityProfileTargetMappingTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListSecurityProfilesRequestListSecurityProfilesPaginateTypeDef = TypedDict(
    "ListSecurityProfilesRequestListSecurityProfilesPaginateTypeDef",
    {
        "dimensionName": NotRequired[str],
        "metricName": NotRequired[str],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListSecurityProfilesRequestRequestTypeDef = TypedDict(
    "ListSecurityProfilesRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "dimensionName": NotRequired[str],
        "metricName": NotRequired[str],
    },
)

ListSecurityProfilesResponseTypeDef = TypedDict(
    "ListSecurityProfilesResponseTypeDef",
    {
        "securityProfileIdentifiers": List["SecurityProfileIdentifierTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListStreamsRequestListStreamsPaginateTypeDef = TypedDict(
    "ListStreamsRequestListStreamsPaginateTypeDef",
    {
        "ascendingOrder": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListStreamsRequestRequestTypeDef = TypedDict(
    "ListStreamsRequestRequestTypeDef",
    {
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
        "ascendingOrder": NotRequired[bool],
    },
)

ListStreamsResponseTypeDef = TypedDict(
    "ListStreamsResponseTypeDef",
    {
        "streams": List["StreamSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListTagsForResourceRequestListTagsForResourcePaginateTypeDef = TypedDict(
    "ListTagsForResourceRequestListTagsForResourcePaginateTypeDef",
    {
        "resourceArn": str,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListTagsForResourceRequestRequestTypeDef = TypedDict(
    "ListTagsForResourceRequestRequestTypeDef",
    {
        "resourceArn": str,
        "nextToken": NotRequired[str],
    },
)

ListTagsForResourceResponseTypeDef = TypedDict(
    "ListTagsForResourceResponseTypeDef",
    {
        "tags": List["TagTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListTargetsForPolicyRequestListTargetsForPolicyPaginateTypeDef = TypedDict(
    "ListTargetsForPolicyRequestListTargetsForPolicyPaginateTypeDef",
    {
        "policyName": str,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListTargetsForPolicyRequestRequestTypeDef = TypedDict(
    "ListTargetsForPolicyRequestRequestTypeDef",
    {
        "policyName": str,
        "marker": NotRequired[str],
        "pageSize": NotRequired[int],
    },
)

ListTargetsForPolicyResponseTypeDef = TypedDict(
    "ListTargetsForPolicyResponseTypeDef",
    {
        "targets": List[str],
        "nextMarker": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListTargetsForSecurityProfileRequestListTargetsForSecurityProfilePaginateTypeDef = TypedDict(
    "ListTargetsForSecurityProfileRequestListTargetsForSecurityProfilePaginateTypeDef",
    {
        "securityProfileName": str,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListTargetsForSecurityProfileRequestRequestTypeDef = TypedDict(
    "ListTargetsForSecurityProfileRequestRequestTypeDef",
    {
        "securityProfileName": str,
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListTargetsForSecurityProfileResponseTypeDef = TypedDict(
    "ListTargetsForSecurityProfileResponseTypeDef",
    {
        "securityProfileTargets": List["SecurityProfileTargetTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingGroupsForThingRequestListThingGroupsForThingPaginateTypeDef = TypedDict(
    "ListThingGroupsForThingRequestListThingGroupsForThingPaginateTypeDef",
    {
        "thingName": str,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingGroupsForThingRequestRequestTypeDef = TypedDict(
    "ListThingGroupsForThingRequestRequestTypeDef",
    {
        "thingName": str,
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListThingGroupsForThingResponseTypeDef = TypedDict(
    "ListThingGroupsForThingResponseTypeDef",
    {
        "thingGroups": List["GroupNameAndArnTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingGroupsRequestListThingGroupsPaginateTypeDef = TypedDict(
    "ListThingGroupsRequestListThingGroupsPaginateTypeDef",
    {
        "parentGroup": NotRequired[str],
        "namePrefixFilter": NotRequired[str],
        "recursive": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingGroupsRequestRequestTypeDef = TypedDict(
    "ListThingGroupsRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "parentGroup": NotRequired[str],
        "namePrefixFilter": NotRequired[str],
        "recursive": NotRequired[bool],
    },
)

ListThingGroupsResponseTypeDef = TypedDict(
    "ListThingGroupsResponseTypeDef",
    {
        "thingGroups": List["GroupNameAndArnTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingPrincipalsRequestListThingPrincipalsPaginateTypeDef = TypedDict(
    "ListThingPrincipalsRequestListThingPrincipalsPaginateTypeDef",
    {
        "thingName": str,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingPrincipalsRequestRequestTypeDef = TypedDict(
    "ListThingPrincipalsRequestRequestTypeDef",
    {
        "thingName": str,
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListThingPrincipalsResponseTypeDef = TypedDict(
    "ListThingPrincipalsResponseTypeDef",
    {
        "principals": List[str],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingRegistrationTaskReportsRequestListThingRegistrationTaskReportsPaginateTypeDef = TypedDict(
    "ListThingRegistrationTaskReportsRequestListThingRegistrationTaskReportsPaginateTypeDef",
    {
        "taskId": str,
        "reportType": ReportTypeType,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingRegistrationTaskReportsRequestRequestTypeDef = TypedDict(
    "ListThingRegistrationTaskReportsRequestRequestTypeDef",
    {
        "taskId": str,
        "reportType": ReportTypeType,
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListThingRegistrationTaskReportsResponseTypeDef = TypedDict(
    "ListThingRegistrationTaskReportsResponseTypeDef",
    {
        "resourceLinks": List[str],
        "reportType": ReportTypeType,
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingRegistrationTasksRequestListThingRegistrationTasksPaginateTypeDef = TypedDict(
    "ListThingRegistrationTasksRequestListThingRegistrationTasksPaginateTypeDef",
    {
        "status": NotRequired[StatusType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingRegistrationTasksRequestRequestTypeDef = TypedDict(
    "ListThingRegistrationTasksRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "status": NotRequired[StatusType],
    },
)

ListThingRegistrationTasksResponseTypeDef = TypedDict(
    "ListThingRegistrationTasksResponseTypeDef",
    {
        "taskIds": List[str],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingTypesRequestListThingTypesPaginateTypeDef = TypedDict(
    "ListThingTypesRequestListThingTypesPaginateTypeDef",
    {
        "thingTypeName": NotRequired[str],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingTypesRequestRequestTypeDef = TypedDict(
    "ListThingTypesRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "thingTypeName": NotRequired[str],
    },
)

ListThingTypesResponseTypeDef = TypedDict(
    "ListThingTypesResponseTypeDef",
    {
        "thingTypes": List["ThingTypeDefinitionTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingsInBillingGroupRequestListThingsInBillingGroupPaginateTypeDef = TypedDict(
    "ListThingsInBillingGroupRequestListThingsInBillingGroupPaginateTypeDef",
    {
        "billingGroupName": str,
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingsInBillingGroupRequestRequestTypeDef = TypedDict(
    "ListThingsInBillingGroupRequestRequestTypeDef",
    {
        "billingGroupName": str,
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListThingsInBillingGroupResponseTypeDef = TypedDict(
    "ListThingsInBillingGroupResponseTypeDef",
    {
        "things": List[str],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingsInThingGroupRequestListThingsInThingGroupPaginateTypeDef = TypedDict(
    "ListThingsInThingGroupRequestListThingsInThingGroupPaginateTypeDef",
    {
        "thingGroupName": str,
        "recursive": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingsInThingGroupRequestRequestTypeDef = TypedDict(
    "ListThingsInThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": str,
        "recursive": NotRequired[bool],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListThingsInThingGroupResponseTypeDef = TypedDict(
    "ListThingsInThingGroupResponseTypeDef",
    {
        "things": List[str],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListThingsRequestListThingsPaginateTypeDef = TypedDict(
    "ListThingsRequestListThingsPaginateTypeDef",
    {
        "attributeName": NotRequired[str],
        "attributeValue": NotRequired[str],
        "thingTypeName": NotRequired[str],
        "usePrefixAttributeValue": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListThingsRequestRequestTypeDef = TypedDict(
    "ListThingsRequestRequestTypeDef",
    {
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "attributeName": NotRequired[str],
        "attributeValue": NotRequired[str],
        "thingTypeName": NotRequired[str],
        "usePrefixAttributeValue": NotRequired[bool],
    },
)

ListThingsResponseTypeDef = TypedDict(
    "ListThingsResponseTypeDef",
    {
        "things": List["ThingAttributeTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListTopicRuleDestinationsRequestListTopicRuleDestinationsPaginateTypeDef = TypedDict(
    "ListTopicRuleDestinationsRequestListTopicRuleDestinationsPaginateTypeDef",
    {
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListTopicRuleDestinationsRequestRequestTypeDef = TypedDict(
    "ListTopicRuleDestinationsRequestRequestTypeDef",
    {
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
    },
)

ListTopicRuleDestinationsResponseTypeDef = TypedDict(
    "ListTopicRuleDestinationsResponseTypeDef",
    {
        "destinationSummaries": List["TopicRuleDestinationSummaryTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListTopicRulesRequestListTopicRulesPaginateTypeDef = TypedDict(
    "ListTopicRulesRequestListTopicRulesPaginateTypeDef",
    {
        "topic": NotRequired[str],
        "ruleDisabled": NotRequired[bool],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListTopicRulesRequestRequestTypeDef = TypedDict(
    "ListTopicRulesRequestRequestTypeDef",
    {
        "topic": NotRequired[str],
        "maxResults": NotRequired[int],
        "nextToken": NotRequired[str],
        "ruleDisabled": NotRequired[bool],
    },
)

ListTopicRulesResponseTypeDef = TypedDict(
    "ListTopicRulesResponseTypeDef",
    {
        "rules": List["TopicRuleListItemTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListV2LoggingLevelsRequestListV2LoggingLevelsPaginateTypeDef = TypedDict(
    "ListV2LoggingLevelsRequestListV2LoggingLevelsPaginateTypeDef",
    {
        "targetType": NotRequired[LogTargetTypeType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListV2LoggingLevelsRequestRequestTypeDef = TypedDict(
    "ListV2LoggingLevelsRequestRequestTypeDef",
    {
        "targetType": NotRequired[LogTargetTypeType],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListV2LoggingLevelsResponseTypeDef = TypedDict(
    "ListV2LoggingLevelsResponseTypeDef",
    {
        "logTargetConfigurations": List["LogTargetConfigurationTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ListViolationEventsRequestListViolationEventsPaginateTypeDef = TypedDict(
    "ListViolationEventsRequestListViolationEventsPaginateTypeDef",
    {
        "startTime": Union[datetime, str],
        "endTime": Union[datetime, str],
        "thingName": NotRequired[str],
        "securityProfileName": NotRequired[str],
        "behaviorCriteriaType": NotRequired[BehaviorCriteriaTypeType],
        "listSuppressedAlerts": NotRequired[bool],
        "verificationState": NotRequired[VerificationStateType],
        "PaginationConfig": NotRequired["PaginatorConfigTypeDef"],
    },
)

ListViolationEventsRequestRequestTypeDef = TypedDict(
    "ListViolationEventsRequestRequestTypeDef",
    {
        "startTime": Union[datetime, str],
        "endTime": Union[datetime, str],
        "thingName": NotRequired[str],
        "securityProfileName": NotRequired[str],
        "behaviorCriteriaType": NotRequired[BehaviorCriteriaTypeType],
        "listSuppressedAlerts": NotRequired[bool],
        "verificationState": NotRequired[VerificationStateType],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
    },
)

ListViolationEventsResponseTypeDef = TypedDict(
    "ListViolationEventsResponseTypeDef",
    {
        "violationEvents": List["ViolationEventTypeDef"],
        "nextToken": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

LogTargetConfigurationTypeDef = TypedDict(
    "LogTargetConfigurationTypeDef",
    {
        "logTarget": NotRequired["LogTargetTypeDef"],
        "logLevel": NotRequired[LogLevelType],
    },
)

LogTargetTypeDef = TypedDict(
    "LogTargetTypeDef",
    {
        "targetType": LogTargetTypeType,
        "targetName": NotRequired[str],
    },
)

LoggingOptionsPayloadTypeDef = TypedDict(
    "LoggingOptionsPayloadTypeDef",
    {
        "roleArn": str,
        "logLevel": NotRequired[LogLevelType],
    },
)

MachineLearningDetectionConfigTypeDef = TypedDict(
    "MachineLearningDetectionConfigTypeDef",
    {
        "confidenceLevel": ConfidenceLevelType,
    },
)

ManagedJobTemplateSummaryTypeDef = TypedDict(
    "ManagedJobTemplateSummaryTypeDef",
    {
        "templateArn": NotRequired[str],
        "templateName": NotRequired[str],
        "description": NotRequired[str],
        "environments": NotRequired[List[str]],
        "templateVersion": NotRequired[str],
    },
)

MetricDimensionTypeDef = TypedDict(
    "MetricDimensionTypeDef",
    {
        "dimensionName": str,
        "operator": NotRequired[DimensionValueOperatorType],
    },
)

MetricToRetainTypeDef = TypedDict(
    "MetricToRetainTypeDef",
    {
        "metric": str,
        "metricDimension": NotRequired["MetricDimensionTypeDef"],
    },
)

MetricValueTypeDef = TypedDict(
    "MetricValueTypeDef",
    {
        "count": NotRequired[int],
        "cidrs": NotRequired[Sequence[str]],
        "ports": NotRequired[Sequence[int]],
        "number": NotRequired[float],
        "numbers": NotRequired[Sequence[float]],
        "strings": NotRequired[Sequence[str]],
    },
)

MitigationActionIdentifierTypeDef = TypedDict(
    "MitigationActionIdentifierTypeDef",
    {
        "actionName": NotRequired[str],
        "actionArn": NotRequired[str],
        "creationDate": NotRequired[datetime],
    },
)

MitigationActionParamsTypeDef = TypedDict(
    "MitigationActionParamsTypeDef",
    {
        "updateDeviceCertificateParams": NotRequired["UpdateDeviceCertificateParamsTypeDef"],
        "updateCACertificateParams": NotRequired["UpdateCACertificateParamsTypeDef"],
        "addThingsToThingGroupParams": NotRequired["AddThingsToThingGroupParamsTypeDef"],
        "replaceDefaultPolicyVersionParams": NotRequired[
            "ReplaceDefaultPolicyVersionParamsTypeDef"
        ],
        "enableIoTLoggingParams": NotRequired["EnableIoTLoggingParamsTypeDef"],
        "publishFindingToSnsParams": NotRequired["PublishFindingToSnsParamsTypeDef"],
    },
)

MitigationActionTypeDef = TypedDict(
    "MitigationActionTypeDef",
    {
        "name": NotRequired[str],
        "id": NotRequired[str],
        "roleArn": NotRequired[str],
        "actionParams": NotRequired["MitigationActionParamsTypeDef"],
    },
)

MqttContextTypeDef = TypedDict(
    "MqttContextTypeDef",
    {
        "username": NotRequired[str],
        "password": NotRequired[Union[bytes, IO[bytes], StreamingBody]],
        "clientId": NotRequired[str],
    },
)

NonCompliantResourceTypeDef = TypedDict(
    "NonCompliantResourceTypeDef",
    {
        "resourceType": NotRequired[ResourceTypeType],
        "resourceIdentifier": NotRequired["ResourceIdentifierTypeDef"],
        "additionalInfo": NotRequired[Dict[str, str]],
    },
)

OTAUpdateFileTypeDef = TypedDict(
    "OTAUpdateFileTypeDef",
    {
        "fileName": NotRequired[str],
        "fileType": NotRequired[int],
        "fileVersion": NotRequired[str],
        "fileLocation": NotRequired["FileLocationTypeDef"],
        "codeSigning": NotRequired["CodeSigningTypeDef"],
        "attributes": NotRequired[Mapping[str, str]],
    },
)

OTAUpdateInfoTypeDef = TypedDict(
    "OTAUpdateInfoTypeDef",
    {
        "otaUpdateId": NotRequired[str],
        "otaUpdateArn": NotRequired[str],
        "creationDate": NotRequired[datetime],
        "lastModifiedDate": NotRequired[datetime],
        "description": NotRequired[str],
        "targets": NotRequired[List[str]],
        "protocols": NotRequired[List[ProtocolType]],
        "awsJobExecutionsRolloutConfig": NotRequired["AwsJobExecutionsRolloutConfigTypeDef"],
        "awsJobPresignedUrlConfig": NotRequired["AwsJobPresignedUrlConfigTypeDef"],
        "targetSelection": NotRequired[TargetSelectionType],
        "otaUpdateFiles": NotRequired[List["OTAUpdateFileTypeDef"]],
        "otaUpdateStatus": NotRequired[OTAUpdateStatusType],
        "awsIotJobId": NotRequired[str],
        "awsIotJobArn": NotRequired[str],
        "errorInfo": NotRequired["ErrorInfoTypeDef"],
        "additionalParameters": NotRequired[Dict[str, str]],
    },
)

OTAUpdateSummaryTypeDef = TypedDict(
    "OTAUpdateSummaryTypeDef",
    {
        "otaUpdateId": NotRequired[str],
        "otaUpdateArn": NotRequired[str],
        "creationDate": NotRequired[datetime],
    },
)

OpenSearchActionTypeDef = TypedDict(
    "OpenSearchActionTypeDef",
    {
        "roleArn": str,
        "endpoint": str,
        "index": str,
        "type": str,
        "id": str,
    },
)

OutgoingCertificateTypeDef = TypedDict(
    "OutgoingCertificateTypeDef",
    {
        "certificateArn": NotRequired[str],
        "certificateId": NotRequired[str],
        "transferredTo": NotRequired[str],
        "transferDate": NotRequired[datetime],
        "transferMessage": NotRequired[str],
        "creationDate": NotRequired[datetime],
    },
)

PaginatorConfigTypeDef = TypedDict(
    "PaginatorConfigTypeDef",
    {
        "MaxItems": NotRequired[int],
        "PageSize": NotRequired[int],
        "StartingToken": NotRequired[str],
    },
)

PercentPairTypeDef = TypedDict(
    "PercentPairTypeDef",
    {
        "percent": NotRequired[float],
        "value": NotRequired[float],
    },
)

PolicyTypeDef = TypedDict(
    "PolicyTypeDef",
    {
        "policyName": NotRequired[str],
        "policyArn": NotRequired[str],
    },
)

PolicyVersionIdentifierTypeDef = TypedDict(
    "PolicyVersionIdentifierTypeDef",
    {
        "policyName": NotRequired[str],
        "policyVersionId": NotRequired[str],
    },
)

PolicyVersionTypeDef = TypedDict(
    "PolicyVersionTypeDef",
    {
        "versionId": NotRequired[str],
        "isDefaultVersion": NotRequired[bool],
        "createDate": NotRequired[datetime],
    },
)

PresignedUrlConfigTypeDef = TypedDict(
    "PresignedUrlConfigTypeDef",
    {
        "roleArn": NotRequired[str],
        "expiresInSec": NotRequired[int],
    },
)

ProvisioningHookTypeDef = TypedDict(
    "ProvisioningHookTypeDef",
    {
        "targetArn": str,
        "payloadVersion": NotRequired[str],
    },
)

ProvisioningTemplateSummaryTypeDef = TypedDict(
    "ProvisioningTemplateSummaryTypeDef",
    {
        "templateArn": NotRequired[str],
        "templateName": NotRequired[str],
        "description": NotRequired[str],
        "creationDate": NotRequired[datetime],
        "lastModifiedDate": NotRequired[datetime],
        "enabled": NotRequired[bool],
    },
)

ProvisioningTemplateVersionSummaryTypeDef = TypedDict(
    "ProvisioningTemplateVersionSummaryTypeDef",
    {
        "versionId": NotRequired[int],
        "creationDate": NotRequired[datetime],
        "isDefaultVersion": NotRequired[bool],
    },
)

PublishFindingToSnsParamsTypeDef = TypedDict(
    "PublishFindingToSnsParamsTypeDef",
    {
        "topicArn": str,
    },
)

PutAssetPropertyValueEntryTypeDef = TypedDict(
    "PutAssetPropertyValueEntryTypeDef",
    {
        "propertyValues": Sequence["AssetPropertyValueTypeDef"],
        "entryId": NotRequired[str],
        "assetId": NotRequired[str],
        "propertyId": NotRequired[str],
        "propertyAlias": NotRequired[str],
    },
)

PutItemInputTypeDef = TypedDict(
    "PutItemInputTypeDef",
    {
        "tableName": str,
    },
)

PutVerificationStateOnViolationRequestRequestTypeDef = TypedDict(
    "PutVerificationStateOnViolationRequestRequestTypeDef",
    {
        "violationId": str,
        "verificationState": VerificationStateType,
        "verificationStateDescription": NotRequired[str],
    },
)

RateIncreaseCriteriaTypeDef = TypedDict(
    "RateIncreaseCriteriaTypeDef",
    {
        "numberOfNotifiedThings": NotRequired[int],
        "numberOfSucceededThings": NotRequired[int],
    },
)

RegisterCACertificateRequestRequestTypeDef = TypedDict(
    "RegisterCACertificateRequestRequestTypeDef",
    {
        "caCertificate": str,
        "verificationCertificate": str,
        "setAsActive": NotRequired[bool],
        "allowAutoRegistration": NotRequired[bool],
        "registrationConfig": NotRequired["RegistrationConfigTypeDef"],
        "tags": NotRequired[Sequence["TagTypeDef"]],
    },
)

RegisterCACertificateResponseTypeDef = TypedDict(
    "RegisterCACertificateResponseTypeDef",
    {
        "certificateArn": str,
        "certificateId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

RegisterCertificateRequestRequestTypeDef = TypedDict(
    "RegisterCertificateRequestRequestTypeDef",
    {
        "certificatePem": str,
        "caCertificatePem": NotRequired[str],
        "setAsActive": NotRequired[bool],
        "status": NotRequired[CertificateStatusType],
    },
)

RegisterCertificateResponseTypeDef = TypedDict(
    "RegisterCertificateResponseTypeDef",
    {
        "certificateArn": str,
        "certificateId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

RegisterCertificateWithoutCARequestRequestTypeDef = TypedDict(
    "RegisterCertificateWithoutCARequestRequestTypeDef",
    {
        "certificatePem": str,
        "status": NotRequired[CertificateStatusType],
    },
)

RegisterCertificateWithoutCAResponseTypeDef = TypedDict(
    "RegisterCertificateWithoutCAResponseTypeDef",
    {
        "certificateArn": str,
        "certificateId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

RegisterThingRequestRequestTypeDef = TypedDict(
    "RegisterThingRequestRequestTypeDef",
    {
        "templateBody": str,
        "parameters": NotRequired[Mapping[str, str]],
    },
)

RegisterThingResponseTypeDef = TypedDict(
    "RegisterThingResponseTypeDef",
    {
        "certificatePem": str,
        "resourceArns": Dict[str, str],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

RegistrationConfigTypeDef = TypedDict(
    "RegistrationConfigTypeDef",
    {
        "templateBody": NotRequired[str],
        "roleArn": NotRequired[str],
    },
)

RejectCertificateTransferRequestRequestTypeDef = TypedDict(
    "RejectCertificateTransferRequestRequestTypeDef",
    {
        "certificateId": str,
        "rejectReason": NotRequired[str],
    },
)

RelatedResourceTypeDef = TypedDict(
    "RelatedResourceTypeDef",
    {
        "resourceType": NotRequired[ResourceTypeType],
        "resourceIdentifier": NotRequired["ResourceIdentifierTypeDef"],
        "additionalInfo": NotRequired[Dict[str, str]],
    },
)

RemoveThingFromBillingGroupRequestRequestTypeDef = TypedDict(
    "RemoveThingFromBillingGroupRequestRequestTypeDef",
    {
        "billingGroupName": NotRequired[str],
        "billingGroupArn": NotRequired[str],
        "thingName": NotRequired[str],
        "thingArn": NotRequired[str],
    },
)

RemoveThingFromThingGroupRequestRequestTypeDef = TypedDict(
    "RemoveThingFromThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": NotRequired[str],
        "thingGroupArn": NotRequired[str],
        "thingName": NotRequired[str],
        "thingArn": NotRequired[str],
    },
)

ReplaceDefaultPolicyVersionParamsTypeDef = TypedDict(
    "ReplaceDefaultPolicyVersionParamsTypeDef",
    {
        "templateName": Literal["BLANK_POLICY"],
    },
)

ReplaceTopicRuleRequestRequestTypeDef = TypedDict(
    "ReplaceTopicRuleRequestRequestTypeDef",
    {
        "ruleName": str,
        "topicRulePayload": "TopicRulePayloadTypeDef",
    },
)

RepublishActionTypeDef = TypedDict(
    "RepublishActionTypeDef",
    {
        "roleArn": str,
        "topic": str,
        "qos": NotRequired[int],
    },
)

ResourceIdentifierTypeDef = TypedDict(
    "ResourceIdentifierTypeDef",
    {
        "deviceCertificateId": NotRequired[str],
        "caCertificateId": NotRequired[str],
        "cognitoIdentityPoolId": NotRequired[str],
        "clientId": NotRequired[str],
        "policyVersionIdentifier": NotRequired["PolicyVersionIdentifierTypeDef"],
        "account": NotRequired[str],
        "iamRoleArn": NotRequired[str],
        "roleAliasArn": NotRequired[str],
    },
)

ResponseMetadataTypeDef = TypedDict(
    "ResponseMetadataTypeDef",
    {
        "RequestId": str,
        "HostId": str,
        "HTTPStatusCode": int,
        "HTTPHeaders": Dict[str, str],
        "RetryAttempts": int,
    },
)

RetryCriteriaTypeDef = TypedDict(
    "RetryCriteriaTypeDef",
    {
        "failureType": RetryableFailureTypeType,
        "numberOfRetries": int,
    },
)

RoleAliasDescriptionTypeDef = TypedDict(
    "RoleAliasDescriptionTypeDef",
    {
        "roleAlias": NotRequired[str],
        "roleAliasArn": NotRequired[str],
        "roleArn": NotRequired[str],
        "owner": NotRequired[str],
        "credentialDurationSeconds": NotRequired[int],
        "creationDate": NotRequired[datetime],
        "lastModifiedDate": NotRequired[datetime],
    },
)

S3ActionTypeDef = TypedDict(
    "S3ActionTypeDef",
    {
        "roleArn": str,
        "bucketName": str,
        "key": str,
        "cannedAcl": NotRequired[CannedAccessControlListType],
    },
)

S3DestinationTypeDef = TypedDict(
    "S3DestinationTypeDef",
    {
        "bucket": NotRequired[str],
        "prefix": NotRequired[str],
    },
)

S3LocationTypeDef = TypedDict(
    "S3LocationTypeDef",
    {
        "bucket": NotRequired[str],
        "key": NotRequired[str],
        "version": NotRequired[str],
    },
)

SalesforceActionTypeDef = TypedDict(
    "SalesforceActionTypeDef",
    {
        "token": str,
        "url": str,
    },
)

ScheduledAuditMetadataTypeDef = TypedDict(
    "ScheduledAuditMetadataTypeDef",
    {
        "scheduledAuditName": NotRequired[str],
        "scheduledAuditArn": NotRequired[str],
        "frequency": NotRequired[AuditFrequencyType],
        "dayOfMonth": NotRequired[str],
        "dayOfWeek": NotRequired[DayOfWeekType],
    },
)

SearchIndexRequestRequestTypeDef = TypedDict(
    "SearchIndexRequestRequestTypeDef",
    {
        "queryString": str,
        "indexName": NotRequired[str],
        "nextToken": NotRequired[str],
        "maxResults": NotRequired[int],
        "queryVersion": NotRequired[str],
    },
)

SearchIndexResponseTypeDef = TypedDict(
    "SearchIndexResponseTypeDef",
    {
        "nextToken": str,
        "things": List["ThingDocumentTypeDef"],
        "thingGroups": List["ThingGroupDocumentTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

SecurityProfileIdentifierTypeDef = TypedDict(
    "SecurityProfileIdentifierTypeDef",
    {
        "name": str,
        "arn": str,
    },
)

SecurityProfileTargetMappingTypeDef = TypedDict(
    "SecurityProfileTargetMappingTypeDef",
    {
        "securityProfileIdentifier": NotRequired["SecurityProfileIdentifierTypeDef"],
        "target": NotRequired["SecurityProfileTargetTypeDef"],
    },
)

SecurityProfileTargetTypeDef = TypedDict(
    "SecurityProfileTargetTypeDef",
    {
        "arn": str,
    },
)

ServerCertificateSummaryTypeDef = TypedDict(
    "ServerCertificateSummaryTypeDef",
    {
        "serverCertificateArn": NotRequired[str],
        "serverCertificateStatus": NotRequired[ServerCertificateStatusType],
        "serverCertificateStatusDetail": NotRequired[str],
    },
)

SetDefaultAuthorizerRequestRequestTypeDef = TypedDict(
    "SetDefaultAuthorizerRequestRequestTypeDef",
    {
        "authorizerName": str,
    },
)

SetDefaultAuthorizerResponseTypeDef = TypedDict(
    "SetDefaultAuthorizerResponseTypeDef",
    {
        "authorizerName": str,
        "authorizerArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

SetDefaultPolicyVersionRequestRequestTypeDef = TypedDict(
    "SetDefaultPolicyVersionRequestRequestTypeDef",
    {
        "policyName": str,
        "policyVersionId": str,
    },
)

SetLoggingOptionsRequestRequestTypeDef = TypedDict(
    "SetLoggingOptionsRequestRequestTypeDef",
    {
        "loggingOptionsPayload": "LoggingOptionsPayloadTypeDef",
    },
)

SetV2LoggingLevelRequestRequestTypeDef = TypedDict(
    "SetV2LoggingLevelRequestRequestTypeDef",
    {
        "logTarget": "LogTargetTypeDef",
        "logLevel": LogLevelType,
    },
)

SetV2LoggingOptionsRequestRequestTypeDef = TypedDict(
    "SetV2LoggingOptionsRequestRequestTypeDef",
    {
        "roleArn": NotRequired[str],
        "defaultLogLevel": NotRequired[LogLevelType],
        "disableAllLogs": NotRequired[bool],
    },
)

SigV4AuthorizationTypeDef = TypedDict(
    "SigV4AuthorizationTypeDef",
    {
        "signingRegion": str,
        "serviceName": str,
        "roleArn": str,
    },
)

SigningProfileParameterTypeDef = TypedDict(
    "SigningProfileParameterTypeDef",
    {
        "certificateArn": NotRequired[str],
        "platform": NotRequired[str],
        "certificatePathOnDevice": NotRequired[str],
    },
)

SnsActionTypeDef = TypedDict(
    "SnsActionTypeDef",
    {
        "targetArn": str,
        "roleArn": str,
        "messageFormat": NotRequired[MessageFormatType],
    },
)

SqsActionTypeDef = TypedDict(
    "SqsActionTypeDef",
    {
        "roleArn": str,
        "queueUrl": str,
        "useBase64": NotRequired[bool],
    },
)

StartAuditMitigationActionsTaskRequestRequestTypeDef = TypedDict(
    "StartAuditMitigationActionsTaskRequestRequestTypeDef",
    {
        "taskId": str,
        "target": "AuditMitigationActionsTaskTargetTypeDef",
        "auditCheckToActionsMapping": Mapping[str, Sequence[str]],
        "clientRequestToken": str,
    },
)

StartAuditMitigationActionsTaskResponseTypeDef = TypedDict(
    "StartAuditMitigationActionsTaskResponseTypeDef",
    {
        "taskId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

StartDetectMitigationActionsTaskRequestRequestTypeDef = TypedDict(
    "StartDetectMitigationActionsTaskRequestRequestTypeDef",
    {
        "taskId": str,
        "target": "DetectMitigationActionsTaskTargetTypeDef",
        "actions": Sequence[str],
        "clientRequestToken": str,
        "violationEventOccurrenceRange": NotRequired["ViolationEventOccurrenceRangeTypeDef"],
        "includeOnlyActiveViolations": NotRequired[bool],
        "includeSuppressedAlerts": NotRequired[bool],
    },
)

StartDetectMitigationActionsTaskResponseTypeDef = TypedDict(
    "StartDetectMitigationActionsTaskResponseTypeDef",
    {
        "taskId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

StartOnDemandAuditTaskRequestRequestTypeDef = TypedDict(
    "StartOnDemandAuditTaskRequestRequestTypeDef",
    {
        "targetCheckNames": Sequence[str],
    },
)

StartOnDemandAuditTaskResponseTypeDef = TypedDict(
    "StartOnDemandAuditTaskResponseTypeDef",
    {
        "taskId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

StartSigningJobParameterTypeDef = TypedDict(
    "StartSigningJobParameterTypeDef",
    {
        "signingProfileParameter": NotRequired["SigningProfileParameterTypeDef"],
        "signingProfileName": NotRequired[str],
        "destination": NotRequired["DestinationTypeDef"],
    },
)

StartThingRegistrationTaskRequestRequestTypeDef = TypedDict(
    "StartThingRegistrationTaskRequestRequestTypeDef",
    {
        "templateBody": str,
        "inputFileBucket": str,
        "inputFileKey": str,
        "roleArn": str,
    },
)

StartThingRegistrationTaskResponseTypeDef = TypedDict(
    "StartThingRegistrationTaskResponseTypeDef",
    {
        "taskId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

StatisticalThresholdTypeDef = TypedDict(
    "StatisticalThresholdTypeDef",
    {
        "statistic": NotRequired[str],
    },
)

StatisticsTypeDef = TypedDict(
    "StatisticsTypeDef",
    {
        "count": NotRequired[int],
        "average": NotRequired[float],
        "sum": NotRequired[float],
        "minimum": NotRequired[float],
        "maximum": NotRequired[float],
        "sumOfSquares": NotRequired[float],
        "variance": NotRequired[float],
        "stdDeviation": NotRequired[float],
    },
)

StepFunctionsActionTypeDef = TypedDict(
    "StepFunctionsActionTypeDef",
    {
        "stateMachineName": str,
        "roleArn": str,
        "executionNamePrefix": NotRequired[str],
    },
)

StopThingRegistrationTaskRequestRequestTypeDef = TypedDict(
    "StopThingRegistrationTaskRequestRequestTypeDef",
    {
        "taskId": str,
    },
)

StreamFileTypeDef = TypedDict(
    "StreamFileTypeDef",
    {
        "fileId": NotRequired[int],
        "s3Location": NotRequired["S3LocationTypeDef"],
    },
)

StreamInfoTypeDef = TypedDict(
    "StreamInfoTypeDef",
    {
        "streamId": NotRequired[str],
        "streamArn": NotRequired[str],
        "streamVersion": NotRequired[int],
        "description": NotRequired[str],
        "files": NotRequired[List["StreamFileTypeDef"]],
        "createdAt": NotRequired[datetime],
        "lastUpdatedAt": NotRequired[datetime],
        "roleArn": NotRequired[str],
    },
)

StreamSummaryTypeDef = TypedDict(
    "StreamSummaryTypeDef",
    {
        "streamId": NotRequired[str],
        "streamArn": NotRequired[str],
        "streamVersion": NotRequired[int],
        "description": NotRequired[str],
    },
)

StreamTypeDef = TypedDict(
    "StreamTypeDef",
    {
        "streamId": NotRequired[str],
        "fileId": NotRequired[int],
    },
)

TagResourceRequestRequestTypeDef = TypedDict(
    "TagResourceRequestRequestTypeDef",
    {
        "resourceArn": str,
        "tags": Sequence["TagTypeDef"],
    },
)

TagTypeDef = TypedDict(
    "TagTypeDef",
    {
        "Key": str,
        "Value": NotRequired[str],
    },
)

TaskStatisticsForAuditCheckTypeDef = TypedDict(
    "TaskStatisticsForAuditCheckTypeDef",
    {
        "totalFindingsCount": NotRequired[int],
        "failedFindingsCount": NotRequired[int],
        "succeededFindingsCount": NotRequired[int],
        "skippedFindingsCount": NotRequired[int],
        "canceledFindingsCount": NotRequired[int],
    },
)

TaskStatisticsTypeDef = TypedDict(
    "TaskStatisticsTypeDef",
    {
        "totalChecks": NotRequired[int],
        "inProgressChecks": NotRequired[int],
        "waitingForDataCollectionChecks": NotRequired[int],
        "compliantChecks": NotRequired[int],
        "nonCompliantChecks": NotRequired[int],
        "failedChecks": NotRequired[int],
        "canceledChecks": NotRequired[int],
    },
)

TermsAggregationTypeDef = TypedDict(
    "TermsAggregationTypeDef",
    {
        "maxBuckets": NotRequired[int],
    },
)

TestAuthorizationRequestRequestTypeDef = TypedDict(
    "TestAuthorizationRequestRequestTypeDef",
    {
        "authInfos": Sequence["AuthInfoTypeDef"],
        "principal": NotRequired[str],
        "cognitoIdentityPoolId": NotRequired[str],
        "clientId": NotRequired[str],
        "policyNamesToAdd": NotRequired[Sequence[str]],
        "policyNamesToSkip": NotRequired[Sequence[str]],
    },
)

TestAuthorizationResponseTypeDef = TypedDict(
    "TestAuthorizationResponseTypeDef",
    {
        "authResults": List["AuthResultTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

TestInvokeAuthorizerRequestRequestTypeDef = TypedDict(
    "TestInvokeAuthorizerRequestRequestTypeDef",
    {
        "authorizerName": str,
        "token": NotRequired[str],
        "tokenSignature": NotRequired[str],
        "httpContext": NotRequired["HttpContextTypeDef"],
        "mqttContext": NotRequired["MqttContextTypeDef"],
        "tlsContext": NotRequired["TlsContextTypeDef"],
    },
)

TestInvokeAuthorizerResponseTypeDef = TypedDict(
    "TestInvokeAuthorizerResponseTypeDef",
    {
        "isAuthenticated": bool,
        "principalId": str,
        "policyDocuments": List[str],
        "refreshAfterInSeconds": int,
        "disconnectAfterInSeconds": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ThingAttributeTypeDef = TypedDict(
    "ThingAttributeTypeDef",
    {
        "thingName": NotRequired[str],
        "thingTypeName": NotRequired[str],
        "thingArn": NotRequired[str],
        "attributes": NotRequired[Dict[str, str]],
        "version": NotRequired[int],
    },
)

ThingConnectivityTypeDef = TypedDict(
    "ThingConnectivityTypeDef",
    {
        "connected": NotRequired[bool],
        "timestamp": NotRequired[int],
        "disconnectReason": NotRequired[str],
    },
)

ThingDocumentTypeDef = TypedDict(
    "ThingDocumentTypeDef",
    {
        "thingName": NotRequired[str],
        "thingId": NotRequired[str],
        "thingTypeName": NotRequired[str],
        "thingGroupNames": NotRequired[List[str]],
        "attributes": NotRequired[Dict[str, str]],
        "shadow": NotRequired[str],
        "deviceDefender": NotRequired[str],
        "connectivity": NotRequired["ThingConnectivityTypeDef"],
    },
)

ThingGroupDocumentTypeDef = TypedDict(
    "ThingGroupDocumentTypeDef",
    {
        "thingGroupName": NotRequired[str],
        "thingGroupId": NotRequired[str],
        "thingGroupDescription": NotRequired[str],
        "attributes": NotRequired[Dict[str, str]],
        "parentGroupNames": NotRequired[List[str]],
    },
)

ThingGroupIndexingConfigurationTypeDef = TypedDict(
    "ThingGroupIndexingConfigurationTypeDef",
    {
        "thingGroupIndexingMode": ThingGroupIndexingModeType,
        "managedFields": NotRequired[List["FieldTypeDef"]],
        "customFields": NotRequired[List["FieldTypeDef"]],
    },
)

ThingGroupMetadataTypeDef = TypedDict(
    "ThingGroupMetadataTypeDef",
    {
        "parentGroupName": NotRequired[str],
        "rootToParentThingGroups": NotRequired[List["GroupNameAndArnTypeDef"]],
        "creationDate": NotRequired[datetime],
    },
)

ThingGroupPropertiesTypeDef = TypedDict(
    "ThingGroupPropertiesTypeDef",
    {
        "thingGroupDescription": NotRequired[str],
        "attributePayload": NotRequired["AttributePayloadTypeDef"],
    },
)

ThingIndexingConfigurationTypeDef = TypedDict(
    "ThingIndexingConfigurationTypeDef",
    {
        "thingIndexingMode": ThingIndexingModeType,
        "thingConnectivityIndexingMode": NotRequired[ThingConnectivityIndexingModeType],
        "deviceDefenderIndexingMode": NotRequired[DeviceDefenderIndexingModeType],
        "namedShadowIndexingMode": NotRequired[NamedShadowIndexingModeType],
        "managedFields": NotRequired[List["FieldTypeDef"]],
        "customFields": NotRequired[List["FieldTypeDef"]],
    },
)

ThingTypeDefinitionTypeDef = TypedDict(
    "ThingTypeDefinitionTypeDef",
    {
        "thingTypeName": NotRequired[str],
        "thingTypeArn": NotRequired[str],
        "thingTypeProperties": NotRequired["ThingTypePropertiesTypeDef"],
        "thingTypeMetadata": NotRequired["ThingTypeMetadataTypeDef"],
    },
)

ThingTypeMetadataTypeDef = TypedDict(
    "ThingTypeMetadataTypeDef",
    {
        "deprecated": NotRequired[bool],
        "deprecationDate": NotRequired[datetime],
        "creationDate": NotRequired[datetime],
    },
)

ThingTypePropertiesTypeDef = TypedDict(
    "ThingTypePropertiesTypeDef",
    {
        "thingTypeDescription": NotRequired[str],
        "searchableAttributes": NotRequired[Sequence[str]],
    },
)

TimeoutConfigTypeDef = TypedDict(
    "TimeoutConfigTypeDef",
    {
        "inProgressTimeoutInMinutes": NotRequired[int],
    },
)

TimestreamActionTypeDef = TypedDict(
    "TimestreamActionTypeDef",
    {
        "roleArn": str,
        "databaseName": str,
        "tableName": str,
        "dimensions": Sequence["TimestreamDimensionTypeDef"],
        "timestamp": NotRequired["TimestreamTimestampTypeDef"],
    },
)

TimestreamDimensionTypeDef = TypedDict(
    "TimestreamDimensionTypeDef",
    {
        "name": str,
        "value": str,
    },
)

TimestreamTimestampTypeDef = TypedDict(
    "TimestreamTimestampTypeDef",
    {
        "value": str,
        "unit": str,
    },
)

TlsContextTypeDef = TypedDict(
    "TlsContextTypeDef",
    {
        "serverName": NotRequired[str],
    },
)

TopicRuleDestinationConfigurationTypeDef = TypedDict(
    "TopicRuleDestinationConfigurationTypeDef",
    {
        "httpUrlConfiguration": NotRequired["HttpUrlDestinationConfigurationTypeDef"],
        "vpcConfiguration": NotRequired["VpcDestinationConfigurationTypeDef"],
    },
)

TopicRuleDestinationSummaryTypeDef = TypedDict(
    "TopicRuleDestinationSummaryTypeDef",
    {
        "arn": NotRequired[str],
        "status": NotRequired[TopicRuleDestinationStatusType],
        "createdAt": NotRequired[datetime],
        "lastUpdatedAt": NotRequired[datetime],
        "statusReason": NotRequired[str],
        "httpUrlSummary": NotRequired["HttpUrlDestinationSummaryTypeDef"],
        "vpcDestinationSummary": NotRequired["VpcDestinationSummaryTypeDef"],
    },
)

TopicRuleDestinationTypeDef = TypedDict(
    "TopicRuleDestinationTypeDef",
    {
        "arn": NotRequired[str],
        "status": NotRequired[TopicRuleDestinationStatusType],
        "createdAt": NotRequired[datetime],
        "lastUpdatedAt": NotRequired[datetime],
        "statusReason": NotRequired[str],
        "httpUrlProperties": NotRequired["HttpUrlDestinationPropertiesTypeDef"],
        "vpcProperties": NotRequired["VpcDestinationPropertiesTypeDef"],
    },
)

TopicRuleListItemTypeDef = TypedDict(
    "TopicRuleListItemTypeDef",
    {
        "ruleArn": NotRequired[str],
        "ruleName": NotRequired[str],
        "topicPattern": NotRequired[str],
        "createdAt": NotRequired[datetime],
        "ruleDisabled": NotRequired[bool],
    },
)

TopicRulePayloadTypeDef = TypedDict(
    "TopicRulePayloadTypeDef",
    {
        "sql": str,
        "actions": Sequence["ActionTypeDef"],
        "description": NotRequired[str],
        "ruleDisabled": NotRequired[bool],
        "awsIotSqlVersion": NotRequired[str],
        "errorAction": NotRequired["ActionTypeDef"],
    },
)

TopicRuleTypeDef = TypedDict(
    "TopicRuleTypeDef",
    {
        "ruleName": NotRequired[str],
        "sql": NotRequired[str],
        "description": NotRequired[str],
        "createdAt": NotRequired[datetime],
        "actions": NotRequired[List["ActionTypeDef"]],
        "ruleDisabled": NotRequired[bool],
        "awsIotSqlVersion": NotRequired[str],
        "errorAction": NotRequired["ActionTypeDef"],
    },
)

TransferCertificateRequestRequestTypeDef = TypedDict(
    "TransferCertificateRequestRequestTypeDef",
    {
        "certificateId": str,
        "targetAwsAccount": str,
        "transferMessage": NotRequired[str],
    },
)

TransferCertificateResponseTypeDef = TypedDict(
    "TransferCertificateResponseTypeDef",
    {
        "transferredCertificateArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

TransferDataTypeDef = TypedDict(
    "TransferDataTypeDef",
    {
        "transferMessage": NotRequired[str],
        "rejectReason": NotRequired[str],
        "transferDate": NotRequired[datetime],
        "acceptDate": NotRequired[datetime],
        "rejectDate": NotRequired[datetime],
    },
)

UntagResourceRequestRequestTypeDef = TypedDict(
    "UntagResourceRequestRequestTypeDef",
    {
        "resourceArn": str,
        "tagKeys": Sequence[str],
    },
)

UpdateAccountAuditConfigurationRequestRequestTypeDef = TypedDict(
    "UpdateAccountAuditConfigurationRequestRequestTypeDef",
    {
        "roleArn": NotRequired[str],
        "auditNotificationTargetConfigurations": NotRequired[
            Mapping[Literal["SNS"], "AuditNotificationTargetTypeDef"]
        ],
        "auditCheckConfigurations": NotRequired[Mapping[str, "AuditCheckConfigurationTypeDef"]],
    },
)

UpdateAuditSuppressionRequestRequestTypeDef = TypedDict(
    "UpdateAuditSuppressionRequestRequestTypeDef",
    {
        "checkName": str,
        "resourceIdentifier": "ResourceIdentifierTypeDef",
        "expirationDate": NotRequired[Union[datetime, str]],
        "suppressIndefinitely": NotRequired[bool],
        "description": NotRequired[str],
    },
)

UpdateAuthorizerRequestRequestTypeDef = TypedDict(
    "UpdateAuthorizerRequestRequestTypeDef",
    {
        "authorizerName": str,
        "authorizerFunctionArn": NotRequired[str],
        "tokenKeyName": NotRequired[str],
        "tokenSigningPublicKeys": NotRequired[Mapping[str, str]],
        "status": NotRequired[AuthorizerStatusType],
        "enableCachingForHttp": NotRequired[bool],
    },
)

UpdateAuthorizerResponseTypeDef = TypedDict(
    "UpdateAuthorizerResponseTypeDef",
    {
        "authorizerName": str,
        "authorizerArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateBillingGroupRequestRequestTypeDef = TypedDict(
    "UpdateBillingGroupRequestRequestTypeDef",
    {
        "billingGroupName": str,
        "billingGroupProperties": "BillingGroupPropertiesTypeDef",
        "expectedVersion": NotRequired[int],
    },
)

UpdateBillingGroupResponseTypeDef = TypedDict(
    "UpdateBillingGroupResponseTypeDef",
    {
        "version": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateCACertificateParamsTypeDef = TypedDict(
    "UpdateCACertificateParamsTypeDef",
    {
        "action": Literal["DEACTIVATE"],
    },
)

UpdateCACertificateRequestRequestTypeDef = TypedDict(
    "UpdateCACertificateRequestRequestTypeDef",
    {
        "certificateId": str,
        "newStatus": NotRequired[CACertificateStatusType],
        "newAutoRegistrationStatus": NotRequired[AutoRegistrationStatusType],
        "registrationConfig": NotRequired["RegistrationConfigTypeDef"],
        "removeAutoRegistration": NotRequired[bool],
    },
)

UpdateCertificateRequestRequestTypeDef = TypedDict(
    "UpdateCertificateRequestRequestTypeDef",
    {
        "certificateId": str,
        "newStatus": CertificateStatusType,
    },
)

UpdateCustomMetricRequestRequestTypeDef = TypedDict(
    "UpdateCustomMetricRequestRequestTypeDef",
    {
        "metricName": str,
        "displayName": str,
    },
)

UpdateCustomMetricResponseTypeDef = TypedDict(
    "UpdateCustomMetricResponseTypeDef",
    {
        "metricName": str,
        "metricArn": str,
        "metricType": CustomMetricTypeType,
        "displayName": str,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateDeviceCertificateParamsTypeDef = TypedDict(
    "UpdateDeviceCertificateParamsTypeDef",
    {
        "action": Literal["DEACTIVATE"],
    },
)

UpdateDimensionRequestRequestTypeDef = TypedDict(
    "UpdateDimensionRequestRequestTypeDef",
    {
        "name": str,
        "stringValues": Sequence[str],
    },
)

UpdateDimensionResponseTypeDef = TypedDict(
    "UpdateDimensionResponseTypeDef",
    {
        "name": str,
        "arn": str,
        "type": Literal["TOPIC_FILTER"],
        "stringValues": List[str],
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateDomainConfigurationRequestRequestTypeDef = TypedDict(
    "UpdateDomainConfigurationRequestRequestTypeDef",
    {
        "domainConfigurationName": str,
        "authorizerConfig": NotRequired["AuthorizerConfigTypeDef"],
        "domainConfigurationStatus": NotRequired[DomainConfigurationStatusType],
        "removeAuthorizerConfig": NotRequired[bool],
    },
)

UpdateDomainConfigurationResponseTypeDef = TypedDict(
    "UpdateDomainConfigurationResponseTypeDef",
    {
        "domainConfigurationName": str,
        "domainConfigurationArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateDynamicThingGroupRequestRequestTypeDef = TypedDict(
    "UpdateDynamicThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": str,
        "thingGroupProperties": "ThingGroupPropertiesTypeDef",
        "expectedVersion": NotRequired[int],
        "indexName": NotRequired[str],
        "queryString": NotRequired[str],
        "queryVersion": NotRequired[str],
    },
)

UpdateDynamicThingGroupResponseTypeDef = TypedDict(
    "UpdateDynamicThingGroupResponseTypeDef",
    {
        "version": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateEventConfigurationsRequestRequestTypeDef = TypedDict(
    "UpdateEventConfigurationsRequestRequestTypeDef",
    {
        "eventConfigurations": NotRequired[Mapping[EventTypeType, "ConfigurationTypeDef"]],
    },
)

UpdateFleetMetricRequestRequestTypeDef = TypedDict(
    "UpdateFleetMetricRequestRequestTypeDef",
    {
        "metricName": str,
        "indexName": str,
        "queryString": NotRequired[str],
        "aggregationType": NotRequired["AggregationTypeTypeDef"],
        "period": NotRequired[int],
        "aggregationField": NotRequired[str],
        "description": NotRequired[str],
        "queryVersion": NotRequired[str],
        "unit": NotRequired[FleetMetricUnitType],
        "expectedVersion": NotRequired[int],
    },
)

UpdateIndexingConfigurationRequestRequestTypeDef = TypedDict(
    "UpdateIndexingConfigurationRequestRequestTypeDef",
    {
        "thingIndexingConfiguration": NotRequired["ThingIndexingConfigurationTypeDef"],
        "thingGroupIndexingConfiguration": NotRequired["ThingGroupIndexingConfigurationTypeDef"],
    },
)

UpdateJobRequestRequestTypeDef = TypedDict(
    "UpdateJobRequestRequestTypeDef",
    {
        "jobId": str,
        "description": NotRequired[str],
        "presignedUrlConfig": NotRequired["PresignedUrlConfigTypeDef"],
        "jobExecutionsRolloutConfig": NotRequired["JobExecutionsRolloutConfigTypeDef"],
        "abortConfig": NotRequired["AbortConfigTypeDef"],
        "timeoutConfig": NotRequired["TimeoutConfigTypeDef"],
        "namespaceId": NotRequired[str],
        "jobExecutionsRetryConfig": NotRequired["JobExecutionsRetryConfigTypeDef"],
    },
)

UpdateMitigationActionRequestRequestTypeDef = TypedDict(
    "UpdateMitigationActionRequestRequestTypeDef",
    {
        "actionName": str,
        "roleArn": NotRequired[str],
        "actionParams": NotRequired["MitigationActionParamsTypeDef"],
    },
)

UpdateMitigationActionResponseTypeDef = TypedDict(
    "UpdateMitigationActionResponseTypeDef",
    {
        "actionArn": str,
        "actionId": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateProvisioningTemplateRequestRequestTypeDef = TypedDict(
    "UpdateProvisioningTemplateRequestRequestTypeDef",
    {
        "templateName": str,
        "description": NotRequired[str],
        "enabled": NotRequired[bool],
        "defaultVersionId": NotRequired[int],
        "provisioningRoleArn": NotRequired[str],
        "preProvisioningHook": NotRequired["ProvisioningHookTypeDef"],
        "removePreProvisioningHook": NotRequired[bool],
    },
)

UpdateRoleAliasRequestRequestTypeDef = TypedDict(
    "UpdateRoleAliasRequestRequestTypeDef",
    {
        "roleAlias": str,
        "roleArn": NotRequired[str],
        "credentialDurationSeconds": NotRequired[int],
    },
)

UpdateRoleAliasResponseTypeDef = TypedDict(
    "UpdateRoleAliasResponseTypeDef",
    {
        "roleAlias": str,
        "roleAliasArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateScheduledAuditRequestRequestTypeDef = TypedDict(
    "UpdateScheduledAuditRequestRequestTypeDef",
    {
        "scheduledAuditName": str,
        "frequency": NotRequired[AuditFrequencyType],
        "dayOfMonth": NotRequired[str],
        "dayOfWeek": NotRequired[DayOfWeekType],
        "targetCheckNames": NotRequired[Sequence[str]],
    },
)

UpdateScheduledAuditResponseTypeDef = TypedDict(
    "UpdateScheduledAuditResponseTypeDef",
    {
        "scheduledAuditArn": str,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateSecurityProfileRequestRequestTypeDef = TypedDict(
    "UpdateSecurityProfileRequestRequestTypeDef",
    {
        "securityProfileName": str,
        "securityProfileDescription": NotRequired[str],
        "behaviors": NotRequired[Sequence["BehaviorTypeDef"]],
        "alertTargets": NotRequired[Mapping[Literal["SNS"], "AlertTargetTypeDef"]],
        "additionalMetricsToRetain": NotRequired[Sequence[str]],
        "additionalMetricsToRetainV2": NotRequired[Sequence["MetricToRetainTypeDef"]],
        "deleteBehaviors": NotRequired[bool],
        "deleteAlertTargets": NotRequired[bool],
        "deleteAdditionalMetricsToRetain": NotRequired[bool],
        "expectedVersion": NotRequired[int],
    },
)

UpdateSecurityProfileResponseTypeDef = TypedDict(
    "UpdateSecurityProfileResponseTypeDef",
    {
        "securityProfileName": str,
        "securityProfileArn": str,
        "securityProfileDescription": str,
        "behaviors": List["BehaviorTypeDef"],
        "alertTargets": Dict[Literal["SNS"], "AlertTargetTypeDef"],
        "additionalMetricsToRetain": List[str],
        "additionalMetricsToRetainV2": List["MetricToRetainTypeDef"],
        "version": int,
        "creationDate": datetime,
        "lastModifiedDate": datetime,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateStreamRequestRequestTypeDef = TypedDict(
    "UpdateStreamRequestRequestTypeDef",
    {
        "streamId": str,
        "description": NotRequired[str],
        "files": NotRequired[Sequence["StreamFileTypeDef"]],
        "roleArn": NotRequired[str],
    },
)

UpdateStreamResponseTypeDef = TypedDict(
    "UpdateStreamResponseTypeDef",
    {
        "streamId": str,
        "streamArn": str,
        "description": str,
        "streamVersion": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateThingGroupRequestRequestTypeDef = TypedDict(
    "UpdateThingGroupRequestRequestTypeDef",
    {
        "thingGroupName": str,
        "thingGroupProperties": "ThingGroupPropertiesTypeDef",
        "expectedVersion": NotRequired[int],
    },
)

UpdateThingGroupResponseTypeDef = TypedDict(
    "UpdateThingGroupResponseTypeDef",
    {
        "version": int,
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

UpdateThingGroupsForThingRequestRequestTypeDef = TypedDict(
    "UpdateThingGroupsForThingRequestRequestTypeDef",
    {
        "thingName": NotRequired[str],
        "thingGroupsToAdd": NotRequired[Sequence[str]],
        "thingGroupsToRemove": NotRequired[Sequence[str]],
        "overrideDynamicGroups": NotRequired[bool],
    },
)

UpdateThingRequestRequestTypeDef = TypedDict(
    "UpdateThingRequestRequestTypeDef",
    {
        "thingName": str,
        "thingTypeName": NotRequired[str],
        "attributePayload": NotRequired["AttributePayloadTypeDef"],
        "expectedVersion": NotRequired[int],
        "removeThingType": NotRequired[bool],
    },
)

UpdateTopicRuleDestinationRequestRequestTypeDef = TypedDict(
    "UpdateTopicRuleDestinationRequestRequestTypeDef",
    {
        "arn": str,
        "status": TopicRuleDestinationStatusType,
    },
)

ValidateSecurityProfileBehaviorsRequestRequestTypeDef = TypedDict(
    "ValidateSecurityProfileBehaviorsRequestRequestTypeDef",
    {
        "behaviors": Sequence["BehaviorTypeDef"],
    },
)

ValidateSecurityProfileBehaviorsResponseTypeDef = TypedDict(
    "ValidateSecurityProfileBehaviorsResponseTypeDef",
    {
        "valid": bool,
        "validationErrors": List["ValidationErrorTypeDef"],
        "ResponseMetadata": "ResponseMetadataTypeDef",
    },
)

ValidationErrorTypeDef = TypedDict(
    "ValidationErrorTypeDef",
    {
        "errorMessage": NotRequired[str],
    },
)

ViolationEventAdditionalInfoTypeDef = TypedDict(
    "ViolationEventAdditionalInfoTypeDef",
    {
        "confidenceLevel": NotRequired[ConfidenceLevelType],
    },
)

ViolationEventOccurrenceRangeTypeDef = TypedDict(
    "ViolationEventOccurrenceRangeTypeDef",
    {
        "startTime": datetime,
        "endTime": datetime,
    },
)

ViolationEventTypeDef = TypedDict(
    "ViolationEventTypeDef",
    {
        "violationId": NotRequired[str],
        "thingName": NotRequired[str],
        "securityProfileName": NotRequired[str],
        "behavior": NotRequired["BehaviorTypeDef"],
        "metricValue": NotRequired["MetricValueTypeDef"],
        "violationEventAdditionalInfo": NotRequired["ViolationEventAdditionalInfoTypeDef"],
        "violationEventType": NotRequired[ViolationEventTypeType],
        "verificationState": NotRequired[VerificationStateType],
        "verificationStateDescription": NotRequired[str],
        "violationEventTime": NotRequired[datetime],
    },
)

VpcDestinationConfigurationTypeDef = TypedDict(
    "VpcDestinationConfigurationTypeDef",
    {
        "subnetIds": Sequence[str],
        "vpcId": str,
        "roleArn": str,
        "securityGroups": NotRequired[Sequence[str]],
    },
)

VpcDestinationPropertiesTypeDef = TypedDict(
    "VpcDestinationPropertiesTypeDef",
    {
        "subnetIds": NotRequired[List[str]],
        "securityGroups": NotRequired[List[str]],
        "vpcId": NotRequired[str],
        "roleArn": NotRequired[str],
    },
)

VpcDestinationSummaryTypeDef = TypedDict(
    "VpcDestinationSummaryTypeDef",
    {
        "subnetIds": NotRequired[List[str]],
        "securityGroups": NotRequired[List[str]],
        "vpcId": NotRequired[str],
        "roleArn": NotRequired[str],
    },
)
