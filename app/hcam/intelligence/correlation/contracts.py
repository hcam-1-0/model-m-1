from __future__ import annotations

from datetime import timedelta
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from hcam.analytics.contracts import ProcessingLineage
from hcam.analytics.spatial.contracts import EventKind
from hcam.intelligence.contracts import (
    Confidence,
    ContractModel,
    Department,
    Digest,
    EvidenceRole,
    HypothesisId,
    StableName,
    UtcDateTime,
)
from hcam.intelligence.correlation.bounds import (
    MAX_ACTIVE_WINDOWS_PER_PARTITION,
    MAX_ALLOWED_LATENESS_SECONDS,
    MAX_EVENTS_PER_WINDOW,
    MAX_EVIDENCE_REFS,
    MAX_FUTURE_CLOCK_SKEW_SECONDS,
    MAX_GRAPH_EDGES,
    MAX_GRAPH_NODES,
    MAX_WINDOW_SECONDS,
    MIN_WINDOW_SECONDS,
)


EventId = Annotated[
    str,
    Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]
GraphReferenceId = Annotated[
    str,
    Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]
StreamId = Annotated[str, Field(pattern=r"^str_[0-9a-f]{32}$")]
CameraId = Annotated[
    str,
    Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]
ReceiptId = Annotated[str, Field(pattern=r"^crec_[0-9a-f]{32}$")]
RunId = Annotated[str, Field(pattern=r"^crun_[0-9a-f]{32}$")]
WindowId = Annotated[str, Field(pattern=r"^cwin_[0-9a-f]{32}$")]
RevisionId = Annotated[str, Field(pattern=r"^hrev_[0-9a-f]{32}$")]
EventType = Annotated[
    str,
    Field(
        max_length=120,
        pattern=r"^hcam\.analytics\.[a-z0-9_.-]+\.v[0-9]+$",
    ),
]
SubjectKind = Literal["anonymous_person", "vehicle", "object", "event_group"]
SignalKind = Literal[
    "observation",
    "contradiction",
    "absence",
    "stale",
    "correction",
    "retraction",
]
PartitionDimension = Literal[
    "camera",
    "stream",
    "object_class",
    "direction",
    "location_relation",
    "track_local",
    "generated_reference",
]
ReceiptDisposition = Literal[
    "accepted",
    "duplicate",
    "conflict",
    "late_accepted",
    "late_rejected",
    "gap_accepted",
    "future_rejected",
    "policy_rejected",
    "capacity_rejected",
]
CorrelationLane = Literal[
    "deterministic_cpu",
    "probabilistic",
    "temporal_graph",
    "model_first_shadow",
    "uncertainty_ensemble",
]
LaneStatus = Literal["unavailable", "skipped", "completed", "failed"]


class CorrelationVersionedReferenceV1(ContractModel):
    id: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    digest: Digest


class Phase3SpatialEventPayloadV1(ContractModel):
    """Closed read model for generated Phase 3 spatial outbox payloads."""

    alert_state: Literal["not_evaluated"]
    assignment_id: StableName
    camera_id: CameraId
    confidence: Confidence
    count: Annotated[int, Field(ge=0, le=2_147_483_647)] | None = None
    department: Department
    direction: StableName | None = None
    dwell_ms: Annotated[int, Field(ge=0, le=86_400_000)] | None = None
    epoch_id: StableName
    event_id: EventId
    event_kind: EventKind
    geometry: CorrelationVersionedReferenceV1
    lifecycle_id: StableName
    lineage: ProcessingLineage
    occurred_at: UtcDateTime
    retention_class: Literal[
        "derived.analytics.standard",
        "derived.analytics.restricted",
    ]
    rule: CorrelationVersionedReferenceV1
    source_sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    state_cycle_id: StableName
    stream_id: StreamId
    track_id: StableName | None = None


class CorrelationChronologyV1(ContractModel):
    occurred_at: UtcDateTime
    observed_at: UtcDateTime
    received_at: UtcDateTime
    recorded_at: UtcDateTime
    corrected_at: UtcDateTime | None = None

    @model_validator(mode="after")
    def ordered(self) -> CorrelationChronologyV1:
        if not (
            self.occurred_at
            <= self.observed_at
            <= self.received_at
            <= self.recorded_at
        ):
            raise ValueError("correlation chronology is not ordered")
        if self.corrected_at is not None and self.corrected_at < self.recorded_at:
            raise ValueError("correction cannot precede durable recording")
        return self


class CorrelationSignalsV1(ContractModel):
    object_class: StableName
    signal_kind: SignalKind = "observation"
    confidence: Confidence
    direction: StableName | None = None
    location_relation: StableName | None = None
    local_track_id: StableName | None = None
    tracker_epoch: StableName | None = None
    generated_reference: StableName | None = None
    source_sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)] | None = None

    @model_validator(mode="after")
    def local_track_has_epoch(self) -> CorrelationSignalsV1:
        if (self.local_track_id is None) != (self.tracker_epoch is None):
            raise ValueError("a local track and tracker epoch must appear together")
        return self


class CorrelationIngressEventV1(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-ingress-event.v1"] = (
        "hcam.intelligence.correlation-ingress-event.v1"
    )
    event_id: EventId
    event_type: EventType
    schema_version: Annotated[int, Field(ge=1, le=10)]
    department: Department
    stream_id: StreamId
    camera_id: CameraId
    profile_id: StableName
    subject_kind: SubjectKind
    signals: CorrelationSignalsV1
    chronology: CorrelationChronologyV1
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class CorrelationProfileV1(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-profile.v1"] = (
        "hcam.intelligence.correlation-profile.v1"
    )
    profile_id: StableName
    profile_version: Digest
    allowed_event_types: Annotated[list[EventType], Field(min_length=1, max_length=32)]
    subject_kind: SubjectKind
    partition_dimensions: Annotated[
        list[PartitionDimension], Field(min_length=1, max_length=7)
    ]
    window_kind: Literal["fixed", "tumbling", "session"] = "tumbling"
    window_seconds: Annotated[
        int, Field(ge=MIN_WINDOW_SECONDS, le=MAX_WINDOW_SECONDS)
    ] = 60
    session_gap_seconds: Annotated[
        int, Field(ge=MIN_WINDOW_SECONDS, le=MAX_WINDOW_SECONDS)
    ] | None = None
    allowed_lateness_seconds: Annotated[
        int, Field(ge=0, le=MAX_ALLOWED_LATENESS_SECONDS)
    ] = 30
    future_clock_skew_seconds: Annotated[
        int, Field(ge=0, le=MAX_FUTURE_CLOCK_SKEW_SECONDS)
    ] = 5
    minimum_supporting_events: Annotated[int, Field(ge=1, le=MAX_EVIDENCE_REFS)] = 2
    maximum_contradictions: Annotated[int, Field(ge=0, le=MAX_EVIDENCE_REFS)] = 0
    maximum_events_per_window: Annotated[
        int, Field(ge=1, le=MAX_EVENTS_PER_WINDOW)
    ] = MAX_EVENTS_PER_WINDOW
    maximum_active_windows: Annotated[
        int, Field(ge=1, le=MAX_ACTIVE_WINDOWS_PER_PARTITION)
    ] = 32
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @field_validator("allowed_event_types", "partition_dimensions")
    @classmethod
    def values_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("correlation profile values must be unique")
        return value

    @model_validator(mode="after")
    def window_configuration_is_consistent(self) -> CorrelationProfileV1:
        if self.window_kind == "session" and self.session_gap_seconds is None:
            raise ValueError("session windows require a session gap")
        if self.window_kind != "session" and self.session_gap_seconds is not None:
            raise ValueError("only session windows may define a session gap")
        return self


class CorrelationReplayBindingV1(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-replay-binding.v1"] = (
        "hcam.intelligence.correlation-replay-binding.v1"
    )
    event_contract_version: Literal[
        "hcam.intelligence.correlation-ingress-event.v1"
    ] = "hcam.intelligence.correlation-ingress-event.v1"
    clock_semantics_version: Literal[
        "hcam.intelligence.event-time-watermark.v1"
    ] = "hcam.intelligence.event-time-watermark.v1"
    partition_semantics_version: Literal[
        "hcam.intelligence.partitioning.v1"
    ] = "hcam.intelligence.partitioning.v1"
    window_semantics_version: Literal[
        "hcam.intelligence.windows.v1"
    ] = "hcam.intelligence.windows.v1"
    profile_id: StableName
    profile_version: Digest
    profile_configuration_digest: Digest
    ordered_event_digests: Annotated[list[Digest], Field(min_length=1, max_length=1_000)]


class CorrelationReceiptV1(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-receipt.v1"] = (
        "hcam.intelligence.correlation-receipt.v1"
    )
    receipt_id: ReceiptId
    event_id: EventId
    event_digest: Digest
    department: Department
    partition_digest: Digest | None
    disposition: ReceiptDisposition
    reason_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
    accepted: bool
    receipt_sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    occurred_at: UtcDateTime
    recorded_at: UtcDateTime
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def disposition_is_consistent(self) -> CorrelationReceiptV1:
        accepted_states = {"accepted", "late_accepted", "gap_accepted"}
        if self.accepted != (self.disposition in accepted_states):
            raise ValueError("receipt acceptance is inconsistent")
        if self.accepted != (self.partition_digest is not None):
            raise ValueError("accepted receipts require a partition digest")
        return self


class PartitionCheckpointV1(ContractModel):
    contract_type: Literal["hcam.intelligence.partition-checkpoint.v1"] = (
        "hcam.intelligence.partition-checkpoint.v1"
    )
    department: Department
    profile_id: StableName
    partition_digest: Digest
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    receipt_sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    last_source_sequence: Annotated[
        int, Field(ge=0, le=9_223_372_036_854_775_807)
    ] | None = None
    maximum_occurred_at: UtcDateTime
    watermark_at: UtcDateTime
    active_window_count: Annotated[
        int, Field(ge=0, le=MAX_ACTIVE_WINDOWS_PER_PARTITION)
    ]
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def watermark_is_bounded(self) -> PartitionCheckpointV1:
        if self.watermark_at > self.maximum_occurred_at:
            raise ValueError("watermark cannot exceed maximum event time")
        return self


class CorrelationWindowV1(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-window.v1"] = (
        "hcam.intelligence.correlation-window.v1"
    )
    window_id: WindowId
    department: Department
    profile_id: StableName
    partition_digest: Digest
    window_kind: Literal["fixed", "tumbling", "session"]
    window_start: UtcDateTime
    window_end: UtcDateTime
    watermark_at: UtcDateTime
    completeness: Literal["open", "complete", "degraded"]
    event_ids: Annotated[list[EventId], Field(min_length=1, max_length=MAX_EVENTS_PER_WINDOW)]
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def interval_is_ordered(self) -> CorrelationWindowV1:
        if self.window_end <= self.window_start:
            raise ValueError("correlation window must have positive duration")
        if len(self.event_ids) != len(set(self.event_ids)):
            raise ValueError("window event identifiers must be unique")
        return self


class LaneCapabilityV1(ContractModel):
    contract_type: Literal["hcam.intelligence.lane-capability.v1"] = (
        "hcam.intelligence.lane-capability.v1"
    )
    lane: CorrelationLane
    implementation_version: Digest
    execution_state: Literal["enabled_generated_only", "unavailable"]
    resource_class: Literal["cpu", "accelerator_optional", "contract_only"]
    deterministic: bool
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def execution_boundary_is_consistent(self) -> LaneCapabilityV1:
        if self.lane == "deterministic_cpu":
            if self.execution_state != "enabled_generated_only" or not self.deterministic:
                raise ValueError("the deterministic CPU lane must be enabled and deterministic")
        elif self.execution_state != "unavailable":
            raise ValueError("optional P4.1 lanes must remain unavailable")
        return self


class LaneResultV1(ContractModel):
    contract_type: Literal["hcam.intelligence.lane-result.v1"] = (
        "hcam.intelligence.lane-result.v1"
    )
    lane: CorrelationLane
    status: LaneStatus
    score: Confidence | None = None
    uncertainty: Confidence | None = None
    abstained: bool
    evidence_ids: Annotated[list[EventId], Field(max_length=MAX_EVIDENCE_REFS)] = Field(
        default_factory=list
    )
    contradiction_count: Annotated[int, Field(ge=0, le=MAX_EVIDENCE_REFS)] = 0
    failure_code: Literal[
        "runtime_disabled",
        "capability_unavailable",
        "resource_budget_exceeded",
        "invalid_generated_input",
        "insufficient_evidence",
        "policy_veto",
    ] | None = None
    lineage_digest: Digest
    generated_fixture_result: bool = False
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @field_validator("evidence_ids")
    @classmethod
    def evidence_is_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("lane evidence identifiers must be unique")
        return value

    @model_validator(mode="after")
    def state_is_consistent(self) -> LaneResultV1:
        if self.status == "completed":
            if self.score is None or self.uncertainty is None or self.failure_code is not None:
                raise ValueError("completed lane result is incomplete")
        elif self.score is not None or self.uncertainty is not None:
            raise ValueError("inactive lane cannot contain scores")
        if self.status in {"failed", "unavailable"} and self.failure_code is None:
            raise ValueError("failed or unavailable lane requires a safe reason")
        if self.status == "skipped" and self.failure_code is not None:
            raise ValueError("skipped lane cannot contain a failure code")
        if self.lane != "deterministic_cpu" and self.status == "completed":
            if not self.generated_fixture_result:
                raise ValueError("optional P4.1 results must be generated fixtures")
        return self


class ArbitrationResultV1(ContractModel):
    contract_type: Literal["hcam.intelligence.arbitration-result.v1"] = (
        "hcam.intelligence.arbitration-result.v1"
    )
    state: Literal["proposed", "abstained"]
    confidence: Confidence
    uncertainty: Confidence
    abstained: bool
    reason_codes: Annotated[
        list[Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]],
        Field(min_length=1, max_length=16),
    ]
    lane_results: Annotated[list[LaneResultV1], Field(min_length=1, max_length=5)]
    contradiction_count: Annotated[int, Field(ge=0, le=MAX_EVIDENCE_REFS)]
    arbitration_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def arbitration_is_consistent(self) -> ArbitrationResultV1:
        if self.abstained != (self.state == "abstained"):
            raise ValueError("arbitration abstention is inconsistent")
        if sum(item.lane == "deterministic_cpu" for item in self.lane_results) != 1:
            raise ValueError("arbitration requires exactly one deterministic lane")
        return self


class CorrelationEvidenceV1(ContractModel):
    evidence_id: Annotated[str, Field(pattern=r"^evid_[0-9a-f]{32}$")]
    event_id: EventId
    role: EvidenceRole
    source_digest: Digest
    sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    chronology: CorrelationChronologyV1


class CorrelationGraphNodeV1(ContractModel):
    node_id: StableName
    kind: Literal["hypothesis", "event", "lane", "constraint"]
    reference_id: GraphReferenceId
    reference_digest: Digest


class CorrelationGraphEdgeV1(ContractModel):
    edge_id: StableName
    source_node_id: StableName
    target_node_id: StableName
    role: EvidenceRole


class CorrelationGraphV1(ContractModel):
    nodes: Annotated[list[CorrelationGraphNodeV1], Field(min_length=1, max_length=MAX_GRAPH_NODES)]
    edges: Annotated[list[CorrelationGraphEdgeV1], Field(max_length=MAX_GRAPH_EDGES)]

    @model_validator(mode="after")
    def graph_is_valid(self) -> CorrelationGraphV1:
        node_ids = [item.node_id for item in self.nodes]
        edge_ids = [item.edge_id for item in self.edges]
        if len(node_ids) != len(set(node_ids)) or len(edge_ids) != len(set(edge_ids)):
            raise ValueError("correlation graph identifiers must be unique")
        known = set(node_ids)
        if any(
            edge.source_node_id not in known or edge.target_node_id not in known
            for edge in self.edges
        ):
            raise ValueError("correlation graph edge references an unknown node")
        return self


class CorrelationFlatProjectionV1(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-flat-projection.v1"] = (
        "hcam.intelligence.correlation-flat-projection.v1"
    )
    hypothesis_id: HypothesisId
    projection_version: Literal["hcam.intelligence.correlation-flat-projection.v1"] = (
        "hcam.intelligence.correlation-flat-projection.v1"
    )
    graph_digest: Digest
    event_count: Annotated[int, Field(ge=0, le=MAX_EVENTS_PER_WINDOW)]
    supporting_evidence_count: Annotated[int, Field(ge=0, le=MAX_EVIDENCE_REFS)]
    contradiction_count: Annotated[int, Field(ge=0, le=MAX_EVIDENCE_REFS)]
    missing_evidence_count: Annotated[int, Field(ge=0, le=MAX_EVIDENCE_REFS)]
    summary_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
    projection_digest: Digest


class CorrelationHypothesisV2(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-hypothesis.v2"] = (
        "hcam.intelligence.correlation-hypothesis.v2"
    )
    hypothesis_id: HypothesisId
    revision: Annotated[int, Field(ge=1, le=2_147_483_647)]
    run_id: RunId
    department: Department
    profile_id: StableName
    profile_version: Digest
    partition_digest: Digest
    hypothesis_key: Digest
    subject_kind: SubjectKind
    state: Literal["proposed", "abstained", "expired", "superseded", "retracted", "corrected"]
    authority_class: Literal["mandatory_review"] = "mandatory_review"
    operational: Literal[False] = False
    generated_only: Literal[True] = True
    confidence: Confidence
    uncertainty: Confidence
    abstained: bool
    abstention_reason: Annotated[
        str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")
    ] | None = None
    contradiction_count: Annotated[int, Field(ge=0, le=MAX_EVIDENCE_REFS)]
    window: CorrelationWindowV1
    lane_results: Annotated[list[LaneResultV1], Field(min_length=1, max_length=5)]
    evidence: Annotated[list[CorrelationEvidenceV1], Field(max_length=MAX_EVIDENCE_REFS)]
    graph: CorrelationGraphV1
    graph_digest: Digest
    flat_projection: CorrelationFlatProjectionV1
    arbitration_digest: Digest
    chronology: CorrelationChronologyV1
    retention_class: Literal["derived.intelligence.standard"] = (
        "derived.intelligence.standard"
    )

    @model_validator(mode="after")
    def hypothesis_is_consistent(self) -> CorrelationHypothesisV2:
        if self.abstained != (self.state == "abstained"):
            raise ValueError("hypothesis abstention is inconsistent")
        if self.abstained != (self.abstention_reason is not None):
            raise ValueError("hypothesis abstention reason is inconsistent")
        if self.flat_projection.hypothesis_id != self.hypothesis_id:
            raise ValueError("flat projection references another hypothesis")
        if self.flat_projection.graph_digest != self.graph_digest:
            raise ValueError("flat projection graph digest is inconsistent")
        if self.contradiction_count != sum(
            item.role == "contradicts" for item in self.evidence
        ):
            raise ValueError("hypothesis contradiction count is inconsistent")
        return self


class HypothesisRevisionV1(ContractModel):
    contract_type: Literal["hcam.intelligence.hypothesis-revision.v1"] = (
        "hcam.intelligence.hypothesis-revision.v1"
    )
    revision_id: RevisionId
    hypothesis_id: HypothesisId
    revision: Annotated[int, Field(ge=1, le=2_147_483_647)]
    previous_state: Literal["none", "proposed", "abstained", "expired", "superseded", "retracted", "corrected"]
    new_state: Literal["proposed", "abstained", "expired", "superseded", "retracted", "corrected"]
    reason_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
    snapshot_digest: Digest
    recorded_at: UtcDateTime
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class CorrelationBatchResultV1(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-batch-result.v1"] = (
        "hcam.intelligence.correlation-batch-result.v1"
    )
    run_id: RunId
    profile_id: StableName
    replay_binding: CorrelationReplayBindingV1
    receipts: Annotated[list[CorrelationReceiptV1], Field(max_length=1_000)]
    windows: Annotated[list[CorrelationWindowV1], Field(max_length=32_768)]
    hypotheses: Annotated[list[CorrelationHypothesisV2], Field(max_length=32_768)]
    checkpoints: Annotated[list[PartitionCheckpointV1], Field(max_length=128)]
    input_count: Annotated[int, Field(ge=0, le=1_000)]
    accepted_count: Annotated[int, Field(ge=0, le=1_000)]
    duplicate_count: Annotated[int, Field(ge=0, le=1_000)]
    rejected_count: Annotated[int, Field(ge=0, le=1_000)]
    result_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def counts_are_consistent(self) -> CorrelationBatchResultV1:
        if self.profile_id != self.replay_binding.profile_id:
            raise ValueError("batch replay profile is inconsistent")
        if self.input_count != len(self.replay_binding.ordered_event_digests):
            raise ValueError("batch replay event count is inconsistent")
        if self.input_count != len(self.receipts):
            raise ValueError("batch input count is inconsistent")
        accepted = sum(item.accepted for item in self.receipts)
        duplicates = sum(item.disposition == "duplicate" for item in self.receipts)
        if self.accepted_count != accepted or self.duplicate_count != duplicates:
            raise ValueError("batch receipt counts are inconsistent")
        if self.rejected_count != self.input_count - accepted - duplicates:
            raise ValueError("batch rejection count is inconsistent")
        return self


def subtract_seconds(value: UtcDateTime, seconds: int) -> UtcDateTime:
    return value - timedelta(seconds=seconds)
