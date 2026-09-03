from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from hcam.analytics.activation import (
    P3_3_APPROVAL_RECORD_ID,
    P3_3_CAPABILITY,
    P3_3_CONFIGURATION_VERSION,
    P3_3_PIPELINE_ID,
    P3_3_PIPELINE_VERSION,
    P3_3_POLICY_VERSION,
    P3_3_TAXONOMY_VERSION,
    P3_3_TRACKER_ID,
    P3_3_TRACKER_VERSION,
)
from hcam.analytics.contracts import TrackLifecycleV2, parse_analytics_event
from hcam.analytics.models import (
    AnalyticsTrackerEpoch,
    AnalyticsTrack,
    AnalyticsTrackLifecycle,
    AnalyticsTrackingRun,
)
from hcam.analytics.tracking import (
    GeneratedTrackingLaneStore,
    StreamLocalTracker,
    TrackerConfiguration,
    build_generated_tracking_scenario,
    evaluate_tracking_sequence,
)
from hcam.analytics.tracking.types import TrackingResourceError
from hcam.analytics.tracking_execution import purge_expired_generated_tracking
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


OBSERVED_AT = "2026-08-25T12:00:00Z"


def _assignment_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "capability": P3_3_CAPABILITY,
        "desired_state": "paused",
        "pipeline": {
            "id": P3_3_PIPELINE_ID,
            "version": P3_3_PIPELINE_VERSION,
        },
        "models": [{"id": P3_3_TRACKER_ID, "version": P3_3_TRACKER_VERSION}],
        "taxonomy_version": P3_3_TAXONOMY_VERSION,
        "policy_version": P3_3_POLICY_VERSION,
        "configuration_digest": P3_3_CONFIGURATION_VERSION,
        "minimum_confidence": 0.25,
        "sampling_fps": 1.0,
        "maximum_queue_age_ms": 1_000,
        "geometry_refs": [],
        "retention_class": "derived.analytics.standard",
        "approval_record_id": P3_3_APPROVAL_RECORD_ID,
    }
    payload.update(overrides)
    return payload


def _create_and_activate(app, headers: dict[str, str]) -> str:
    app.state.settings = replace(
        app.state.settings,
        analytics_generated_tracking_enabled=True,
    )
    with app.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=1)
    with TestClient(app) as client:
        created = client.post(
            f"/streams/{synthetic_stream_id(1)}/analytics-assignments",
            json=_assignment_payload(),
            headers={
                **headers,
                "X-HCAM-Reason": "Register approved generated tracking assignment",
            },
        )
        assert created.status_code == 201
        assert created.json()["activation_eligible"] is True
        assignment_id = created.json()["assignment_id"]
        activated = client.post(
            f"/analytics-assignments/{assignment_id}/activate",
            headers={
                **headers,
                "If-Match": created.headers["ETag"],
                "X-HCAM-Reason": "Activate generated-only stream-local tracker",
            },
        )
    assert activated.status_code == 200
    assert activated.json()["lifecycle_state"] == "running"
    return assignment_id


def _event_document(event: StreamEventOutbox) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "schema_version": event.schema_version,
        "stream_id": event.stream_id,
        "camera_id": event.camera_id,
        "partition_key": event.stream_id,
        "occurred_at": event.occurred_at.isoformat(),
        "payload": event.payload,
    }


def test_generated_tracking_run_is_deterministic_scoped_and_idempotent(
    app,
    editor_headers: dict[str, str],
) -> None:
    assignment_id = _create_and_activate(app, editor_headers)
    request = {
        "scenario_id": "all-tier-a",
        "seed": 7,
        "observed_at": OBSERVED_AT,
    }
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Execute deterministic generated tracking suite",
    }
    with TestClient(app) as client:
        created = client.post(
            f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
            json=request,
            headers=headers,
        )
        replay = client.post(
            f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
            json=request,
            headers=headers,
        )
        run_id = created.json()["run_id"]
        fetched = client.get(
            f"/analytics-tracking-runs/{run_id}", headers=editor_headers
        )
        epochs = client.get(
            f"/analytics-tracking-runs/{run_id}/epochs", headers=editor_headers
        )
        tracks = client.get(
            f"/analytics-tracking-runs/{run_id}/tracks", headers=editor_headers
        )
        lifecycle = client.get(
            f"/analytics-tracking-runs/{run_id}/lifecycle",
            headers=editor_headers,
        )

    assert created.status_code == 201
    assert created.headers["location"] == f"/analytics-tracking-runs/{run_id}"
    assert created.json()["status"] == "succeeded"
    assert created.json()["metrics"]["hota"] == pytest.approx(1.0)
    assert created.json()["metrics"]["idf1"] == pytest.approx(1.0)
    assert replay.status_code == 201
    assert replay.json()["run_id"] == run_id
    assert replay.json()["reused"] is True
    assert fetched.status_code == 200
    assert epochs.status_code == 200
    assert epochs.json()["total"] == 1
    assert epochs.json()["items"][0]["end_reason"] == "explicit_reset"
    assert tracks.status_code == 200
    assert tracks.json()["total"] == 7
    assert {item["class_id"] for item in tracks.json()["items"]} == {
        "object.person",
        "vehicle.bicycle",
        "vehicle.car",
        "vehicle.motorcycle",
        "vehicle.bus",
        "vehicle.truck",
        "object.unknown",
    }
    assert all(item["state"] == "ended" for item in tracks.json()["items"])
    assert lifecycle.status_code == 200
    assert lifecycle.json()["total"] == created.json()["transition_count"]
    assert all("identity" not in str(item).lower() for item in lifecycle.json()["items"])

    with app.state.database.session_factory() as session:
        assert session.scalar(
            select(func.count()).select_from(AnalyticsTrackingRun)
        ) == 1
        events = session.scalars(
            select(StreamEventOutbox).where(
                StreamEventOutbox.event_type
                == "hcam.analytics.track.lifecycle.v2"
            )
        ).all()
    assert len(events) == created.json()["transition_count"]
    parsed = parse_analytics_event(_event_document(events[0]))
    assert isinstance(parsed, TrackLifecycleV2)
    assert parsed.payload.stream_id == synthetic_stream_id(1)


def test_discontinuity_creates_separate_epochs_and_never_reuses_tracks(
    app,
    editor_headers: dict[str, str],
) -> None:
    assignment_id = _create_and_activate(app, editor_headers)
    with TestClient(app) as client:
        created = client.post(
            f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
            json={
                "scenario_id": "discontinuity",
                "seed": 1,
                "observed_at": OBSERVED_AT,
            },
            headers={
                **editor_headers,
                "X-HCAM-Reason": "Verify generated tracker reset isolation",
            },
        )
        run_id = created.json()["run_id"]
        epochs = client.get(
            f"/analytics-tracking-runs/{run_id}/epochs", headers=editor_headers
        ).json()["items"]
        tracks = client.get(
            f"/analytics-tracking-runs/{run_id}/tracks", headers=editor_headers
        ).json()["items"]

    assert created.status_code == 201
    assert len(epochs) == 2
    assert [item["end_reason"] for item in epochs] == [
        "explicit_reset",
        "explicit_reset",
    ]
    assert len({item["epoch_id"] for item in tracks}) == 2
    assert len({item["track_id"] for item in tracks}) == len(tracks)


def test_overload_fails_closed_and_department_scope_hides_run(
    app,
    editor_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    assignment_id = _create_and_activate(app, editor_headers)
    request = {
        "scenario_id": "overload",
        "seed": 2,
        "observed_at": OBSERVED_AT,
    }
    with TestClient(app) as client:
        viewer_attempt = client.post(
            f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
            json=request,
            headers={
                **viewer_headers,
                "X-HCAM-Reason": "Viewer cannot execute generated tracker",
            },
        )
        created = client.post(
            f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
            json=request,
            headers={
                **editor_headers,
                "X-HCAM-Reason": "Verify generated tracker overload boundary",
            },
        )
        replay = client.post(
            f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
            json=request,
            headers={
                **editor_headers,
                "X-HCAM-Reason": "Replay generated tracker overload boundary",
            },
        )
        hidden = client.get(
            f"/analytics-tracking-runs/{created.json()['run_id']}",
            headers={
                **viewer_headers,
                "X-HCAM-Departments": "Traffic",
            },
        )

    assert viewer_attempt.status_code == 403
    assert created.status_code == 201
    assert created.json()["status"] == "failed"
    assert created.json()["failure_code"] == "resource_exhausted"
    assert created.json()["transition_count"] == 0
    assert replay.status_code == 201
    assert replay.json()["run_id"] == created.json()["run_id"]
    assert replay.json()["reused"] is True
    assert hidden.status_code == 404


def test_tracking_retention_deletes_lifecycle_and_outbox(
    app,
    editor_headers: dict[str, str],
) -> None:
    assignment_id = _create_and_activate(app, editor_headers)
    with TestClient(app) as client:
        created = client.post(
            f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
            json={
                "scenario_id": "single-object",
                "seed": 3,
                "observed_at": OBSERVED_AT,
            },
            headers={
                **editor_headers,
                "X-HCAM-Reason": "Create generated tracking retention fixture",
            },
        )
    run_id = created.json()["run_id"]
    with app.state.database.session_factory() as session:
        run = session.get(AnalyticsTrackingRun, run_id)
        assert run is not None
        run.completed_at = datetime.now(UTC) - timedelta(hours=169)
        session.commit()
        with session.begin():
            deleted = purge_expired_generated_tracking(
                session,
                now=datetime.now(UTC),
            )
        assert deleted == 1
        assert session.scalar(
            select(func.count()).select_from(AnalyticsTrackingRun)
        ) == 0
        assert session.scalar(
            select(func.count()).select_from(AnalyticsTrackerEpoch)
        ) == 0
        assert session.scalar(select(func.count()).select_from(AnalyticsTrack)) == 0
        assert session.scalar(
            select(func.count()).select_from(AnalyticsTrackLifecycle)
        ) == 0
        assert session.scalar(
            select(func.count())
            .select_from(StreamEventOutbox)
            .where(
                StreamEventOutbox.event_type
                == "hcam.analytics.track.lifecycle.v2"
            )
        ) == 0


def test_generated_component_suite_is_deterministic_and_bounded() -> None:
    observed_at = datetime(2026, 8, 25, 12, tzinfo=UTC)
    scenario = build_generated_tracking_scenario("two-crossing", 5, observed_at)

    def execute():
        tracker = StreamLocalTracker(
            department="Engineering Lab",
            assignment_id="ana_" + "1" * 32,
            camera_id="synthetic:cctv-001",
            stream_id="str_" + "2" * 32,
            configuration=TrackerConfiguration(),
            execution_id="component-determinism",
        )
        return tuple(tracker.update(item.frame) for item in scenario.frames)

    first = execute()
    second = execute()
    assert first == second
    metric = evaluate_tracking_sequence(scenario, first)
    assert metric.hota >= 0.85
    assert metric.idf1 >= 0.90
    assert metric.identity_switches == 0

    overloaded = build_generated_tracking_scenario("overload", 5, observed_at)
    tracker = StreamLocalTracker(
        department="Engineering Lab",
        assignment_id="ana_" + "1" * 32,
        camera_id="synthetic:cctv-001",
        stream_id="str_" + "2" * 32,
        configuration=TrackerConfiguration(),
    )
    with pytest.raises(TrackingResourceError):
        tracker.update(overloaded.frames[0].frame)


def test_generated_tracking_lanes_serialize_and_timeout_closed() -> None:
    lanes = GeneratedTrackingLaneStore(
        maximum_active_lanes=1,
        maximum_queued_per_stream=1,
        maximum_queue_age_ms=20,
    )
    with lanes.lease("str_" + "1" * 32):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                lambda: _acquire_tracking_lane(lanes, "str_" + "1" * 32)
            )
            with pytest.raises(TrackingResourceError):
                future.result(timeout=1)
        assert lanes.active_lanes == 1
    assert lanes.active_lanes == 0
    assert lanes.queued_batches == 0


def _acquire_tracking_lane(
    lanes: GeneratedTrackingLaneStore,
    stream_id: str,
) -> None:
    with lanes.lease(stream_id):
        pass
