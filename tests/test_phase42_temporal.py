from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hcam.intelligence.rules.compiler import compile_rule
from hcam.intelligence.rules.contracts import (
    RuleInputV1,
    RuleScheduleV1,
    VisualRuleDocumentV1,
)
from hcam.intelligence.rules.evaluator import (
    EvaluationState,
    evaluate_generated_rule,
    revision_for_correction,
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


ROOT = Path("contracts/phase-4/p4-2/fixtures")
BASE = datetime(2026, 9, 7, tzinfo=UTC)
DIGEST = "sha256:" + "1" * 64


def token(identifier: str, seconds: int, stream: int = 1) -> TemporalToken:
    return TemporalToken(
        identifier, BASE + timedelta(seconds=seconds), "str_" + str(stream) * 32
    )


def input_value(
    identifier: str, type_code: str, seconds: int, *, confidence: float = 0.9
) -> RuleInputV1:
    return RuleInputV1(
        input_id=identifier,
        input_kind="event",
        type_code=type_code,
        department="generated-lab",
        partition_digest=DIGEST,
        stream_id="str_" + "1" * 32,
        occurred_at=BASE + timedelta(seconds=seconds),
        watermark_at=BASE + timedelta(seconds=120),
        values={
            "event_kind": type_code,
            "object_class": "vehicle.car",
            "confidence": confidence,
            "uncertainty": 0.1,
            "direction": "forward",
            "count": 1,
            "rate": 1.0,
            "chronology_complete": True,
            "contradiction": False,
        },
    )


def document(index: int) -> VisualRuleDocumentV1:
    payload = json.loads(
        (ROOT / "generated-rule-documents-v1.json").read_text(encoding="utf-8")
    )
    return VisualRuleDocumentV1.model_validate(deepcopy(payload["documents"][index]))


def operator_document(
    kind: str,
    parameters: dict[str, object],
    *,
    source_count: int = 1,
    boolean_inputs: bool = False,
    schedule: bool = False,
) -> VisualRuleDocumentV1:
    nodes: list[dict[str, object]] = []
    inputs: list[str] = []
    for index in range(source_count):
        source_id = f"source-{index}"
        nodes.append(
            {
                "node_id": source_id,
                "kind": "event_match",
                "inputs": [],
                "parameters": {"event_types": [f"generated.source-{index}"]},
            }
        )
        if boolean_inputs:
            predicate_id = f"predicate-{index}"
            nodes.append(
                {
                    "node_id": predicate_id,
                    "kind": "cel_predicate",
                    "inputs": [source_id],
                    "parameters": {"cel_source": "confidence >= 0.5"},
                }
            )
            inputs.append(predicate_id)
        else:
            inputs.append(source_id)
    nodes.extend(
        [
            {
                "node_id": "operator",
                "kind": kind,
                "inputs": inputs,
                "parameters": parameters,
            },
            {
                "node_id": "output",
                "kind": "propose_review_candidate",
                "inputs": ["operator"],
                "parameters": {"output_code": "generated.operator-review"},
            },
        ]
    )
    schedule_value = None
    if schedule:
        schedule_value = {
            "schedule_id": "generated.always-test-window",
            "timezone": "UTC",
            "timezone_data_version": "tzdata.2026c",
            "intervals": [{"weekday": 0, "start_minute": 0, "end_minute": 600}],
        }
    return VisualRuleDocumentV1.model_validate(
        {
            "department": "generated-lab",
            "rule_key": f"generated.{kind}-review",
            "version": 1,
            "semantics": {"nodes": nodes, "output_node_id": "output"},
            "presentation": {
                "nodes": [
                    {
                        "node_id": item["node_id"],
                        "label": str(item["node_id"]),
                        "x": 0,
                        "y": 0,
                    }
                    for item in nodes
                ]
            },
            "schedule": schedule_value,
        }
    )


def test_generated_sequence_goldens() -> None:
    payload = json.loads(
        (ROOT / "generated-temporal-sequences-v1.json").read_text(encoding="utf-8")
    )
    for case in payload["cases"]:
        groups = [
            tuple(token(f"generated-{index}-{value}", value) for value in values)
            for index, values in enumerate(case["input_seconds"])
        ]
        assert (
            ordered_sequence(
                groups, maximum_span_ms=case["maximum_span_ms"]
            ).reason_code
            == case["expected"]
        )


def test_absence_waits_for_watermark_and_duration_is_visible() -> None:
    assert absence(
        (),
        interval_start=BASE,
        watermark_at=BASE + timedelta(seconds=4),
        duration_ms=5000,
    ).pending
    closed = absence(
        (),
        interval_start=BASE,
        watermark_at=BASE + timedelta(seconds=5),
        duration_ms=5000,
    )
    assert closed.matched and closed.reason_code == "absence_watermark_closed"
    observed = absence(
        (token("generated-present", 2),),
        interval_start=BASE,
        watermark_at=BASE + timedelta(seconds=10),
        duration_ms=5000,
    )
    assert not observed.matched and observed.reason_code == "absence_disproved"
    assert for_at_least(
        (token("generated-a", 0), token("generated-b", 5)), duration_ms=5000
    ).matched


def test_within_until_aggregates_cooldown_and_repeat_are_deterministic() -> None:
    evidence = (
        token("generated-a", 1),
        token("generated-b", 3),
        token("generated-c", 4, 2),
    )
    assert within(evidence, duration_ms=4000).matched
    assert (
        until((evidence[0],), (evidence[1],), duration_ms=5000).reason_code
        == "until_stopped"
    )
    assert threshold_count(evidence, threshold=3).matched
    assert threshold_rate(evidence, duration_ms=60_000, rate_per_minute=3).matched
    assert distinct_stream_count(evidence, threshold=2).matched
    initial = TemporalResult(True, False, "matched", evidence)
    assert (
        apply_cooldown(
            initial,
            now=BASE + timedelta(seconds=3),
            previous_match_at=BASE,
            duration_ms=5000,
        ).reason_code
        == "cooldown_suppressed"
    )
    assert (
        apply_repeat_limit(initial, emitted_count=2, maximum=2).reason_code
        == "repeat_limit_exhausted"
    )


def test_schedule_goldens_cover_fixed_offset_and_dst_fold() -> None:
    payload = json.loads(
        (ROOT / "generated-schedule-dst-v1.json").read_text(encoding="utf-8")
    )
    for case in payload["cases"]:
        schedule = RuleScheduleV1(
            schedule_id="generated.schedule",
            timezone=case["timezone"],
            timezone_data_version="tzdata.2026c",
            intervals=[
                {
                    "weekday": case["weekday"],
                    "start_minute": case["start_minute"],
                    "end_minute": case["end_minute"],
                }
            ],
        )
        assert (
            schedule_is_open(
                schedule, datetime.fromisoformat(case["instant"].replace("Z", "+00:00"))
            )
            is case["expected_open"]
        )


def test_generated_evaluator_is_replay_deterministic_and_nonoperational() -> None:
    compiled = compile_rule(document(0))
    inputs = [input_value("generated-one", "generated.vehicle.observed", 1)]
    first = evaluate_generated_rule(compiled, inputs, interval_start=BASE)
    second = evaluate_generated_rule(
        compiled, list(reversed(inputs)), interval_start=BASE
    )
    assert first == second
    assert first.state == "matched"
    assert first.reason_code == "review_candidate_proposed"
    assert first.generated_only and not first.operational
    low = evaluate_generated_rule(
        compiled,
        [input_value("generated-low", "generated.vehicle.observed", 1, confidence=0.2)],
        interval_start=BASE,
    )
    assert low.state == "not_matched"


def test_sequence_evaluator_preserves_suppression_and_correction_history() -> None:
    compiled = compile_rule(document(1))
    inputs = [
        input_value("generated-entry", "generated.zone.entry", 1),
        input_value("generated-departure", "generated.zone.departure", 2),
    ]
    state = EvaluationState()
    first = evaluate_generated_rule(compiled, inputs, interval_start=BASE, state=state)
    second = evaluate_generated_rule(compiled, inputs, interval_start=BASE, state=state)
    assert first.state == "matched"
    assert second.state == "suppressed"
    assert second.suppressed_count == 1
    revision = revision_for_correction(
        first, second, reason_code="retracted", recorded_at=BASE + timedelta(minutes=3)
    )
    assert revision.revision == 2
    assert revision.snapshot.revision == 2
    assert revision.generated_only and not revision.operational


def test_evaluator_rejects_scope_mixing() -> None:
    compiled = compile_rule(document(0))
    item = input_value("generated-one", "generated.vehicle.observed", 1).model_copy(
        update={"department": "other-lab"}
    )
    with pytest.raises(ValueError, match="scope"):
        evaluate_generated_rule(compiled, [item], interval_start=BASE)


@pytest.mark.parametrize(
    ("kind", "parameters", "source_count", "expected"),
    [
        ("sequence", {"duration_ms": 5_000}, 2, "matched"),
        ("within", {"duration_ms": 5_000}, 1, "matched"),
        ("until", {"duration_ms": 5_000}, 2, "not_matched"),
        ("for_at_least", {"duration_ms": 1_000}, 1, "matched"),
        ("absence", {"duration_ms": 1_000}, 1, "matched"),
        (
            "count",
            {"duration_ms": 5_000, "threshold": 2, "grouping_field": "object_class"},
            1,
            "matched",
        ),
        (
            "rate",
            {
                "duration_ms": 60_000,
                "rate_per_minute": 1.0,
                "grouping_field": "object_class",
            },
            1,
            "matched",
        ),
        (
            "distinct_stream_count",
            {"duration_ms": 5_000, "threshold": 2},
            1,
            "matched",
        ),
        (
            "schedule_gate",
            {"schedule_ref": "generated.always-test-window"},
            1,
            "matched",
        ),
    ],
)
def test_evaluator_covers_bounded_temporal_node_families(
    kind: str,
    parameters: dict[str, object],
    source_count: int,
    expected: str,
) -> None:
    compiled = compile_rule(
        operator_document(
            kind,
            parameters,
            source_count=source_count,
            schedule=kind == "schedule_gate",
        )
    )
    inputs = [
        input_value(f"generated-{index}", f"generated.source-{index}", index + 1)
        for index in range(source_count)
    ]
    if kind in {"for_at_least", "count", "rate"}:
        inputs.append(input_value("generated-extra", "generated.source-0", 3))
    if kind == "absence":
        inputs = [input_value("generated-unrelated", "generated.unrelated", 1)]
    if kind == "distinct_stream_count":
        inputs.append(
            input_value("generated-other-stream", "generated.source-0", 2).model_copy(
                update={"stream_id": "str_" + "2" * 32}
            )
        )
    result = evaluate_generated_rule(compiled, inputs, interval_start=BASE)
    assert result.state == expected


@pytest.mark.parametrize(
    ("kind", "parameters", "source_count", "expected"),
    [
        ("all", {}, 2, "matched"),
        ("any", {}, 2, "matched"),
        ("quorum", {"quorum": 2}, 2, "matched"),
        ("not", {}, 1, "not_matched"),
    ],
)
def test_evaluator_covers_typed_boolean_node_families(
    kind: str,
    parameters: dict[str, object],
    source_count: int,
    expected: str,
) -> None:
    compiled = compile_rule(
        operator_document(
            kind,
            parameters,
            source_count=source_count,
            boolean_inputs=True,
        )
    )
    inputs = [
        input_value(f"generated-{index}", f"generated.source-{index}", index + 1)
        for index in range(source_count)
    ]
    result = evaluate_generated_rule(compiled, inputs, interval_start=BASE)
    assert result.state == expected


def test_evaluator_accepts_generated_hypothesis_sources() -> None:
    value = operator_document("within", {"duration_ms": 5_000})
    payload = value.model_dump(mode="json")
    payload["semantics"]["nodes"][0]["kind"] = "hypothesis_match"
    payload["semantics"]["nodes"][0]["parameters"] = {
        "hypothesis_states": ["generated.supported"]
    }
    compiled = compile_rule(VisualRuleDocumentV1.model_validate(payload))
    item = input_value("generated-hypothesis", "generated.supported", 1).model_copy(
        update={"input_kind": "hypothesis"}
    )
    assert (
        evaluate_generated_rule(compiled, [item], interval_start=BASE).state
        == "matched"
    )


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("confidence", "0.9"),
        ("count", True),
        ("chronology_complete", 1),
        ("event_kind", 7),
    ],
)
def test_evaluator_rejects_coercible_but_wrong_scalar_types(
    field: str,
    invalid: object,
) -> None:
    compiled = compile_rule(document(0))
    item = input_value("generated-one", "generated.vehicle.observed", 1)
    values = dict(item.values)
    values[field] = invalid
    malformed = item.model_copy(update={"values": values})
    with pytest.raises(ValueError, match="invalid scalar type"):
        evaluate_generated_rule(compiled, [malformed], interval_start=BASE)
