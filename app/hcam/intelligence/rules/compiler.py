from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from hcam.intelligence.rules.bounds import RuleBounds, RuleLimitError
from hcam.intelligence.rules.canonical import canonical_rule_bytes, rule_sha256
from hcam.intelligence.rules.cel_adapter import (
    CheckedRuleCel,
    ConstrainedRuleCelEnvironment,
)
from hcam.intelligence.rules.contracts import (
    CanonicalRuleAstV1,
    CanonicalRuleNodeV1,
    RuleCompilationV1,
    RuleScheduleV1,
    SemanticRuleNodeV1,
    ValueType,
    VisualRuleDocumentV1,
)


_COMMUTATIVE = {"all", "any", "quorum"}
_SOURCE = {"event_match": "event_match", "hypothesis_match": "hypothesis_match"}
_TEMPORAL = {
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
}
_PARAMETERS = {
    "event_match": {"event_types"},
    "hypothesis_match": {"hypothesis_states"},
    "cel_predicate": {"cel_source"},
    "all": set(),
    "any": set(),
    "not": set(),
    "quorum": {"quorum"},
    "sequence": {"duration_ms"},
    "within": {"duration_ms"},
    "until": {"duration_ms"},
    "for_at_least": {"duration_ms"},
    "absence": {"duration_ms"},
    "count": {"duration_ms", "threshold", "grouping_field"},
    "rate": {"duration_ms", "rate_per_minute", "grouping_field"},
    "distinct_stream_count": {"duration_ms", "threshold"},
    "schedule_gate": {"schedule_ref"},
    "cooldown": {"duration_ms"},
    "repeat_limit": {"threshold"},
    "propose_review_candidate": {"output_code"},
}


class RuleCompilationError(ValueError):
    """A visual rule cannot be reduced to one bounded typed canonical AST."""


@dataclass(frozen=True, slots=True)
class CompiledRule:
    compilation: RuleCompilationV1
    checked_cel: dict[str, CheckedRuleCel]
    canonical_bytes: bytes
    schedule: RuleScheduleV1 | None


def _parameters(node: SemanticRuleNodeV1) -> dict[str, Any]:
    values = node.parameters.model_dump(mode="json", exclude_none=True)
    allowed = _PARAMETERS[node.kind]
    if set(values) != allowed:
        missing = allowed - set(values)
        extra = set(values) - allowed
        if missing:
            raise RuleCompilationError(f"{node.kind} is missing required parameters")
        if extra:
            raise RuleCompilationError(f"{node.kind} contains unrelated parameters")
    for name in ("event_types", "hypothesis_states"):
        if name in values:
            values[name] = sorted(values[name])
    return values


def _validate_arity(node: SemanticRuleNodeV1) -> None:
    count = len(node.inputs)
    if node.kind in _SOURCE and count != 0:
        raise RuleCompilationError("source nodes cannot have inputs")
    if (
        node.kind
        in {
            "cel_predicate",
            "not",
            "within",
            "for_at_least",
            "absence",
            "count",
            "rate",
            "distinct_stream_count",
            "schedule_gate",
            "cooldown",
            "repeat_limit",
            "propose_review_candidate",
        }
        and count != 1
    ):
        raise RuleCompilationError(f"{node.kind} requires exactly one input")
    if node.kind == "until" and count != 2:
        raise RuleCompilationError("until requires exactly two ordered inputs")
    if node.kind in {"all", "any", "quorum", "sequence"} and count < 2:
        raise RuleCompilationError(f"{node.kind} requires at least two inputs")


def _output_type(node: SemanticRuleNodeV1, inputs: list[ValueType]) -> ValueType:
    _validate_arity(node)
    if node.kind in _SOURCE:
        return _SOURCE[node.kind]  # type: ignore[return-value]
    if node.kind == "cel_predicate":
        if inputs[0] not in {"event_match", "hypothesis_match", "temporal_match"}:
            raise RuleCompilationError("cel_predicate requires a match input")
        return "bool"
    if node.kind in {"all", "any", "not", "quorum"}:
        if any(item != "bool" for item in inputs):
            raise RuleCompilationError("Boolean nodes require Boolean inputs")
        return "bool"
    if node.kind in _TEMPORAL:
        if node.kind == "sequence" and any(
            item not in {"event_match", "hypothesis_match", "temporal_match"}
            for item in inputs
        ):
            raise RuleCompilationError("sequence requires match inputs")
        if node.kind != "sequence" and any(
            item not in {"event_match", "hypothesis_match", "temporal_match"}
            for item in inputs
        ):
            raise RuleCompilationError("temporal node requires match input")
        return "temporal_match"
    if node.kind == "propose_review_candidate":
        if inputs[0] not in {
            "bool",
            "temporal_match",
            "event_match",
            "hypothesis_match",
        }:
            raise RuleCompilationError("output requires a typed decision input")
        return "review_candidate_nonoperational"
    raise RuleCompilationError("rule node kind is unsupported")


def compile_rule(
    document: VisualRuleDocumentV1,
    *,
    bounds: RuleBounds | None = None,
) -> CompiledRule:
    effective = bounds or RuleBounds()
    encoded_authoring = canonical_rule_bytes(document)
    if len(document.semantics.nodes) > effective.semantic_nodes:
        raise RuleLimitError("rule exceeds the semantic node limit")
    node_by_id = {node.node_id: node for node in document.semantics.nodes}
    for node in document.semantics.nodes:
        if len(node.inputs) > effective.inputs_per_node:
            raise RuleLimitError("rule node exceeds the input limit")
        if any(item not in node_by_id for item in node.inputs):
            raise RuleCompilationError("rule node references a missing input")
        _parameters(node)

    visiting: set[str] = set()
    visited: set[str] = set()
    depth_by_id: dict[str, int] = {}
    output_by_id: dict[str, ValueType] = {}
    fingerprint_by_id: dict[str, str] = {}

    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise RuleCompilationError("rule graph contains a cycle")
        if node_id in visited:
            return
        visiting.add(node_id)
        node = node_by_id[node_id]
        for child in node.inputs:
            visit(child)
        depths = [depth_by_id[child] for child in node.inputs]
        depth_by_id[node_id] = 1 + (max(depths) if depths else 0)
        if depth_by_id[node_id] > effective.graph_depth:
            raise RuleLimitError("rule graph exceeds the depth limit")
        output_by_id[node_id] = _output_type(
            node, [output_by_id[item] for item in node.inputs]
        )
        child_fingerprints = [fingerprint_by_id[item] for item in node.inputs]
        if node.kind in _COMMUTATIVE:
            child_fingerprints.sort()
        fingerprint_by_id[node_id] = rule_sha256(
            {
                "kind": node.kind,
                "inputs": child_fingerprints,
                "parameters": _parameters(node),
                "output_type": output_by_id[node_id],
            }
        )
        visiting.remove(node_id)
        visited.add(node_id)

    visit(document.semantics.output_node_id)
    if visited != set(node_by_id):
        raise RuleCompilationError("rule graph contains unreachable nodes")
    if node_by_id[document.semantics.output_node_id].kind != "propose_review_candidate":
        raise RuleCompilationError("rule must have one non-operational output node")

    ordered_ids: list[str] = []
    emitted: set[str] = set()

    def emit(node_id: str) -> None:
        if node_id in emitted:
            return
        node = node_by_id[node_id]
        children = list(node.inputs)
        if node.kind in _COMMUTATIVE:
            children.sort(key=lambda item: fingerprint_by_id[item])
        for child in children:
            emit(child)
        emitted.add(node_id)
        ordered_ids.append(node_id)

    emit(document.semantics.output_node_id)
    canonical_id = {
        node_id: f"n{index:03d}" for index, node_id in enumerate(ordered_ids)
    }
    cel_environment = ConstrainedRuleCelEnvironment(effective)
    checked: dict[str, CheckedRuleCel] = {}
    canonical_nodes: list[CanonicalRuleNodeV1] = []
    static_cost = 0
    for node_id in ordered_ids:
        node = node_by_id[node_id]
        inputs = list(node.inputs)
        if node.kind in _COMMUTATIVE:
            inputs.sort(key=lambda item: fingerprint_by_id[item])
        parameters = _parameters(node)
        node_cost = 1
        if node.kind == "cel_predicate":
            cel_result = cel_environment.compile(
                parameters["cel_source"], canonical_id[node_id]
            )
            checked[canonical_id[node_id]] = cel_result
            parameters = {
                "cel_profile": cel_result.compilation.profile,
                "source_sha256": cel_result.compilation.source_sha256,
                "structural_ast_sha256": cel_result.compilation.structural_ast_sha256,
            }
            node_cost += cel_result.compilation.static_cost
        canonical_nodes.append(
            CanonicalRuleNodeV1(
                node_id=canonical_id[node_id],
                kind=node.kind,
                inputs=[canonical_id[item] for item in inputs],
                parameters=parameters,
                output_type=output_by_id[node_id],
                semantic_digest=fingerprint_by_id[node_id],
            )
        )
        static_cost += node_cost
    ast = CanonicalRuleAstV1(
        nodes=canonical_nodes,
        output_node_id=canonical_id[document.semantics.output_node_id],
        static_cost=static_cost,
    )
    ast_digest = rule_sha256(ast)
    schedule_digest = rule_sha256(document.schedule) if document.schedule else None
    material = f"{document.department}\x00{document.rule_key}\x00{document.version}\x00{ast_digest}"
    compilation_id = "rcmp_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
    compilation = RuleCompilationV1(
        compilation_id=compilation_id,
        department=document.department,
        rule_key=document.rule_key,
        rule_version=document.version,
        authoring_digest="sha256:" + hashlib.sha256(encoded_authoring).hexdigest(),
        semantic_digest=ast_digest,
        ast_digest=ast_digest,
        schedule_digest=schedule_digest,
        canonical_ast=ast,
        cel_compilations=[checked[key].compilation for key in sorted(checked)],
        diagnostic_map=canonical_id,
    )
    return CompiledRule(
        compilation, checked, canonical_rule_bytes(ast), document.schedule
    )
