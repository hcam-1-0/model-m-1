#!/usr/bin/env python3
"""Generate and verify aggregate-only P3.5 W8 consensus evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from hcam.analytics.anpr import (  # noqa: E402
    BoundedSyntheticConsensus,
    ConsensusGeneratedEvaluationV1,
    ConsensusGeneratedScenarioV1,
    ConsensusViolation,
    EphemeralConsensusObservationV1,
    EphemeralConsensusResultV1,
    EphemeralPlateNormalizationV1,
    SyntheticAnprExecutionPolicyV1,
    SyntheticConsensusPolicyV1,
    derive_generated_request,
    generate_ephemeral_token,
    synthetic_corpus_plan_fixture,
)
from hcam.analytics.anpr.guardrails import canonical_anpr_evidence_json  # noqa: E402


EVIDENCE_PATH = ROOT / "contracts" / "phase-3" / "p3-5-consensus-evaluation.json"
MAX_EVIDENCE_BYTES = 64 * 1024
MAX_EVIDENCE_NODES = 4_096
_CONSENSUS_AUTHORIZATION = (
    "P35-W7_normalization_confidence_abstention_and_bounded_consensus"
)
_EVIDENCE_AUTHORIZATION = (
    "P35-W8_zero_retention_aggregate_evidence_security_and_documentation"
)


class ConsensusToolError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _ScenarioResult:
    name: str
    execution_count: int
    results: tuple[EphemeralConsensusResultV1, ...]
    violation_count: int = 0

    def aggregate(self) -> ConsensusGeneratedScenarioV1:
        return ConsensusGeneratedScenarioV1(
            scenario=self.name,
            execution_count=self.execution_count,
            closed_result_count=len(self.results),
            abstained_result_count=sum(result.abstain for result in self.results),
            violation_count=self.violation_count,
        )


def _identifier(prefix: str, value: int) -> str:
    return f"{prefix}_{value:032x}"


def _load_authorization() -> None:
    path = ROOT / "contracts" / "phase-3" / "p3-5-start-authorization.json"
    try:
        authorization = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConsensusToolError("W8 authorization cannot be read") from exc
    runtime = authorization.get("allowed_runtime")
    work_packages = authorization.get("allowed_work_packages", [])
    if not isinstance(runtime, dict) or (
        authorization.get("decision_id") != "D-P3.5-START"
        or authorization.get("effective") is not True
        or _CONSENSUS_AUTHORIZATION not in work_packages
        or _EVIDENCE_AUTHORIZATION not in work_packages
        or authorization.get("allowed_network_actions") != []
        or runtime.get("network_access") is not False
        or runtime.get("repository_dependency_or_lockfile_change") is not False
        or runtime.get("tesseract_runtime_authorized") is not False
    ):
        raise ConsensusToolError("W8 authorization boundary changed")


def _blocked_network_attempt() -> int:
    original = socket.create_connection

    def denied(*_args: object, **_kwargs: object) -> socket.socket:
        raise PermissionError("network denied by P3.5 W8")

    socket.create_connection = denied
    try:
        try:
            socket.create_connection(("127.0.0.1", 9), timeout=0.01)
        except PermissionError:
            return 1
        raise ConsensusToolError("W8 network denial did not fail closed")
    finally:
        socket.create_connection = original


def _generated_tokens() -> tuple[str, str]:
    plan = synthetic_corpus_plan_fixture()
    policy = SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")
    tokens = tuple(
        generate_ephemeral_token(
            derive_generated_request(plan, "development", index),
            policy=policy,
        ).token
        for index in range(2)
    )
    if tokens[0] == tokens[1]:
        raise ConsensusToolError("generated W8 token fixtures collided")
    return tokens


def _normalization(value: str, confidence: float) -> EphemeralPlateNormalizationV1:
    return EphemeralPlateNormalizationV1(
        candidate_id="OCR-L0",
        script_lane="latin",
        raw_hypothesis_digest=(
            "sha256:" + hashlib.sha256(value.encode("ascii")).hexdigest()
        ),
        nfc_value=value,
        graphemes=tuple(value),
        normalized_display_candidate=value,
        raw_scalar_count=len(value),
        nfc_scalar_count=len(value),
        grapheme_count=len(value),
        format_family="synthetic_non_issuable",
        validation_outcomes=(
            "allowlist_valid",
            "graphemes_segmented",
            "nfc_derived",
            "synthetic_grammar_valid",
            "unicode_scalar_valid",
            "utf8_valid",
        ),
        nfc_transform_performed=False,
        case_transform_performed=False,
        raw_confidence=confidence,
        calibrated_confidence=confidence,
        abstention_reason="quality_threshold_unapproved",
    )


def _observation(
    sequence: int,
    *,
    token: str,
    confidence: float = 0.8,
    stream: int = 1,
    epoch: int = 1,
    track: int = 1,
    event_time_ms: int | None = None,
) -> EphemeralConsensusObservationV1:
    return EphemeralConsensusObservationV1(
        stream_id=_identifier("str", stream),
        tracker_epoch=_identifier("epoch", epoch),
        track_id=_identifier("trk", track),
        event_time_ms=sequence * 100 if event_time_ms is None else event_time_ms,
        source_sequence=sequence,
        normalization=_normalization(token, confidence),
    )


def _engine() -> BoundedSyntheticConsensus:
    return BoundedSyntheticConsensus(
        SyntheticConsensusPolicyV1(enabled=True, environment="test")
    )


def _run_scenarios() -> tuple[tuple[_ScenarioResult, ...], int]:
    first, second = _generated_tokens()
    scenarios: list[_ScenarioResult] = []

    engine = _engine()
    agreement: tuple[EphemeralConsensusResultV1, ...] = ()
    for sequence in range(1, 6):
        agreement += engine.observe(_observation(sequence, token=first))
    scenarios.append(_ScenarioResult("agreement", 5, agreement))

    engine = _engine()
    disagreement: tuple[EphemeralConsensusResultV1, ...] = ()
    for sequence, token in enumerate(
        (first, second, first, second, first), start=1
    ):
        disagreement += engine.observe(
            _observation(sequence, token=token, confidence=0.5)
        )
    scenarios.append(_ScenarioResult("disagreement", 5, disagreement))

    engine = _engine()
    for stream, epoch, track in ((1, 1, 1), (2, 1, 1), (1, 2, 1), (1, 1, 2)):
        engine.observe(
            _observation(
                1,
                token=first,
                stream=stream,
                epoch=epoch,
                track=track,
            )
        )
    isolated = (
        engine.reset_epoch(_identifier("str", 1), _identifier("epoch", 1))
        + engine.reset_epoch(_identifier("str", 1), _identifier("epoch", 2))
        + engine.reset_epoch(_identifier("str", 2), _identifier("epoch", 1))
    )
    if len(isolated) != 4 or any(item.observation_count != 1 for item in isolated):
        raise ConsensusToolError("W8 grouping boundaries merged")
    scenarios.append(_ScenarioResult("cross_boundary_isolation", 4, isolated))

    engine = _engine()
    engine.observe(_observation(1, token=first))
    duplicate_violations = 0
    try:
        engine.observe(_observation(1, token=first, event_time_ms=101))
    except ConsensusViolation as exc:
        if exc.code != "duplicate_observation":
            raise
        duplicate_violations = 1
    duplicate = engine.close_track(
        _identifier("str", 1), _identifier("epoch", 1), _identifier("trk", 1)
    )
    scenarios.append(
        _ScenarioResult("duplicate_rejection", 2, duplicate, duplicate_violations)
    )

    engine = _engine()
    engine.observe(_observation(2, token=first, event_time_ms=200))
    ordering_violations = 0
    try:
        engine.observe(_observation(1, token=first, event_time_ms=300))
    except ConsensusViolation as exc:
        if exc.code != "out_of_order_observation":
            raise
        ordering_violations = 1
    ordering = engine.close_track(
        _identifier("str", 1), _identifier("epoch", 1), _identifier("trk", 1)
    )
    scenarios.append(
        _ScenarioResult(
            "out_of_order_rejection", 2, ordering, ordering_violations
        )
    )

    engine = _engine()
    engine.observe(_observation(1, token=first, event_time_ms=100))
    window = engine.observe(_observation(2, token=first, event_time_ms=2_100))
    scenarios.append(_ScenarioResult("event_time_window", 2, window))

    engine = _engine()
    engine.observe(_observation(1, token=first, track=1))
    engine.observe(_observation(1, token=second, track=2))
    epoch_reset = engine.reset_epoch(
        _identifier("str", 1), _identifier("epoch", 1)
    )
    scenarios.append(_ScenarioResult("epoch_reset", 2, epoch_reset))

    engine = _engine()
    engine.observe(_observation(1, token=first))
    engine.observe(_observation(2, token=first))
    track_end = engine.close_track(
        _identifier("str", 1), _identifier("epoch", 1), _identifier("trk", 1)
    )
    scenarios.append(_ScenarioResult("track_end", 2, track_end))

    engine = _engine()
    for track in range(1, 257):
        engine.observe(_observation(1, token=first, track=track))
    maximum_active_states = engine.active_state_count(_identifier("str", 1))
    overload = engine.observe(_observation(1, token=second, track=257))
    overload += engine.reset_epoch(
        _identifier("str", 1), _identifier("epoch", 1)
    )
    scenarios.append(_ScenarioResult("overload", 257, overload))

    return tuple(sorted(scenarios, key=lambda item: item.name)), maximum_active_states


def build_evaluation() -> ConsensusGeneratedEvaluationV1:
    _load_authorization()
    replay_observations = tuple(_run_scenarios() for _ in range(20))
    canonical = tuple(
        json.dumps(
            [item.aggregate().model_dump(mode="json") for item in scenarios],
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        for scenarios, _ in replay_observations
    )
    scenarios, maximum_active_states = replay_observations[0]
    aggregates = tuple(item.aggregate() for item in scenarios)
    return ConsensusGeneratedEvaluationV1(
        scenario_evaluations=aggregates,
        replay_output_deterministic=len(set(canonical)) == 1,
        maximum_active_states_observed=maximum_active_states,
        consensus_execution_count=sum(item.execution_count for item in aggregates),
        consensus_closed_result_count=sum(
            item.closed_result_count for item in aggregates
        ),
        consensus_abstained_result_count=sum(
            item.abstained_result_count for item in aggregates
        ),
        duplicate_rejection_count=sum(
            item.violation_count
            for item in aggregates
            if item.scenario == "duplicate_rejection"
        ),
        out_of_order_rejection_count=sum(
            item.violation_count
            for item in aggregates
            if item.scenario == "out_of_order_rejection"
        ),
        network_attempt_count=_blocked_network_attempt(),
    )


def render_evaluation(evaluation: ConsensusGeneratedEvaluationV1) -> str:
    return canonical_anpr_evidence_json(
        evaluation,
        maximum_bytes=MAX_EVIDENCE_BYTES,
        maximum_nodes=MAX_EVIDENCE_NODES,
    )


def check_evidence() -> int:
    try:
        actual = EVIDENCE_PATH.read_text(encoding="utf-8")
        parsed = ConsensusGeneratedEvaluationV1.model_validate_json(actual)
        canonical = render_evaluation(parsed)
    except (OSError, ValueError) as exc:
        print(f"[fail] P3.5 W8 evidence: {exc}")
        return 1
    prohibited = (
        '"nfc_value":',
        '"normalized_display_candidate":',
        '"raw_hypothesis_digest":',
        '"ranked_votes":',
        '"stream_id":',
        '"track_id":',
        '"tracker_epoch":',
        '"winning_candidate":',
        "SYN-",
        "anprsample_",
        "anprregion_",
        "str_000000",
        "epoch_000000",
        "trk_000000",
        "B:\\",
    )
    if actual != canonical or any(value in actual for value in prohibited):
        print("[fail] P3.5 W8 evidence contains ephemeral text or identifiers")
        return 1
    print(f"[pass] {EVIDENCE_PATH.relative_to(ROOT)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--write-evidence", action="store_true")
    evaluate.add_argument(
        "--acknowledge-generated-only-evidence", action="store_true"
    )
    subparsers.add_parser("check-evidence")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "check-evidence":
            return check_evidence()
        if args.write_evidence and not args.acknowledge_generated_only_evidence:
            print("Refusing to write W8 evidence without generated-only acknowledgment")
            return 2
        evaluation = build_evaluation()
        rendered = render_evaluation(evaluation)
        if args.write_evidence:
            EVIDENCE_PATH.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"[write] {EVIDENCE_PATH.relative_to(ROOT)}")
        else:
            print(rendered, end="")
        return 0
    except (ConsensusToolError, OSError, ValueError) as exc:
        print(f"P3.5 W8 failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
