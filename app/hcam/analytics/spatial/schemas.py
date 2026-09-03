from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from hcam.analytics.contracts import (
    ClassId,
    ContractModel,
    ImmutableDigest,
    StableName,
    UtcDateTime,
)
from hcam.analytics.geometry import GeometryScheduleV1, GeometryShapeV1
from hcam.analytics.spatial.contracts import EventKind, RuleGraphV1


class GeometryCreate(ContractModel):
    geometry_id: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    shape: Annotated[GeometryShapeV1, Field(discriminator="kind")]
    schedule: GeometryScheduleV1 = Field(default_factory=GeometryScheduleV1)
    intended_use: Annotated[str, Field(min_length=1, max_length=500)]
    policy_version: ImmutableDigest


class GeometryApproval(ContractModel):
    approval_record_id: StableName


class GeometryResponse(ContractModel):
    geometry_record_id: Annotated[str, Field(pattern=r"^geom_[0-9a-f]{32}$")]
    record_version: Annotated[int, Field(ge=1)]
    geometry_id: StableName
    version: Annotated[int, Field(ge=1)]
    department: str
    stream_id: str
    camera_id: str
    status: Literal["draft", "approved", "retired"]
    shape: Annotated[GeometryShapeV1, Field(discriminator="kind")]
    schedule: GeometryScheduleV1
    intended_use: str
    policy_version: ImmutableDigest
    configuration_digest: ImmutableDigest
    wkb_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    shapely_version: str
    geos_version: str
    owner_id: str
    approval_record_id: StableName | None
    created_at: UtcDateTime
    updated_at: UtcDateTime


class GeometryListResponse(ContractModel):
    items: list[GeometryResponse]
    total: int
    limit: int
    offset: int


class GeometryRuleCreate(ContractModel):
    rule_id: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    assignment_id: Annotated[str, Field(pattern=r"^ana_[0-9a-f]{32}$")]
    event_kind: EventKind
    class_filter: Annotated[list[ClassId], Field(min_length=1, max_length=7)]
    anchor_policy: Literal["bottom_center", "bbox_center"] = "bottom_center"
    boundary_policy: Literal["inside_inclusive", "inside_exclusive"] = (
        "inside_inclusive"
    )
    line_direction: Literal["both", "a_to_b", "b_to_a"] | None = None
    deadband: Annotated[float, Field(ge=0, le=0.1)] | None = None
    rearm_distance: Annotated[float, Field(gt=0, le=0.2)] | None = None
    zone_hysteresis: Annotated[float, Field(ge=0, le=0.1)] | None = None
    dwell_threshold_ms: Annotated[int, Field(ge=100, le=3_600_000)] | None = None
    occlusion_grace_ms: Annotated[int, Field(ge=0, le=60_000)] = 0
    occupancy_enter_threshold: Annotated[int, Field(ge=1, le=512)] | None = None
    occupancy_reset_threshold: Annotated[int, Field(ge=0, le=511)] | None = None
    cel_condition: Annotated[str, Field(min_length=1, max_length=512)] = "true"
    graph: RuleGraphV1
    retention_class: Literal[
        "derived.analytics.standard",
        "derived.analytics.restricted",
    ]
    effective_from: UtcDateTime
    effective_until: UtcDateTime | None = None


class GeometryRuleApproval(ContractModel):
    approval_record_id: StableName


class GeometryRuleResponse(ContractModel):
    rule_record_id: Annotated[str, Field(pattern=r"^rule_[0-9a-f]{32}$")]
    record_version: Annotated[int, Field(ge=1)]
    geometry_record_id: Annotated[str, Field(pattern=r"^geom_[0-9a-f]{32}$")]
    geometry_id: StableName
    geometry_version: Annotated[int, Field(ge=1)]
    rule_id: StableName
    version: Annotated[int, Field(ge=1)]
    status: Literal["draft", "approved", "retired"]
    department: str
    assignment_id: str
    stream_id: str
    camera_id: str
    event_kind: EventKind
    class_filter: list[ClassId]
    anchor_policy: Literal["bottom_center", "bbox_center"]
    boundary_policy: Literal["inside_inclusive", "inside_exclusive"]
    initial_state_policy: Literal["initialize_without_event"]
    line_direction: Literal["both", "a_to_b", "b_to_a"] | None
    deadband: float | None
    rearm_distance: float | None
    zone_hysteresis: float | None
    dwell_threshold_ms: int | None
    occlusion_grace_ms: int
    occupancy_enter_threshold: int | None
    occupancy_reset_threshold: int | None
    cel_condition: str
    graph: RuleGraphV1
    configuration_digest: ImmutableDigest
    checked_cel_digest: ImmutableDigest
    static_cost: int
    retention_class: str
    owner_id: str
    approval_record_id: StableName | None
    effective_from: UtcDateTime
    effective_until: UtcDateTime | None
    created_at: UtcDateTime
    updated_at: UtcDateTime


class GeometryRuleListResponse(ContractModel):
    items: list[GeometryRuleResponse]
    total: int
    limit: int
    offset: int


class RuleCompilePreview(ContractModel):
    configuration_digest: ImmutableDigest
    checked_cel_digest: ImmutableDigest
    cel_static_cost: int
    graph_static_cost: int
    total_static_cost: int
    geometry_digest: ImmutableDigest
    accepted: Literal[True] = True


GeneratedGeometryScenarioId = Literal[
    "c10-line-crossing",
    "c10-zone-lifecycle",
    "c10-dwell",
    "c10-occupancy",
    "c10-out-of-order",
]


class GeneratedGeometryRunCreate(ContractModel):
    scenario_id: GeneratedGeometryScenarioId
    rule_record_ids: Annotated[list[str], Field(min_length=1, max_length=64)]
    seed: Annotated[int, Field(ge=0, le=4_294_967_295)] = 0
    observed_at: UtcDateTime


class GeneratedGeometryRunResponse(ContractModel):
    run_id: Annotated[str, Field(pattern=r"^grun_[0-9a-f]{32}$")]
    assignment_id: Annotated[str, Field(pattern=r"^ana_[0-9a-f]{32}$")]
    execution_scope: Literal["generated_only"]
    scenario_id: GeneratedGeometryScenarioId
    seed: int
    input_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    configuration_digest: ImmutableDigest
    status: Literal["succeeded", "failed"]
    close_reason: str | None
    input_count: int
    event_count: int
    duplicate_count: int
    late_count: int
    maximum_buffer_depth: int
    maximum_candidate_count: int
    maximum_state_count: int
    duration_ms: int
    retention_class: str
    started_at: UtcDateTime
    completed_at: UtcDateTime
    reused: bool = False


class AnalyticEventResponse(ContractModel):
    event_id: Annotated[str, Field(pattern=r"^evt_[0-9a-f]{32}$")]
    event_kind: EventKind
    occurred_at: UtcDateTime
    department: str
    assignment_id: str
    stream_id: str
    camera_id: str
    epoch_id: str
    track_id: str | None
    lifecycle_id: str
    source_sequence: int
    payload: dict[str, object]
    retention_class: str
    alert_state: Literal["not_evaluated"]


class AnalyticEventListResponse(ContractModel):
    items: list[AnalyticEventResponse]
    total: int
    limit: int
    offset: int
