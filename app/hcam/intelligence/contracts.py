from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated, Literal, TypeAlias

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


UtcDateTime = Annotated[datetime, AfterValidator(_utc)]
Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
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
OpaqueRef = Annotated[str, Field(pattern=r"^ref_[0-9a-f]{32}$")]
RuleId = Annotated[str, Field(pattern=r"^irule_[0-9a-f]{32}$")]
HypothesisId = Annotated[str, Field(pattern=r"^hyp_[0-9a-f]{32}$")]
EvidenceId = Annotated[str, Field(pattern=r"^evid_[0-9a-f]{32}$")]
ProviderId = Annotated[str, Field(pattern=r"^prov_[0-9a-f]{32}$")]
QueryId = Annotated[str, Field(pattern=r"^qry_[0-9a-f]{32}$")]
AlertId = Annotated[str, Field(pattern=r"^alt_[0-9a-f]{32}$")]
TimelineId = Annotated[str, Field(pattern=r"^tml_[0-9a-f]{32}$")]
TimelineEntryId = Annotated[str, Field(pattern=r"^tent_[0-9a-f]{32}$")]
Confidence = Annotated[float, Field(ge=0, le=1)]
ReasonText = Annotated[str, Field(min_length=8, max_length=1000)]
RetentionClass = Literal[
    "derived.intelligence.standard",
    "derived.intelligence.restricted",
    "audit.security",
]
AuthorityClass = Literal[
    "mandatory_review",
    "bounded_system_health",
    "future_autonomous_action",
]


class ContractModel(BaseModel):
    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


class ChronologyV1(ContractModel):
    occurred_at: UtcDateTime
    observed_at: UtcDateTime
    received_at: UtcDateTime
    recorded_at: UtcDateTime
    corrected_at: UtcDateTime | None = None

    @model_validator(mode="after")
    def ordered(self) -> ChronologyV1:
        if not (
            self.occurred_at
            <= self.observed_at
            <= self.received_at
            <= self.recorded_at
        ):
            raise ValueError("event chronology is not ordered")
        if self.corrected_at is not None and self.corrected_at < self.recorded_at:
            raise ValueError("correction cannot precede durable recording")
        return self


Longitude = Annotated[float, Field(ge=-180, le=180)]
Latitude = Annotated[float, Field(ge=-90, le=90)]
Position = tuple[Longitude, Latitude]


class GeoJsonPointV1(ContractModel):
    type: Literal["Point"] = "Point"
    coordinates: Position


class GeoJsonPolygonV1(ContractModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: Annotated[
        list[Annotated[list[Position], Field(min_length=4, max_length=256)]],
        Field(min_length=1, max_length=8),
    ]

    @field_validator("coordinates")
    @classmethod
    def rings_are_closed(cls, value: list[list[Position]]) -> list[list[Position]]:
        for ring in value:
            if ring[0] != ring[-1]:
                raise ValueError("GeoJSON polygon rings must be closed")
            if len(set(ring[:-1])) < 3:
                raise ValueError("GeoJSON polygon rings must have three unique positions")
        return value


GeoJsonGeometryV1: TypeAlias = Annotated[
    GeoJsonPointV1 | GeoJsonPolygonV1,
    Field(discriminator="type"),
]


class GeoJsonProfileV1(ContractModel):
    contract_type: Literal["hcam.intelligence.geojson-profile.v1"] = (
        "hcam.intelligence.geojson-profile.v1"
    )
    crs: Literal["EPSG:4326"] = "EPSG:4326"
    geometry: GeoJsonGeometryV1
    precision_decimal_places: Annotated[int, Field(ge=0, le=7)] = 7


class ProvenanceV1(ContractModel):
    contract_type: Literal["hcam.intelligence.provenance.v1"] = (
        "hcam.intelligence.provenance.v1"
    )
    source_ref: OpaqueRef
    source_digest: Digest
    activity_id: StableName
    activity_digest: Digest
    agent_kind: Literal["generated_fixture", "service", "operator"]
    agent_id: ActorId
    policy_version: Digest
    transaction_id: StableName
    generated_only: Literal[True] = True


EvidenceRole = Literal[
    "supports",
    "contradicts",
    "missing",
    "stale",
    "supersedes",
    "retracts",
]


class EvidenceReferenceV1(ContractModel):
    contract_type: Literal["hcam.intelligence.evidence-reference.v1"] = (
        "hcam.intelligence.evidence-reference.v1"
    )
    evidence_id: EvidenceId
    role: EvidenceRole
    source_type: Literal[
        "analytics_event",
        "generated_reference",
        "system_health",
        "operator_observation",
    ]
    source_ref: OpaqueRef
    source_digest: Digest
    sequence: Annotated[int, Field(ge=0, le=9_223_372_036_854_775_807)]
    chronology: ChronologyV1
    provenance: ProvenanceV1


class HypothesisNodeV1(ContractModel):
    node_id: StableName
    kind: Literal["hypothesis", "evidence", "constraint"]
    reference_id: StableName


class HypothesisEdgeV1(ContractModel):
    edge_id: StableName
    source_node_id: StableName
    target_node_id: StableName
    role: EvidenceRole


class HypothesisGraphV1(ContractModel):
    nodes: Annotated[list[HypothesisNodeV1], Field(min_length=1, max_length=1024)]
    edges: Annotated[list[HypothesisEdgeV1], Field(max_length=4096)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def graph_is_referentially_valid(self) -> HypothesisGraphV1:
        node_ids = [node.node_id for node in self.nodes]
        edge_ids = [edge.edge_id for edge in self.edges]
        if len(node_ids) != len(set(node_ids)) or len(edge_ids) != len(set(edge_ids)):
            raise ValueError("hypothesis graph identifiers must be unique")
        known = set(node_ids)
        if any(
            edge.source_node_id not in known or edge.target_node_id not in known
            for edge in self.edges
        ):
            raise ValueError("hypothesis edge references an unknown node")
        return self


class FlatHypothesisProjectionV1(ContractModel):
    hypothesis_id: HypothesisId
    graph_digest: Digest
    projection_version: Literal["hcam.intelligence.flat-projection.v1"] = (
        "hcam.intelligence.flat-projection.v1"
    )
    event_count: Annotated[int, Field(ge=0, le=4096)]
    supporting_evidence_count: Annotated[int, Field(ge=0, le=256)]
    contradiction_count: Annotated[int, Field(ge=0, le=256)]
    summary_code: Annotated[
        str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")
    ]


class CorrelationHypothesisV1(ContractModel):
    contract_type: Literal["hcam.intelligence.correlation-hypothesis.v1"] = (
        "hcam.intelligence.correlation-hypothesis.v1"
    )
    hypothesis_id: HypothesisId
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    department: Department
    hypothesis_key: Digest
    subject_kind: Literal["anonymous_person", "vehicle", "object", "event_group"]
    state: Literal["proposed", "abstained", "retracted", "corrected"]
    authority_class: Literal["mandatory_review"] = "mandatory_review"
    operational: Literal[False] = False
    generated_only: Literal[True] = True
    confidence: Confidence
    uncertainty: Confidence
    abstained: bool
    contradiction_count: Annotated[int, Field(ge=0, le=256)]
    evidence: Annotated[list[EvidenceReferenceV1], Field(max_length=256)]
    graph: HypothesisGraphV1
    flat_projection: FlatHypothesisProjectionV1
    chronology: ChronologyV1
    provenance: ProvenanceV1
    retention_class: RetentionClass

    @model_validator(mode="after")
    def uncertainty_and_projection_are_consistent(self) -> CorrelationHypothesisV1:
        if self.abstained != (self.state == "abstained"):
            raise ValueError("abstention state is inconsistent")
        if self.flat_projection.hypothesis_id != self.hypothesis_id:
            raise ValueError("flat projection references another hypothesis")
        if self.contradiction_count != sum(
            item.role == "contradicts" for item in self.evidence
        ):
            raise ValueError("contradiction count does not match evidence")
        return self


class AdaptiveLaneResultV1(ContractModel):
    contract_type: Literal["hcam.intelligence.adaptive-lane-result.v1"] = (
        "hcam.intelligence.adaptive-lane-result.v1"
    )
    lane: Literal["deterministic", "probabilistic", "temporal_graph", "ensemble"]
    status: Literal["unavailable", "skipped", "completed", "failed"]
    score: Confidence | None = None
    uncertainty: Confidence | None = None
    abstained: bool
    evidence_refs: Annotated[list[EvidenceId], Field(max_length=256)] = Field(
        default_factory=list
    )
    failure_code: Literal[
        "runtime_disabled",
        "capability_unavailable",
        "resource_budget_exceeded",
        "invalid_generated_input",
    ] | None = None
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def state_is_consistent(self) -> AdaptiveLaneResultV1:
        if self.status == "completed" and self.score is None:
            raise ValueError("completed lane requires a score")
        if self.status != "completed" and self.score is not None:
            raise ValueError("inactive lane cannot contain a score")
        if self.status == "failed" and self.failure_code is None:
            raise ValueError("failed lane requires a safe failure code")
        if self.status != "failed" and self.failure_code is not None:
            raise ValueError("failure code is only valid for a failed lane")
        return self


RuleValue: TypeAlias = str | int | float | bool


class RuleNodeV1(ContractModel):
    node_id: StableName
    kind: Literal[
        "event",
        "predicate",
        "sequence",
        "window",
        "count",
        "absence",
        "cooldown",
    ]
    inputs: Annotated[list[StableName], Field(max_length=16)] = Field(
        default_factory=list
    )
    field: Annotated[
        str, Field(pattern=r"^[a-z][a-z0-9_.]{0,127}$")
    ] | None = None
    operator: Literal["eq", "ne", "lt", "lte", "gt", "gte", "in"] | None = None
    value: RuleValue | None = None
    duration_ms: Annotated[int, Field(ge=1, le=86_400_000)] | None = None
    threshold: Annotated[int, Field(ge=1, le=100_000)] | None = None

    @model_validator(mode="after")
    def parameters_match_kind(self) -> RuleNodeV1:
        if self.kind == "predicate":
            if self.field is None or self.operator is None or self.value is None:
                raise ValueError("predicate requires field, operator, and value")
        elif any(value is not None for value in (self.field, self.operator, self.value)):
            raise ValueError("only a predicate may contain predicate parameters")
        if self.kind in {"window", "absence", "cooldown"}:
            if self.duration_ms is None:
                raise ValueError("temporal node requires a duration")
        elif self.duration_ms is not None:
            raise ValueError("duration is only valid on a temporal node")
        if self.kind == "count":
            if self.threshold is None:
                raise ValueError("count node requires a threshold")
        elif self.threshold is not None:
            raise ValueError("threshold is only valid on a count node")
        return self


class RuleGraphV1(ContractModel):
    nodes: Annotated[list[RuleNodeV1], Field(min_length=1, max_length=320)]
    output_node_id: StableName

    @model_validator(mode="after")
    def is_acyclic_and_bounded(self) -> RuleGraphV1:
        ids = [node.node_id for node in self.nodes]
        if len(ids) != len(set(ids)) or self.output_node_id not in set(ids):
            raise ValueError("rule node identifiers are invalid")
        known = set(ids)
        if any(reference not in known for node in self.nodes for reference in node.inputs):
            raise ValueError("rule node references an unknown input")
        incoming = {node.node_id: set(node.inputs) for node in self.nodes}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ValueError("rule graph must be acyclic")
            if node_id in visited:
                return
            visiting.add(node_id)
            for dependency in incoming[node_id]:
                visit(dependency)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in ids:
            visit(node_id)
        return self


class IntelligenceRuleV1(ContractModel):
    contract_type: Literal["hcam.intelligence.rule.v1"] = "hcam.intelligence.rule.v1"
    rule_id: RuleId
    rule_key: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    department: Department
    status: Literal["draft", "validated", "retired"]
    authority_class: Literal["mandatory_review"] = "mandatory_review"
    operational: Literal[False] = False
    generated_only: Literal[True] = True
    graph: RuleGraphV1
    graph_digest: Digest
    static_cost: Annotated[int, Field(ge=1, le=320)]
    intended_use: ReasonText
    policy_version: Digest
    retention_class: RetentionClass
    owner_id: ActorId
    approval_record_id: None = None
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @model_validator(mode="after")
    def state_is_consistent(self) -> IntelligenceRuleV1:
        if self.static_cost != len(self.graph.nodes):
            raise ValueError("static cost must equal the generated node count")
        if self.updated_at < self.created_at:
            raise ValueError("rule update cannot precede creation")
        return self


class AlertAggregateV1(ContractModel):
    contract_type: Literal["hcam.intelligence.alert.v1"] = "hcam.intelligence.alert.v1"
    alert_id: AlertId
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    department: Department
    dedupe_key: Digest
    hypothesis_id: HypothesisId
    state: Literal["proposed"] = "proposed"
    authority_class: Literal["mandatory_review"] = "mandatory_review"
    operational: Literal[False] = False
    generated_only: Literal[True] = True
    severity: Literal["information", "low", "medium", "high", "critical"]
    priority: Literal["routine", "standard", "urgent", "immediate"]
    confidence: Confidence
    disposition: Literal["unreviewed"] = "unreviewed"
    evidence_refs: Annotated[list[EvidenceId], Field(min_length=1, max_length=256)]
    chronology: ChronologyV1
    provenance: ProvenanceV1
    retention_class: RetentionClass


class AlertLifecycleEventV1(ContractModel):
    contract_type: Literal["hcam.intelligence.alert-lifecycle-event.v1"] = (
        "hcam.intelligence.alert-lifecycle-event.v1"
    )
    alert_id: AlertId
    revision: Annotated[int, Field(ge=1)]
    previous_state: Literal["none", "proposed"]
    new_state: Literal["proposed"]
    actor_id: ActorId
    reason: ReasonText
    authority_class: Literal["mandatory_review"] = "mandatory_review"
    operational: Literal[False] = False
    generated_only: Literal[True] = True
    recorded_at: UtcDateTime


class ReferenceProviderV1(ContractModel):
    contract_type: Literal["hcam.intelligence.reference-provider.v1"] = (
        "hcam.intelligence.reference-provider.v1"
    )
    provider_id: ProviderId
    provider_key: StableName
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    department: Department
    status: Literal["disabled"] = "disabled"
    enabled: Literal[False] = False
    transport_state: Literal["absent"] = "absent"
    credential_state: Literal["none"] = "none"
    provider_kind: Literal["generated_fixture"] = "generated_fixture"
    policy_ref: OpaqueRef
    destination_policy_ref: OpaqueRef
    allowed_fields: Annotated[
        list[Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.]{0,63}$")]],
        Field(min_length=1, max_length=32),
    ]
    generated_only: Literal[True] = True
    owner_id: ActorId
    created_at: UtcDateTime
    updated_at: UtcDateTime

    @field_validator("allowed_fields")
    @classmethod
    def fields_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("provider fields must be unique")
        return value


class ReferenceQueryV1(ContractModel):
    contract_type: Literal["hcam.intelligence.reference-query.v1"] = (
        "hcam.intelligence.reference-query.v1"
    )
    query_id: QueryId
    provider_id: ProviderId
    department: Department
    purpose_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
    requested_fields: Annotated[list[str], Field(min_length=1, max_length=32)]
    status: Literal["blocked"] = "blocked"
    reason_code: Literal["provider_disabled"] = "provider_disabled"
    requested_by: ActorId
    generated_only: Literal[True] = True
    requested_at: UtcDateTime


class TimelineEntryV1(ContractModel):
    contract_type: Literal["hcam.intelligence.timeline-entry.v1"] = (
        "hcam.intelligence.timeline-entry.v1"
    )
    entry_id: TimelineEntryId
    timeline_id: TimelineId
    sequence: Annotated[int, Field(ge=1, le=9_223_372_036_854_775_807)]
    department: Department
    entry_type: Literal[
        "source_fact",
        "system_hypothesis",
        "operator_observation",
        "review_decision",
        "correction",
    ]
    source_ref: OpaqueRef
    source_digest: Digest
    summary_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
    chronology: ChronologyV1
    provenance: ProvenanceV1
    generated_only: Literal[True] = True
    retention_class: RetentionClass


class ReviewDecisionV1(ContractModel):
    contract_type: Literal["hcam.intelligence.review-decision.v1"] = (
        "hcam.intelligence.review-decision.v1"
    )
    review_id: StableName
    target_type: Literal["hypothesis", "alert", "timeline_entry"]
    target_ref: OpaqueRef
    decision: Literal["confirmed", "rejected", "needs_more_evidence", "abstain"]
    actor_id: ActorId
    reason: ReasonText
    policy_version: Digest
    generated_only: Literal[True] = True
    decided_at: UtcDateTime


class RetentionHoldV1(ContractModel):
    contract_type: Literal["hcam.intelligence.retention-hold.v1"] = (
        "hcam.intelligence.retention-hold.v1"
    )
    hold_id: StableName
    target_ref: OpaqueRef
    retention_class: RetentionClass
    status: Literal["proposed"] = "proposed"
    purpose_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")]
    requested_by: ActorId
    reason: ReasonText
    generated_only: Literal[True] = True
    requested_at: UtcDateTime


class OperatorSurfaceStateV1(ContractModel):
    contract_type: Literal["hcam.intelligence.operator-surface-state.v1"] = (
        "hcam.intelligence.operator-surface-state.v1"
    )
    resource_type: Literal["rule", "hypothesis", "alert", "provider", "timeline"]
    resource_ref: OpaqueRef
    runtime_state: Literal["disabled"] = "disabled"
    data_state: Literal["generated_only"] = "generated_only"
    authority_class: Literal["mandatory_review"] = "mandatory_review"
    available_actions: Annotated[
        list[Literal["view", "edit_draft", "validate", "retire", "review"]],
        Field(max_length=5),
    ]
    unavailable_reason: Literal["p4_0_runtime_disabled"] = "p4_0_runtime_disabled"

    @field_validator("available_actions")
    @classmethod
    def actions_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("operator actions must be unique")
        return value


CONTRACT_MODELS: dict[str, type[ContractModel]] = {
    "hcam.intelligence.adaptive-lane-result.v1": AdaptiveLaneResultV1,
    "hcam.intelligence.alert-lifecycle-event.v1": AlertLifecycleEventV1,
    "hcam.intelligence.alert.v1": AlertAggregateV1,
    "hcam.intelligence.correlation-hypothesis.v1": CorrelationHypothesisV1,
    "hcam.intelligence.evidence-reference.v1": EvidenceReferenceV1,
    "hcam.intelligence.geojson-profile.v1": GeoJsonProfileV1,
    "hcam.intelligence.operator-surface-state.v1": OperatorSurfaceStateV1,
    "hcam.intelligence.provenance.v1": ProvenanceV1,
    "hcam.intelligence.reference-provider.v1": ReferenceProviderV1,
    "hcam.intelligence.reference-query.v1": ReferenceQueryV1,
    "hcam.intelligence.retention-hold.v1": RetentionHoldV1,
    "hcam.intelligence.review-decision.v1": ReviewDecisionV1,
    "hcam.intelligence.rule.v1": IntelligenceRuleV1,
    "hcam.intelligence.timeline-entry.v1": TimelineEntryV1,
}
