from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hcam.analytics.contracts import (
    AnalyticsAssignmentV1,
    ClassId,
    CapabilityId,
    Confidence,
    ImmutableDigest,
    ProcessingLineage,
    StableName,
    TaxonomyVersion,
    TrackLifecyclePayloadV2,
    UtcDateTime,
    VersionedArtifact,
    VersionedConfiguration,
)
from hcam.analytics.runtime import RuntimeFailureCode


RetentionClass = Literal[
    "derived.analytics.standard",
    "derived.analytics.restricted",
]
AssignmentBlockingReason = Literal[
    "runtime_unconfigured",
    "taxonomy_unapproved",
    "retention_policy_unapproved",
    "implementation_scope_unapproved",
    "authorization_expired",
]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalyticsAssignmentCreate(ApiModel):
    capability: CapabilityId
    desired_state: Literal["paused"] = "paused"
    pipeline: VersionedArtifact
    models: Annotated[list[VersionedArtifact], Field(max_length=8)] = Field(
        default_factory=list
    )
    taxonomy_version: TaxonomyVersion
    policy_version: ImmutableDigest
    configuration_digest: ImmutableDigest
    minimum_confidence: Confidence
    sampling_fps: Annotated[float, Field(gt=0, le=60)]
    maximum_queue_age_ms: Annotated[int, Field(ge=50, le=60_000)]
    geometry_refs: Annotated[list[VersionedConfiguration], Field(max_length=64)] = (
        Field(default_factory=list)
    )
    retention_class: RetentionClass
    approval_record_id: StableName


class AnalyticsAssignmentPatch(ApiModel):
    desired_state: Literal["paused"] | None = None
    pipeline: VersionedArtifact | None = None
    models: Annotated[list[VersionedArtifact], Field(max_length=8)] | None = None
    taxonomy_version: TaxonomyVersion | None = None
    policy_version: ImmutableDigest | None = None
    configuration_digest: ImmutableDigest | None = None
    minimum_confidence: Confidence | None = None
    sampling_fps: Annotated[float, Field(gt=0, le=60)] | None = None
    maximum_queue_age_ms: Annotated[int, Field(ge=50, le=60_000)] | None = None
    geometry_refs: (
        Annotated[list[VersionedConfiguration], Field(max_length=64)] | None
    ) = None
    retention_class: RetentionClass | None = None
    approval_record_id: StableName | None = None

    @model_validator(mode="after")
    def contains_a_change(self) -> AnalyticsAssignmentPatch:
        if not self.model_fields_set:
            raise ValueError("analytics assignment update requires at least one field")
        return self


class AnalyticsAssignmentResponse(AnalyticsAssignmentV1):
    execution_scope: Literal["generated_only"] = "generated_only"
    lifecycle_state: Literal["blocked", "paused", "running", "degraded", "failed"]
    reason_code: Literal[
        "owner_gates_pending",
        "manual_pause",
        "generated_runtime_active",
        "runtime_degraded",
        "runtime_failed",
    ]
    activation_eligible: bool
    blocking_reasons: list[AssignmentBlockingReason]
    created_at: datetime


class AnalyticsAssignmentListResponse(ApiModel):
    items: list[AnalyticsAssignmentResponse]
    total: int
    limit: int
    offset: int


class AnalyticsAssignmentRevisionResponse(ApiModel):
    assignment_id: str
    version: int
    snapshot: AnalyticsAssignmentV1
    actor_id: str
    reason: str
    recorded_at: datetime


class AnalyticsAssignmentRevisionListResponse(ApiModel):
    items: list[AnalyticsAssignmentRevisionResponse]
    total: int
    limit: int
    offset: int


class GeneratedAnalyticsRunCreate(ApiModel):
    seed: Annotated[int, Field(ge=0, le=4_294_967_295)] = 0
    sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    observed_at: UtcDateTime


class GeneratedAnalyticsRunResponse(ApiModel):
    run_id: Annotated[str, Field(pattern=r"^run_[0-9a-f]{32}$")]
    assignment_id: Annotated[str, Field(pattern=r"^ana_[0-9a-f]{32}$")]
    assignment_version: int
    execution_scope: Literal["generated_only"] = "generated_only"
    source_sequence: int
    source_observed_at: UtcDateTime
    generator_id: StableName
    generator_version: ImmutableDigest
    input_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    status: Literal["succeeded", "degraded", "failed"]
    failure_code: RuntimeFailureCode | None
    candidate_count: Annotated[int, Field(ge=0, le=300)]
    duration_ms: Annotated[int, Field(ge=0, le=60_000)]
    retention_class: RetentionClass
    started_at: UtcDateTime
    completed_at: UtcDateTime
    reused: bool = False


class AnalyticsObservationResponse(ApiModel):
    observation_id: Annotated[str, Field(pattern=r"^obs_[0-9a-f]{32}$")]
    run_id: Annotated[str, Field(pattern=r"^run_[0-9a-f]{32}$")]
    assignment_id: Annotated[str, Field(pattern=r"^ana_[0-9a-f]{32}$")]
    candidate_index: Annotated[int, Field(ge=0, lt=300)]
    observed_at: UtcDateTime
    processed_at: UtcDateTime
    source_sequence: int
    source_width: Annotated[int, Field(ge=1, le=32_768)]
    source_height: Annotated[int, Field(ge=1, le=32_768)]
    model_id: StableName
    model_version: ImmutableDigest
    class_id: ClassId
    confidence: Confidence
    bbox_x: Annotated[float, Field(ge=0, le=1)]
    bbox_y: Annotated[float, Field(ge=0, le=1)]
    bbox_width: Annotated[float, Field(gt=0, le=1)]
    bbox_height: Annotated[float, Field(gt=0, le=1)]
    lineage: ProcessingLineage
    retention_class: RetentionClass
    created_at: UtcDateTime


class AnalyticsObservationListResponse(ApiModel):
    items: list[AnalyticsObservationResponse]
    total: int
    limit: int
    offset: int


GeneratedTrackingScenarioId = Literal[
    "single-object",
    "two-crossing",
    "short-occlusion",
    "long-occlusion",
    "all-tier-a",
    "discontinuity",
    "overload",
]


class GeneratedTrackingRunCreate(ApiModel):
    scenario_id: GeneratedTrackingScenarioId
    seed: Annotated[int, Field(ge=0, le=4_294_967_295)] = 0
    observed_at: UtcDateTime


class TrackingClassMetricResponse(ApiModel):
    hota: Annotated[float, Field(ge=0, le=1)]
    detection_accuracy: Annotated[float, Field(ge=0, le=1)]
    association_accuracy: Annotated[float, Field(ge=0, le=1)]
    localization_accuracy: Annotated[float, Field(ge=0, le=1)]
    idf1: Annotated[float, Field(ge=0, le=1)]
    id_precision: Annotated[float, Field(ge=0, le=1)]
    id_recall: Annotated[float, Field(ge=0, le=1)]
    id_true_positives: Annotated[int, Field(ge=0)]
    id_false_positives: Annotated[int, Field(ge=0)]
    id_false_negatives: Annotated[int, Field(ge=0)]
    identity_switches: Annotated[int, Field(ge=0)]


class TrackingMetricsResponse(TrackingClassMetricResponse):
    per_class: dict[ClassId, TrackingClassMetricResponse]


class GeneratedTrackingRunResponse(ApiModel):
    run_id: Annotated[str, Field(pattern=r"^trun_[0-9a-f]{32}$")]
    assignment_id: Annotated[str, Field(pattern=r"^ana_[0-9a-f]{32}$")]
    assignment_version: int
    execution_scope: Literal["generated_only"] = "generated_only"
    scenario_id: GeneratedTrackingScenarioId
    seed: int
    input_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    generator_id: StableName
    generator_version: ImmutableDigest
    tracker_id: StableName
    tracker_version: ImmutableDigest
    pipeline_id: StableName
    pipeline_version: ImmutableDigest
    configuration_digest: ImmutableDigest
    status: Literal["succeeded", "failed"]
    failure_code: Literal["resource_exhausted"] | None
    frame_count: Annotated[int, Field(ge=0, le=10_000)]
    transition_count: Annotated[int, Field(ge=0, le=1_000_000)]
    duration_ms: Annotated[int, Field(ge=0, le=60_000)]
    metrics: TrackingMetricsResponse
    retention_class: RetentionClass
    started_at: UtcDateTime
    completed_at: UtcDateTime
    reused: bool = False


class TrackingEpochResponse(ApiModel):
    epoch_id: Annotated[str, Field(pattern=r"^epoch_[0-9a-f]{32}$")]
    run_id: Annotated[str, Field(pattern=r"^trun_[0-9a-f]{32}$")]
    epoch_index: Annotated[int, Field(ge=1)]
    tracker_id: StableName
    tracker_version: ImmutableDigest
    configuration_digest: ImmutableDigest
    start_sequence: Annotated[int, Field(ge=0)]
    end_sequence: Annotated[int, Field(ge=0)] | None
    started_at: UtcDateTime
    ended_at: UtcDateTime | None
    end_reason: Literal[
        "explicit_reset",
        "sequence_gap",
        "sequence_regression",
        "timestamp_regression",
        "configuration_change",
        "source_change",
        "worker_restart",
        "resource_exhausted",
    ] | None


class TrackingEpochListResponse(ApiModel):
    items: list[TrackingEpochResponse]
    total: int
    limit: int
    offset: int


class TrackResponse(ApiModel):
    track_id: Annotated[str, Field(pattern=r"^trk_[0-9a-f]{32}$")]
    epoch_id: Annotated[str, Field(pattern=r"^epoch_[0-9a-f]{32}$")]
    run_id: Annotated[str, Field(pattern=r"^trun_[0-9a-f]{32}$")]
    local_track_number: Annotated[int, Field(ge=1)]
    class_id: ClassId
    state: Literal["started", "updated", "lost", "ended"]
    first_observed_at: UtcDateTime
    first_sequence: Annotated[int, Field(ge=0)]
    latest_observed_at: UtcDateTime
    latest_sequence: Annotated[int, Field(ge=0)]
    last_visible_at: UtcDateTime
    last_visible_sequence: Annotated[int, Field(ge=0)]
    latest_observation_id: Annotated[str, Field(pattern=r"^obs_[0-9a-f]{32}$")]
    bbox_x: Annotated[float, Field(ge=0, le=1)]
    bbox_y: Annotated[float, Field(ge=0, le=1)]
    bbox_width: Annotated[float, Field(gt=0, le=1)]
    bbox_height: Annotated[float, Field(gt=0, le=1)]
    confidence: Confidence
    age_frames: Annotated[int, Field(ge=1)]
    visible_frames: Annotated[int, Field(ge=1)]
    missed_frames: Annotated[int, Field(ge=0)]
    tracker_id: StableName
    tracker_version: ImmutableDigest
    pipeline_id: StableName
    pipeline_version: ImmutableDigest
    taxonomy_version: TaxonomyVersion
    configuration_digest: ImmutableDigest
    retention_class: RetentionClass
    created_at: UtcDateTime
    updated_at: UtcDateTime


class TrackListResponse(ApiModel):
    items: list[TrackResponse]
    total: int
    limit: int
    offset: int


class TrackLifecycleResponse(ApiModel):
    lifecycle_id: Annotated[str, Field(pattern=r"^lfc_[0-9a-f]{32}$")]
    event_id: Annotated[str, Field(pattern=r"^evt_[0-9a-f]{32}$")]
    run_id: Annotated[str, Field(pattern=r"^trun_[0-9a-f]{32}$")]
    transition_index: Annotated[int, Field(ge=0)]
    state: Literal["started", "updated", "lost", "ended"]
    reason: str
    payload: TrackLifecyclePayloadV2
    retention_class: RetentionClass
    created_at: UtcDateTime


class TrackLifecycleListResponse(ApiModel):
    items: list[TrackLifecycleResponse]
    total: int
    limit: int
    offset: int
