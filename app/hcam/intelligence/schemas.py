from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from hcam.intelligence.alerts.contracts import AlertAggregateV2
from hcam.intelligence.contracts import (
    AlertAggregateV1,
    CorrelationHypothesisV1,
    Department,
    Digest,
    IntelligenceRuleV1,
    OpaqueRef,
    ReferenceProviderV1,
    RetentionClass,
    RuleGraphV1,
    StableName,
)
from hcam.intelligence.correlation.contracts import (
    CorrelationFlatProjectionV1,
    CorrelationGraphV1,
    CorrelationHypothesisV2,
    CorrelationReplayBindingV1,
    HypothesisRevisionV1,
)
from hcam.intelligence.rules.contracts import (
    RuleCompilationV1,
    RuleEvaluationV1,
    RuleShadowComparisonV1,
    VisualRuleDocumentV1,
)


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IntelligenceRuleCreate(ApiModel):
    department: Department
    rule_key: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    graph: RuleGraphV1
    intended_use: Annotated[str, Field(min_length=8, max_length=1000)]
    policy_version: Digest
    retention_class: RetentionClass


class IntelligenceRuleStatusPatch(ApiModel):
    status: Literal["validated", "retired"]


class IntelligenceRuleResponse(IntelligenceRuleV1):
    rule_record_id: Annotated[str, Field(pattern=r"^irlr_[0-9a-f]{32}$")]
    record_version: Annotated[int, Field(ge=1)]
    stream_id: Annotated[str, Field(pattern=r"^str_[0-9a-f]{32}$")]
    camera_id: Annotated[str, Field(min_length=3, max_length=160)]
    runtime_state: Literal["disabled"] = "disabled"
    unavailable_reason: Literal["p4_0_runtime_disabled"] = "p4_0_runtime_disabled"


class P42RuleCreate(ApiModel):
    document: VisualRuleDocumentV1
    scope_stream_ids: Annotated[
        list[Annotated[str, Field(pattern=r"^str_[0-9a-f]{32}$")]],
        Field(min_length=1, max_length=16),
    ]


class P42CompilePreview(ApiModel):
    document: VisualRuleDocumentV1


class P42CompilationResponse(RuleCompilationV1):
    pass


class P42RuleResponse(ApiModel):
    contract_type: Literal["hcam.p4-2.intelligence-rule-response.v1"]
    rule_record_id: Annotated[str, Field(pattern=r"^irlr_[0-9a-f]{32}$")]
    record_version: Annotated[int, Field(ge=1)]
    rule_id: Annotated[str, Field(pattern=r"^irule_[0-9a-f]{32}$")]
    rule_key: StableName
    version: Annotated[int, Field(ge=1)]
    department: Department
    status: Literal["draft", "validated", "approved", "shadow", "suspended", "retired"]
    authority_class: Literal["mandatory_review"] = "mandatory_review"
    operational: Literal[False] = False
    generated_only: Literal[True] = True
    authoring_digest: Digest
    semantic_digest: Digest
    compilation_id: Annotated[str, Field(pattern=r"^rcmp_[0-9a-f]{32}$")]
    schedule_digest: Digest | None = None
    document: VisualRuleDocumentV1
    runtime_state: Literal["generated_evidence_only"] = "generated_evidence_only"
    created_at: datetime
    updated_at: datetime


class P42RuleVersionListResponse(ApiModel):
    items: list[P42RuleResponse]
    total: int


class P42EvaluationListResponse(ApiModel):
    items: list[RuleEvaluationV1]
    total: int
    limit: int
    offset: int


class P42ShadowComparisonListResponse(ApiModel):
    items: list[RuleShadowComparisonV1]
    total: int
    limit: int
    offset: int


class IntelligenceRuleListResponse(ApiModel):
    items: list[IntelligenceRuleResponse | P42RuleResponse]
    total: int
    limit: int
    offset: int


class ReferenceProviderCreate(ApiModel):
    department: Department
    provider_key: StableName
    policy_ref: OpaqueRef
    destination_policy_ref: OpaqueRef
    allowed_fields: Annotated[
        list[Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.]{0,63}$")]],
        Field(min_length=1, max_length=32),
    ]


class ReferenceProviderResponse(ReferenceProviderV1):
    configuration_digest: Digest
    runtime_state: Literal["disabled"] = "disabled"
    unavailable_reason: Literal["p4_0_provider_disabled"] = "p4_0_provider_disabled"


class ReferenceProviderListResponse(ApiModel):
    items: list[ReferenceProviderResponse]
    total: int
    limit: int
    offset: int


class CorrelationHypothesisListResponse(ApiModel):
    items: list[CorrelationHypothesisV1 | CorrelationHypothesisV2]
    total: int
    limit: int
    offset: int


class CorrelationRunResponse(ApiModel):
    run_id: Annotated[str, Field(pattern=r"^crun_[0-9a-f]{32}$")]
    department: Department
    status: Literal["blocked", "queued", "running", "succeeded", "failed"]
    execution_scope: Literal["contract_only", "generated_event_correlation"]
    reason_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
    profile_id: StableName | None
    profile_version: Digest | None
    result_digest: Digest | None
    replay_binding: CorrelationReplayBindingV1 | None
    input_count: Annotated[int, Field(ge=0, le=1_000)] | None
    accepted_count: Annotated[int, Field(ge=0, le=1_000)] | None
    duplicate_count: Annotated[int, Field(ge=0, le=1_000)] | None
    rejected_count: Annotated[int, Field(ge=0, le=1_000)] | None
    watermark_at: datetime | None
    created_at: datetime
    updated_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class CorrelationRunListResponse(ApiModel):
    items: list[CorrelationRunResponse]
    total: int
    limit: int
    offset: int


class CorrelationGraphResponse(ApiModel):
    hypothesis_id: Annotated[str, Field(pattern=r"^hyp_[0-9a-f]{32}$")]
    graph: CorrelationGraphV1
    graph_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class CorrelationProjectionResponse(ApiModel):
    projection: CorrelationFlatProjectionV1
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class CorrelationRevisionListResponse(ApiModel):
    items: list[HypothesisRevisionV1]
    total: int
    limit: int
    offset: int


class AlertListResponse(ApiModel):
    items: list[AlertAggregateV1 | AlertAggregateV2]
    total: int
    limit: int
    offset: int


class InvestigationTimelineResponse(ApiModel):
    timeline_id: Annotated[str, Field(pattern=r"^tml_[0-9a-f]{32}$")]
    record_version: Annotated[int, Field(ge=1)]
    department: Department
    status: Literal["draft", "closed"]
    title_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
    generated_only: Literal[True] = True
    owner_id: Annotated[str, Field(min_length=1, max_length=160)]
    created_at: datetime
    updated_at: datetime
    runtime_state: Literal["disabled"] = "disabled"


class InvestigationTimelineListResponse(ApiModel):
    items: list[InvestigationTimelineResponse]
    total: int
    limit: int
    offset: int


class IntelligenceHealthResponse(ApiModel):
    control_plane_enabled: bool
    runtime_state: Literal["disabled"] = "disabled"
    provider_transport_state: Literal["absent"] = "absent"
    data_state: Literal["generated_only"] = "generated_only"
    operational_alerting: Literal[False] = False
    reason_code: Literal["p4_0_runtime_disabled"] = "p4_0_runtime_disabled"
