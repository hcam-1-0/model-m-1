from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.bounds import CorrelationLimitError
from hcam.intelligence.correlation.contracts import CorrelationIngressEventV1, CorrelationProfileV1
from hcam.intelligence.correlation.ingress import classify_ingress
from hcam.intelligence.correlation.ordering import build_windows, classify_partition_order


BASE = datetime(2026, 1, 1, tzinfo=UTC)


def profile(**updates: object) -> CorrelationProfileV1:
    values: dict[str, object] = {
        "profile_id": "ordering-profile",
        "profile_version": canonical_sha256({"profile": "ordering"}),
        "allowed_event_types": ["hcam.analytics.observation.created.v1"],
        "subject_kind": "vehicle",
        "partition_dimensions": ["generated_reference"],
        "window_seconds": 10,
        "allowed_lateness_seconds": 5,
        "maximum_events_per_window": 20,
        "maximum_active_windows": 10,
    }
    values.update(updates)
    return CorrelationProfileV1(**values)


def event(identifier: int, seconds: int, sequence: int | None = None) -> CorrelationIngressEventV1:
    instant = BASE + timedelta(seconds=seconds)
    return CorrelationIngressEventV1(
        event_id=f"event-{identifier}",
        event_type="hcam.analytics.observation.created.v1",
        schema_version=1,
        department="generated-lab",
        stream_id="str_" + "2" * 32,
        camera_id="cam-2",
        profile_id="ordering-profile",
        subject_kind="vehicle",
        signals={
            "object_class": "car",
            "confidence": 0.8,
            "generated_reference": "vehicle-a",
            "source_sequence": sequence,
        },
        chronology={
            "occurred_at": instant,
            "observed_at": instant,
            "received_at": instant,
            "recorded_at": instant,
        },
    )


def receipts(events, selected):
    return [
        classify_ingress(item, selected, {}, receipt_sequence=index)
        for index, item in enumerate(events)
    ]


def test_event_time_ordering_reports_late_gap_and_watermark_rejection() -> None:
    selected = profile()
    events = [event(1, 20, 1), event(2, 18, 4), event(3, 10, 5)]
    ordered, checkpoints = classify_partition_order(events, receipts(events, selected), selected)
    assert [item.disposition for item in ordered] == [
        "accepted",
        "gap_accepted",
        "late_rejected",
    ]
    assert checkpoints[0].watermark_at == BASE + timedelta(seconds=15)


def test_tumbling_windows_are_deterministic_and_mark_completion() -> None:
    selected = profile()
    events = [event(1, 1), event(2, 2), event(3, 20)]
    ordered, checkpoints = classify_partition_order(events, receipts(events, selected), selected)
    windows, updated = build_windows(events, ordered, checkpoints, selected)
    assert [item.completeness for item in windows] == ["complete", "open"]
    assert windows[0].event_ids == ["event-1", "event-2"]
    assert updated[0].active_window_count == 2


def test_session_windows_split_on_configured_gap() -> None:
    selected = profile(window_kind="session", session_gap_seconds=3)
    events = [event(1, 1), event(2, 3), event(3, 9)]
    ordered, checkpoints = classify_partition_order(events, receipts(events, selected), selected)
    windows, _ = build_windows(events, ordered, checkpoints, selected)
    assert len(windows) == 2


def test_window_capacity_is_visible() -> None:
    selected = profile(maximum_active_windows=1)
    events = [event(1, 1), event(2, 20)]
    ordered, checkpoints = classify_partition_order(events, receipts(events, selected), selected)
    with pytest.raises(CorrelationLimitError, match="active window"):
        build_windows(events, ordered, checkpoints, selected)
