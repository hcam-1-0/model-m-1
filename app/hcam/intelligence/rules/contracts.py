from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
StableId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,127}$")]
Department = Annotated[str, Field(min_length=2, max_length=120)]
Scalar: TypeAlias = bool | int | float | str
NodeKind = Literal[
    "event_match",
    "hypothesis_match",
    "cel_predicate",
    "all",
    "any",
    "not",
    "quorum",
    "sequence",
    "within",
    "until",
    "for_at_least",
    "absence",
    "count",
    "rate",
    "distinct_stream_count",
    "schedule_gate",
    "cooldown",
    "repeat_limit",
    "propose_review_candidate",
]
ValueType = Literal[
    "event_match",
    "hypothesis_match",
    "bool",
    "bounded_int",
    "bounded_rate",
    "temporal_match",
    "review_candidate_nonoperational",
]


class RuleContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RuleNodeParametersV1(RuleContract):
    event_types: (
        Annotated[list[StableId], Field(min_length=1, max_length=16)] | None
    ) = None
    hypothesis_states: (
        Annotated[list[StableId], Field(min_length=1, max_length=8)] | None
    ) = None
    cel_source: Annotated[str, Field(min_length=1, max_length=512)] | None = None
    duration_ms: Annotated[int, Field(ge=1, le=900_000)] | None = None
    threshold: Annotated[int, Field(ge=1, le=100_000)] | None = None
    quorum: Annotated[int, Field(ge=1, le=16)] | None = None
    rate_per_minute: (
        Annotated[float, Field(gt=0, le=100_000, allow_inf_nan=False)] | None
    ) = None
    grouping_field: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")] | None = (
        None
    )
    schedule_ref: StableId | None = None
    output_code: StableId | None = None

    @field_validator("event_types", "hypothesis_states")
    @classmethod
    def unique_values(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError("parameter values must be unique")
        return value


class SemanticRuleNodeV1(RuleContract):
    node_id: StableId
    kind: NodeKind
    inputs: Annotated[list[StableId], Field(max_length=16)] = Field(
        default_factory=list
    )
    parameters: RuleNodeParametersV1 = Field(default_factory=RuleNodeParametersV1)

    @field_validator("inputs")
    @classmethod
    def unique_inputs(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("node inputs must be unique")
        return value


class RuleSemanticsV1(RuleContract):
    contract_type: Literal["hcam.p4-2.rule-semantics.v1"] = (
        "hcam.p4-2.rule-semantics.v1"
    )
    nodes: Annotated[list[SemanticRuleNodeV1], Field(min_length=2, max_length=128)]
    output_node_id: StableId

    @model_validator(mode="after")
    def identifiers_are_unambiguous(self) -> RuleSemanticsV1:
        identifiers = [node.node_id for node in self.nodes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("semantic node identifiers must be unique")
        if self.output_node_id not in set(identifiers):
            raise ValueError("semantic output node is missing")
        return self


class VisualNodePresentationV1(RuleContract):
    node_id: StableId
    x: Annotated[int, Field(ge=-100_000, le=100_000)]
    y: Annotated[int, Field(ge=-100_000, le=100_000)]
    label: Annotated[str, Field(min_length=1, max_length=120)]
    color_token: Literal["neutral", "source", "logic", "temporal", "output"] = "neutral"
    collapsed: bool = False


class RulePresentationV1(RuleContract):
    nodes: Annotated[
        list[VisualNodePresentationV1], Field(min_length=2, max_length=128)
    ]
    viewport_x: Annotated[int, Field(ge=-100_000, le=100_000)] = 0
    viewport_y: Annotated[int, Field(ge=-100_000, le=100_000)] = 0
    zoom_percent: Annotated[int, Field(ge=25, le=400)] = 100

    @field_validator("nodes")
    @classmethod
    def unique_nodes(cls, value: list[VisualNodePresentationV1]):
        if len(value) != len({item.node_id for item in value}):
            raise ValueError("presentation node identifiers must be unique")
        return value


class VisualRuleDocumentV1(RuleContract):
    contract_type: Literal["hcam.p4-2.visual-rule-document.v1"] = (
        "hcam.p4-2.visual-rule-document.v1"
    )
    department: Department
    rule_key: StableId
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]
    semantics: RuleSemanticsV1
    presentation: RulePresentationV1
    schedule: RuleScheduleV1 | None = None
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def presentation_matches_semantics(self) -> VisualRuleDocumentV1:
        semantic_ids = {item.node_id for item in self.semantics.nodes}
        presentation_ids = {item.node_id for item in self.presentation.nodes}
        if semantic_ids != presentation_ids:
            raise ValueError(
                "presentation must describe every semantic node exactly once"
            )
        return self


class WeeklyScheduleIntervalV1(RuleContract):
    weekday: Annotated[int, Field(ge=0, le=6)]
    start_minute: Annotated[int, Field(ge=0, le=1_439)]
    end_minute: Annotated[int, Field(ge=1, le=1_440)]

    @model_validator(mode="after")
    def ordered(self) -> WeeklyScheduleIntervalV1:
        if self.end_minute <= self.start_minute:
            raise ValueError("schedule interval must not cross midnight")
        return self


class RuleScheduleV1(RuleContract):
    schedule_id: StableId
    timezone: Annotated[str, Field(min_length=1, max_length=128)]
    timezone_data_version: StableId
    intervals: Annotated[
        list[WeeklyScheduleIntervalV1], Field(min_length=1, max_length=64)
    ]

    @model_validator(mode="after")
    def intervals_do_not_overlap(self) -> RuleScheduleV1:
        ordered = sorted(
            (item.weekday, item.start_minute, item.end_minute)
            for item in self.intervals
        )
        for previous, current in zip(ordered, ordered[1:], strict=False):
            if previous[0] == current[0] and previous[2] > current[1]:
                raise ValueError("schedule intervals must not overlap")
        return self


class CanonicalRuleNodeV1(RuleContract):
    node_id: Annotated[str, Field(pattern=r"^n[0-9]{3}$")]
    kind: NodeKind
    inputs: Annotated[
        list[Annotated[str, Field(pattern=r"^n[0-9]{3}$")]], Field(max_length=16)
    ]
    parameters: dict[str, Scalar | list[str]]
    output_type: ValueType
    semantic_digest: Digest


class CanonicalRuleAstV1(RuleContract):
    contract_type: Literal["hcam.p4-2.canonical-rule-ast.v1"] = (
        "hcam.p4-2.canonical-rule-ast.v1"
    )
    compiler_version: Literal["hcam.p4-2.compiler.v1"] = "hcam.p4-2.compiler.v1"
    temporal_version: Literal["hcam.p4-2.temporal.v1"] = "hcam.p4-2.temporal.v1"
    cel_environment_version: Literal["hcam.p4-2.constrained-cel.v1"] = (
        "hcam.p4-2.constrained-cel.v1"
    )
    schedule_contract_version: Literal["hcam.p4-2.schedule.v1"] = (
        "hcam.p4-2.schedule.v1"
    )
    input_schema_versions: list[Literal["hcam.p4-1.generated-input.v1"]] = [
        "hcam.p4-1.generated-input.v1"
    ]
    nodes: Annotated[list[CanonicalRuleNodeV1], Field(min_length=2, max_length=128)]
    output_node_id: Annotated[str, Field(pattern=r"^n[0-9]{3}$")]
    static_cost: Annotated[int, Field(ge=1, le=10_000)]


class CelCompilationV1(RuleContract):
    profile: Literal["hcam.p4-2.constrained-cel.v1"] = "hcam.p4-2.constrained-cel.v1"
    canonical_node_id: Annotated[str, Field(pattern=r"^n[0-9]{3}$")]
    source_sha256: Digest
    structural_ast_sha256: Digest
    checked_sha256: Digest
    checked_bytes_b64: Annotated[str, Field(min_length=4, max_length=90_000)]
    ast_node_count: Annotated[int, Field(ge=1, le=128)]
    ast_depth: Annotated[int, Field(ge=1, le=16)]
    static_cost: Annotated[int, Field(ge=1, le=128)]


class RuleCompilationV1(RuleContract):
    contract_type: Literal["hcam.p4-2.rule-compilation.v1"] = (
        "hcam.p4-2.rule-compilation.v1"
    )
    compilation_id: Annotated[str, Field(pattern=r"^rcmp_[0-9a-f]{32}$")]
    department: Department
    rule_key: StableId
    rule_version: Annotated[int, Field(ge=1)]
    authoring_digest: Digest
    semantic_digest: Digest
    ast_digest: Digest
    schedule_digest: Digest | None = None
    canonical_ast: CanonicalRuleAstV1
    cel_compilations: list[CelCompilationV1]
    diagnostic_map: dict[StableId, Annotated[str, Field(pattern=r"^n[0-9]{3}$")]]
    status: Literal["compiled"] = "compiled"
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class RuleInputV1(RuleContract):
    input_id: StableId
    input_kind: Literal["event", "hypothesis"]
    type_code: StableId
    department: Department
    partition_digest: Digest
    stream_id: Annotated[str, Field(pattern=r"^str_[0-9a-f]{32}$")]
    occurred_at: datetime
    watermark_at: datetime
    values: dict[Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")], Scalar]
    correction: Literal["none", "supersede", "retract"] = "none"
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def watermark_is_aware(self) -> RuleInputV1:
        if self.occurred_at.tzinfo is None or self.watermark_at.tzinfo is None:
            raise ValueError("rule input timestamps must include an offset")
        return self


class RuleEvaluationV1(RuleContract):
    contract_type: Literal["hcam.p4-2.rule-evaluation.v1"] = (
        "hcam.p4-2.rule-evaluation.v1"
    )
    evaluation_id: Annotated[str, Field(pattern=r"^revl_[0-9a-f]{32}$")]
    compilation_id: Annotated[str, Field(pattern=r"^rcmp_[0-9a-f]{32}$")]
    department: Department
    partition_digest: Digest
    state: Literal["pending", "matched", "not_matched", "suppressed", "abstained"]
    reason_code: StableId
    evidence_input_ids: Annotated[list[StableId], Field(max_length=256)]
    suppressed_count: Annotated[int, Field(ge=0, le=100_000)] = 0
    evaluation_digest: Digest
    revision: Annotated[int, Field(ge=1)] = 1
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class RuleEvaluationRevisionV1(RuleContract):
    revision_id: Annotated[str, Field(pattern=r"^rrev_[0-9a-f]{32}$")]
    evaluation_id: Annotated[str, Field(pattern=r"^revl_[0-9a-f]{32}$")]
    revision: Annotated[int, Field(ge=1)]
    reason_code: Literal["initial", "late_input", "superseded", "retracted", "replay"]
    snapshot: RuleEvaluationV1
    recorded_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class RuleShadowComparisonV1(RuleContract):
    comparison_id: Annotated[str, Field(pattern=r"^rshd_[0-9a-f]{32}$")]
    department: Department
    candidate_compilation_id: Annotated[str, Field(pattern=r"^rcmp_[0-9a-f]{32}$")]
    baseline_compilation_id: Annotated[str, Field(pattern=r"^rcmp_[0-9a-f]{32}$")]
    candidate_matches: Annotated[int, Field(ge=0, le=100_000)]
    baseline_matches: Annotated[int, Field(ge=0, le=100_000)]
    disagreement_count: Annotated[int, Field(ge=0, le=100_000)]
    comparison_digest: Digest
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class RuleStateCheckpointV1(RuleContract):
    checkpoint_id: Annotated[str, Field(pattern=r"^rchk_[0-9a-f]{32}$")]
    compilation_id: Annotated[str, Field(pattern=r"^rcmp_[0-9a-f]{32}$")]
    department: Department
    partition_digest: Digest
    watermark_at: datetime
    state_generation: Annotated[int, Field(ge=1)]
    active_keys: Annotated[int, Field(ge=0, le=16_384)]
    state_digest: Digest
    closed_reason: StableId | None = None
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class RuleLifecycleEventV1(RuleContract):
    event_id: Annotated[str, Field(pattern=r"^rlfe_[0-9a-f]{32}$")]
    rule_record_id: Annotated[str, Field(pattern=r"^irlr_[0-9a-f]{32}$")]
    department: Department
    from_status: Literal[
        "draft", "validated", "approved", "shadow", "suspended", "retired"
    ]
    to_status: Literal[
        "draft", "validated", "approved", "shadow", "suspended", "retired"
    ]
    actor_id: Annotated[str, Field(min_length=1, max_length=160)]
    reason_code: StableId
    compilation_digest: Digest | None = None
    occurred_at: datetime
    generated_only: Literal[True] = True
    operational: Literal[False] = False
