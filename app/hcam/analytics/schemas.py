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
