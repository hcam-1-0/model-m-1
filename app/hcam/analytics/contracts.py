from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


MAX_EVENT_BYTES = 64 * 1024

EventId = Annotated[str, Field(pattern=r"^evt_[0-9a-f]{32}$")]
AssignmentId = Annotated[str, Field(pattern=r"^ana_[0-9a-f]{32}$")]
ObservationId = Annotated[str, Field(pattern=r"^obs_[0-9a-f]{32}$")]
TrackId = Annotated[str, Field(pattern=r"^trk_[0-9a-f]{32}$")]
TrackerEpoch = Annotated[str, Field(pattern=r"^epoch_[0-9a-f]{32}$")]
AnalyticEventId = Annotated[str, Field(pattern=r"^aevt_[0-9a-f]{32}$")]
StreamId = Annotated[str, Field(pattern=r"^str_[0-9a-f]{32}$")]
CameraId = Annotated[
    str,
    Field(
        min_length=3,
        max_length=160,
        pattern=r"^[a-z][a-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._:-]*$",
    ),
]
Department = Annotated[
    str,
    Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9 ._-]*$"),
]
ActorId = Annotated[
    str,
    Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:@-]*$"),
]
StableName = Annotated[
    str,
    Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]
ImmutableDigest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
TaxonomyVersion = Annotated[
    str,
    Field(pattern=r"^hcam\.[a-z][a-z0-9_.-]*\.v[1-9][0-9]*$", max_length=128),
]
ClassId = Annotated[
    str,
    Field(
        min_length=3,
        max_length=128,
        pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$",
    ),
]
CapabilityId = Annotated[
    str,
    Field(
        min_length=3,
        max_length=128,
        pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$",
    ),
]
ReasonCode = Annotated[
    str,
    Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_.-]*$"),
]
Confidence = Annotated[float, Field(ge=0, le=1)]
NormalizedCoordinate = Annotated[float, Field(ge=0, le=1)]
TrackReference = Annotated[
    str,
    Field(pattern=r"^epoch_[0-9a-f]{32}:trk_[0-9a-f]{32}$"),
]


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_require_utc)]


class AnalyticsContractSafetyError(ValueError):
    """Raised without echoing a sensitive field value into an error message."""


class ContractModel(BaseModel):
    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


class VersionedArtifact(ContractModel):
    id: StableName
    version: ImmutableDigest


class VersionedConfiguration(ContractModel):
    id: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]


class RuntimeReference(ContractModel):
    name: StableName
    version: Annotated[str, Field(min_length=1, max_length=128)]

    @field_validator("version")
    @classmethod
    def version_is_immutable(cls, value: str) -> str:
        if value.strip() != value or value.lower() in {
            "candidate",
            "champion",
            "latest",
            "shadow",
        }:
            raise ValueError("runtime version must resolve to an immutable value")
        return value


class ProcessingLineage(ContractModel):
    code_version: ImmutableDigest
    pipeline: VersionedArtifact
    preprocessing_version: ImmutableDigest
    postprocessing_version: ImmutableDigest
    taxonomy_version: TaxonomyVersion
    policy_version: ImmutableDigest
    runtime: RuntimeReference
    configuration_digest: ImmutableDigest


class NormalizedBoundingBox(ContractModel):
    x: NormalizedCoordinate
    y: NormalizedCoordinate
    width: Annotated[float, Field(gt=0, le=1)]
    height: Annotated[float, Field(gt=0, le=1)]

    @model_validator(mode="after")
    def remains_inside_frame(self) -> NormalizedBoundingBox:
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("normalized bounding box must remain inside the frame")
        return self


class SourceFrame(ContractModel):
    sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    width: Annotated[int, Field(ge=1, le=32_768)]
    height: Annotated[int, Field(ge=1, le=32_768)]
    timestamp_source: Literal[
        "presentation_time",
        "source_clock",
        "receive_clock",
        "generated",
    ]
    timestamp_confidence: Confidence


class ObservationQuality(ContractModel):
    blur_score: Confidence | None = None
    occlusion: Literal["none", "partial", "heavy", "unknown"] = "unknown"
    truncated: bool = False


class ObjectClassification(ContractModel):
    id: ClassId
    confidence: Confidence


class AnalyticsAssignmentV1(ContractModel):
    contract_type: Literal["hcam.analytics.assignment.v1"] = (
        "hcam.analytics.assignment.v1"
    )
    assignment_id: AssignmentId
    department: Department
    stream_id: StreamId
    camera_id: CameraId
    capability: CapabilityId
    desired_state: Literal["enabled", "paused"]
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
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
    retention_class: Literal[
        "derived.analytics.standard",
        "derived.analytics.restricted",
    ]
    actor_id: ActorId
    reason: Annotated[str, Field(min_length=1, max_length=500)]
    approval_record_id: StableName
    updated_at: UtcDateTime

    @field_validator("reason")
    @classmethod
    def reason_is_not_blank(cls, value: str) -> str:
        if not value.strip() or value.strip() != value:
            raise ValueError("reason must be non-blank without outer whitespace")
        return value


class ObservationPayloadV1(ContractModel):
    observation_id: ObservationId
    stream_id: StreamId
    camera_id: CameraId
    observed_at: UtcDateTime
    processed_at: UtcDateTime
    source: SourceFrame
    lineage: ProcessingLineage
    model: VersionedArtifact
    classification: ObjectClassification = Field(
        alias="class",
        serialization_alias="class",
    )
    bbox: NormalizedBoundingBox
    quality: ObservationQuality
    retention_class: Literal[
        "derived.analytics.standard",
        "derived.analytics.restricted",
    ]
    review_state: Literal["unreviewed", "confirmed", "rejected"] = "unreviewed"


class TrackPayloadV1(ContractModel):
    track_id: TrackId
    tracker_epoch: TrackerEpoch
    stream_id: StreamId
    camera_id: CameraId
    state: Literal["started", "updated", "ended", "lost"]
    observed_at: UtcDateTime
    class_id: ClassId
    latest_observation_id: ObservationId
    age_frames: Annotated[int, Field(ge=1, le=2_147_483_647)]
    visible_frames: Annotated[int, Field(ge=1, le=2_147_483_647)]
    tracker: VersionedArtifact
    pipeline: VersionedArtifact
    configuration_digest: ImmutableDigest

    @model_validator(mode="after")
    def visible_frames_do_not_exceed_age(self) -> TrackPayloadV1:
        if self.visible_frames > self.age_frames:
            raise ValueError("visible_frames cannot exceed age_frames")
        return self


class TrackLifecyclePayloadV2(ContractModel):
    track_id: TrackId
    tracker_epoch: TrackerEpoch
    stream_id: StreamId
    camera_id: CameraId
    state: Literal["started", "updated", "lost", "ended"]
    reason: Literal[
        "confirmed",
        "matched",
        "recovered",
        "temporarily_unmatched",
        "lost_timeout",
        "explicit_reset",
        "sequence_gap",
        "sequence_regression",
        "timestamp_regression",
        "configuration_change",
        "source_change",
        "worker_restart",
        "resource_exhausted",
    ]
    first_observed_at: UtcDateTime
    first_sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    observed_at: UtcDateTime
    source_sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    last_visible_at: UtcDateTime
    last_visible_sequence: Annotated[
        int, Field(ge=0, le=9_223_372_036_854_775_807)
    ]
    latest_observation_id: ObservationId
    class_id: ClassId
    bbox: NormalizedBoundingBox
    confidence: Confidence
    age_frames: Annotated[int, Field(ge=1, le=2_147_483_647)]
    visible_frames: Annotated[int, Field(ge=1, le=2_147_483_647)]
    missed_frames: Annotated[int, Field(ge=0, le=2_147_483_647)]
    tracker: VersionedArtifact
    lineage: ProcessingLineage
    retention_class: Literal[
        "derived.analytics.standard",
        "derived.analytics.restricted",
    ]

    @model_validator(mode="after")
    def chronology_and_counts_are_consistent(self) -> TrackLifecyclePayloadV2:
        if self.visible_frames > self.age_frames:
            raise ValueError("visible_frames cannot exceed age_frames")
        if not (
            self.first_observed_at <= self.last_visible_at <= self.observed_at
        ):
            raise ValueError("track lifecycle timestamps are not chronological")
        if self.first_sequence > self.last_visible_sequence:
            raise ValueError("track lifecycle sequences are not chronological")
        if (
            self.reason != "sequence_regression"
            and self.first_sequence > self.source_sequence
        ):
            raise ValueError("track transition sequence precedes the track")
        return self


class AnalyticEventPayloadV1(ContractModel):
    analytic_event_id: AnalyticEventId
    stream_id: StreamId
    camera_id: CameraId
    event_kind: Annotated[
        str,
        Field(
            min_length=3,
            max_length=128,
            pattern=r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$",
        ),
    ]
    observed_at: UtcDateTime
    track_refs: Annotated[list[TrackReference], Field(max_length=64)] = Field(
        default_factory=list
    )
    observation_refs: Annotated[list[ObservationId], Field(max_length=64)] = Field(
        default_factory=list
    )
    rule: VersionedConfiguration
    geometry_ref: VersionedConfiguration
    lineage: ProcessingLineage
    confidence: Confidence
    review_state: Literal["unreviewed", "confirmed", "rejected"] = "unreviewed"
    alert_state: Literal["not_evaluated"] = "not_evaluated"

    @model_validator(mode="after")
    def contains_local_evidence_reference(self) -> AnalyticEventPayloadV1:
        if not self.track_refs and not self.observation_refs:
            raise ValueError("analytic event requires a local evidence reference")
        return self


class DeploymentTargetV1(ContractModel):
    pipeline: VersionedArtifact
    models: Annotated[list[VersionedArtifact], Field(max_length=8)] = Field(
        default_factory=list
    )
    configuration_digest: ImmutableDigest


class ModelDeploymentPayloadV1(ContractModel):
    assignment_id: AssignmentId
    department: Department
    stream_id: StreamId
    camera_id: CameraId
    capability: CapabilityId
    previous: DeploymentTargetV1 | None = None
    current: DeploymentTargetV1 | None = None
    lifecycle_state: Literal[
        "pending",
        "starting",
        "running",
        "degraded",
        "paused",
        "blocked",
        "failed",
    ]
    reason_code: ReasonCode
    actor_id: ActorId
    change_reason: Annotated[str, Field(min_length=1, max_length=500)]
    approval_record_id: StableName
    effective_at: UtcDateTime

    @field_validator("change_reason")
    @classmethod
    def change_reason_is_not_blank(cls, value: str) -> str:
        if not value.strip() or value.strip() != value:
            raise ValueError("change_reason must be non-blank without outer whitespace")
        return value

    @model_validator(mode="after")
    def deployment_transition_changes_target(self) -> ModelDeploymentPayloadV1:
        if self.previous is None and self.current is None:
            raise ValueError(
                "deployment transition requires a previous or current target"
            )
        if self.previous is not None and self.previous == self.current:
            raise ValueError("deployment transition must change the target")
        return self


class AnalyticsEventBase(ContractModel):
    event_id: EventId
    schema_version: Literal[1] = 1
    stream_id: StreamId
    camera_id: CameraId
    partition_key: StreamId
    occurred_at: UtcDateTime

    @model_validator(mode="after")
    def partition_matches_stream(self) -> AnalyticsEventBase:
        if self.partition_key != self.stream_id:
            raise ValueError("partition_key must equal stream_id")
        return self


class AnalyticsEventBaseV2(ContractModel):
    event_id: EventId
    schema_version: Literal[2] = 2
    stream_id: StreamId
    camera_id: CameraId
    partition_key: StreamId
    occurred_at: UtcDateTime

    @model_validator(mode="after")
    def partition_matches_stream(self) -> AnalyticsEventBaseV2:
        if self.partition_key != self.stream_id:
            raise ValueError("partition_key must equal stream_id")
        return self


class ObservationCreatedV1(AnalyticsEventBase):
    event_type: Literal["hcam.analytics.observation.created.v1"] = (
        "hcam.analytics.observation.created.v1"
    )
    payload: ObservationPayloadV1

    @model_validator(mode="after")
    def payload_scope_matches_envelope(self) -> ObservationCreatedV1:
        _require_matching_scope(self, self.payload)
        return self


class TrackUpdatedV1(AnalyticsEventBase):
    event_type: Literal["hcam.analytics.track.updated.v1"] = (
        "hcam.analytics.track.updated.v1"
    )
    payload: TrackPayloadV1

    @model_validator(mode="after")
    def payload_scope_matches_envelope(self) -> TrackUpdatedV1:
        _require_matching_scope(self, self.payload)
        return self


class TrackLifecycleV2(AnalyticsEventBaseV2):
    event_type: Literal["hcam.analytics.track.lifecycle.v2"] = (
        "hcam.analytics.track.lifecycle.v2"
    )
    payload: TrackLifecyclePayloadV2

    @model_validator(mode="after")
    def payload_scope_matches_envelope(self) -> TrackLifecycleV2:
        _require_matching_scope(self, self.payload)
        return self


class AnalyticEventCreatedV1(AnalyticsEventBase):
    event_type: Literal["hcam.analytics.event.created.v1"] = (
        "hcam.analytics.event.created.v1"
    )
    payload: AnalyticEventPayloadV1

    @model_validator(mode="after")
    def payload_scope_matches_envelope(self) -> AnalyticEventCreatedV1:
        _require_matching_scope(self, self.payload)
        return self


class ModelDeploymentChangedV1(AnalyticsEventBase):
    event_type: Literal["hcam.analytics.model.deployment.changed.v1"] = (
        "hcam.analytics.model.deployment.changed.v1"
    )
    payload: ModelDeploymentPayloadV1

    @model_validator(mode="after")
    def payload_scope_matches_envelope(self) -> ModelDeploymentChangedV1:
        _require_matching_scope(self, self.payload)
        return self


AnalyticsEvent: TypeAlias = (
    ObservationCreatedV1
    | TrackUpdatedV1
    | TrackLifecycleV2
    | AnalyticEventCreatedV1
    | ModelDeploymentChangedV1
)
AnalyticsEventModel: TypeAlias = type[
    ObservationCreatedV1
    | TrackUpdatedV1
    | TrackLifecycleV2
    | AnalyticEventCreatedV1
    | ModelDeploymentChangedV1
]

ANALYTICS_EVENT_MODELS: dict[str, AnalyticsEventModel] = {
    "hcam.analytics.observation.created.v1": ObservationCreatedV1,
    "hcam.analytics.track.updated.v1": TrackUpdatedV1,
    "hcam.analytics.track.lifecycle.v2": TrackLifecycleV2,
    "hcam.analytics.event.created.v1": AnalyticEventCreatedV1,
    "hcam.analytics.model.deployment.changed.v1": ModelDeploymentChangedV1,
}


def _require_matching_scope(
    envelope: AnalyticsEventBase | AnalyticsEventBaseV2,
    payload: ObservationPayloadV1
    | TrackPayloadV1
    | TrackLifecyclePayloadV2
    | AnalyticEventPayloadV1
    | ModelDeploymentPayloadV1,
) -> None:
    if payload.stream_id != envelope.stream_id:
        raise ValueError("payload stream_id must match the event envelope")
    if payload.camera_id != envelope.camera_id:
        raise ValueError("payload camera_id must match the event envelope")


_PROHIBITED_FIELD_NAMES = frozenset(
    {
        "access_token",
        "biometric",
        "biometrics",
        "clip",
        "credential",
        "credentials",
        "crop",
        "embedding",
        "face_embedding",
        "face_template",
        "frame_bytes",
        "frame_data",
        "government_data",
        "government_record",
        "image",
        "image_bytes",
        "locator",
        "management_locator",
        "media",
        "owner_details",
        "owner_record",
        "password",
        "person_embedding",
        "raw_frame",
        "refresh_token",
        "secret",
        "secret_ref",
        "source_url",
        "stream_url",
        "username",
        "video",
        "watchlist",
        "watchlist_match",
    }
)
_PROHIBITED_VALUE = re.compile(
    r"(?i)(?:\b(?:rtsp|rtsps|http|https)://|\bbearer\s+|"
    r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----)"
)


def inspect_contract_safety(value: object, *, path: str = "$") -> None:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", by_alias=True)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AnalyticsContractSafetyError(
                    f"analytics contract contains a non-string key at {path}"
                )
            normalized = key.lower().replace("-", "_")
            if normalized in _PROHIBITED_FIELD_NAMES:
                raise AnalyticsContractSafetyError(
                    f"analytics contract contains prohibited field at {path}.{key}"
                )
            inspect_contract_safety(item, path=f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            inspect_contract_safety(item, path=f"{path}[{index}]")
        return
    if isinstance(value, str) and _PROHIBITED_VALUE.search(value):
        raise AnalyticsContractSafetyError(
            f"analytics contract contains prohibited sensitive value at {path}"
        )


def canonical_contract_json(value: BaseModel | Mapping[str, object]) -> str:
    document: object
    if isinstance(value, BaseModel):
        document = value.model_dump(mode="json", by_alias=True)
    else:
        document = value
    inspect_contract_safety(document)
    try:
        return (
            json.dumps(
                document,
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("analytics contract must be canonical JSON data") from exc


def _bounded_document(
    document: Mapping[str, object],
    *,
    max_bytes: int,
) -> None:
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    serialized = canonical_contract_json(document)
    if len(serialized.encode("utf-8")) > max_bytes:
        raise ValueError("analytics event exceeds the maximum payload size")


def parse_analytics_assignment(
    document: Mapping[str, object],
    *,
    forward_compatible: bool = False,
) -> AnalyticsAssignmentV1:
    inspect_contract_safety(document)
    return AnalyticsAssignmentV1.model_validate(
        document,
        extra="ignore" if forward_compatible else "forbid",
    )


def parse_analytics_event(
    document: Mapping[str, object],
    *,
    forward_compatible: bool = False,
    max_bytes: int = MAX_EVENT_BYTES,
) -> AnalyticsEvent:
    _bounded_document(document, max_bytes=max_bytes)
    event_type = document.get("event_type")
    if not isinstance(event_type, str) or event_type not in ANALYTICS_EVENT_MODELS:
        raise ValueError("unsupported analytics event type or major version")
    model = ANALYTICS_EVENT_MODELS[event_type]
    return model.model_validate(
        document,
        extra="ignore" if forward_compatible else "forbid",
    )


def analytics_contract_bundle() -> dict[str, Any]:
    from hcam.analytics.geometry import (
        GeometryDefinitionV1,
        GeometryScheduleV1,
        LineGeometryV1,
        ZoneGeometryV1,
    )
    from hcam.analytics.runtime import (
        RuntimeAdapterDescriptorV1,
        RuntimeBatchRequestV1,
        RuntimeBatchRequestV2,
        RuntimeBatchResultV1,
    )
    from hcam.analytics.taxonomy import TaxonomyManifestV1

    return {
        "contract_format": "hcam.analytics.contract-bundle.v1",
        "assignment": AnalyticsAssignmentV1.model_json_schema(
            by_alias=True,
            mode="validation",
        ),
        "events": {
            event_type: model.model_json_schema(by_alias=True, mode="validation")
            for event_type, model in sorted(ANALYTICS_EVENT_MODELS.items())
        },
        "geometry": {
            "definition": GeometryDefinitionV1.model_json_schema(mode="validation"),
            "line": LineGeometryV1.model_json_schema(mode="validation"),
            "schedule": GeometryScheduleV1.model_json_schema(mode="validation"),
            "zone": ZoneGeometryV1.model_json_schema(mode="validation"),
        },
        "runtime": {
            "adapter": RuntimeAdapterDescriptorV1.model_json_schema(mode="validation"),
            "request": RuntimeBatchRequestV1.model_json_schema(mode="validation"),
            "request_v2": RuntimeBatchRequestV2.model_json_schema(mode="validation"),
            "result": RuntimeBatchResultV1.model_json_schema(mode="validation"),
        },
        "taxonomy": TaxonomyManifestV1.model_json_schema(mode="validation"),
        "delivery": {
            "deduplication_key": "event_id",
            "ordering_scope": "stream_id",
            "partition_key": "stream_id",
            "semantics": "at_least_once",
        },
        "maximum_event_bytes": MAX_EVENT_BYTES,
        "prohibited_fields": sorted(_PROHIBITED_FIELD_NAMES),
    }
