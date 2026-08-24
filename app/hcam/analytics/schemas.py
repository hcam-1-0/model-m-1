from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hcam.analytics.contracts import (
    AnalyticsAssignmentV1,
    CapabilityId,
    Confidence,
    ImmutableDigest,
    StableName,
    TaxonomyVersion,
    VersionedArtifact,
    VersionedConfiguration,
)


RetentionClass = Literal[
    "derived.analytics.standard",
    "derived.analytics.restricted",
]
AssignmentBlockingReason = Literal[
    "runtime_unconfigured",
    "taxonomy_unapproved",
    "retention_policy_unapproved",
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
    lifecycle_state: Literal["blocked"] = "blocked"
    reason_code: Literal["owner_gates_pending"] = "owner_gates_pending"
    activation_eligible: Literal[False] = False
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
