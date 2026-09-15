from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import Field, field_validator, model_validator

from hcam.intelligence.contracts import ActorId, ContractModel, Department, Digest, StableName
from hcam.intelligence.investigations.bounds import (
    MAX_EXPORT_REFERENCES,
    MAX_IMPACT_TARGETS,
    MAX_PROVENANCE_EDGES,
    MAX_PROVENANCE_NODES,
    bounded_reason,
    validate_generated_document,
)


TimelineId = Annotated[str, Field(pattern=r"^inv_[0-9a-f]{32}$")]
TimelineEntryId = Annotated[str, Field(pattern=r"^ient_[0-9a-f]{32}$")]
EvidenceReferenceId = Annotated[str, Field(pattern=r"^iref_[0-9a-f]{32}$")]
IntegrityAssessmentId = Annotated[str, Field(pattern=r"^iasm_[0-9a-f]{32}$")]
ProvenanceNodeId = Annotated[str, Field(pattern=r"^ipnd_[0-9a-f]{32}$")]
ProvenanceEdgeId = Annotated[str, Field(pattern=r"^iped_[0-9a-f]{32}$")]
CorrectionId = Annotated[str, Field(pattern=r"^icor_[0-9a-f]{32}$")]
ImpactId = Annotated[str, Field(pattern=r"^iimp_[0-9a-f]{32}$")]
ReviewId = Annotated[str, Field(pattern=r"^irev_[0-9a-f]{32}$")]
RelationshipId = Annotated[str, Field(pattern=r"^irel_[0-9a-f]{32}$")]
PolicyEvaluationId = Annotated[str, Field(pattern=r"^ipev_[0-9a-f]{32}$")]
DeletionReceiptId = Annotated[str, Field(pattern=r"^idel_[0-9a-f]{32}$")]
ExportManifestId = Annotated[str, Field(pattern=r"^iexp_[0-9a-f]{32}$")]
JobId = Annotated[str, Field(pattern=r"^ijob_[0-9a-f]{32}$")]
OpaqueReference = Annotated[str, Field(pattern=r"^ref_[0-9a-f]{32}$")]
ReasonCode = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,95}$")]
Revision = Annotated[int, Field(ge=1, le=2_147_483_647)]
SequenceNumber = Annotated[int, Field(ge=1, le=9_223_372_036_854_775_807)]


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return value.astimezone(UTC)


class TemporalAssertionV1(ContractModel):
    occurred_at: datetime | None = None
    observed_at: datetime
    received_at: datetime
    recorded_at: datetime
    occurrence_precision: Literal["exact", "millisecond", "second", "interval", "unknown"]
    clock_trust: Literal["trusted", "bounded_skew", "untrusted", "unknown"]
    clock_skew_ms: Annotated[int, Field(ge=-86_400_000, le=86_400_000)] | None = None

    _occurred_utc = field_validator("occurred_at")(_utc)
    _observed_utc = field_validator("observed_at")(_utc)
    _received_utc = field_validator("received_at")(_utc)
    _recorded_utc = field_validator("recorded_at")(_utc)

    @model_validator(mode="after")
    def chronology_is_consistent(self) -> TemporalAssertionV1:
        if not self.observed_at <= self.received_at <= self.recorded_at:
            raise ValueError("trusted record chronology is not ordered")
        if self.occurrence_precision == "unknown" and self.occurred_at is not None:
            raise ValueError("unknown occurrence time cannot include occurred_at")
        if self.occurrence_precision != "unknown" and self.occurred_at is None:
            raise ValueError("known occurrence precision requires occurred_at")
        if self.clock_trust == "bounded_skew" and self.clock_skew_ms is None:
            raise ValueError("bounded clock skew requires a measured skew")
        if self.clock_trust != "bounded_skew" and self.clock_skew_ms is not None:
            raise ValueError("clock skew is only valid for bounded_skew")
        return self


class TimelineCreateCommandV2(ContractModel):
    contract_type: Literal["hcam.investigation.timeline-create.v2"] = (
        "hcam.investigation.timeline-create.v2"
    )
    timeline_id: TimelineId
    department: Department
    title: Annotated[str, Field(pattern=r"^generated\.[a-z0-9._-]{1,118}$")]
    purpose_code: ReasonCode
    actor_id: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    delivery_id: StableName
    requested_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _requested_at_utc = field_validator("requested_at")(_utc)
    _reason = field_validator("reason")(bounded_reason)


class InvestigationTimelineV2(ContractModel):
    contract_type: Literal["hcam.investigation.timeline.v2"] = (
        "hcam.investigation.timeline.v2"
    )
    timeline_id: TimelineId
    department: Department
    title: Annotated[str, Field(pattern=r"^generated\.[a-z0-9._-]{1,118}$")]
    purpose_code: ReasonCode
    lifecycle: Literal["open", "closed", "reopened"]
    disposition: Literal["unreviewed", "review_pending", "reviewed", "resolved"]
    revision: Revision
    entry_count: Annotated[int, Field(ge=0, le=10_000)]
    canonical_timeline_id: TimelineId
    content_digest: Digest
    created_at: datetime
    updated_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _created_at_utc = field_validator("created_at")(_utc)
    _updated_at_utc = field_validator("updated_at")(_utc)

    @model_validator(mode="after")
    def timeline_is_consistent(self) -> InvestigationTimelineV2:
        if self.updated_at < self.created_at:
            raise ValueError("timeline update cannot precede creation")
        return self


EntryFamily = Literal[
    "source",
    "event",
    "hypothesis",
    "alert",
    "operator_observation",
    "review",
    "action_record",
    "correction",
    "retraction",
    "disposition",
    "merge",
    "reopen",
    "retention",
    "hold",
    "deletion",
    "export",
]


class TimelineEntryV2(ContractModel):
    contract_type: Literal["hcam.investigation.timeline-entry.v2"] = (
        "hcam.investigation.timeline-entry.v2"
    )
    entry_id: TimelineEntryId
    timeline_id: TimelineId
    department: Department
    family: EntryFamily
    subject_ref: OpaqueReference
    sequence: SequenceNumber
    aggregate_revision: Revision
    temporal: TemporalAssertionV1
    payload: Annotated[dict[str, Any], Field(max_length=128)]
    actor_id: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    semantic_key: Digest
    delivery_key: Digest
    content_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _reason = field_validator("reason")(bounded_reason)

    @field_validator("payload")
    @classmethod
    def payload_is_generated_and_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        validate_generated_document(value)
        return value


class ReconstructionV1(ContractModel):
    timeline_id: TimelineId
    department: Department
    view: Literal["record_sequence", "event_time"]
    through_revision: Revision
    entries: Annotated[list[TimelineEntryV2], Field(max_length=10_000)]
    later_correction_entry_ids: Annotated[list[TimelineEntryId], Field(max_length=10_000)]
    completeness: Literal["complete", "partial", "inconsistent"]
    reconstruction_digest: Digest
    generated_only: Literal[True] = True


class EvidenceReferenceV2(ContractModel):
    contract_type: Literal["hcam.investigation.evidence-reference.v2"] = (
        "hcam.investigation.evidence-reference.v2"
    )
    reference_id: EvidenceReferenceId
    timeline_id: TimelineId
    department: Department
    source_system_ref: OpaqueReference
    source_object_ref: OpaqueReference
    source_version: StableName
    content_digest: Digest
    canonicalization_profile: StableName
    classification: Literal["generated.public", "generated.restricted"]
    source_payload_retained: Literal[False] = False
    locator_retained: Literal[False] = False
    registered_by: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    registered_at: datetime
    generated_only: Literal[True] = True

    _registered_at_utc = field_validator("registered_at")(_utc)
    _reason = field_validator("reason")(bounded_reason)


class IntegrityAssessmentV1(ContractModel):
    assessment_id: IntegrityAssessmentId
    reference_id: EvidenceReferenceId
    timeline_id: TimelineId
    department: Department
    state: Literal["matched", "mismatched", "unavailable", "denied", "unverifiable"]
    algorithm: Literal["sha256"]
    expected_digest: Digest
    observed_digest: Digest | None = None
    authenticity: Literal["not_assessed"] = "not_assessed"
    custody: Literal["not_assessed"] = "not_assessed"
    legal_status: Literal["not_assessed"] = "not_assessed"
    source_payload_retained: Literal[False] = False
    assessed_by: ActorId
    reason_code: ReasonCode
    assessed_at: datetime
    generated_only: Literal[True] = True

    _assessed_at_utc = field_validator("assessed_at")(_utc)

    @model_validator(mode="after")
    def digest_state_is_consistent(self) -> IntegrityAssessmentV1:
        has_observed = self.observed_digest is not None
        if self.state in {"matched", "mismatched"} and not has_observed:
            raise ValueError("comparison states require an observed digest")
        if self.state not in {"matched", "mismatched"} and has_observed:
            raise ValueError("non-comparison states cannot retain an observed digest")
        if self.state == "matched" and self.observed_digest != self.expected_digest:
            raise ValueError("matched integrity requires equal digests")
        if self.state == "mismatched" and self.observed_digest == self.expected_digest:
            raise ValueError("mismatched integrity requires different digests")
        return self


class ProvenanceNodeV1(ContractModel):
    node_id: ProvenanceNodeId
    kind: Literal["entity", "activity", "agent"]
    reference_id: OpaqueReference
    version: Revision
    attributes: Annotated[dict[str, Any], Field(max_length=32)] = Field(default_factory=dict)

    @field_validator("attributes")
    @classmethod
    def attributes_are_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        validate_generated_document(value)
        return value


class ProvenanceEdgeV1(ContractModel):
    edge_id: ProvenanceEdgeId
    relation: Literal[
        "used",
        "was_generated_by",
        "was_derived_from",
        "was_attributed_to",
        "was_associated_with",
        "acted_on_behalf_of",
        "was_informed_by",
        "was_revision_of",
        "had_primary_source",
        "was_invalidated_by",
        "was_quoted_from",
    ]
    source_node_id: ProvenanceNodeId
    target_node_id: ProvenanceNodeId
    recorded_at: datetime

    _recorded_at_utc = field_validator("recorded_at")(_utc)

    @model_validator(mode="after")
    def edge_is_not_self_referential(self) -> ProvenanceEdgeV1:
        if self.source_node_id == self.target_node_id:
            raise ValueError("provenance self edges are forbidden")
        return self


class ProvenanceBundleV1(ContractModel):
    bundle_id: Annotated[str, Field(pattern=r"^iprv_[0-9a-f]{32}$")]
    timeline_id: TimelineId
    department: Department
    nodes: Annotated[list[ProvenanceNodeV1], Field(max_length=MAX_PROVENANCE_NODES)]
    edges: Annotated[list[ProvenanceEdgeV1], Field(max_length=MAX_PROVENANCE_EDGES)]
    bundle_digest: Digest
    completeness: Literal["complete", "partial", "inconsistent"]
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def identifiers_are_unique_and_closed(self) -> ProvenanceBundleV1:
        node_ids = [item.node_id for item in self.nodes]
        edge_ids = [item.edge_id for item in self.edges]
        if len(node_ids) != len(set(node_ids)) or len(edge_ids) != len(set(edge_ids)):
            raise ValueError("provenance identifiers must be unique")
        known = set(node_ids)
        if any(
            edge.source_node_id not in known or edge.target_node_id not in known
            for edge in self.edges
        ):
            raise ValueError("provenance edges must reference bundle nodes")
        return self


class CorrectionCommandV1(ContractModel):
    correction_id: CorrectionId
    timeline_id: TimelineId
    department: Department
    kind: Literal["correction", "retraction"]
    target_type: Literal["entry", "evidence", "hypothesis", "alert", "review", "export"]
    target_ref: OpaqueReference
    target_version: Revision
    replacement_ref: OpaqueReference | None = None
    actor_id: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    delivery_id: StableName
    recorded_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _recorded_at_utc = field_validator("recorded_at")(_utc)
    _reason = field_validator("reason")(bounded_reason)

    @model_validator(mode="after")
    def replacement_is_consistent(self) -> CorrectionCommandV1:
        if self.kind == "correction" and self.replacement_ref is None:
            raise ValueError("correction requires a replacement reference")
        if self.kind == "retraction" and self.replacement_ref is not None:
            raise ValueError("retraction cannot include a replacement reference")
        return self


class ImpactRecordV1(ContractModel):
    impact_id: ImpactId
    correction_id: CorrectionId
    timeline_id: TimelineId
    department: Department
    target_type: Literal["entry", "evidence", "hypothesis", "alert", "review", "search", "export"]
    target_ref: OpaqueReference
    state: Literal["pending", "applied", "blocked", "failed"]
    reason_code: ReasonCode
    recorded_at: datetime
    generated_only: Literal[True] = True

    _recorded_at_utc = field_validator("recorded_at")(_utc)


class ImpactSetV1(ContractModel):
    correction_id: CorrectionId
    timeline_id: TimelineId
    department: Department
    impacts: Annotated[list[ImpactRecordV1], Field(max_length=MAX_IMPACT_TARGETS)]
    propagation_state: Literal["pending", "partial", "blocked", "failed", "complete"]
    impact_digest: Digest
    generated_only: Literal[True] = True


class ReviewDecisionV1(ContractModel):
    review_id: ReviewId
    timeline_id: TimelineId
    department: Department
    target_ref: OpaqueReference
    decision: Literal["support", "contradict", "request_information", "correct", "no_conclusion"]
    disposition: Literal["unreviewed", "review_pending", "reviewed", "resolved"]
    revision: Revision
    supersedes_review_id: ReviewId | None = None
    reviewer_id: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    evidence_digest: Digest
    recorded_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _recorded_at_utc = field_validator("recorded_at")(_utc)
    _reason = field_validator("reason")(bounded_reason)

    @model_validator(mode="after")
    def supersession_is_consistent(self) -> ReviewDecisionV1:
        if (self.revision > 1) != (self.supersedes_review_id is not None):
            raise ValueError("review revisions after one must supersede a review")
        return self


class RelationshipRevisionV1(ContractModel):
    relationship_id: RelationshipId
    department: Department
    source_timeline_id: TimelineId
    target_timeline_id: TimelineId
    kind: Literal["related", "duplicate_of", "merged_into"]
    revision: Revision
    active: bool
    actor_id: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    recorded_at: datetime
    generated_only: Literal[True] = True

    _recorded_at_utc = field_validator("recorded_at")(_utc)
    _reason = field_validator("reason")(bounded_reason)

    @model_validator(mode="after")
    def relationship_is_not_self_referential(self) -> RelationshipRevisionV1:
        if self.source_timeline_id == self.target_timeline_id:
            raise ValueError("timeline self relationships are forbidden")
        return self


class RetentionPolicyReferenceV1(ContractModel):
    policy_ref: OpaqueReference
    policy_version: StableName
    policy_digest: Digest
    classification: Literal["generated.public", "generated.restricted"]
    generated_only: Literal[True] = True


class HoldOverlayV1(ContractModel):
    hold_ref: OpaqueReference
    timeline_id: TimelineId
    department: Department
    state: Literal["proposed", "simulated_active", "simulated_released", "simulated_expired", "superseded"]
    scope_digest: Digest
    authority_ref: OpaqueReference
    grants_access: Literal[False] = False
    effective_runtime_action: Literal[False] = False
    revision: Revision
    recorded_at: datetime
    generated_only: Literal[True] = True

    _recorded_at_utc = field_validator("recorded_at")(_utc)


class RetentionEvaluationV1(ContractModel):
    evaluation_id: PolicyEvaluationId
    timeline_id: TimelineId
    department: Department
    policy: RetentionPolicyReferenceV1
    hold_refs: Annotated[list[OpaqueReference], Field(max_length=128)]
    outcome: Literal["retain", "eligible_for_simulation", "blocked", "unknown"]
    reason_codes: Annotated[list[ReasonCode], Field(min_length=1, max_length=16)]
    advisory_only: Literal[True] = True
    legal_period_selected: Literal[False] = False
    evaluated_at: datetime
    generated_only: Literal[True] = True

    _evaluated_at_utc = field_validator("evaluated_at")(_utc)


class DeletionIntentV1(ContractModel):
    intent_id: Annotated[str, Field(pattern=r"^idin_[0-9a-f]{32}$")]
    timeline_id: TimelineId
    department: Department
    target_refs: Annotated[list[OpaqueReference], Field(min_length=1, max_length=MAX_IMPACT_TARGETS)]
    policy_evaluation_id: PolicyEvaluationId
    dry_run: Literal[True] = True
    requested_by: ActorId
    reason: Annotated[str, Field(min_length=8, max_length=2000)]
    requested_at: datetime
    generated_only: Literal[True] = True

    _requested_at_utc = field_validator("requested_at")(_utc)
    _reason = field_validator("reason")(bounded_reason)


class DeletionReceiptV1(ContractModel):
    receipt_id: DeletionReceiptId
    intent_id: Annotated[str, Field(pattern=r"^idin_[0-9a-f]{32}$")]
    timeline_id: TimelineId
    department: Department
    target_ref: OpaqueReference
    outcome: Literal["simulated_deleted", "blocked", "unknown", "residual_known"]
    residual_states: Annotated[list[ReasonCode], Field(max_length=32)]
    universal_deletion_proven: Literal[False] = False
    external_action_executed: Literal[False] = False
    recorded_at: datetime
    generated_only: Literal[True] = True

    _recorded_at_utc = field_validator("recorded_at")(_utc)


class ExportReferenceV1(ContractModel):
    reference_id: EvidenceReferenceId
    version: StableName
    content_digest: Digest
    inclusion: Literal["included", "excluded", "denied", "unresolved"]
    reason_code: ReasonCode


class ExportManifestV1(ContractModel):
    manifest_id: ExportManifestId
    timeline_id: TimelineId
    department: Department
    purpose_code: ReasonCode
    recipient_class: Literal["generated.reviewer", "generated.records"]
    policy_ref: OpaqueReference
    references: Annotated[list[ExportReferenceV1], Field(max_length=MAX_EXPORT_REFERENCES)]
    completeness: Literal["complete", "partial", "blocked"]
    manifest_digest: Digest
    source_payload_included: Literal[False] = False
    signature_profile: Literal["disabled"] = "disabled"
    timestamp_profile: Literal["disabled"] = "disabled"
    delivery_state: Literal["not_authorized"] = "not_authorized"
    prepared_by: ActorId
    prepared_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _prepared_at_utc = field_validator("prepared_at")(_utc)


class CaseManagementBridgeContractV1(ContractModel):
    contract_type: Literal["hcam.investigation.case-bridge.v1"] = (
        "hcam.investigation.case-bridge.v1"
    )
    bridge_id: StableName
    timeline_id: TimelineId
    external_case_ref: OpaqueReference
    mapping_profile: StableName
    mapping_profile_digest: Digest
    direction: Literal["projection_only", "import_reference_only"]
    enabled: Literal[False] = False
    external_connection: Literal[False] = False
    legal_workflow: Literal[False] = False
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class ProvProjectionStatementV1(ContractModel):
    subject: ProvenanceNodeId
    relation: Literal[
        "used",
        "wasGeneratedBy",
        "wasDerivedFrom",
        "wasAttributedTo",
        "wasAssociatedWith",
        "actedOnBehalfOf",
        "wasInformedBy",
        "wasRevisionOf",
        "hadPrimarySource",
        "wasInvalidatedBy",
        "wasQuotedFrom",
    ]
    object: ProvenanceNodeId


class ProvInterchangeProjectionV1(ContractModel):
    contract_type: Literal["hcam.investigation.prov-projection.v1"] = (
        "hcam.investigation.prov-projection.v1"
    )
    projection_id: Annotated[str, Field(pattern=r"^iprx_[0-9a-f]{32}$")]
    bundle_id: Annotated[str, Field(pattern=r"^iprv_[0-9a-f]{32}$")]
    bundle_digest: Digest
    mapping_profile: Literal["hcam.prov.generated-subset.v1"] = (
        "hcam.prov.generated-subset.v1"
    )
    statements: Annotated[list[ProvProjectionStatementV1], Field(max_length=MAX_PROVENANCE_EDGES)]
    unmapped_edge_ids: Annotated[list[ProvenanceEdgeId], Field(max_length=MAX_PROVENANCE_EDGES)]
    import_enabled: Literal[False] = False
    conformance_state: Literal["not_claimed"] = "not_claimed"
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class ImpactJobV1(ContractModel):
    job_id: JobId
    correction_id: CorrectionId
    timeline_id: TimelineId
    department: Department
    state: Literal["queued", "leased", "succeeded", "failed", "dead_letter"]
    attempt_count: Annotated[int, Field(ge=0, le=3)]
    lease_owner: StableName | None = None
    lease_until: datetime | None = None
    reason_code: ReasonCode
    created_at: datetime
    updated_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    _lease_until_utc = field_validator("lease_until")(_utc)
    _created_at_utc = field_validator("created_at")(_utc)
    _updated_at_utc = field_validator("updated_at")(_utc)

    @model_validator(mode="after")
    def lease_is_consistent(self) -> ImpactJobV1:
        leased = self.state == "leased"
        if leased != (self.lease_owner is not None and self.lease_until is not None):
            raise ValueError("impact job lease fields are inconsistent")
        return self
