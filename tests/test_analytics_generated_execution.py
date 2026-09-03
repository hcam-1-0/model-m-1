from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from hcam.analytics.activation import (
    P3_2_APPROVAL_RECORD_ID,
    P3_2_MODEL_ID,
    P3_2_MODEL_VERSION,
    P3_2_PIPELINE_ID,
    P3_2_PIPELINE_VERSION,
    P3_2_POLICY_VERSION,
    P3_2_TAXONOMY_VERSION,
)
from hcam.analytics.contracts import NormalizedBoundingBox, ObservationCreatedV1
from hcam.analytics.execution import purge_expired_generated_analytics
from hcam.analytics.generated import GeneratedFrameLeaseStore
from hcam.analytics.models import (
    AnalyticsGeneratedRun,
    AnalyticsObservation,
)
from hcam.analytics.runtime import (
    GuardedAnalyticsRuntimeAdapter,
    RuntimeAdapterDescriptorV1,
    RuntimeBatchResultV1,
    RuntimeObservationCandidateV1,
)
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


CONFIGURATION_DIGEST = "sha256:" + "d" * 64
OBSERVED_AT = "2026-08-24T12:00:00Z"


class SyntheticResultAdapter:
    def __init__(self, *, failure_code: str | None = None) -> None:
        self.failure_code = failure_code
        self.descriptor = RuntimeAdapterDescriptorV1(
            adapter_id="hcam.yolox_tiny.onnxruntime_cpu",
            adapter_version=P3_2_MODEL_VERSION,
            supported_capabilities=["object_detection"],
            maximum_batch_size=1,
            configured=True,
        )

    def infer(self, request):
        if self.failure_code is not None:
            return RuntimeBatchResultV1(
                request_id=request.request_id,
                status="failed",
                failure_code=self.failure_code,
            )
        return RuntimeBatchResultV1(
            request_id=request.request_id,
            status="succeeded",
            candidates=[
                RuntimeObservationCandidateV1(
                    input_id=request.inputs[0].input_id,
                    class_id="vehicle.car",
                    confidence=0.91,
                    bbox=NormalizedBoundingBox(
                        x=0.1,
                        y=0.2,
                        width=0.3,
                        height=0.4,
                    ),
                )
            ],
        )


def _configure_runtime(app, *, failure_code: str | None = None) -> None:
    app.state.analytics_runtime = GuardedAnalyticsRuntimeAdapter(
        SyntheticResultAdapter(failure_code=failure_code)
    )
    app.state.analytics_frame_leases = GeneratedFrameLeaseStore()


def _payload() -> dict[str, object]:
    return {
        "capability": "object_detection",
        "desired_state": "paused",
        "pipeline": {"id": P3_2_PIPELINE_ID, "version": P3_2_PIPELINE_VERSION},
        "models": [{"id": P3_2_MODEL_ID, "version": P3_2_MODEL_VERSION}],
        "taxonomy_version": P3_2_TAXONOMY_VERSION,
        "policy_version": P3_2_POLICY_VERSION,
        "configuration_digest": CONFIGURATION_DIGEST,
        "minimum_confidence": 0.25,
        "sampling_fps": 1.0,
        "maximum_queue_age_ms": 1_000,
        "geometry_refs": [],
        "retention_class": "derived.analytics.standard",
        "approval_record_id": P3_2_APPROVAL_RECORD_ID,
    }


def _create_and_activate(app, editor_headers: dict[str, str]) -> tuple[str, str]:
    with app.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=1)
    stream_id = synthetic_stream_id(1)
    with TestClient(app) as client:
        created = client.post(
            f"/streams/{stream_id}/analytics-assignments",
            json=_payload(),
            headers={
                **editor_headers,
                "X-HCAM-Reason": "Register approved generated detector assignment",
            },
        )
        assert created.status_code == 201
        assert created.json()["activation_eligible"] is True
        assignment_id = created.json()["assignment_id"]
        activated = client.post(
            f"/analytics-assignments/{assignment_id}/activate",
            headers={
                **editor_headers,
                "If-Match": created.headers["ETag"],
                "X-HCAM-Reason": "Activate approved generated-only detector",
            },
        )
    assert activated.status_code == 200
    assert activated.json()["lifecycle_state"] == "running"
    return assignment_id, activated.headers["ETag"]


def test_generated_run_is_deterministic_metadata_only_and_idempotent(
    app,
    editor_headers: dict[str, str],
) -> None:
    _configure_runtime(app)
    assignment_id, assignment_etag = _create_and_activate(app, editor_headers)
    request_payload = {"seed": 0, "sequence": 17, "observed_at": OBSERVED_AT}
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Execute deterministic generated-frame detector test",
    }
    with TestClient(app) as client:
        first = client.post(
            f"/analytics-assignments/{assignment_id}/generated-runs",
            json=request_payload,
            headers=headers,
        )
        replay = client.post(
            f"/analytics-assignments/{assignment_id}/generated-runs",
            json=request_payload,
            headers=headers,
        )
        run_id = first.json()["run_id"]
        fetched = client.get(
            f"/analytics-generated-runs/{run_id}",
            headers=editor_headers,
        )
        observations = client.get(
            f"/analytics-generated-runs/{run_id}/observations",
            headers=editor_headers,
        )
        paused = client.post(
            f"/analytics-assignments/{assignment_id}/pause",
            headers={
                **editor_headers,
                "If-Match": assignment_etag,
                "X-HCAM-Reason": "Pause generated detector after deterministic test",
            },
        )
        blocked_run = client.post(
            f"/analytics-assignments/{assignment_id}/generated-runs",
            json={"seed": 1, "sequence": 18, "observed_at": OBSERVED_AT},
            headers=headers,
        )

    assert first.status_code == 201
    assert first.headers["location"] == f"/analytics-generated-runs/{run_id}"
    assert first.json()["status"] == "succeeded"
    assert first.json()["candidate_count"] == 1
    assert first.json()["reused"] is False
    assert replay.status_code == 201
    assert replay.json()["run_id"] == run_id
    assert replay.json()["reused"] is True
    assert fetched.status_code == 200
    assert observations.status_code == 200
    assert observations.json()["total"] == 1
    assert observations.json()["items"][0]["class_id"] == "vehicle.car"
    assert paused.status_code == 200
    assert paused.json()["lifecycle_state"] == "paused"
    assert blocked_run.status_code == 409
    assert app.state.analytics_frame_leases.active_leases == 0

    with app.state.database.session_factory() as session:
        assert (
            session.scalar(select(func.count()).select_from(AnalyticsGeneratedRun)) == 1
        )
        assert (
            session.scalar(select(func.count()).select_from(AnalyticsObservation)) == 1
        )
        events = session.scalars(
            select(StreamEventOutbox).where(
                StreamEventOutbox.event_type == "hcam.analytics.observation.created.v1"
            )
        ).all()
    assert len(events) == 1
    event = ObservationCreatedV1.model_validate(
        {
            "event_id": events[0].event_id,
            "event_type": events[0].event_type,
            "schema_version": events[0].schema_version,
            "stream_id": events[0].stream_id,
            "camera_id": events[0].camera_id,
            "partition_key": events[0].stream_id,
            "occurred_at": events[0].occurred_at,
            "payload": events[0].payload,
        }
    )
    assert event.payload.classification.id == "vehicle.car"
    serialized = str(events[0].payload).lower()
    assert "pixels" not in serialized
    assert "locator" not in serialized
    assert "path" not in serialized


def test_generated_failure_degrades_and_success_recovers(
    app,
    editor_headers: dict[str, str],
) -> None:
    _configure_runtime(app, failure_code="deadline_exceeded")
    assignment_id, _ = _create_and_activate(app, editor_headers)
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Validate generated detector failure controls",
    }
    with TestClient(app) as client:
        failed = client.post(
            f"/analytics-assignments/{assignment_id}/generated-runs",
            json={"seed": 2, "sequence": 20, "observed_at": OBSERVED_AT},
            headers=headers,
        )
        degraded = client.get(
            f"/analytics-assignments/{assignment_id}",
            headers=editor_headers,
        )
        _configure_runtime(app)
        recovered = client.post(
            f"/analytics-assignments/{assignment_id}/generated-runs",
            json={"seed": 3, "sequence": 21, "observed_at": OBSERVED_AT},
            headers=headers,
        )
        running = client.get(
            f"/analytics-assignments/{assignment_id}",
            headers=editor_headers,
        )

    assert failed.status_code == 201
    assert failed.json()["status"] == "failed"
    assert failed.json()["failure_code"] == "deadline_exceeded"
    assert degraded.json()["lifecycle_state"] == "degraded"
    assert degraded.json()["reason_code"] == "runtime_degraded"
    assert recovered.status_code == 201
    assert recovered.json()["status"] == "succeeded"
    assert running.json()["lifecycle_state"] == "running"
    assert app.state.analytics_frame_leases.active_leases == 0


def test_generated_run_department_scope_and_retention(
    app,
    editor_headers: dict[str, str],
) -> None:
    _configure_runtime(app)
    assignment_id, _ = _create_and_activate(app, editor_headers)
    with TestClient(app) as client:
        created = client.post(
            f"/analytics-assignments/{assignment_id}/generated-runs",
            json={"seed": 4, "sequence": 30, "observed_at": OBSERVED_AT},
            headers={
                **editor_headers,
                "X-HCAM-Reason": "Create metadata for retention validation",
            },
        )
        hidden = client.get(
            f"/analytics-generated-runs/{created.json()['run_id']}",
            headers={
                **editor_headers,
                "X-HCAM-Departments": "Traffic",
            },
        )
    assert hidden.status_code == 404

    with app.state.database.session_factory() as session:
        run = session.get(AnalyticsGeneratedRun, created.json()["run_id"])
        assert run is not None
        run.completed_at = datetime.now(UTC) - timedelta(hours=169)
        session.commit()
        with session.begin():
            deleted = purge_expired_generated_analytics(
                session,
                now=datetime.now(UTC),
            )
        remaining_runs = session.scalar(
            select(func.count()).select_from(AnalyticsGeneratedRun)
        )
        remaining_observations = session.scalar(
            select(func.count()).select_from(AnalyticsObservation)
        )
        remaining_observation_events = session.scalar(
            select(func.count())
            .select_from(StreamEventOutbox)
            .where(
                StreamEventOutbox.event_type == "hcam.analytics.observation.created.v1"
            )
        )
    assert deleted == 1
    assert remaining_runs == 0
    assert remaining_observations == 0
    assert remaining_observation_events == 0


def test_unapproved_assignment_cannot_activate(
    app,
    editor_headers: dict[str, str],
) -> None:
    _configure_runtime(app)
    with app.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=1)
    payload = _payload()
    payload["pipeline"] = {
        "id": "unapproved-pipeline",
        "version": P3_2_PIPELINE_VERSION,
    }
    with TestClient(app) as client:
        created = client.post(
            f"/streams/{synthetic_stream_id(1)}/analytics-assignments",
            json=payload,
            headers={
                **editor_headers,
                "X-HCAM-Reason": "Register deliberately unapproved test assignment",
            },
        )
        activated = client.post(
            f"/analytics-assignments/{created.json()['assignment_id']}/activate",
            headers={
                **editor_headers,
                "If-Match": created.headers["ETag"],
                "X-HCAM-Reason": "Verify unapproved pipeline remains blocked",
            },
        )
    assert created.status_code == 201
    assert created.json()["activation_eligible"] is False
    assert created.json()["blocking_reasons"] == ["implementation_scope_unapproved"]
    assert activated.status_code == 422
