#!/usr/bin/env python3
"""Generate and verify deterministic P3.4 C10 geometry-event evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from pathlib import Path

import shapely

from hcam.analytics.geometry import (
    GeometryDefinitionV1,
    LineGeometryV1,
    NormalizedPoint,
    ZoneGeometryV1,
)
from hcam.analytics.spatial import (
    BoundedEventBuffer,
    CompiledGeometryRule,
    ConstrainedCelEnvironment,
    GeometryEventEvaluator,
    GeometryRuleV1,
    RuleGraphV1,
    RuleNodeV1,
    canonicalize_geometry,
)
from hcam.analytics.spatial.generated import (
    GENERATOR_ID,
    GENERATOR_VERSION,
    GeneratedLifecycleScenario,
    build_generated_lifecycle_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "contracts" / "phase-3" / "p3-4-c10-evidence.json"
NOW = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)
ASSIGNMENT_ID = "ana_" + "2" * 32
STREAM_ID = "str_" + "1" * 32
CAMERA_ID = "synthetic:c10-evidence"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64

EXPECTED_EVENTS = {
    "c10-line-crossing": ["hcam.analytics.line.crossing.v1"],
    "c10-zone-lifecycle": [
        "hcam.analytics.zone.entry.v1",
        "hcam.analytics.zone.exit.v1",
    ],
    "c10-dwell": ["hcam.analytics.zone.dwell.threshold_met.v1"],
    "c10-occupancy": [
        "hcam.analytics.zone.occupancy.threshold_entered.v1",
        "hcam.analytics.zone.occupancy.threshold_exited.v1",
    ],
    "c10-out-of-order": ["hcam.analytics.line.crossing.v1"],
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _geometry(shape: LineGeometryV1 | ZoneGeometryV1, geometry_id: str):
    return GeometryDefinitionV1(
        geometry_id=geometry_id,
        version=1,
        department="traffic",
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
        status="approved",
        shape=shape,
        intended_use="Generated-only P3.4 C10 evidence",
        policy_version=DIGEST_A,
        owner_id="mayank-admin",
        approval_record_id="D-P3.4-START",
        created_at=NOW,
        updated_at=NOW,
    )


def _graph(signal: str) -> RuleGraphV1:
    return RuleGraphV1(
        nodes=[RuleNodeV1(node_id="primitive", kind="spatial", signal=signal)],
        output_node_id="primitive",
    )


def _rule(
    geometry: GeometryDefinitionV1,
    rule_id: str,
    event_kind: str,
    signal: str,
    **overrides: object,
) -> GeometryRuleV1:
    values: dict[str, object] = {
        "rule_id": rule_id,
        "version": 1,
        "status": "approved",
        "department": geometry.department,
        "assignment_id": ASSIGNMENT_ID,
        "stream_id": geometry.stream_id,
        "camera_id": geometry.camera_id,
        "geometry_id": geometry.geometry_id,
        "geometry_version": geometry.version,
        "event_kind": event_kind,
        "class_filter": ["vehicle.car"],
        "cel_condition": "confidence >= 0.5 && class_id == 'vehicle.car'",
        "graph": _graph(signal),
        "configuration_digest": DIGEST_B,
        "retention_class": "derived.analytics.standard",
        "owner_id": "mayank-admin",
        "approval_record_id": "D-P3.4-START",
        "effective_from": NOW - timedelta(minutes=1),
        "created_at": NOW,
        "updated_at": NOW,
    }
    if event_kind == "hcam.analytics.line.crossing.v1":
        values.update(
            line_direction="both",
            deadband=0.01,
            rearm_distance=0.04,
        )
    else:
        values["zone_hysteresis"] = 0.01
    values.update(overrides)
    return GeometryRuleV1.model_validate(values)


def _compiled(
    geometry: GeometryDefinitionV1,
    definitions: list[GeometryRuleV1],
) -> tuple[CompiledGeometryRule, ...]:
    environment = ConstrainedCelEnvironment()
    canonical = canonicalize_geometry(geometry.shape)
    return tuple(
        CompiledGeometryRule.build(item, geometry, canonical, environment)
        for item in definitions
    )


def _scenario_rules(
    scenario_id: str,
) -> tuple[GeneratedLifecycleScenario, tuple[CompiledGeometryRule, ...]]:
    scenario = build_generated_lifecycle_scenario(
        scenario_id,
        seed=34,
        observed_at=NOW,
        department="traffic",
        assignment_id=ASSIGNMENT_ID,
        stream_id=STREAM_ID,
        camera_id=CAMERA_ID,
    )
    if scenario_id in {"c10-line-crossing", "c10-out-of-order"}:
        geometry = _geometry(
            LineGeometryV1(
                start=NormalizedPoint(x=0.5, y=0.1),
                end=NormalizedPoint(x=0.5, y=0.9),
            ),
            "c10-line",
        )
        rules = [
            _rule(
                geometry,
                "c10-line-crossing",
                "hcam.analytics.line.crossing.v1",
                "line_crossing",
            )
        ]
    else:
        geometry = _geometry(
            ZoneGeometryV1(
                vertices=[
                    NormalizedPoint(x=0.2, y=0.2),
                    NormalizedPoint(x=0.8, y=0.2),
                    NormalizedPoint(x=0.8, y=0.8),
                    NormalizedPoint(x=0.2, y=0.8),
                ]
            ),
            "c10-zone",
        )
        if scenario_id == "c10-zone-lifecycle":
            rules = [
                _rule(
                    geometry,
                    "c10-zone-entry",
                    "hcam.analytics.zone.entry.v1",
                    "zone_entry",
                ),
                _rule(
                    geometry,
                    "c10-zone-exit",
                    "hcam.analytics.zone.exit.v1",
                    "zone_exit",
                ),
            ]
        elif scenario_id == "c10-dwell":
            rules = [
                _rule(
                    geometry,
                    "c10-dwell",
                    "hcam.analytics.zone.dwell.threshold_met.v1",
                    "zone_dwell_threshold",
                    dwell_threshold_ms=2_000,
                    occlusion_grace_ms=1_000,
                )
            ]
        else:
            rules = [
                _rule(
                    geometry,
                    "c10-occupancy-enter",
                    "hcam.analytics.zone.occupancy.threshold_entered.v1",
                    "zone_occupancy_entered",
                    occupancy_enter_threshold=2,
                    occupancy_reset_threshold=0,
                ),
                _rule(
                    geometry,
                    "c10-occupancy-exit",
                    "hcam.analytics.zone.occupancy.threshold_exited.v1",
                    "zone_occupancy_exited",
                    occupancy_enter_threshold=2,
                    occupancy_reset_threshold=0,
                ),
            ]
    return scenario, _compiled(geometry, rules)


def _input_document(item: object) -> dict[str, object]:
    lifecycle = item
    return {
        "bbox": list(lifecycle.bbox),
        "class_id": lifecycle.class_id,
        "confidence": lifecycle.confidence,
        "digest": lifecycle.digest,
        "epoch_id": lifecycle.epoch_id,
        "lifecycle_id": lifecycle.lifecycle_id,
        "observed_at": lifecycle.observed_at.astimezone(UTC).isoformat(),
        "source_sequence": lifecycle.source_sequence,
        "state": lifecycle.state,
        "track_id": lifecycle.track_id,
    }


def _execute(
    scenario: GeneratedLifecycleScenario,
    rules: tuple[CompiledGeometryRule, ...],
) -> dict[str, object]:
    evaluator = GeometryEventEvaluator(rules)
    buffer = BoundedEventBuffer()
    transitions: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    outcomes: list[dict[str, object]] = []
    for item in scenario.inputs:
        outcome = buffer.push(item)
        outcomes.append({"outcome": outcome, "source_sequence": item.source_sequence})
        for ready in buffer.pop_ready():
            emitted = evaluator.evaluate(ready)
            events.extend(event.document() for event in emitted)
            transitions.append(
                {
                    "emitted_event_ids": [event.event_id for event in emitted],
                    "source_sequence": ready.source_sequence,
                    "states": evaluator.state_snapshots(),
                }
            )
    for ready in buffer.drain():
        emitted = evaluator.evaluate(ready)
        events.extend(event.document() for event in emitted)
        transitions.append(
            {
                "emitted_event_ids": [event.event_id for event in emitted],
                "source_sequence": ready.source_sequence,
                "states": evaluator.state_snapshots(),
            }
        )
    actual_kinds = [str(event["event_kind"]) for event in events]
    return {
        "actual_event_kinds": actual_kinds,
        "arrival_outcomes": outcomes,
        "event_digest": _digest(events),
        "events": events,
        "expected_event_kinds": EXPECTED_EVENTS[scenario.scenario_id],
        "input_digest": "sha256:" + scenario.digest,
        "inputs": [_input_document(item) for item in scenario.inputs],
        "logic_agreement": 1.0
        if actual_kinds == EXPECTED_EVENTS[scenario.scenario_id]
        else 0.0,
        "processed_transitions": transitions,
        "scenario_id": scenario.scenario_id,
        "seed": scenario.seed,
    }


def build_report() -> dict[str, object]:
    reports = []
    replay_hashes: dict[str, list[str]] = {}
    for scenario_id in EXPECTED_EVENTS:
        scenario, rules = _scenario_rules(scenario_id)
        report = _execute(scenario, rules)
        reports.append(report)
        replay_hashes[scenario_id] = [
            str(_execute(*_scenario_rules(scenario_id))["event_digest"])
            for _ in range(20)
        ]
    body: dict[str, object] = {
        "dataset_id": "DATA-GEO-EVT-GEN-C10",
        "dependencies": {
            "cel_expr_python": version("cel-expr-python"),
            "geos": shapely.geos_version_string,
            "shapely": shapely.__version__,
        },
        "execution_scope": "generated_only",
        "generator_id": GENERATOR_ID,
        "generator_version": GENERATOR_VERSION,
        "limitations": [
            "no_real_camera_accuracy_claim",
            "no_operational_utility_claim",
            "no_scale_or_latency_claim",
            "no_legal_or_deployment_approval",
        ],
        "logic_agreement": min(
            float(item["logic_agreement"]) for item in reports
        ),
        "prohibited_inputs_present": False,
        "replay_count": 20,
        "replay_hashes": replay_hashes,
        "replay_stable": all(len(set(values)) == 1 for values in replay_hashes.values()),
        "scenario_reports": reports,
        "schema_version": "1.0.0",
    }
    body["content_digest"] = _digest(body)
    return json.loads(_canonical(body))


def validate(document: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if document.get("dataset_id") != "DATA-GEO-EVT-GEN-C10":
        failures.append("dataset_id")
    if document.get("execution_scope") != "generated_only":
        failures.append("execution_scope")
    if document.get("logic_agreement") != 1.0:
        failures.append("logic_agreement")
    if document.get("replay_count") != 20 or document.get("replay_stable") is not True:
        failures.append("replay")
    if document.get("prohibited_inputs_present") is not False:
        failures.append("prohibited_inputs")
    scenarios = document.get("scenario_reports")
    if not isinstance(scenarios, list) or len(scenarios) != len(EXPECTED_EVENTS):
        failures.append("scenario_reports")
    content_digest = document.get("content_digest")
    unsigned = dict(document)
    unsigned.pop("content_digest", None)
    if content_digest != _digest(unsigned):
        failures.append("content_digest")
    return failures


def _serialized(document: dict[str, object]) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    write = subparsers.add_parser("write")
    write.add_argument("--acknowledge-generated-only-evidence", action="store_true")
    subparsers.add_parser("check")
    args = parser.parse_args()
    expected = build_report()
    failures = validate(expected)
    if failures:
        print("[fail] generated report: " + ", ".join(failures))
        return 1
    if args.command == "write":
        if not args.acknowledge_generated_only_evidence:
            print("[fail] explicit generated-only evidence acknowledgment is required")
            return 2
        REPORT.write_text(_serialized(expected), encoding="utf-8", newline="\n")
        print(f"[write] {REPORT.relative_to(ROOT)} {expected['content_digest']}")
        return 0
    try:
        actual = json.loads(REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[fail] {exc}")
        return 1
    if actual != expected:
        print("[fail] C10 evidence drift")
        return 1
    print(f"[pass] {REPORT.relative_to(ROOT)} {expected['content_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
