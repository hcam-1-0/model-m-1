from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from hcam.analytics.contracts import (
    ActorId,
    AssignmentId,
    CameraId,
    ClassId,
    ContractModel,
    Department,
    ImmutableDigest,
    StableName,
    StreamId,
    UtcDateTime,
)


PrimitiveSignal = Literal[
    "line_crossing",
    "zone_entry",
    "zone_exit",
    "zone_presence",
    "zone_dwell_threshold",
    "zone_occupancy_entered",
    "zone_occupancy_exited",
]
RuleNodeKind = Literal[
    "spatial",
    "all",
    "any",
    "not",
    "sequence",
    "within",
    "for_at_least",
    "cooldown",
    "repeat_limit",
]


class RuleNodeV1(ContractModel):
    node_id: StableName
    kind: RuleNodeKind
    inputs: Annotated[list[StableName], Field(max_length=8)] = Field(
        default_factory=list
    )
    signal: PrimitiveSignal | None = None
    duration_ms: Annotated[int, Field(ge=1, le=3_600_000)] | None = None
    repeat_limit: Annotated[int, Field(ge=1, le=100)] | None = None

    @model_validator(mode="after")
    def fields_match_kind(self) -> RuleNodeV1:
        if self.kind == "spatial":
            if self.signal is None or self.inputs:
                raise ValueError("spatial node requires one signal and no inputs")
        elif self.signal is not None:
            raise ValueError("only spatial nodes may declare a signal")

        if self.kind in {"all", "any"} and not self.inputs:
            raise ValueError("all and any nodes require inputs")
        if self.kind == "sequence" and len(self.inputs) < 2:
            raise ValueError("sequence node requires at least two inputs")
        if self.kind in {"not", "within", "for_at_least", "cooldown", "repeat_limit"}:
            if len(self.inputs) != 1:
                raise ValueError(f"{self.kind} node requires exactly one input")
        if self.kind in {"within", "for_at_least", "cooldown", "sequence"}:
            if self.duration_ms is None:
                raise ValueError(f"{self.kind} node requires duration_ms")
        elif self.duration_ms is not None:
            raise ValueError(f"{self.kind} node cannot declare duration_ms")
        if self.kind == "repeat_limit":
            if self.repeat_limit is None:
                raise ValueError("repeat_limit node requires repeat_limit")
        elif self.repeat_limit is not None:
            raise ValueError(f"{self.kind} node cannot declare repeat_limit")
        return self


class RuleGraphV1(ContractModel):
    graph_type: Literal["hcam.analytics.rule_graph.v1"] = (
        "hcam.analytics.rule_graph.v1"
    )
    nodes: Annotated[list[RuleNodeV1], Field(min_length=1, max_length=64)]
    output_node_id: StableName

    @model_validator(mode="after")
    def graph_is_bounded_topological_dag(self) -> RuleGraphV1:
        identifiers = [node.node_id for node in self.nodes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("rule graph node identifiers must be unique")
        seen: set[str] = set()
        depths: dict[str, int] = {}
        for node in self.nodes:
            if any(reference not in seen for reference in node.inputs):
                raise ValueError("rule graph inputs must reference earlier nodes")
            depth = 1 + max((depths[reference] for reference in node.inputs), default=0)
            if depth > 16:
                raise ValueError("rule graph depth exceeds 16")
            depths[node.node_id] = depth
            seen.add(node.node_id)
        if self.output_node_id not in seen:
            raise ValueError("rule graph output must reference a node")
        static_cost = sum(1 + len(node.inputs) for node in self.nodes)
        if static_cost > 256:
            raise ValueError("rule graph static cost exceeds 256")
        return self

    @property
    def static_cost(self) -> int:
        return sum(1 + len(node.inputs) for node in self.nodes)


EventKind = Literal[
    "hcam.analytics.line.crossing.v1",
    "hcam.analytics.zone.entry.v1",
    "hcam.analytics.zone.exit.v1",
    "hcam.analytics.zone.dwell.threshold_met.v1",
    "hcam.analytics.zone.occupancy.threshold_entered.v1",
    "hcam.analytics.zone.occupancy.threshold_exited.v1",
]


_SIGNAL_FOR_EVENT: dict[str, str] = {
    "hcam.analytics.line.crossing.v1": "line_crossing",
    "hcam.analytics.zone.entry.v1": "zone_entry",
    "hcam.analytics.zone.exit.v1": "zone_exit",
    "hcam.analytics.zone.dwell.threshold_met.v1": "zone_dwell_threshold",
    "hcam.analytics.zone.occupancy.threshold_entered.v1": (
        "zone_occupancy_entered"
    ),
    "hcam.analytics.zone.occupancy.threshold_exited.v1": (
        "zone_occupancy_exited"
    ),
}


class GeometryRuleV1(ContractModel):
    contract_type: Literal["hcam.analytics.geometry_rule.v1"] = (
        "hcam.analytics.geometry_rule.v1"
    )
    rule_id: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    status: Literal["draft", "approved", "retired"]
    department: Department
    assignment_id: AssignmentId
    stream_id: StreamId
    camera_id: CameraId
    geometry_id: StableName
    geometry_version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    event_kind: EventKind
    class_filter: Annotated[list[ClassId], Field(min_length=1, max_length=7)]
    anchor_policy: Literal["bottom_center", "bbox_center"] = "bottom_center"
    boundary_policy: Literal["inside_inclusive", "inside_exclusive"] = (
        "inside_inclusive"
    )
    initial_state_policy: Literal["initialize_without_event"] = (
        "initialize_without_event"
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
    configuration_digest: ImmutableDigest
    retention_class: Literal[
        "derived.analytics.standard",
        "derived.analytics.restricted",
    ]
    owner_id: ActorId
    approval_record_id: StableName | None = None
    effective_from: UtcDateTime
    effective_until: UtcDateTime | None = None
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @field_validator("class_filter")
    @classmethod
    def class_filter_is_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("class filter values must be unique")
        return value

    @model_validator(mode="after")
    def event_configuration_is_closed(self) -> GeometryRuleV1:
        is_line = self.event_kind == "hcam.analytics.line.crossing.v1"
        is_dwell = self.event_kind == "hcam.analytics.zone.dwell.threshold_met.v1"
        is_occupancy = self.event_kind.startswith("hcam.analytics.zone.occupancy.")
        if is_line:
            if self.line_direction is None or self.deadband is None:
                raise ValueError("line rule requires direction and deadband")
            if self.rearm_distance is None or self.rearm_distance < self.deadband:
                raise ValueError("line rearm distance must be at least the deadband")
            if any(
                value is not None
                for value in (
                    self.zone_hysteresis,
                    self.dwell_threshold_ms,
                    self.occupancy_enter_threshold,
                    self.occupancy_reset_threshold,
                )
            ):
                raise ValueError("line rule contains zone-only fields")
        else:
            if self.zone_hysteresis is None:
                raise ValueError("zone rule requires zone_hysteresis")
            if any(
                value is not None
                for value in (self.line_direction, self.deadband, self.rearm_distance)
            ):
                raise ValueError("zone rule contains line-only fields")
        if is_dwell != (self.dwell_threshold_ms is not None):
            raise ValueError("dwell threshold is permitted only on dwell rules")
        if is_occupancy:
            if (
                self.occupancy_enter_threshold is None
                or self.occupancy_reset_threshold is None
                or self.occupancy_reset_threshold >= self.occupancy_enter_threshold
            ):
                raise ValueError("occupancy reset threshold must be below enter threshold")
        elif any(
            value is not None
            for value in (
                self.occupancy_enter_threshold,
                self.occupancy_reset_threshold,
            )
        ):
            raise ValueError("occupancy thresholds are permitted only on occupancy rules")
        required_signal = _SIGNAL_FOR_EVENT[self.event_kind]
        signals = {
            node.signal for node in self.graph.nodes if node.signal is not None
        }
        if required_signal not in signals:
            raise ValueError("rule graph does not include its event primitive")
        if self.status in {"approved", "retired"} and self.approval_record_id is None:
            raise ValueError("approved or retired rule requires approval record")
        if self.effective_until is not None and self.effective_until <= self.effective_from:
            raise ValueError("rule effective interval is invalid")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")
        return self
