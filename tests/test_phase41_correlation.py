from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.arbitration import (
    CorrelationArbitrationError,
    arbitrate_lane_results,
)
from hcam.intelligence.correlation.bounds import CorrelationBounds, CorrelationLimitError
from hcam.intelligence.correlation.contracts import (
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    LaneResultV1,
)
from hcam.intelligence.correlation.deterministic import evaluate_deterministic_lane
from hcam.intelligence.correlation.lanes import lane_capabilities
from hcam.intelligence.correlation.metrics import CorrelationMetrics
from hcam.intelligence.correlation.runtime import CorrelationRuntimeError, run_generated_batch
from hcam.intelligence.correlation.worker import (
    CorrelationWorkerDisabledError,
    GeneratedCorrelationWorker,
)


BASE = datetime(2026, 1, 1, tzinfo=UTC)


def profile(**updates: object) -> CorrelationProfileV1:
    values: dict[str, object] = {
        "profile_id": "correlation-profile",
        "profile_version": canonical_sha256({"profile": "correlation"}),
        "allowed_event_types": ["hcam.analytics.observation.created.v1"],
        "subject_kind": "vehicle",
        "partition_dimensions": ["generated_reference"],
        "window_seconds": 10,
        "allowed_lateness_seconds": 2,
        "minimum_supporting_events": 2,
        "maximum_events_per_window": 100,
        "maximum_active_windows": 8,
    }
    values.update(updates)
    return CorrelationProfileV1(**values)


def event(
    identifier: int,
    seconds: int,
    *,
    signal_kind: str = "observation",
    event_id: str | None = None,
) -> CorrelationIngressEventV1:
    instant = BASE + timedelta(seconds=seconds)
    return CorrelationIngressEventV1(
        event_id=event_id or f"event-{identifier}",
        event_type="hcam.analytics.observation.created.v1",
        schema_version=1,
        department="generated-lab",
        stream_id="str_" + "3" * 32,
        camera_id="cam-3",
        profile_id="correlation-profile",
        subject_kind="vehicle",
        signals={
            "object_class": "car",
            "signal_kind": signal_kind,
            "confidence": 0.9,
            "generated_reference": "vehicle-a",
            "source_sequence": identifier,
        },
        chronology={
            "occurred_at": instant,
            "observed_at": instant,
            "received_at": instant,
            "recorded_at": instant,
        },
    )


def optional_result(score: float) -> LaneResultV1:
    return LaneResultV1(
        lane="probabilistic",
        status="completed",
        score=score,
        uncertainty=0.1,
        abstained=False,
        lineage_digest=canonical_sha256({"fixture": score}),
        generated_fixture_result=True,
    )


def test_runtime_proposes_complete_window_and_abstains_on_open_window() -> None:
    metrics = CorrelationMetrics()
    result = run_generated_batch(
        [event(1, 1), event(2, 2), event(3, 20)],
        profile(),
        metrics=metrics,
    )
    assert result.accepted_count == 3
    assert [item.state for item in result.hypotheses] == ["proposed", "abstained"]
    assert result.hypotheses[0].authority_class == "mandatory_review"
    assert not result.hypotheses[0].operational
    metric_values = metrics.snapshot()
    duration_keys = [
        key for key in metric_values if key.startswith("correlation_duration_seconds:")
    ]
    assert len(duration_keys) == 1
    metric_values.pop(duration_keys[0])
    assert metric_values == {
        "correlation_hypotheses_total:abstained": 1,
        "correlation_hypotheses_total:proposed": 1,
        "correlation_receipts_total:accepted": 3,
        "correlation_runs_total:succeeded": 1,
        "correlation_windows_total:complete": 1,
        "correlation_windows_total:open": 1,
    }


def test_runtime_preserves_duplicate_and_conflict_outcomes() -> None:
    first = event(1, 1, event_id="shared-event")
    duplicate = first.model_copy(deep=True)
    conflict = event(2, 2, event_id="shared-event")
    result = run_generated_batch([first, duplicate, conflict], profile())
    assert [item.disposition for item in result.receipts] == [
        "accepted",
        "duplicate",
        "conflict",
    ]
    assert result.accepted_count == 1
    assert result.duplicate_count == 1
    assert result.rejected_count == 1


def test_generated_optional_lane_can_influence_but_not_bypass_arbitration() -> None:
    baseline = run_generated_batch([event(1, 1), event(2, 2), event(3, 20)], profile())
    window_id = baseline.windows[0].window_id
    result = run_generated_batch(
        [event(1, 1), event(2, 2), event(3, 20)],
        profile(),
        optional_results={window_id: [optional_result(0.2)]},
    )
    hypothesis = result.hypotheses[0]
    assert hypothesis.state == "proposed"
    assert hypothesis.confidence == pytest.approx(0.6)
    assert hypothesis.uncertainty > 0.0


def test_runtime_rejects_empty_unknown_duplicate_or_deterministic_optional_input() -> None:
    selected = profile()
    with pytest.raises(CorrelationRuntimeError, match="cannot be empty"):
        run_generated_batch([], selected)
    events = [event(1, 1)]
    with pytest.raises(CorrelationRuntimeError, match="unknown window"):
        run_generated_batch(events, selected, optional_results={"cwin_" + "1" * 32: []})
    duplicate = optional_result(0.2)
    with pytest.raises(CorrelationRuntimeError, match="repeats a lane"):
        baseline = run_generated_batch(events, selected)
        run_generated_batch(
            events,
            selected,
            optional_results={baseline.windows[0].window_id: [duplicate, duplicate]},
        )
    deterministic = LaneResultV1(
        lane="deterministic_cpu",
        status="completed",
        score=1.0,
        uncertainty=0.0,
        abstained=False,
        lineage_digest=canonical_sha256({"bad": "replacement"}),
    )
    baseline = run_generated_batch(events, selected)
    with pytest.raises(CorrelationRuntimeError, match="cannot replace"):
        run_generated_batch(
            events,
            selected,
            optional_results={baseline.windows[0].window_id: [deterministic]},
        )


def test_bounds_worker_and_production_gates_fail_closed() -> None:
    selected = profile(maximum_active_windows=8)
    with pytest.raises(CorrelationLimitError, match="batch capacity"):
        run_generated_batch([event(1, 1), event(2, 2)], selected, bounds=CorrelationBounds(events_per_batch=1))
    with pytest.raises(CorrelationWorkerDisabledError, match="disabled by default"):
        GeneratedCorrelationWorker().process([event(1, 1)], selected)
    with pytest.raises(CorrelationWorkerDisabledError, match="forbidden in production"):
        GeneratedCorrelationWorker(enabled=True, environment="production")
    assert GeneratedCorrelationWorker(enabled=True).process([event(1, 1)], selected).input_count == 1


def test_lane_capabilities_and_arbitration_are_closed() -> None:
    capabilities = lane_capabilities()
    assert capabilities[0].lane == "deterministic_cpu"
    assert all(item.execution_state == "unavailable" for item in capabilities[1:])
    with pytest.raises(CorrelationArbitrationError, match="exactly one"):
        arbitrate_lane_results([optional_result(0.5)])
    deterministic = LaneResultV1(
        lane="deterministic_cpu",
        status="completed",
        score=1.0,
        uncertainty=0.0,
        abstained=False,
        lineage_digest=canonical_sha256({"deterministic": 1}),
    )
    with pytest.raises(CorrelationArbitrationError, match="unique"):
        arbitrate_lane_results([deterministic, deterministic])


def test_deterministic_failure_and_policy_veto_force_abstention() -> None:
    selected = profile(maximum_contradictions=0)
    baseline = run_generated_batch([event(1, 1), event(2, 20)], selected)
    missing_input = evaluate_deterministic_lane(
        baseline.windows[0],
        [],
        selected,
    )
    unavailable = arbitrate_lane_results([missing_input])
    assert missing_input.status == "failed"
    assert unavailable.state == "abstained"
    assert unavailable.reason_codes == ["deterministic_lane_unavailable"]

    vetoed = run_generated_batch(
        [
            event(1, 1),
            event(2, 2, signal_kind="contradiction"),
            event(3, 20),
        ],
        selected,
    )
    assert vetoed.hypotheses[0].state == "abstained"
    assert vetoed.hypotheses[0].abstention_reason == "deterministic_policy_veto"


def test_exact_replay_is_stable_and_binds_order_profile_clock_and_windows() -> None:
    events = [event(1, 1), event(2, 2), event(3, 20)]
    selected = profile()
    first = run_generated_batch(events, selected)
    replay = run_generated_batch(events, selected)
    assert replay.model_dump(mode="json") == first.model_dump(mode="json")
    assert replay.result_digest == first.result_digest
    assert replay.run_id == first.run_id

    reordered = run_generated_batch([events[1], events[0], events[2]], selected)
    changed_window = run_generated_batch(events, profile(window_seconds=11))
    changed_clock = run_generated_batch(
        [event(1, 1), event(2, 3), event(3, 20)],
        selected,
    )
    changed_profile = run_generated_batch(
        events,
        profile(profile_version=canonical_sha256({"profile": "revision-2"})),
    )
    assert {
        reordered.run_id,
        changed_window.run_id,
        changed_clock.run_id,
        changed_profile.run_id,
    }.isdisjoint({first.run_id})
    assert changed_window.replay_binding.window_semantics_version.endswith(".v1")
