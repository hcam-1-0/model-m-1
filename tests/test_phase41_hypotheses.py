from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.contracts import CorrelationIngressEventV1, CorrelationProfileV1
from hcam.intelligence.correlation.hypotheses import revise_hypothesis_state
from hcam.intelligence.correlation.runtime import run_generated_batch


BASE = datetime(2026, 1, 1, tzinfo=UTC)


def profile() -> CorrelationProfileV1:
    return CorrelationProfileV1(
        profile_id="hypothesis-profile",
        profile_version=canonical_sha256({"profile": "hypothesis"}),
        allowed_event_types=["hcam.analytics.event.created.v1"],
        subject_kind="event_group",
        partition_dimensions=["generated_reference"],
        window_seconds=10,
        allowed_lateness_seconds=1,
        minimum_supporting_events=1,
        maximum_contradictions=1,
        maximum_events_per_window=100,
        maximum_active_windows=8,
    )


def event(identifier: str, seconds: int, signal_kind: str) -> CorrelationIngressEventV1:
    instant = BASE + timedelta(seconds=seconds)
    return CorrelationIngressEventV1(
        event_id=identifier,
        event_type="hcam.analytics.event.created.v1",
        schema_version=1,
        department="generated-lab",
        stream_id="str_" + "4" * 32,
        camera_id="cam-4",
        profile_id="hypothesis-profile",
        subject_kind="event_group",
        signals={
            "object_class": "generated-event",
            "signal_kind": signal_kind,
            "confidence": 0.7,
            "generated_reference": "group-a",
        },
        chronology={
            "occurred_at": instant,
            "observed_at": instant,
            "received_at": instant,
            "recorded_at": instant,
        },
    )


def test_hypothesis_graph_is_canonical_and_projection_is_rebuildable() -> None:
    long_id = "event-" + "x" * 130
    result = run_generated_batch(
        [
            event(long_id, 1, "observation"),
            event("event-contradiction", 2, "contradiction"),
            event("event-missing", 3, "absence"),
            event("event-stale", 4, "stale"),
            event("event-next-window", 20, "observation"),
        ],
        profile(),
    )
    hypothesis = result.hypotheses[0]
    roles = {item.role for item in hypothesis.evidence}
    assert roles == {"supports", "contradicts", "missing", "stale"}
    assert canonical_sha256(hypothesis.graph) == hypothesis.graph_digest
    assert hypothesis.flat_projection.graph_digest == hypothesis.graph_digest
    assert hypothesis.flat_projection.event_count == 4
    assert all(node.reference_id for node in hypothesis.graph.nodes)


def test_correction_and_retraction_roles_remain_explicit() -> None:
    result = run_generated_batch(
        [
            event("event-support", 1, "observation"),
            event("event-correction", 2, "correction"),
            event("event-retraction", 3, "retraction"),
            event("event-next-window", 20, "observation"),
        ],
        profile(),
    )
    assert [item.role for item in result.hypotheses[0].evidence] == [
        "supports",
        "supersedes",
        "retracts",
    ]


def test_state_revisions_append_graph_provenance_without_rewriting_evidence() -> None:
    result = run_generated_batch(
        [event("event-support", 1, "observation"), event("event-next", 20, "observation")],
        profile(),
    )
    original = result.hypotheses[0]
    revised, revision = revise_hypothesis_state(
        original,
        new_state="corrected",
        reason_code="generated_correction",
        recorded_at=BASE + timedelta(seconds=30),
    )
    assert revised.revision == 2
    assert revised.state == "corrected"
    assert revised.evidence == original.evidence
    assert len(revised.graph.nodes) == len(original.graph.nodes) + 1
    assert revised.graph_digest != original.graph_digest
    assert revision.previous_state == original.state
    assert revision.new_state == "corrected"


@pytest.mark.parametrize(
    ("new_state", "expected_role"),
    [
        ("expired", "stale"),
        ("superseded", "supersedes"),
        ("corrected", "supersedes"),
        ("retracted", "retracts"),
    ],
)
def test_every_planned_revision_transition_is_explicit(
    new_state: str,
    expected_role: str,
) -> None:
    result = run_generated_batch(
        [event("event-support", 1, "observation"), event("event-next", 20, "observation")],
        profile(),
    )
    revised, revision = revise_hypothesis_state(
        result.hypotheses[0],
        new_state=new_state,
        reason_code=f"generated_{new_state}",
        recorded_at=BASE + timedelta(seconds=30),
    )
    assert revised.state == revision.new_state == new_state
    assert revised.graph.edges[-1].role == expected_role


def test_state_revisions_reject_invalid_or_backdated_transitions() -> None:
    result = run_generated_batch(
        [event("event-support", 1, "observation"), event("event-next", 20, "observation")],
        profile(),
    )
    original = result.hypotheses[0]
    with pytest.raises(ValueError, match="not allowed"):
        revise_hypothesis_state(
            original,
            new_state="proposed",
            reason_code="generated_invalid",
            recorded_at=BASE + timedelta(seconds=30),
        )
    with pytest.raises(ValueError, match="cannot precede"):
        revise_hypothesis_state(
            original,
            new_state="expired",
            reason_code="generated_expiry",
            recorded_at=BASE,
        )
