from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from hcam.intelligence.rules.bounds import RuleBounds, RuleLimitError
from hcam.intelligence.rules.canonical import rule_sha256
from hcam.intelligence.rules.cel_adapter import ConstrainedRuleCelEnvironment
from hcam.intelligence.rules.compiler import CompiledRule
from hcam.intelligence.rules.contracts import (
    RuleEvaluationRevisionV1,
    RuleEvaluationV1,
    RuleInputV1,
)
from hcam.intelligence.rules.temporal import (
    TemporalResult,
    TemporalToken,
    absence,
    apply_cooldown,
    apply_repeat_limit,
    distinct_stream_count,
    for_at_least,
    ordered_sequence,
    schedule_is_open,
    threshold_count,
    threshold_rate,
    until,
    within,
)


class RuleEvaluationError(ValueError):
    """Generated rule evaluation failed without producing a positive result."""


@dataclass(slots=True)
class EvaluationState:
    last_match_at: dict[str, datetime] = field(default_factory=dict)
    repeat_counts: dict[str, int] = field(default_factory=dict)
    suppressed_counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NodeResult:
    matched: bool
    pending: bool
    reason_code: str
    tokens: tuple[TemporalToken, ...] = ()
    suppressed_count: int = 0

    @classmethod
    def temporal(cls, result: TemporalResult) -> NodeResult:
        return cls(
            result.matched,
            result.pending,
            result.reason_code,
            result.evidence,
            result.suppressed_count,
        )


def _identifier(prefix: str, material: str) -> str:
    return prefix + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _cel_context(
    item: RuleInputV1, *, prior_result: bool, schedule_open: bool
) -> dict[str, Any]:
    values = item.values
    expected_types: dict[str, type[object]] = {
        "event_kind": str,
        "object_class": str,
        "confidence": float,
        "uncertainty": float,
        "direction": str,
        "count": int,
        "rate": float,
        "chronology_complete": bool,
        "contradiction": bool,
    }
    defaults: dict[str, object] = {
        "event_kind": item.type_code,
        "object_class": "generated.unknown",
        "confidence": 0.0,
        "uncertainty": 1.0,
        "direction": "unknown",
        "count": 0,
        "rate": 0.0,
        "chronology_complete": False,
        "contradiction": False,
    }
    context: dict[str, Any] = {}
    for name, expected in expected_types.items():
        value = values.get(name, defaults[name])
        if type(value) is not expected:
            raise RuleEvaluationError("generated input contains an invalid scalar type")
        context[name] = value
    context.update(schedule_open=schedule_open, prior_result=prior_result)
    return context


def evaluate_generated_rule(
    compiled: CompiledRule,
    inputs: list[RuleInputV1],
    *,
    interval_start: datetime,
    state: EvaluationState | None = None,
    bounds: RuleBounds | None = None,
) -> RuleEvaluationV1:
    effective = bounds or RuleBounds()
    if not inputs:
        raise RuleEvaluationError("generated evaluation requires at least one input")
    if len(inputs) > effective.inputs_per_batch:
        raise RuleLimitError("generated evaluation input limit exceeded")
    if any(not item.generated_only for item in inputs):
        raise RuleEvaluationError("generated evaluation rejected a non-generated input")
    departments = {item.department for item in inputs}
    partitions = {item.partition_digest for item in inputs}
    if departments != {compiled.compilation.department} or len(partitions) != 1:
        raise RuleEvaluationError("generated evaluation scope is inconsistent")
    ordered_inputs = sorted(inputs, key=lambda item: (item.occurred_at, item.input_id))
    watermark = min(item.watermark_at for item in inputs)
    runtime_state = state or EvaluationState()
    results: dict[str, NodeResult] = {}
    cel_by_node = {
        item.compilation.canonical_node_id: item
        for item in compiled.checked_cel.values()
    }
    cel_environment = ConstrainedRuleCelEnvironment(effective)
    schedule = compiled.schedule

    for node in compiled.compilation.canonical_ast.nodes:
        children = [results[item] for item in node.inputs]
        parameters = node.parameters
        if node.kind in {"event_match", "hypothesis_match"}:
            expected_kind = "event" if node.kind == "event_match" else "hypothesis"
            accepted_types = set(
                parameters["event_types"]
                if node.kind == "event_match"
                else parameters["hypothesis_states"]
            )
            selected = [
                item
                for item in ordered_inputs
                if item.input_kind == expected_kind
                and item.type_code in accepted_types
                and item.correction != "retract"
            ]
            tokens = tuple(
                TemporalToken(item.input_id, item.occurred_at, item.stream_id)
                for item in selected
            )
            results[node.node_id] = NodeResult(
                bool(tokens),
                not tokens,
                "source_matched" if tokens else "source_pending",
                tokens,
            )
        elif node.kind == "cel_predicate":
            source = children[0]
            checked = cel_by_node.get(node.node_id)
            if checked is None:
                raise RuleEvaluationError("CEL compilation is unavailable")
            passed: list[TemporalToken] = []
            by_id = {item.input_id: item for item in ordered_inputs}
            for token in source.tokens:
                item = by_id[token.input_id]
                open_now = (
                    schedule_is_open(schedule, item.occurred_at) if schedule else True
                )
                if cel_environment.evaluate(
                    checked,
                    _cel_context(item, prior_result=False, schedule_open=open_now),
                ):
                    passed.append(token)
            results[node.node_id] = NodeResult(
                bool(passed),
                source.pending,
                "cel_matched" if passed else "cel_not_matched",
                tuple(passed),
            )
        elif node.kind in {"all", "any", "not", "quorum"}:
            if node.kind == "all":
                matched = all(item.matched for item in children)
            elif node.kind == "any":
                matched = any(item.matched for item in children)
            elif node.kind == "not":
                matched = not children[0].matched and not children[0].pending
            else:
                matched = sum(item.matched for item in children) >= int(
                    parameters["quorum"]
                )
            pending = not matched and any(item.pending for item in children)
            tokens = tuple(
                {
                    token.input_id: token
                    for child in children
                    for token in child.tokens
                }.values()
            )
            results[node.node_id] = NodeResult(
                matched,
                pending,
                "boolean_matched"
                if matched
                else ("boolean_pending" if pending else "boolean_not_matched"),
                tokens,
            )
        elif node.kind == "sequence":
            results[node.node_id] = NodeResult.temporal(
                ordered_sequence(
                    [item.tokens for item in children],
                    maximum_span_ms=int(parameters["duration_ms"]),
                )
            )
        elif node.kind == "within":
            results[node.node_id] = NodeResult.temporal(
                within(children[0].tokens, duration_ms=int(parameters["duration_ms"]))
            )
        elif node.kind == "until":
            results[node.node_id] = NodeResult.temporal(
                until(
                    children[0].tokens,
                    children[1].tokens,
                    duration_ms=int(parameters["duration_ms"]),
                )
            )
        elif node.kind == "for_at_least":
            results[node.node_id] = NodeResult.temporal(
                for_at_least(
                    children[0].tokens, duration_ms=int(parameters["duration_ms"])
                )
            )
        elif node.kind == "absence":
            results[node.node_id] = NodeResult.temporal(
                absence(
                    children[0].tokens,
                    interval_start=interval_start,
                    watermark_at=watermark,
                    duration_ms=int(parameters["duration_ms"]),
                )
            )
        elif node.kind == "count":
            results[node.node_id] = NodeResult.temporal(
                threshold_count(
                    children[0].tokens, threshold=int(parameters["threshold"])
                )
            )
        elif node.kind == "rate":
            results[node.node_id] = NodeResult.temporal(
                threshold_rate(
                    children[0].tokens,
                    duration_ms=int(parameters["duration_ms"]),
                    rate_per_minute=float(parameters["rate_per_minute"]),
                )
            )
        elif node.kind == "distinct_stream_count":
            results[node.node_id] = NodeResult.temporal(
                distinct_stream_count(
                    children[0].tokens, threshold=int(parameters["threshold"])
                )
            )
        elif node.kind == "schedule_gate":
            if schedule is None:
                raise RuleEvaluationError("schedule gate has no bound schedule")
            open_tokens = tuple(
                item
                for item in children[0].tokens
                if schedule_is_open(schedule, item.occurred_at)
            )
            results[node.node_id] = NodeResult(
                bool(open_tokens),
                not open_tokens,
                "schedule_open" if open_tokens else "schedule_closed",
                open_tokens,
            )
        elif node.kind == "cooldown":
            child = children[0]
            instant = child.tokens[-1].occurred_at if child.tokens else watermark
            result = apply_cooldown(
                TemporalResult(
                    child.matched, child.pending, child.reason_code, child.tokens
                ),
                now=instant,
                previous_match_at=runtime_state.last_match_at.get(node.node_id),
                duration_ms=int(parameters["duration_ms"]),
                prior_suppressed_count=runtime_state.suppressed_counts.get(
                    node.node_id, 0
                ),
            )
            if result.matched:
                runtime_state.last_match_at[node.node_id] = instant
            runtime_state.suppressed_counts[node.node_id] = result.suppressed_count
            results[node.node_id] = NodeResult.temporal(result)
        elif node.kind == "repeat_limit":
            count = runtime_state.repeat_counts.get(node.node_id, 0)
            result = apply_repeat_limit(
                TemporalResult(
                    children[0].matched,
                    children[0].pending,
                    children[0].reason_code,
                    children[0].tokens,
                    children[0].suppressed_count,
                ),
                emitted_count=count,
                maximum=int(parameters["threshold"]),
            )
            if result.matched:
                runtime_state.repeat_counts[node.node_id] = count + 1
            results[node.node_id] = NodeResult.temporal(result)
        elif node.kind == "propose_review_candidate":
            child = children[0]
            results[node.node_id] = NodeResult(
                child.matched,
                child.pending,
                "review_candidate_proposed" if child.matched else child.reason_code,
                child.tokens,
                child.suppressed_count,
            )
        else:
            raise RuleEvaluationError("compiled rule contains an unsupported node")

    output = results[compiled.compilation.canonical_ast.output_node_id]
    if output.matched:
        evaluation_state = "matched"
    elif output.reason_code in {"cooldown_suppressed", "repeat_limit_exhausted"}:
        evaluation_state = "suppressed"
    elif output.pending:
        evaluation_state = "pending"
    else:
        evaluation_state = "not_matched"
    evidence_ids = sorted({item.input_id for item in output.tokens})
    material = {
        "compilation_id": compiled.compilation.compilation_id,
        "partition_digest": next(iter(partitions)),
        "state": evaluation_state,
        "reason_code": output.reason_code,
        "evidence_input_ids": evidence_ids,
        "suppressed_count": output.suppressed_count,
    }
    digest = rule_sha256(material)
    return RuleEvaluationV1(
        evaluation_id=_identifier("revl_", digest),
        compilation_id=compiled.compilation.compilation_id,
        department=compiled.compilation.department,
        partition_digest=next(iter(partitions)),
        state=evaluation_state,
        reason_code=output.reason_code,
        evidence_input_ids=evidence_ids,
        suppressed_count=output.suppressed_count,
        evaluation_digest=digest,
    )


def revision_for_correction(
    previous: RuleEvaluationV1,
    updated: RuleEvaluationV1,
    *,
    reason_code: str,
    recorded_at: datetime,
) -> RuleEvaluationRevisionV1:
    if reason_code not in {"late_input", "superseded", "retracted", "replay"}:
        raise RuleEvaluationError("evaluation revision reason is not allowed")
    revision = previous.revision + 1
    snapshot = updated.model_copy(update={"revision": revision})
    material = f"{previous.evaluation_id}\x00{revision}\x00{snapshot.evaluation_digest}"
    return RuleEvaluationRevisionV1(
        revision_id=_identifier("rrev_", material),
        evaluation_id=previous.evaluation_id,
        revision=revision,
        reason_code=reason_code,
        snapshot=snapshot,
        recorded_at=recorded_at,
    )
