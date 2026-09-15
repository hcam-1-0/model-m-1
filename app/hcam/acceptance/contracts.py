from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from hcam.acceptance.bounds import (
    MAX_CLAIMS,
    MAX_COMPATIBILITY_ENTRIES,
    MAX_EVIDENCE_COMPONENTS,
    MAX_EVIDENCE_EDGES,
    MAX_HANDOFF_OPERATIONS,
    MAX_LIMITATIONS,
    MAX_SCENARIOS,
    MAX_STEPS_PER_SCENARIO,
    MAX_UI_STATES,
    bounded_text,
    validate_generated_document,
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


UtcDateTime = Annotated[datetime, AfterValidator(_utc)]
Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
StableName = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")]
GeneratedRef = Annotated[str, Field(pattern=r"^(?:p47|ref|cmp|edge)_[0-9a-f]{32}$")]
ReasonCode = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,95}$")]
Revision = Annotated[int, Field(ge=1, le=2_147_483_647)]

ScenarioCategory = Literal[
    "golden",
    "abstention",
    "duplicate_replay",
    "late_conflict",
    "authorization_isolation",
    "reference_degradation",
    "review_lifecycle_denial",
    "correction_retraction",
    "worker_recovery",
]
ScenarioAction = Literal[
    "observe_event",
    "correlate",
    "evaluate_rule",
    "propose_alert",
    "query_reference",
    "review_alert",
    "transition_alert",
    "open_investigation",
    "append_evidence_reference",
    "duplicate_event",
    "record_late_conflict",
    "deny_cross_scope",
    "record_correction",
    "record_retraction",
    "degrade_worker",
    "recover_worker",
    "emit_signal",
]
AssertionFamily = Literal[
    "schema",
    "authorization",
    "chronology",
    "identity",
    "rule",
    "review",
    "integrity",
    "redaction",
    "recovery",
    "side_effect",
    "replay",
    "handoff",
    "accessibility",
]


class ScenarioStepV1(ContractModel):
    step_id: StableName
    sequence: Annotated[int, Field(ge=1, le=MAX_STEPS_PER_SCENARIO)]
    action: ScenarioAction
    advance_ms: Annotated[int, Field(ge=0, le=86_400_000)]
    input_data: Annotated[dict[str, Any], Field(max_length=64)]
    expected_outcome: Literal[
        "accepted", "abstained", "duplicate", "denied", "degraded", "recovered"
    ]
    expected_reason: ReasonCode

    @field_validator("input_data")
    @classmethod
    def input_is_generated(cls, value: dict[str, Any]) -> dict[str, Any]:
        validate_generated_document(value)
        return value


class ScenarioDefinitionV1(ContractModel):
    scenario_id: Annotated[str, Field(pattern=r"^S0[0-8]$")]
    category: ScenarioCategory
    title: Annotated[str, Field(min_length=8, max_length=160)]
    steps: Annotated[
        tuple[ScenarioStepV1, ...],
        Field(min_length=1, max_length=MAX_STEPS_PER_SCENARIO),
    ]
    expected_terminal_state: StableName
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def ordered_steps(self) -> ScenarioDefinitionV1:
        sequences = [item.sequence for item in self.steps]
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("scenario steps must have contiguous sequence numbers")
        if len({item.step_id for item in self.steps}) != len(self.steps):
            raise ValueError("scenario step IDs must be unique")
        return self


class ScenarioManifestV1(ContractModel):
    contract_type: Literal["hcam.acceptance.scenario-manifest.v1"] = (
        "hcam.acceptance.scenario-manifest.v1"
    )
    manifest_id: GeneratedRef
    seed: Annotated[int, Field(ge=0, le=2_147_483_647)]
    logical_epoch: UtcDateTime
    timezone: Literal["UTC"] = "UTC"
    identifier_namespace: Literal["generated.p47"] = "generated.p47"
    step_quantum_ms: Annotated[int, Field(ge=1, le=60_000)]
    source_order: Annotated[tuple[StableName, ...], Field(min_length=1, max_length=64)]
    policy_revisions: Annotated[
        dict[StableName, Revision], Field(min_length=1, max_length=64)
    ]
    fixture_digests: Annotated[dict[StableName, Digest], Field(max_length=64)]
    normalization_profile: Literal["hcam.acceptance.semantic.v1"] = (
        "hcam.acceptance.semantic.v1"
    )
    allowed_variance: Annotated[tuple[StableName, ...], Field(max_length=16)] = ()
    scenarios: Annotated[
        tuple[ScenarioDefinitionV1, ...], Field(min_length=1, max_length=MAX_SCENARIOS)
    ]
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def scenario_ids_are_unique(self) -> ScenarioManifestV1:
        identifiers = [item.scenario_id for item in self.scenarios]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("scenario IDs must be unique")
        return self


class AdapterResponseV1(ContractModel):
    action: ScenarioAction
    outcome: Literal[
        "accepted", "abstained", "duplicate", "denied", "degraded", "recovered"
    ]
    reason_code: ReasonCode
    state: StableName
    output: Annotated[dict[str, Any], Field(max_length=64)]
    mutation_count: Annotated[int, Field(ge=0, le=MAX_STEPS_PER_SCENARIO)]

    @field_validator("output")
    @classmethod
    def output_is_generated(cls, value: dict[str, Any]) -> dict[str, Any]:
        validate_generated_document(value)
        return value


class StepObservationV1(ContractModel):
    observation_id: GeneratedRef
    scenario_id: Annotated[str, Field(pattern=r"^S0[0-8]$")]
    step_id: StableName
    sequence: Annotated[int, Field(ge=1, le=MAX_STEPS_PER_SCENARIO)]
    logical_at: UtcDateTime
    action: ScenarioAction
    outcome: Literal[
        "accepted", "abstained", "duplicate", "denied", "degraded", "recovered"
    ]
    reason_code: ReasonCode
    state: StableName
    output_digest: Digest
    mutation_count: Annotated[int, Field(ge=0, le=MAX_STEPS_PER_SCENARIO)]
    generated_only: Literal[True] = True


class AssertionResultV1(ContractModel):
    assertion_id: GeneratedRef
    scenario_id: Annotated[str, Field(pattern=r"^S0[0-8]$")]
    family: AssertionFamily
    status: Literal["passed", "failed", "unknown", "skipped", "incomplete"]
    reason_code: ReasonCode
    evidence_refs: Annotated[tuple[GeneratedRef, ...], Field(max_length=128)]
    generated_only: Literal[True] = True


class SideEffectLedgerV1(ContractModel):
    network_attempts: Literal[0] = 0
    process_attempts: Literal[0] = 0
    provider_attempts: Literal[0] = 0
    camera_or_media_attempts: Literal[0] = 0
    model_or_dataset_attempts: Literal[0] = 0
    container_or_kubernetes_attempts: Literal[0] = 0
    production_operation_attempts: Literal[0] = 0
    direct_persistence_attempts: Literal[0] = 0
    retained_external_bytes: Literal[0] = 0
    generated_only: Literal[True] = True


class ScenarioRunV1(ContractModel):
    contract_type: Literal["hcam.acceptance.scenario-run.v1"] = (
        "hcam.acceptance.scenario-run.v1"
    )
    run_id: GeneratedRef
    scenario_id: Annotated[str, Field(pattern=r"^S0[0-8]$")]
    replay_index: Literal[1, 2]
    manifest_digest: Digest
    started_at: UtcDateTime
    completed_at: UtcDateTime
    terminal_state: StableName
    observations: Annotated[
        tuple[StepObservationV1, ...],
        Field(min_length=1, max_length=MAX_STEPS_PER_SCENARIO),
    ]
    assertions: Annotated[
        tuple[AssertionResultV1, ...], Field(min_length=1, max_length=32)
    ]
    side_effects: SideEffectLedgerV1
    semantic_digest: Digest
    complete: bool
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class ReplayComparisonV1(ContractModel):
    contract_type: Literal["hcam.acceptance.replay-comparison.v1"] = (
        "hcam.acceptance.replay-comparison.v1"
    )
    scenario_id: Annotated[str, Field(pattern=r"^S0[0-8]$")]
    first_run_id: GeneratedRef
    second_run_id: GeneratedRef
    first_semantic_digest: Digest
    second_semantic_digest: Digest
    equal: bool
    status: Literal["passed", "failed"]
    reason_code: ReasonCode
    generated_only: Literal[True] = True


class EvidenceComponentV1(ContractModel):
    component_id: GeneratedRef
    path: Annotated[str, Field(min_length=1, max_length=512)]
    kind: Literal[
        "source", "contract", "fixture", "result", "projection", "document", "review"
    ]
    byte_length: Annotated[int, Field(ge=0, le=268_435_456)]
    sha256: Annotated[str, Field(pattern=r"^[0-9A-F]{64}$")]
    producer: StableName
    producer_version: StableName
    completeness: Literal["complete", "partial", "unknown"]
    verified: bool
    generated_only: Literal[True] = True


class EvidenceEdgeV1(ContractModel):
    edge_id: GeneratedRef
    source_component_id: GeneratedRef
    target_component_id: GeneratedRef
    relation: Literal["derived_from", "validates", "documents", "supports", "limits"]


class EvidenceIndexV1(ContractModel):
    contract_type: Literal["hcam.acceptance.evidence-index.v1"] = (
        "hcam.acceptance.evidence-index.v1"
    )
    source_commit: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    authorization_digest: Annotated[str, Field(pattern=r"^[0-9A-F]{64}$")]
    components: Annotated[
        tuple[EvidenceComponentV1, ...], Field(max_length=MAX_EVIDENCE_COMPONENTS)
    ]
    edges: Annotated[tuple[EvidenceEdgeV1, ...], Field(max_length=MAX_EVIDENCE_EDGES)]
    completeness: Literal["complete", "partial", "unknown"]
    generated_only: Literal[True] = True


class ClaimRecordV1(ContractModel):
    claim_id: GeneratedRef
    statement: Annotated[str, Field(min_length=8, max_length=512)]
    scope: StableName
    evidence_class: Literal[
        "generated_contract", "generated_scenario", "static_validation", "not_observed"
    ]
    supporting_component_ids: Annotated[tuple[GeneratedRef, ...], Field(max_length=128)]
    limitation_ids: Annotated[tuple[GeneratedRef, ...], Field(max_length=64)]
    status: Literal["supported", "limited", "unsupported", "withdrawn"]
    prohibited_interpretations: Annotated[tuple[str, ...], Field(max_length=32)]
    generated_only: Literal[True] = True

    @field_validator("statement")
    @classmethod
    def statement_is_bounded(cls, value: str) -> str:
        return bounded_text(value, minimum=8, maximum=512)


class LimitationRecordV1(ContractModel):
    limitation_id: GeneratedRef
    statement: Annotated[str, Field(min_length=8, max_length=512)]
    impact: Literal["low", "medium", "high", "blocking"]
    mitigation: Annotated[str, Field(min_length=8, max_length=512)]
    required_future_evidence: Annotated[
        tuple[StableName, ...], Field(min_length=1, max_length=32)
    ]
    owner: StableName
    affected_claim_ids: Annotated[tuple[GeneratedRef, ...], Field(max_length=128)]
    status: Literal["open", "accepted", "resolved", "withdrawn"]
    generated_only: Literal[True] = True


class ClaimRegisterV1(ContractModel):
    contract_type: Literal["hcam.acceptance.claim-register.v1"] = (
        "hcam.acceptance.claim-register.v1"
    )
    claims: Annotated[tuple[ClaimRecordV1, ...], Field(max_length=MAX_CLAIMS)]
    generated_only: Literal[True] = True


class LimitationRegisterV1(ContractModel):
    contract_type: Literal["hcam.acceptance.limitation-register.v1"] = (
        "hcam.acceptance.limitation-register.v1"
    )
    limitations: Annotated[
        tuple[LimitationRecordV1, ...], Field(max_length=MAX_LIMITATIONS)
    ]
    generated_only: Literal[True] = True


class RunbookStepV1(ContractModel):
    order: Annotated[int, Field(ge=1, le=128)]
    action: StableName
    expected_reason: ReasonCode
    failure_reason: ReasonCode
    resumable: bool


class OperationsRunbookV1(ContractModel):
    contract_type: Literal["hcam.acceptance.operations-runbook.v1"] = (
        "hcam.acceptance.operations-runbook.v1"
    )
    runbook_id: GeneratedRef
    purpose: Literal["generated_acceptance_only"] = "generated_acceptance_only"
    preconditions: Annotated[tuple[StableName, ...], Field(min_length=1, max_length=64)]
    steps: Annotated[tuple[RunbookStepV1, ...], Field(min_length=1, max_length=128)]
    cleanup_required: Literal[True] = True
    zero_retention_required: Literal[True] = True
    production_use: Literal[False] = False
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def steps_are_ordered(self) -> OperationsRunbookV1:
        if [item.order for item in self.steps] != list(range(1, len(self.steps) + 1)):
            raise ValueError("runbook steps must be contiguous")
        return self


class ProductionPrerequisiteV1(ContractModel):
    prerequisite_id: GeneratedRef
    category: StableName
    status: Literal["not_operationally_validated"] = "not_operationally_validated"
    required_evidence: Annotated[
        tuple[StableName, ...], Field(min_length=1, max_length=32)
    ]
    accountable_owner_required: Literal[True] = True
    environment_specific_content_present: Literal[False] = False
    executable: Literal[False] = False


class ProductionPrerequisiteOutlineV1(ContractModel):
    contract_type: Literal["hcam.acceptance.production-prerequisites.v1"] = (
        "hcam.acceptance.production-prerequisites.v1"
    )
    prerequisites: Annotated[
        tuple[ProductionPrerequisiteV1, ...], Field(min_length=1, max_length=32)
    ]
    operationally_validated: Literal[False] = False
    executable: Literal[False] = False
    generated_only: Literal[True] = True


class ReconstructionEntryV1(ContractModel):
    entry_id: GeneratedRef
    order: Annotated[int, Field(ge=1, le=MAX_STEPS_PER_SCENARIO)]
    kind: StableName
    source_ref: GeneratedRef
    previous_entry_id: GeneratedRef | None = None
    correction_state: Literal["original", "corrected", "retracted"]


class ReconstructionManifestV1(ContractModel):
    contract_type: Literal["hcam.acceptance.reconstruction-manifest.v1"] = (
        "hcam.acceptance.reconstruction-manifest.v1"
    )
    reconstruction_id: GeneratedRef
    scenario_id: Annotated[str, Field(pattern=r"^S0[0-8]$")]
    entries: Annotated[
        tuple[ReconstructionEntryV1, ...],
        Field(min_length=1, max_length=MAX_STEPS_PER_SCENARIO),
    ]
    chronology_complete: bool
    source_content_copied: Literal[False] = False
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def entries_are_ordered(self) -> ReconstructionManifestV1:
        if [item.order for item in self.entries] != list(
            range(1, len(self.entries) + 1)
        ):
            raise ValueError("reconstruction entries must be contiguous")
        identifiers = {item.entry_id for item in self.entries}
        if len(identifiers) != len(self.entries):
            raise ValueError("reconstruction entry IDs must be unique")
        if any(
            item.previous_entry_id is not None
            and item.previous_entry_id not in identifiers
            for item in self.entries
        ):
            raise ValueError("reconstruction predecessor is missing")
        return self


class HttpOperationV1(ContractModel):
    operation_id: StableName
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    path_template: Annotated[str, Field(pattern=r"^/[A-Za-z0-9_{}./-]+$")]
    purpose: StableName
    audience: Annotated[tuple[StableName, ...], Field(min_length=1, max_length=16)]
    authorization_roles: Annotated[
        tuple[StableName, ...], Field(min_length=1, max_length=32)
    ]
    department_scope_required: bool
    reason_required: bool
    etag_mode: Literal["none", "response", "if_match"]
    idempotency_mode: Literal["none", "required", "semantic_and_delivery"]
    pagination: Literal["none", "cursor"]
    freshness: Literal["current", "fresh_stale_unknown"]
    success_states: Annotated[
        tuple[StableName, ...], Field(min_length=1, max_length=32)
    ]
    failure_codes: Annotated[tuple[ReasonCode, ...], Field(min_length=1, max_length=32)]
    compatibility_class: Literal["stable", "additive", "experimental"]
    generated_only: Literal[True] = True


class HttpCatalogueV1(ContractModel):
    contract_type: Literal["hcam.handoff.http-operation.v1"] = (
        "hcam.handoff.http-operation.v1"
    )
    operations: Annotated[
        tuple[HttpOperationV1, ...], Field(max_length=MAX_HANDOFF_OPERATIONS)
    ]
    generated_only: Literal[True] = True


class EventOperationV1(ContractModel):
    event_type: StableName
    producer: StableName
    consumer_intent: StableName
    ordering: Literal["aggregate", "partition", "none"]
    delivery: Literal["at_least_once_projection", "transactional_outbox"]
    correction_supported: bool
    unknown_version: Literal["reject", "quarantine"]
    grants_authority: Literal[False] = False
    generated_only: Literal[True] = True


class WorkflowStepV1(ContractModel):
    step_id: StableName
    operation_ref: StableName
    depends_on: Annotated[tuple[StableName, ...], Field(max_length=16)]
    success_state: StableName
    failure_codes: Annotated[tuple[ReasonCode, ...], Field(min_length=1, max_length=16)]


class WorkflowV1(ContractModel):
    workflow_id: StableName
    steps: Annotated[tuple[WorkflowStepV1, ...], Field(min_length=1, max_length=64)]
    operational: Literal[False] = False
    generated_only: Literal[True] = True


class EventWorkflowCatalogueV1(ContractModel):
    contract_type: Literal["hcam.handoff.event-workflow.v1"] = (
        "hcam.handoff.event-workflow.v1"
    )
    events: Annotated[
        tuple[EventOperationV1, ...], Field(max_length=MAX_HANDOFF_OPERATIONS)
    ]
    workflows: Annotated[tuple[WorkflowV1, ...], Field(max_length=128)]
    broker_selected: Literal[False] = False
    workflow_engine_selected: Literal[False] = False
    generated_only: Literal[True] = True


class UiStateV1(ContractModel):
    state_id: StableName
    view: StableName
    state: Literal[
        "loading",
        "empty",
        "partial",
        "stale",
        "degraded",
        "denied",
        "conflict",
        "failure",
        "recovery",
        "correction",
        "success",
    ]
    source_fact: StableName
    visible_message: Annotated[str, Field(min_length=1, max_length=256)]
    actions: Annotated[tuple[StableName, ...], Field(max_length=16)]
    focus_rule: StableName
    announcement: Literal["none", "polite", "assertive"]
    non_color_indicator: Literal[True] = True
    generated_only: Literal[True] = True


class AccessibilityRequirementV1(ContractModel):
    requirement_id: StableName
    applies_to: StableName
    category: Literal[
        "keyboard",
        "focus",
        "name_role_value",
        "status",
        "error",
        "non_color",
        "target",
        "contrast",
        "motion",
    ]
    requirement: Annotated[str, Field(min_length=8, max_length=512)]
    evidence_kind: Literal["static", "generated", "future_manual"]
    conformance_claim: Literal[False] = False


class UiAccessibilityCatalogueV1(ContractModel):
    contract_type: Literal["hcam.handoff.ui-accessibility.v1"] = (
        "hcam.handoff.ui-accessibility.v1"
    )
    states: Annotated[tuple[UiStateV1, ...], Field(max_length=MAX_UI_STATES)]
    requirements: Annotated[
        tuple[AccessibilityRequirementV1, ...], Field(max_length=MAX_UI_STATES)
    ]
    UI_implemented: Literal[False] = False
    accessibility_conformance_claim: Literal[False] = False
    generated_only: Literal[True] = True


class CompatibilityEntryV1(ContractModel):
    entry_id: StableName
    contract: StableName
    from_version: StableName
    to_version: StableName
    change_class: Literal[
        "documentation",
        "optional_additive",
        "new_capability",
        "compatible_behavior",
        "deprecation",
        "breaking_schema",
        "breaking_semantic",
        "security_boundary",
    ]
    supported_consumers: Annotated[tuple[StableName, ...], Field(max_length=64)]
    migration_required: bool
    evidence_ref: GeneratedRef
    security_review_required: bool


class CompatibilityMatrixV1(ContractModel):
    contract_type: Literal["hcam.handoff.compatibility.v1"] = (
        "hcam.handoff.compatibility.v1"
    )
    entries: Annotated[
        tuple[CompatibilityEntryV1, ...], Field(max_length=MAX_COMPATIBILITY_ENTRIES)
    ]
    latest_only_policy: Literal[False] = False
    permanent_compatibility_claim: Literal[False] = False
    generated_only: Literal[True] = True
