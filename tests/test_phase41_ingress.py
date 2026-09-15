from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hcam.analytics.fixtures import golden_contract_fixtures
from hcam.intelligence.canonical import canonical_sha256
from hcam.intelligence.correlation.contracts import (
    CorrelationIngressEventV1,
    CorrelationProfileV1,
)
from hcam.intelligence.correlation.ingress import (
    CorrelationIngressError,
    classify_ingress,
    event_digest,
    partition_digest,
    project_stream_event_outbox,
)


BASE = datetime(2026, 1, 1, tzinfo=UTC)


def profile(**updates: object) -> CorrelationProfileV1:
    values: dict[str, object] = {
        "profile_id": "generated-vehicle-path",
        "profile_version": canonical_sha256({"profile": 1}),
        "allowed_event_types": ["hcam.analytics.observation.created.v1"],
        "subject_kind": "vehicle",
        "partition_dimensions": ["generated_reference"],
        "maximum_events_per_window": 100,
        "maximum_active_windows": 8,
    }
    values.update(updates)
    return CorrelationProfileV1(**values)


def event(identifier: str = "event-1", **updates: object) -> CorrelationIngressEventV1:
    values: dict[str, object] = {
        "event_id": identifier,
        "event_type": "hcam.analytics.observation.created.v1",
        "schema_version": 1,
        "department": "generated-lab",
        "stream_id": "str_" + "1" * 32,
        "camera_id": "cam-1",
        "profile_id": "generated-vehicle-path",
        "subject_kind": "vehicle",
        "signals": {
            "object_class": "car",
            "confidence": 0.9,
            "generated_reference": "vehicle-a",
            "source_sequence": 1,
        },
        "chronology": {
            "occurred_at": BASE,
            "observed_at": BASE,
            "received_at": BASE,
            "recorded_at": BASE,
        },
    }
    values.update(updates)
    return CorrelationIngressEventV1(**values)


def classify(item: CorrelationIngressEventV1, selected: CorrelationProfileV1, seen=None):
    return classify_ingress(item, selected, seen or {}, receipt_sequence=0)


def test_ingress_accepts_and_derives_stable_partition() -> None:
    item = event()
    receipt = classify(item, profile())
    assert receipt.disposition == "accepted"
    assert receipt.partition_digest == partition_digest(item, profile())
    assert receipt.event_digest == event_digest(item)


def test_ingress_distinguishes_duplicate_from_conflict() -> None:
    item = event()
    digest = event_digest(item)
    duplicate = classify(item, profile(), {item.event_id: digest})
    changed = item.model_copy(
        update={"signals": item.signals.model_copy(update={"confidence": 0.5})}
    )
    conflict = classify(changed, profile(), {item.event_id: digest})
    assert duplicate.disposition == "duplicate"
    assert conflict.disposition == "conflict"
    assert duplicate.partition_digest is None and conflict.partition_digest is None


def test_ingress_rejects_profile_type_subject_future_and_missing_partition() -> None:
    selected = profile()
    assert classify(event(profile_id="other"), selected).reason_code == "profile_mismatch"
    assert (
        classify(
            event(event_type="hcam.analytics.track.updated.v1"), selected
        ).reason_code
        == "event_type_not_allowed"
    )
    assert classify(event(subject_kind="object"), selected).reason_code == "subject_kind_mismatch"


def test_future_skew_and_partition_requirements_fail_closed() -> None:
    future_time = BASE + timedelta(seconds=10)
    future = event(
        chronology={
            "occurred_at": future_time,
            "observed_at": future_time,
            "received_at": future_time,
            "recorded_at": future_time,
        }
    )
    strict = profile(future_clock_skew_seconds=0)
    receipt = classify_ingress(
        future,
        strict,
        {},
        receipt_sequence=0,
        processing_time=BASE,
    )
    assert receipt.reason_code == "future_clock_skew"
    missing = event(
        signals={"object_class": "car", "confidence": 0.9}
    )
    assert classify(missing, profile()).reason_code == "partition_key_incomplete"


def test_every_declared_partition_dimension_is_supported() -> None:
    selected = profile(
        partition_dimensions=[
            "camera",
            "stream",
            "object_class",
            "direction",
            "location_relation",
            "track_local",
            "generated_reference",
        ]
    )
    item = event(
        signals={
            "object_class": "car",
            "confidence": 0.9,
            "direction": "north",
            "location_relation": "inside-zone-a",
            "local_track_id": "track-1",
            "tracker_epoch": "epoch-1",
            "generated_reference": "vehicle-a",
        }
    )
    assert classify(item, selected).accepted


def _project_phase3(name: str, **updates: object) -> CorrelationIngressEventV1:
    source = golden_contract_fixtures()[name]
    values: dict[str, object] = {
        "event_id": source.event_id,
        "event_type": source.event_type,
        "schema_version": source.schema_version,
        "stream_id": source.stream_id,
        "camera_id": source.camera_id,
        "occurred_at": source.occurred_at,
        "payload": source.payload.model_dump(mode="json", by_alias=True),
        "resolved_stream_id": source.stream_id,
        "resolved_camera_id": source.camera_id,
        "resolved_department": "phase3-lab",
        "profile_id": "generated-phase3-adapter",
        "source_generated_only": True,
    }
    values.update(updates)
    return project_stream_event_outbox(**values)  # type: ignore[arg-type]


def test_read_only_outbox_projection_is_closed_and_scope_bound() -> None:
    observation = _project_phase3("observation-created-v1.json")
    lifecycle = _project_phase3("track-lifecycle-v2.json")
    assert observation.subject_kind == "vehicle"
    assert observation.signals.object_class == "vehicle.car"
    assert observation.signals.source_sequence == 1
    assert lifecycle.signals.local_track_id is not None
    assert lifecycle.signals.tracker_epoch is not None
    assert lifecycle.signals.source_sequence == 10
    assert observation.department == lifecycle.department == "phase3-lab"


@pytest.mark.parametrize(
    ("updates", "reason"),
    [
        ({"source_generated_only": False}, "only generated"),
        ({"resolved_department": None}, "department is not resolved"),
        ({"resolved_camera_id": "another-camera"}, "resolved camera stream"),
        ({"schema_version": 9}, "not supported"),
    ],
)
def test_outbox_projection_fails_closed(updates: dict[str, object], reason: str) -> None:
    with pytest.raises(CorrelationIngressError, match=reason):
        _project_phase3("observation-created-v1.json", **updates)


def test_outbox_projection_rejects_unknown_or_oversized_payloads() -> None:
    source = golden_contract_fixtures()["observation-created-v1.json"]
    payload = source.payload.model_dump(mode="json", by_alias=True)
    with pytest.raises(CorrelationIngressError, match="closed Phase 3 schema"):
        _project_phase3(
            "observation-created-v1.json",
            payload={**payload, "unexpected": True},
        )
    with pytest.raises(ValueError, match="size limit"):
        _project_phase3(
            "observation-created-v1.json",
            payload={**payload, "unexpected": "x" * 70_000},
        )


def test_spatial_outbox_projection_validates_embedded_department_and_scope() -> None:
    observation = golden_contract_fixtures()["observation-created-v1.json"]
    instant = observation.occurred_at
    stream_id = observation.stream_id
    camera_id = observation.camera_id
    event_id = "evt_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    payload = {
        "alert_state": "not_evaluated",
        "assignment_id": "asn_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "camera_id": camera_id,
        "confidence": 0.88,
        "count": None,
        "department": "phase3-lab",
        "direction": "east",
        "dwell_ms": None,
        "epoch_id": "epoch_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "event_id": event_id,
        "event_kind": "hcam.analytics.line.crossing.v1",
        "geometry": {
            "digest": canonical_sha256({"geometry": 1}),
            "id": "generated-line-a",
            "version": 1,
        },
        "lifecycle_id": "life_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "lineage": observation.payload.lineage.model_dump(mode="json"),
        "occurred_at": instant.isoformat(),
        "retention_class": "derived.analytics.standard",
        "rule": {
            "digest": canonical_sha256({"rule": 1}),
            "id": "generated-rule-a",
            "version": 1,
        },
        "source_sequence": 7,
        "state_cycle_id": "generated-cycle-a",
        "stream_id": stream_id,
        "track_id": "trk_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }
    projected = project_stream_event_outbox(
        event_id=event_id,
        event_type="hcam.analytics.line.crossing.v1",
        schema_version=1,
        stream_id=stream_id,
        camera_id=camera_id,
        occurred_at=instant,
        payload=payload,
        resolved_stream_id=stream_id,
        resolved_camera_id=camera_id,
        resolved_department="phase3-lab",
        profile_id="generated-spatial-profile",
        source_generated_only=True,
    )
    assert projected.subject_kind == "event_group"
    assert projected.signals.location_relation == "generated-line-a"
    assert projected.signals.direction == "east"
    with pytest.raises(CorrelationIngressError, match="crosses department"):
        project_stream_event_outbox(
            event_id=event_id,
            event_type="hcam.analytics.line.crossing.v1",
            schema_version=1,
            stream_id=stream_id,
            camera_id=camera_id,
            occurred_at=instant,
            payload={**payload, "department": "another-department"},
            resolved_stream_id=stream_id,
            resolved_camera_id=camera_id,
            resolved_department="phase3-lab",
            profile_id="generated-spatial-profile",
            source_generated_only=True,
        )
