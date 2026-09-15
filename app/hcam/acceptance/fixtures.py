from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from hcam.acceptance.bounds import REQUIRED_SCENARIO_IDS
from hcam.acceptance.canonical import digest, stable_id
from hcam.acceptance.contracts import (
    ScenarioDefinitionV1,
    ScenarioManifestV1,
    ScenarioStepV1,
)


LOGICAL_EPOCH = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
SEED = 470047


def _step(
    scenario_id: str,
    sequence: int,
    action: str,
    outcome: str,
    reason: str,
    **input_data: Any,
) -> ScenarioStepV1:
    return ScenarioStepV1(
        step_id=f"p47.{scenario_id.lower()}.step.{sequence:02d}",
        sequence=sequence,
        action=action,
        advance_ms=1_000 + sequence * 100,
        input_data={"generated_marker": f"p47.{scenario_id.lower()}", **input_data},
        expected_outcome=outcome,
        expected_reason=reason,
    )


def scenario_definitions() -> tuple[ScenarioDefinitionV1, ...]:
    scenarios = (
        ScenarioDefinitionV1(
            scenario_id="S00",
            category="golden",
            title="Generated event through reviewed alert and evidence timeline",
            expected_terminal_state="completed",
            steps=(
                _step(
                    "S00",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.motion",
                ),
                _step(
                    "S00", 2, "correlate", "accepted", "correlation.hypothesis_created"
                ),
                _step("S00", 3, "evaluate_rule", "accepted", "rule.matched"),
                _step("S00", 4, "propose_alert", "accepted", "alert.proposed"),
                _step(
                    "S00",
                    5,
                    "query_reference",
                    "accepted",
                    "reference.candidate_set_created",
                    reference_mode="candidate",
                ),
                _step(
                    "S00",
                    6,
                    "review_alert",
                    "accepted",
                    "review.approved",
                    decision="approve",
                ),
                _step(
                    "S00",
                    7,
                    "transition_alert",
                    "accepted",
                    "alert.closed",
                    target_state="closed",
                ),
                _step(
                    "S00", 8, "open_investigation", "accepted", "investigation.opened"
                ),
                _step(
                    "S00",
                    9,
                    "append_evidence_reference",
                    "accepted",
                    "evidence.reference_registered",
                ),
                _step("S00", 10, "emit_signal", "accepted", "signal.projected"),
            ),
        ),
        ScenarioDefinitionV1(
            scenario_id="S01",
            category="abstention",
            title="Generated non-match and reference abstention remain non-alerting",
            expected_terminal_state="abstained",
            steps=(
                _step(
                    "S01",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.uncertain",
                ),
                _step(
                    "S01",
                    2,
                    "correlate",
                    "abstained",
                    "correlation.no_match",
                    no_match=True,
                ),
                _step("S01", 3, "evaluate_rule", "abstained", "rule.not_matched"),
                _step(
                    "S01",
                    4,
                    "query_reference",
                    "abstained",
                    "reference.abstained",
                    reference_mode="abstain",
                ),
                _step("S01", 5, "emit_signal", "accepted", "signal.projected"),
            ),
        ),
        ScenarioDefinitionV1(
            scenario_id="S02",
            category="duplicate_replay",
            title="Generated duplicate delivery is suppressed without losing provenance",
            expected_terminal_state="accepted",
            steps=(
                _step(
                    "S02",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.vehicle",
                ),
                _step(
                    "S02",
                    2,
                    "duplicate_event",
                    "duplicate",
                    "event.duplicate_suppressed",
                ),
                _step(
                    "S02", 3, "correlate", "accepted", "correlation.hypothesis_created"
                ),
                _step("S02", 4, "evaluate_rule", "accepted", "rule.matched"),
                _step("S02", 5, "propose_alert", "accepted", "alert.proposed"),
                _step(
                    "S02",
                    6,
                    "review_alert",
                    "accepted",
                    "review.approved",
                    decision="approve",
                ),
            ),
        ),
        ScenarioDefinitionV1(
            scenario_id="S03",
            category="late_conflict",
            title="Generated late conflict is retained and correlation abstains",
            expected_terminal_state="conflict_recorded",
            steps=(
                _step(
                    "S03",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.person",
                ),
                _step(
                    "S03",
                    2,
                    "record_late_conflict",
                    "degraded",
                    "chronology.conflict_recorded",
                ),
                _step(
                    "S03", 3, "correlate", "abstained", "correlation.conflict_abstained"
                ),
                _step("S03", 4, "emit_signal", "accepted", "signal.projected"),
            ),
        ),
        ScenarioDefinitionV1(
            scenario_id="S04",
            category="authorization_isolation",
            title="Generated cross-scope request is denied without resource disclosure",
            expected_terminal_state="denied",
            steps=(
                _step(
                    "S04",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.object",
                ),
                _step(
                    "S04",
                    2,
                    "deny_cross_scope",
                    "denied",
                    "authorization.cross_scope_denied",
                ),
                _step("S04", 3, "emit_signal", "accepted", "signal.projected"),
            ),
        ),
        ScenarioDefinitionV1(
            scenario_id="S05",
            category="reference_degradation",
            title="Generated reference dependency failure stays visible and non-authoritative",
            expected_terminal_state="reference_degraded",
            steps=(
                _step(
                    "S05",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.vehicle",
                ),
                _step(
                    "S05", 2, "correlate", "accepted", "correlation.hypothesis_created"
                ),
                _step("S05", 3, "evaluate_rule", "accepted", "rule.matched"),
                _step(
                    "S05",
                    4,
                    "query_reference",
                    "degraded",
                    "reference.unavailable",
                    reference_mode="unavailable",
                ),
                _step("S05", 5, "emit_signal", "accepted", "signal.projected"),
            ),
        ),
        ScenarioDefinitionV1(
            scenario_id="S06",
            category="review_lifecycle_denial",
            title="Generated mandatory review denial blocks alert lifecycle progress",
            expected_terminal_state="review_denied",
            steps=(
                _step(
                    "S06",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.motion",
                ),
                _step(
                    "S06", 2, "correlate", "accepted", "correlation.hypothesis_created"
                ),
                _step("S06", 3, "evaluate_rule", "accepted", "rule.matched"),
                _step("S06", 4, "propose_alert", "accepted", "alert.proposed"),
                _step(
                    "S06", 5, "review_alert", "denied", "review.denied", decision="deny"
                ),
                _step(
                    "S06",
                    6,
                    "transition_alert",
                    "denied",
                    "alert.transition_denied",
                    target_state="closed",
                ),
            ),
        ),
        ScenarioDefinitionV1(
            scenario_id="S07",
            category="correction_retraction",
            title="Generated correction and retraction propagate through investigation evidence",
            expected_terminal_state="retracted",
            steps=(
                _step(
                    "S07",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.object",
                ),
                _step(
                    "S07", 2, "correlate", "accepted", "correlation.hypothesis_created"
                ),
                _step("S07", 3, "evaluate_rule", "accepted", "rule.matched"),
                _step("S07", 4, "propose_alert", "accepted", "alert.proposed"),
                _step(
                    "S07",
                    5,
                    "review_alert",
                    "accepted",
                    "review.approved",
                    decision="approve",
                ),
                _step(
                    "S07", 6, "open_investigation", "accepted", "investigation.opened"
                ),
                _step(
                    "S07",
                    7,
                    "append_evidence_reference",
                    "accepted",
                    "evidence.reference_registered",
                ),
                _step("S07", 8, "record_correction", "accepted", "correction.recorded"),
                _step("S07", 9, "record_retraction", "accepted", "retraction.recorded"),
            ),
        ),
        ScenarioDefinitionV1(
            scenario_id="S08",
            category="worker_recovery",
            title="Generated worker degradation and recovery preserve deterministic progress",
            expected_terminal_state="recovered",
            steps=(
                _step(
                    "S08",
                    1,
                    "observe_event",
                    "accepted",
                    "event.observed",
                    event_kind="generated.motion",
                ),
                _step("S08", 2, "degrade_worker", "degraded", "worker.degraded"),
                _step("S08", 3, "emit_signal", "accepted", "signal.projected"),
                _step("S08", 4, "recover_worker", "recovered", "worker.recovered"),
                _step(
                    "S08", 5, "correlate", "accepted", "correlation.hypothesis_created"
                ),
                _step("S08", 6, "evaluate_rule", "accepted", "rule.matched"),
            ),
        ),
    )
    if tuple(item.scenario_id for item in scenarios) != REQUIRED_SCENARIO_IDS:
        raise RuntimeError("the mandatory P4.7 scenario inventory is incomplete")
    return scenarios


def build_manifest() -> ScenarioManifestV1:
    scenarios = scenario_definitions()
    fixture_digests = {
        f"scenario.{scenario.scenario_id.lower()}": digest(scenario)
        for scenario in scenarios
    }
    return ScenarioManifestV1(
        manifest_id=stable_id("p47", "manifest", SEED),
        seed=SEED,
        logical_epoch=LOGICAL_EPOCH,
        step_quantum_ms=1_000,
        source_order=(
            "analytic_event",
            "correlation",
            "rule_evaluation",
            "proposed_alert",
            "review",
            "investigation",
            "evidence",
            "operations_signal",
        ),
        policy_revisions={
            "authorization": 1,
            "correlation": 1,
            "rules": 1,
            "review": 1,
            "reference": 1,
            "investigation": 1,
            "operations": 1,
        },
        fixture_digests=fixture_digests,
        allowed_variance=(),
        scenarios=scenarios,
    )


def pairwise_cases(count: int = 512) -> list[dict[str, Any]]:
    dimensions = {
        "authorization": ("allowed", "cross_scope", "missing_reason", "role_denied"),
        "concurrency": (
            "etag_match",
            "etag_stale",
            "duplicate_delivery",
            "late_commit",
        ),
        "chronology": ("ordered", "late", "conflict", "unknown_clock"),
        "dependency": ("available", "stale", "unavailable", "unknown"),
        "contract": ("current", "unknown_version", "extra_field", "oversized"),
    }
    keys = tuple(dimensions)
    result: list[dict[str, Any]] = []
    for index in range(count):
        values = {
            key: dimensions[key][(index // (4**position)) % 4]
            for position, key in enumerate(keys)
        }
        denied = any(
            value
            in {
                "cross_scope",
                "missing_reason",
                "role_denied",
                "etag_stale",
                "late_commit",
                "unknown_version",
                "extra_field",
                "oversized",
            }
            for value in values.values()
        )
        result.append(
            {
                "case_id": f"p47.pairwise.{index:04d}",
                "dimensions": values,
                "expected": "denied" if denied else "accepted_or_degraded",
                "generated_only": True,
                "operational": False,
            }
        )
    return result


def fixture_documents() -> dict[str, dict[str, Any]]:
    manifest = build_manifest()
    scenarios = [item.model_dump(mode="json") for item in manifest.scenarios]
    return {
        "generated-scenario-manifest-v1.json": manifest.model_dump(mode="json"),
        "generated-scenario-fixtures-v1.json": {
            "contract_type": "hcam.acceptance.scenario-fixture-set.v1",
            "scenario_count": len(scenarios),
            "scenarios": scenarios,
            "generated_only": True,
            "operational": False,
        },
        "generated-expected-outcomes-v1.json": {
            "contract_type": "hcam.acceptance.expected-outcomes.v1",
            "outcomes": [
                {
                    "scenario_id": item.scenario_id,
                    "terminal_state": item.expected_terminal_state,
                    "steps": [
                        {
                            "step_id": step.step_id,
                            "outcome": step.expected_outcome,
                            "reason_code": step.expected_reason,
                        }
                        for step in item.steps
                    ],
                }
                for item in manifest.scenarios
            ],
            "generated_only": True,
        },
        "generated-pairwise-cases-v1.json": {
            "contract_type": "hcam.acceptance.pairwise-cases.v1",
            "case_count": 512,
            "cases": pairwise_cases(),
            "generated_only": True,
            "operational": False,
        },
    }
