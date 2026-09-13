from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hcam.intelligence.alerts.bounds import (
    MAX_BUDGET_LIMIT,
    MAX_EVIDENCE_REFS,
    MAX_QUORUM,
    MAX_TIMER_ATTEMPTS,
)


Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
StableId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,127}$")]
Department = Annotated[str, Field(min_length=2, max_length=120)]
AlertId = Annotated[str, Field(pattern=r"^alt_[0-9a-f]{32}$")]
EvaluationId = Annotated[str, Field(pattern=r"^revl_[0-9a-f]{32}$")]
RuleRecordId = Annotated[str, Field(pattern=r"^irlr_[0-9a-f]{32}$")]
ActorId = Annotated[str, Field(min_length=1, max_length=160)]
AuthorityClass = Literal["mandatory_review", "bounded_automation"]
AlertDomain = Literal["police_intelligence", "system_health"]
AlertState = Literal[
    "proposed",
    "queued_review",
    "under_review",
    "accepted",
    "rejected",
    "resolved",
    "corrected",
    "suppressed",
    "merged",
]
Severity = Literal["information", "low", "medium", "high", "critical"]
Priority = Literal["routine", "standard", "urgent", "immediate"]


class AlertContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProposedAlertCommandV1(AlertContract):
    contract_type: Literal["hcam.p4-3.proposed-alert-command.v1"] = (
        "hcam.p4-3.proposed-alert-command.v1"
    )
    delivery_id: StableId
    evaluation_id: EvaluationId
    evaluation_revision: Annotated[int, Field(ge=1, le=2_147_483_647)]
    evaluation_digest: Digest
    rule_record_id: RuleRecordId
    compilation_id: Annotated[str, Field(pattern=r"^rcmp_[0-9a-f]{32}$")]
    department: Department
    partition_digest: Digest
    domain: AlertDomain = "police_intelligence"
    authority_class: AuthorityClass = "mandatory_review"
    occurred_at: datetime
    evidence_refs: Annotated[
        list[StableId], Field(min_length=1, max_length=MAX_EVIDENCE_REFS)
    ]
    incident_key: StableId
    severity: Severity
    priority: Priority
    confidence: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
    certainty: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
    chronology_confidence: Annotated[
        float, Field(ge=0, le=1, allow_inf_nan=False)
    ]
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @field_validator("evidence_refs")
    @classmethod
    def evidence_is_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("evidence references must be unique")
        return value

    @model_validator(mode="after")
    def authority_matches_domain(self) -> ProposedAlertCommandV1:
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must include an offset")
        if self.domain == "police_intelligence" and self.authority_class != "mandatory_review":
            raise ValueError("police intelligence requires mandatory review")
        if self.domain == "system_health" and self.authority_class != "bounded_automation":
            raise ValueError("system health requires bounded automation")
        return self


class AlertIdentityV1(AlertContract):
    alert_id: AlertId
    semantic_key: Digest
    delivery_key: Digest
    occurrence_digest: Digest


class AlertAggregateV2(AlertContract):
    contract_type: Literal["hcam.intelligence.alert.v2"] = (
        "hcam.intelligence.alert.v2"
    )
    alert_id: AlertId
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    department: Department
    semantic_key: Digest
    delivery_key: Digest
    source_evaluation_id: EvaluationId
    source_evaluation_revision: Annotated[int, Field(ge=1)]
    source_evaluation_digest: Digest
    incident_key: StableId
    state: AlertState
    domain: AlertDomain
    authority_class: AuthorityClass
    severity: Severity
    priority: Priority
    confidence: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
    certainty: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
    chronology_confidence: Annotated[
        float, Field(ge=0, le=1, allow_inf_nan=False)
    ]
    disposition: Literal[
        "unreviewed",
        "approved",
        "denied",
        "needs_information",
        "corrected",
        "automated",
    ]
    assigned_to: ActorId | None = None
    suppression_code: StableId | None = None
    merged_into: AlertId | None = None
    evidence_refs: Annotated[list[StableId], Field(max_length=MAX_EVIDENCE_REFS)]
    policy_digest: Digest
    created_at: datetime
    updated_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def aggregate_is_consistent(self) -> AlertAggregateV2:
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("aggregate timestamps must include an offset")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")
        if self.domain == "police_intelligence" and self.authority_class != "mandatory_review":
            raise ValueError("police intelligence requires mandatory review")
        if self.state == "merged" and self.merged_into is None:
            raise ValueError("merged alerts require a target")
        if self.state != "merged" and self.merged_into is not None:
            raise ValueError("only merged alerts may have a merge target")
        if self.state == "suppressed" and self.suppression_code is None:
            raise ValueError("suppressed alerts require a reason code")
        return self


class AlertLifecycleCommandV1(AlertContract):
    contract_type: Literal["hcam.p4-3.alert-lifecycle-command.v1"] = (
        "hcam.p4-3.alert-lifecycle-command.v1"
    )
    command_id: StableId
    action: Literal[
        "queue_review",
        "start_review",
        "accept",
        "reject",
        "request_information",
        "resolve",
        "reopen",
        "correct",
        "suppress",
        "merge",
        "assign",
    ]
    expected_version: Annotated[int, Field(ge=1)]
    actor_id: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    evidence_digest: Digest | None = None
    target_alert_id: AlertId | None = None
    assignee_id: ActorId | None = None


class AlertLifecycleEventV2(AlertContract):
    contract_type: Literal["hcam.intelligence.alert-lifecycle-event.v2"] = (
        "hcam.intelligence.alert-lifecycle-event.v2"
    )
    event_id: Annotated[str, Field(pattern=r"^alfe_[0-9a-f]{32}$")]
    alert_id: AlertId
    sequence: Annotated[int, Field(ge=1)]
    department: Department
    previous_state: AlertState
    new_state: AlertState
    action: StableId
    actor_id: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    evidence_digest: Digest | None = None
    recorded_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class ReviewQuorumPolicyV1(AlertContract):
    contract_type: Literal["hcam.p4-3.review-quorum-policy.v1"] = (
        "hcam.p4-3.review-quorum-policy.v1"
    )
    policy_id: StableId
    policy_version: Annotated[int, Field(ge=1)]
    department: Department
    workflow_class: Literal["ordinary", "generated_high_impact"]
    required_distinct_reviewers: Annotated[int, Field(ge=1, le=MAX_QUORUM)] = 1
    permitted_roles: Annotated[list[StableId], Field(min_length=1, max_length=8)]
    evidence_digest: Digest
    effective_at: datetime
    expires_at: datetime | None = None
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def policy_is_bounded(self) -> ReviewQuorumPolicyV1:
        if self.workflow_class == "ordinary" and self.required_distinct_reviewers != 1:
            raise ValueError("ordinary review requires exactly one reviewer")
        if self.effective_at.tzinfo is None:
            raise ValueError("effective_at must include an offset")
        if self.expires_at is not None and self.expires_at <= self.effective_at:
            raise ValueError("quorum expiry must follow activation")
        if len(self.permitted_roles) != len(set(self.permitted_roles)):
            raise ValueError("permitted roles must be unique")
        return self


class AlertReviewDecisionV1(AlertContract):
    contract_type: Literal["hcam.p4-3.alert-review-decision.v1"] = (
        "hcam.p4-3.alert-review-decision.v1"
    )
    decision_id: Annotated[str, Field(pattern=r"^ardc_[0-9a-f]{32}$")]
    alert_id: AlertId
    department: Department
    policy_id: StableId
    policy_version: Annotated[int, Field(ge=1)]
    reviewer_id: ActorId
    reviewer_role: StableId
    decision: Literal["approve", "deny", "request_information", "correct"]
    evidence_digest: Digest
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    supersedes_decision_id: Annotated[
        str | None, Field(pattern=r"^ardc_[0-9a-f]{32}$")
    ] = None
    recorded_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class BudgetLimitV1(AlertContract):
    scope: Literal["rule", "department", "review_queue", "generated_lab"]
    scope_key: StableId
    window_seconds: Annotated[int, Field(ge=1, le=86_400)]
    limit: Annotated[int, Field(ge=1, le=MAX_BUDGET_LIMIT)]


class AlertBudgetPolicyV1(AlertContract):
    contract_type: Literal["hcam.p4-3.alert-budget-policy.v1"] = (
        "hcam.p4-3.alert-budget-policy.v1"
    )
    policy_id: StableId
    version: Annotated[int, Field(ge=1)]
    department: Department
    limits: Annotated[list[BudgetLimitV1], Field(min_length=1, max_length=32)]
    policy_digest: Digest
    generated_only: Literal[True] = True


class AlertTimerIntentV1(AlertContract):
    contract_type: Literal["hcam.p4-3.alert-timer-intent.v1"] = (
        "hcam.p4-3.alert-timer-intent.v1"
    )
    timer_id: Annotated[str, Field(pattern=r"^atmr_[0-9a-f]{32}$")]
    alert_id: AlertId
    department: Department
    timer_kind: Literal["review_sla", "escalation", "quorum_expiry"]
    due_at: datetime
    state: Literal["pending", "leased", "completed", "failed", "cancelled"]
    attempt_count: Annotated[int, Field(ge=0, le=MAX_TIMER_ATTEMPTS)] = 0
    lease_owner: StableId | None = None
    lease_until: datetime | None = None
    expected_alert_version: Annotated[int, Field(ge=1)]
    payload_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class WorkflowExecutionRequestV1(AlertContract):
    contract_type: Literal["hcam.p4-3.workflow-execution-request.v1"] = (
        "hcam.p4-3.workflow-execution-request.v1"
    )
    execution_id: Annotated[str, Field(pattern=r"^awfx_[0-9a-f]{32}$")]
    timer: AlertTimerIntentV1
    adapter_kind: Literal["local_bounded", "generated_simulator", "future_disabled"]


class WorkflowExecutionResultV1(AlertContract):
    contract_type: Literal["hcam.p4-3.workflow-execution-result.v1"] = (
        "hcam.p4-3.workflow-execution-result.v1"
    )
    execution_id: Annotated[str, Field(pattern=r"^awfx_[0-9a-f]{32}$")]
    outcome: Literal["applied", "stale", "rejected", "adapter_disabled"]
    reason_code: StableId
    PostgreSQL_remains_authoritative: Literal[True] = True
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class LabEvaluationIngressV1(AlertContract):
    contract_type: Literal["hcam.p4-3.lab-evaluation-ingress.v1"] = (
        "hcam.p4-3.lab-evaluation-ingress.v1"
    )
    fixture_id: StableId
    adapter_profile: Literal["lab1highadapter", "lab2lowadapter"]
    camera_slot: Annotated[int, Field(ge=1, le=50)]
    media_profile: Literal["low", "medium", "high"]
    availability: Literal["available", "degraded", "offline"]
    sample_epoch: Annotated[int, Field(ge=0)]
    metadata_digest: Digest
    generated_only: Literal[True] = True
    sanitized: Literal[True] = True
    network_locator: None = None
    credential_ref: None = None
    media_payload: None = None


class SystemHealthActionV1(AlertContract):
    contract_type: Literal["hcam.p4-3.system-health-action.v1"] = (
        "hcam.p4-3.system-health-action.v1"
    )
    alert_id: AlertId
    action: Literal["route", "suppress_duplicate", "resolve_synthetic_health"]
    policy_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False
