from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from hcam.acceptance.bounds import GeneratedBoundaryError, validate_generated_document
from hcam.acceptance.canonical import stable_id
from hcam.acceptance.contracts import (
    AssertionResultV1,
    ScenarioDefinitionV1,
    SideEffectLedgerV1,
    StepObservationV1,
)


def _result(
    scenario_id: str,
    family: str,
    passed: bool,
    reason: str,
    observations: Sequence[StepObservationV1],
) -> AssertionResultV1:
    return AssertionResultV1(
        assertion_id=stable_id("p47", scenario_id, "assertion", family),
        scenario_id=scenario_id,
        family=family,
        status="passed" if passed else "failed",
        reason_code=reason,
        evidence_refs=tuple(item.observation_id for item in observations),
    )


def evaluate_assertions(
    scenario: ScenarioDefinitionV1,
    observations: Sequence[StepObservationV1],
    snapshot: Mapping[str, Any],
    side_effects: SideEffectLedgerV1,
) -> tuple[AssertionResultV1, ...]:
    expected = list(scenario.steps)
    ordered_times: list[datetime] = [item.logical_at for item in observations]
    schema_ok = len(observations) == len(expected) and all(
        item.scenario_id == scenario.scenario_id for item in observations
    )
    chronology_ok = ordered_times == sorted(ordered_times) and len(
        set(ordered_times)
    ) == len(ordered_times)
    expected_ok = all(
        actual.step_id == planned.step_id
        and actual.sequence == planned.sequence
        and actual.action == planned.action
        and actual.outcome == planned.expected_outcome
        and actual.reason_code == planned.expected_reason
        for planned, actual in zip(expected, observations, strict=False)
    )
    authorization_ok = (
        snapshot.get("cross_scope_denied") is True
        if scenario.category == "authorization_isolation"
        else True
    )
    review_ok = snapshot.get("accepted_without_review") is False
    integrity_ok = all(
        item.output_digest.startswith("sha256:") and len(item.output_digest) == 71
        for item in observations
    )
    identity_ok = len({item.observation_id for item in observations}) == len(
        observations
    )
    recovery_ok = (
        snapshot.get("worker_state") == "recovered"
        if scenario.category == "worker_recovery"
        else snapshot.get("worker_state") != "degraded"
    )
    side_effect_values = side_effects.model_dump(mode="json")
    side_effect_ok = (
        side_effect_values.pop("generated_only") is True
        and all(
            value == 0 and type(value) is int for value in side_effect_values.values()
        )
        and snapshot.get("external_effects") == 0
        and snapshot.get("direct_persistence_attempts") == 0
    )
    try:
        validate_generated_document(dict(snapshot))
        redaction_ok = True
    except GeneratedBoundaryError:
        redaction_ok = False
    terminal_ok = (
        snapshot.get("generated_only") is True and snapshot.get("operational") is False
    )
    handoff_ok = all(
        item.action in {step.action for step in expected} for item in observations
    )
    accessibility_ok = all(item.reason_code and item.state for item in observations)
    checks = (
        (
            "schema",
            schema_ok,
            "assertion.schema_passed" if schema_ok else "assertion.schema_failed",
        ),
        (
            "authorization",
            authorization_ok,
            "assertion.authorization_passed"
            if authorization_ok
            else "assertion.authorization_failed",
        ),
        (
            "chronology",
            chronology_ok,
            "assertion.chronology_passed"
            if chronology_ok
            else "assertion.chronology_failed",
        ),
        (
            "identity",
            identity_ok,
            "assertion.identity_passed" if identity_ok else "assertion.identity_failed",
        ),
        (
            "rule",
            expected_ok,
            "assertion.expected_outcomes_passed"
            if expected_ok
            else "assertion.expected_outcomes_failed",
        ),
        (
            "review",
            review_ok,
            "assertion.review_passed" if review_ok else "assertion.review_failed",
        ),
        (
            "integrity",
            integrity_ok,
            "assertion.integrity_passed"
            if integrity_ok
            else "assertion.integrity_failed",
        ),
        (
            "redaction",
            redaction_ok,
            "assertion.redaction_passed"
            if redaction_ok
            else "assertion.redaction_failed",
        ),
        (
            "recovery",
            recovery_ok,
            "assertion.recovery_passed" if recovery_ok else "assertion.recovery_failed",
        ),
        (
            "side_effect",
            side_effect_ok,
            "assertion.side_effect_passed"
            if side_effect_ok
            else "assertion.side_effect_failed",
        ),
        (
            "handoff",
            handoff_ok and terminal_ok,
            "assertion.handoff_passed"
            if handoff_ok and terminal_ok
            else "assertion.handoff_failed",
        ),
        (
            "accessibility",
            accessibility_ok,
            "assertion.accessibility_passed"
            if accessibility_ok
            else "assertion.accessibility_failed",
        ),
    )
    return tuple(
        _result(scenario.scenario_id, family, passed, reason, observations)
        for family, passed, reason in checks
    )
