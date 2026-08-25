from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier, Lock, get_ident

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

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
from hcam.analytics.models import (
    AnalyticsAssignment,
    AnalyticsAssignmentRevision,
    AnalyticsTrackerEpoch,
    AnalyticsTrack,
    AnalyticsTrackLifecycle,
    AnalyticsTrackingRun,
)
from hcam.audit.models import AuditEvent
from hcam.camera_registry.importer import RegistryImporter
from hcam.camera_registry.models import Camera
from hcam.database import Database
from hcam.main import create_app
from hcam.security.auth import Principal
from hcam.settings import Settings
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.capabilities import CapabilityDiscoveryResult, CapabilityService
from hcam.streams.capability_worker import (
    CapabilityRefreshWorker,
    _prune_capability_history,
)
from hcam.streams.models import (
    StreamCapabilityRefresh,
    StreamCapabilitySnapshot,
    StreamEndpoint,
    StreamEventOutbox,
)


POSTGRES_TEST_URL = os.getenv("HCAM_POSTGRES_TEST_URL")
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not POSTGRES_TEST_URL,
        reason="HCAM_POSTGRES_TEST_URL is required for PostgreSQL integration",
    ),
]


def test_postgres_analytics_assignment_control_plane() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    now = datetime.now(UTC)
    camera_id = "synthetic:postgres-analytics"
    stream_id = "str_0000000000000000000000000000a301"
    digest_a = "sha256:" + "a" * 64
    digest_b = "sha256:" + "b" * 64
    digest_c = "sha256:" + "c" * 64
    digest_d = "sha256:" + "d" * 64
    try:
        database.check_ready()
        with database.session_factory.begin() as session:
            existing = session.get(Camera, camera_id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(
                Camera(
                    camera_id=camera_id,
                    source_id="postgres-analytics-test",
                    external_id="camera-analytics-01",
                    display_name="PostgreSQL Analytics Control Plane Test",
                    department="Engineering Lab",
                    source_schema="hcam.synthetic.test.v1",
                    provenance={"synthetic": True, "media_access": False},
                    imported_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
            session.add(
                StreamEndpoint(
                    stream_id=stream_id,
                    camera_id=camera_id,
                    name="analytics-control-plane",
                    adapter_kind="synthetic",
                    protocol="rtsp",
                    locator="rtsp://mediamtx:8554/hcam/postgres-analytics",
                    transport="tcp",
                    is_primary=True,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )

        application = create_app(
            Settings(
                database_url=POSTGRES_TEST_URL,
                dev_auth_enabled=True,
                environment="test",
                access_log_enabled=False,
            )
        )
        headers = {
            "X-HCAM-Actor": "postgres-analytics-editor",
            "X-HCAM-Roles": "camera.editor",
            "X-HCAM-Departments": "Engineering Lab",
            "X-HCAM-Reason": "PostgreSQL synthetic analytics control validation",
        }
        payload = {
            "capability": "object_detection",
            "desired_state": "paused",
            "pipeline": {"id": "hcam-object-pipeline", "version": digest_a},
            "models": [{"id": "yolo11n-detector", "version": digest_b}],
            "taxonomy_version": "hcam.object.v1",
            "policy_version": digest_c,
            "configuration_digest": digest_d,
            "minimum_confidence": 0.65,
            "sampling_fps": 5.0,
            "maximum_queue_age_ms": 2_000,
            "geometry_refs": [],
            "retention_class": "derived.analytics.standard",
            "approval_record_id": "DR-P3.0-001",
        }
        with TestClient(application) as client:
            created = client.post(
                f"/streams/{stream_id}/analytics-assignments",
                json=payload,
                headers=headers,
            )
            assignment_id = created.json()["assignment_id"]
            updated = client.patch(
                f"/analytics-assignments/{assignment_id}",
                json={
                    "minimum_confidence": 0.7,
                    "configuration_digest": digest_a,
                },
                headers={**headers, "If-Match": created.headers["ETag"]},
            )

        assert created.status_code == 201
        assert created.json()["activation_eligible"] is False
        assert updated.status_code == 200
        assert updated.headers["ETag"] == '"2"'
        assert updated.json()["desired_state"] == "paused"
        assert updated.json()["lifecycle_state"] == "blocked"

        with database.session_factory() as session:
            assignment = session.get(AnalyticsAssignment, assignment_id)
            revision_count = session.scalar(
                select(func.count())
                .select_from(AnalyticsAssignmentRevision)
                .where(AnalyticsAssignmentRevision.assignment_id == assignment_id)
            )
            outbox_count = session.scalar(
                select(func.count())
                .select_from(StreamEventOutbox)
                .where(
                    StreamEventOutbox.stream_id == stream_id,
                    StreamEventOutbox.event_type
                    == "hcam.analytics.model.deployment.changed.v1",
                )
            )
        assert assignment is not None
        assert assignment.version_id == 2
        assert assignment.lifecycle_state == "blocked"
        assert revision_count == 2
        assert outbox_count == 2
    finally:
        database.dispose()


def test_postgres_migrations_registry_and_audit_contracts(seed_file: Path) -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    try:
        database.check_ready()
        with database.session_factory() as session, session.begin():
            session.execute(delete(AuditEvent))
            session.execute(delete(Camera))
        import_result = RegistryImporter(database.session_factory).import_file(
            seed_file
        )
        assert import_result.created == 2

        application = create_app(
            Settings(
                database_url=POSTGRES_TEST_URL,
                dev_auth_enabled=True,
                environment="test",
                access_log_enabled=False,
            )
        )
        viewer_headers = {
            "X-HCAM-Actor": "postgres-viewer",
            "X-HCAM-Roles": "camera.viewer",
            "X-HCAM-Departments": "*",
        }
        editor_headers = {
            "X-HCAM-Actor": "postgres-editor",
            "X-HCAM-Roles": "camera.editor",
            "X-HCAM-Departments": "*",
            "X-HCAM-Reason": "PostgreSQL synthetic integration validation",
            "X-Request-ID": "postgres.integration:001",
        }
        payload = json.loads(seed_file.read_text(encoding="utf-8"))["cameras"][0]
        payload["camera_id"] = "synthetic:postgres-001"
        payload["external_id"] = "postgres-001"
        payload["stream"] = {
            "selected_url": "rtsp://user:password@example.invalid/live?token=secret",
            "delivery": "metadata-only",
        }

        with TestClient(application) as client:
            assert client.get("/health/ready").status_code == 200
            listed = client.get("/cameras", headers=viewer_headers)
            created = client.post("/cameras", json=payload, headers=editor_headers)
            updated = client.patch(
                "/cameras/synthetic:postgres-001",
                json={"health_status": "synthetic-verified"},
                headers={**editor_headers, "If-Match": created.headers["ETag"]},
            )

        assert listed.status_code == 200
        assert listed.json()["total"] == 2
        assert created.status_code == 201
        assert created.json()["stream"]["selected_url"] == (
            "rtsp://example.invalid/live"
        )
        assert updated.status_code == 200
        assert updated.json()["state"]["health"] == "synthetic-verified"

        with database.session_factory() as session:
            assert session.scalar(select(func.count()).select_from(Camera)) == 3
            correlated = session.scalars(
                select(AuditEvent).where(
                    AuditEvent.action.in_(
                        [
                            "camera_registry.camera.create",
                            "camera_registry.camera.update",
                        ]
                    )
                )
            ).all()
        assert len(correlated) == 2
        assert all(
            event.context["request_id"] == "postgres.integration:001"
            for event in correlated
        )
    finally:
        database.dispose()


def test_postgres_capability_workers_claim_distinct_jobs_concurrently() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    now = datetime.now(UTC)
    camera_id = "synthetic:postgres-capability"
    stream_ids = [f"str_{number:032x}" for number in (9001, 9002)]
    refresh_ids = [f"cpr_{number:032x}" for number in (9001, 9002)]

    class BarrierEngine:
        def __init__(self) -> None:
            self.barrier = Barrier(2)

        def discover(self, endpoint) -> CapabilityDiscoveryResult:
            self.barrier.wait(timeout=10)
            return CapabilityDiscoveryResult(
                source="device_and_media",
                completeness="complete",
                payload={
                    "device": {"model": endpoint.stream_id},
                    "services": [],
                    "media": None,
                    "warnings": [],
                },
                duration_ms=1.0,
            )

    try:
        database.check_ready()
        with database.session_factory.begin() as session:
            existing = session.get(Camera, camera_id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(
                Camera(
                    camera_id=camera_id,
                    source_id="postgres-capability-test",
                    external_id="camera-01",
                    display_name="PostgreSQL Capability Worker Test",
                    department="Engineering Lab",
                    source_schema="hcam.synthetic.test.v1",
                    provenance={"synthetic": True},
                    imported_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
            for index, (stream_id, refresh_id) in enumerate(
                zip(stream_ids, refresh_ids, strict=True)
            ):
                session.add(
                    StreamEndpoint(
                        stream_id=stream_id,
                        camera_id=camera_id,
                        name=f"capability-{index}",
                        adapter_kind="onvif",
                        protocol="https",
                        locator=f"https://10.0.0.{index + 1}/onvif/media_service",
                        management_locator=(
                            f"https://10.0.0.{index + 1}/onvif/device_service"
                        ),
                        capability_refresh_enabled=False,
                        transport="tcp",
                        is_primary=False,
                        enabled=True,
                        created_at=now,
                        updated_at=now,
                    )
                )
                session.flush()
                session.add(
                    StreamCapabilityRefresh(
                        refresh_id=refresh_id,
                        stream_id=stream_id,
                        status="queued",
                        source="manual",
                        priority=100,
                        requested_by="postgres-test",
                        request_id=f"postgres-capability-{index}",
                        audit_reason="Synthetic concurrent worker validation",
                        attempt_count=0,
                        max_attempts=3,
                        next_attempt_at=now,
                        queued_at=now,
                        updated_at=now,
                    )
                )

        engine = BarrierEngine()
        workers = [
            CapabilityRefreshWorker(
                database.session_factory,
                engine,  # type: ignore[arg-type]
                worker_id=f"postgres-worker-{number}",
            )
            for number in (1, 2)
        ]
        with ThreadPoolExecutor(max_workers=2) as executor:
            completed = list(executor.map(lambda worker: worker.run_once(), workers))
        assert completed == [True, True]

        with database.session_factory() as session:
            refreshes = session.scalars(
                select(StreamCapabilityRefresh)
                .where(StreamCapabilityRefresh.refresh_id.in_(refresh_ids))
                .order_by(StreamCapabilityRefresh.refresh_id)
            ).all()
            snapshot_count = session.scalar(
                select(func.count())
                .select_from(StreamCapabilitySnapshot)
                .where(StreamCapabilitySnapshot.stream_id.in_(stream_ids))
            )
        assert len(refreshes) == 2
        assert all(item.status == "succeeded" for item in refreshes)
        assert all(item.attempt_count == 1 for item in refreshes)
        assert len({item.snapshot_id for item in refreshes}) == 2
        assert snapshot_count == 2
    finally:
        database.dispose()


def test_postgres_concurrent_capability_queue_reuses_single_active_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    now = datetime.now(UTC)
    camera_id = "synthetic:postgres-capability-queue"
    stream_id = "str_0000000000000000000000000000c101"
    principal = Principal(
        actor_id="postgres-capability-editor",
        roles=frozenset({"camera.editor"}),
        departments=frozenset({"*"}),
        authentication_method="synthetic-test",
    )
    before_read = Barrier(2)
    after_read = Barrier(2)
    call_lock = Lock()
    calls_by_thread: dict[int, int] = {}
    original_active_refresh = CapabilityService._active_refresh

    def synchronized_first_read(
        service: CapabilityService, candidate_stream_id: str
    ) -> StreamCapabilityRefresh | None:
        thread_id = get_ident()
        with call_lock:
            call_number = calls_by_thread.get(thread_id, 0) + 1
            calls_by_thread[thread_id] = call_number
        if call_number == 1:
            before_read.wait(timeout=10)
        active = original_active_refresh(service, candidate_stream_id)
        if call_number == 1:
            after_read.wait(timeout=10)
        return active

    try:
        database.check_ready()
        with database.session_factory.begin() as session:
            existing = session.get(Camera, camera_id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(
                Camera(
                    camera_id=camera_id,
                    source_id="postgres-capability-queue-test",
                    external_id="camera-queue-01",
                    display_name="PostgreSQL Capability Queue Test",
                    department="Engineering Lab",
                    source_schema="hcam.synthetic.test.v1",
                    provenance={"synthetic": True},
                    imported_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
            session.add(
                StreamEndpoint(
                    stream_id=stream_id,
                    camera_id=camera_id,
                    name="capability-queue",
                    adapter_kind="onvif",
                    protocol="https",
                    locator="https://10.0.1.1/onvif/media_service",
                    management_locator="https://10.0.1.1/onvif/device_service",
                    capability_refresh_enabled=False,
                    transport="tcp",
                    is_primary=False,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )

        monkeypatch.setattr(
            CapabilityService, "_active_refresh", synchronized_first_read
        )

        def queue_refresh(number: int) -> tuple[str, bool]:
            with database.session_factory() as session:
                refresh, deduplicated = CapabilityService(session).queue_refresh(
                    stream_id,
                    principal=principal,
                    reason=f"Synthetic concurrent queue request {number}",
                    request_id=f"postgres-capability-queue-{number}",
                )
                return refresh.refresh_id, deduplicated

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(queue_refresh, (1, 2)))

        assert len({refresh_id for refresh_id, _deduplicated in results}) == 1
        assert sorted(deduplicated for _refresh_id, deduplicated in results) == [
            False,
            True,
        ]
        with database.session_factory() as session:
            active_count = session.scalar(
                select(func.count())
                .select_from(StreamCapabilityRefresh)
                .where(
                    StreamCapabilityRefresh.stream_id == stream_id,
                    StreamCapabilityRefresh.status.in_(("queued", "running")),
                )
            )
            total_count = session.scalar(
                select(func.count())
                .select_from(StreamCapabilityRefresh)
                .where(StreamCapabilityRefresh.stream_id == stream_id)
            )
        assert active_count == 1
        assert total_count == 1
    finally:
        database.dispose()


def test_postgres_generated_tracking_transaction_and_replay() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    stream_id = synthetic_stream_id(99)
    try:
        database.check_ready()
        with database.session_factory.begin() as session:
            session.execute(
                delete(AnalyticsAssignment).where(
                    AnalyticsAssignment.stream_id == stream_id
                )
            )
        with database.session_factory() as session:
            seed_synthetic_lab(session, count=99)

        application = create_app(
            Settings(
                database_url=POSTGRES_TEST_URL,
                dev_auth_enabled=True,
                environment="test",
                access_log_enabled=False,
                analytics_generated_tracking_enabled=True,
            )
        )
        headers = {
            "X-HCAM-Actor": "postgres-tracking-editor",
            "X-HCAM-Roles": "camera.editor",
            "X-HCAM-Departments": "Engineering Lab",
            "X-HCAM-Reason": "PostgreSQL generated tracking validation",
        }
        assignment_payload = {
            "capability": P3_3_CAPABILITY,
            "desired_state": "paused",
            "pipeline": {
                "id": P3_3_PIPELINE_ID,
                "version": P3_3_PIPELINE_VERSION,
            },
            "models": [
                {"id": P3_3_TRACKER_ID, "version": P3_3_TRACKER_VERSION}
            ],
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
        run_payload = {
            "scenario_id": "all-tier-a",
            "seed": 99,
            "observed_at": "2026-08-25T12:00:00Z",
        }
        with TestClient(application) as client:
            created = client.post(
                f"/streams/{stream_id}/analytics-assignments",
                json=assignment_payload,
                headers=headers,
            )
            assert created.status_code == 201
            assignment_id = created.json()["assignment_id"]
            activated = client.post(
                f"/analytics-assignments/{assignment_id}/activate",
                headers={**headers, "If-Match": created.headers["ETag"]},
            )
            assert activated.status_code == 200
            executed = client.post(
                f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
                json=run_payload,
                headers=headers,
            )
            replay = client.post(
                f"/analytics-assignments/{assignment_id}/generated-tracking-runs",
                json=run_payload,
                headers=headers,
            )

        assert executed.status_code == 201
        assert executed.json()["status"] == "succeeded"
        assert replay.status_code == 201
        assert replay.json()["reused"] is True
        run_id = executed.json()["run_id"]
        with database.session_factory() as session:
            assert session.get(AnalyticsTrackingRun, run_id) is not None
            assert session.scalar(
                select(func.count())
                .select_from(AnalyticsTrackerEpoch)
                .where(AnalyticsTrackerEpoch.run_id == run_id)
            ) == 1
            assert session.scalar(
                select(func.count())
                .select_from(AnalyticsTrack)
                .where(AnalyticsTrack.run_id == run_id)
            ) == 7
            lifecycle_count = session.scalar(
                select(func.count())
                .select_from(AnalyticsTrackLifecycle)
                .where(AnalyticsTrackLifecycle.run_id == run_id)
            )
            outbox_count = session.scalar(
                select(func.count())
                .select_from(StreamEventOutbox)
                .where(
                    StreamEventOutbox.stream_id == stream_id,
                    StreamEventOutbox.event_type
                    == "hcam.analytics.track.lifecycle.v2",
                )
            )
        assert lifecycle_count == executed.json()["transition_count"]
        assert outbox_count == lifecycle_count
    finally:
        with database.session_factory.begin() as session:
            session.execute(
                delete(AnalyticsAssignment).where(
                    AnalyticsAssignment.stream_id == stream_id
                )
            )
        database.dispose()


def test_postgres_capability_history_retention_preserves_latest_snapshot() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    now = datetime.now(UTC)
    expired_at = now - timedelta(days=91)
    camera_id = "synthetic:postgres-capability-retention"
    stream_id = "str_0000000000000000000000000000c201"
    old_snapshot_id = "cps_0000000000000000000000000000c201"
    latest_snapshot_id = "cps_0000000000000000000000000000c202"
    old_refresh_id = "cpr_0000000000000000000000000000c201"
    current_refresh_id = "cpr_0000000000000000000000000000c202"
    try:
        database.check_ready()
        with database.session_factory.begin() as session:
            existing = session.get(Camera, camera_id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(
                Camera(
                    camera_id=camera_id,
                    source_id="postgres-capability-retention-test",
                    external_id="camera-retention-01",
                    display_name="PostgreSQL Capability Retention Test",
                    department="Engineering Lab",
                    source_schema="hcam.synthetic.test.v1",
                    provenance={"synthetic": True},
                    imported_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
            session.add(
                StreamEndpoint(
                    stream_id=stream_id,
                    camera_id=camera_id,
                    name="capability-retention",
                    adapter_kind="onvif",
                    protocol="https",
                    locator="https://10.0.2.1/onvif/media_service",
                    management_locator="https://10.0.2.1/onvif/device_service",
                    capability_refresh_enabled=False,
                    transport="tcp",
                    is_primary=False,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
            for snapshot_id, model in (
                (old_snapshot_id, "Expired History"),
                (latest_snapshot_id, "Latest Stale Inventory"),
            ):
                session.add(
                    StreamCapabilitySnapshot(
                        snapshot_id=snapshot_id,
                        stream_id=stream_id,
                        fingerprint=snapshot_id[-1] * 64,
                        source="device_and_media",
                        completeness="complete",
                        payload={"device": {"model": model}},
                        first_observed_at=expired_at,
                        last_observed_at=expired_at,
                        created_at=expired_at,
                    )
                )
            session.flush()
            for refresh_id, snapshot_id, finished_at in (
                (old_refresh_id, old_snapshot_id, expired_at),
                (current_refresh_id, latest_snapshot_id, now),
            ):
                session.add(
                    StreamCapabilityRefresh(
                        refresh_id=refresh_id,
                        stream_id=stream_id,
                        status="succeeded",
                        source="manual",
                        priority=100,
                        requested_by="postgres-retention-test",
                        request_id=refresh_id,
                        audit_reason="Synthetic PostgreSQL retention validation",
                        attempt_count=1,
                        max_attempts=3,
                        next_attempt_at=finished_at,
                        duration_ms=1.0,
                        result_completeness="complete",
                        snapshot_id=snapshot_id,
                        queued_at=finished_at,
                        started_at=finished_at,
                        finished_at=finished_at,
                        created_at=finished_at,
                        updated_at=finished_at,
                    )
                )
            session.flush()
            _prune_capability_history(
                session,
                now=now,
                current_refresh_id=current_refresh_id,
            )

        with database.session_factory() as session:
            assert session.get(StreamCapabilitySnapshot, old_snapshot_id) is None
            latest = session.get(StreamCapabilitySnapshot, latest_snapshot_id)
            assert session.get(StreamCapabilityRefresh, old_refresh_id) is None
            assert session.get(StreamCapabilityRefresh, current_refresh_id) is not None
        assert latest is not None
        assert latest.payload["device"]["model"] == "Latest Stale Inventory"
    finally:
        database.dispose()
