from __future__ import annotations

from datetime import UTC, datetime, timedelta
from dataclasses import replace
import ipaddress
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from hcam.audit.models import AuditEvent
from hcam.streams.capabilities import (
    CapabilityDiscoveryError,
    CapabilityDiscoveryResult,
    CapabilityService,
)
from hcam.streams.capability_worker import (
    CapabilityRefreshWorker,
    CapabilityWorkerLeaseError,
    CapabilityWorkerRuntimeError,
    next_capability_due,
)
from hcam.streams.models import (
    StreamCapabilityRefresh,
    StreamCapabilitySnapshot,
    StreamEndpoint,
    StreamEventOutbox,
)
from hcam.streams.network import OnvifEgressRule
from hcam.streams.onvif_simulator import handler_for


def _onvif_payload(**overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "managed-onvif",
        "adapter_kind": "onvif",
        "protocol": "http",
        "locator": "http://127.0.0.1:8081/onvif/media_service",
        "management_locator": "http://127.0.0.1:8081/onvif/device_service",
        "onvif_auth_mode": "none",
        "capability_refresh_enabled": False,
        "transport": "tcp",
        "is_primary": False,
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _create_managed_stream(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/cameras/synthetic:cctv-002/streams",
        json=_onvif_payload(),
        headers=headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["management_locator"].endswith("/onvif/device_service")
    assert body["onvif_auth_mode"] == "none"
    assert body["capability_refresh_enabled"] is False
    return body["stream_id"]


def _result(*, model: str = "Synthetic One") -> CapabilityDiscoveryResult:
    return CapabilityDiscoveryResult(
        source="device_and_media",
        completeness="complete",
        payload={
            "device": {
                "manufacturer": "H-CAM",
                "model": model,
                "firmware_version": "2.0",
                "serial_number": "SYNTHETIC",
                "hardware_id": "SIM",
                "clock_offset_seconds": 0.5,
            },
            "services": [
                {
                    "namespace": "http://www.onvif.org/ver10/media/wsdl",
                    "version": "2.6",
                }
            ],
            "media": {
                "snapshot_uri": True,
                "rotation": False,
                "video_source_mode": False,
                "osd": True,
                "temporary_osd_text": False,
                "exi_compression": False,
                "maximum_profiles": 1,
                "profiles": [],
            },
            "warnings": [],
        },
        duration_ms=12.5,
    )


class _StaticEngine:
    def __init__(self, result: CapabilityDiscoveryResult) -> None:
        self.result = result

    def discover(self, _endpoint) -> CapabilityDiscoveryResult:
        return self.result


class _FailingEngine:
    def __init__(self, error: CapabilityDiscoveryError) -> None:
        self.error = error

    def discover(self, _endpoint) -> CapabilityDiscoveryResult:
        raise self.error


class _CountingEngine:
    def __init__(self) -> None:
        self.calls = 0

    def discover(self, _endpoint) -> CapabilityDiscoveryResult:
        self.calls += 1
        return _result()


def test_capability_refresh_api_queues_deduplicates_and_scopes(
    imported_app,
    editor_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        queued = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        )
        duplicate = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        )
        status_response = client.get(queued.headers["location"], headers=viewer_headers)
        viewer_queue = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers={
                **viewer_headers,
                "X-HCAM-Reason": "Viewer cannot queue capability work",
            },
        )
        missing_snapshot = client.get(
            f"/streams/{stream_id}/capabilities", headers=viewer_headers
        )

    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"
    assert queued.json()["deduplicated"] is False
    assert duplicate.status_code == 202
    assert duplicate.json()["refresh_id"] == queued.json()["refresh_id"]
    assert duplicate.json()["deduplicated"] is True
    assert status_response.status_code == 200
    assert viewer_queue.status_code == 403
    assert missing_snapshot.status_code == 404


def test_managed_synchronous_compatibility_uses_new_engine_and_caches(
    imported_app,
    editor_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        handler_for("rtsp://127.0.0.1:8554/synthetic-01"),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    imported_app.state.settings = replace(
        imported_app.state.settings,
        onvif_egress_rules=(
            OnvifEgressRule(
                scheme="http",
                host="127.0.0.1",
                port=port,
                approved_addresses=(ipaddress.ip_network("127.0.0.1/32"),),
            ),
        ),
        onvif_lab_http_enabled=True,
    )
    try:
        with TestClient(imported_app) as client:
            created = client.post(
                "/cameras/synthetic:cctv-002/streams",
                json=_onvif_payload(
                    locator=f"http://127.0.0.1:{port}/onvif/media_service",
                    management_locator=(
                        f"http://127.0.0.1:{port}/onvif/device_service"
                    ),
                ),
                headers=editor_headers,
            )
            stream_id = created.json()["stream_id"]
            discovered = client.post(
                f"/streams/{stream_id}/capabilities/discover",
                headers=editor_headers,
            )
            cached = client.get(
                f"/streams/{stream_id}/capabilities", headers=viewer_headers
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert discovered.status_code == 200, discovered.text
    assert discovered.headers["deprecation"] == "true"
    assert "successor-version" in discovered.headers["link"]
    assert discovered.json()["media"]["maximum_profiles"] == 8
    assert cached.status_code == 200
    assert cached.json()["source"] == "device_and_media"
    assert cached.json()["device"]["manufacturer"] == "H-CAM Synthetic"


def test_capability_configuration_and_queue_validation(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        missing_secret = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=_onvif_payload(onvif_auth_mode="http_digest"),
            headers=editor_headers,
        )
        missing_management = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=_onvif_payload(
                name="missing-management",
                management_locator=None,
                capability_refresh_enabled=True,
            ),
            headers=editor_headers,
        )
        wrong_adapter = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=_onvif_payload(
                name="wrong-adapter",
                adapter_kind="http",
                management_locator=None,
                capability_refresh_enabled=False,
            ),
            headers=editor_headers,
        )
        disabled = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=_onvif_payload(name="disabled", enabled=False),
            headers=editor_headers,
        )
        disabled_queue = client.post(
            f"/streams/{disabled.json()['stream_id']}/capability-refreshes",
            headers=editor_headers,
        )
        synthetic = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json={
                **_onvif_payload(name="not-onvif"),
                "adapter_kind": "http",
                "management_locator": None,
            },
            headers=editor_headers,
        )
        synthetic_queue = client.post(
            f"/streams/{synthetic.json()['stream_id']}/capability-refreshes",
            headers=editor_headers,
        )
    assert missing_secret.status_code == 422
    assert missing_management.status_code == 422
    assert wrong_adapter.status_code == 201
    assert disabled_queue.status_code == 422
    assert synthetic_queue.status_code == 422


def test_capability_refresh_cooldown_and_department_scope(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        queued = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()
    with imported_app.state.database.session_factory.begin() as session:
        refresh = session.get(StreamCapabilityRefresh, queued["refresh_id"])
        assert refresh is not None
        refresh.status = "failed"
        refresh.queued_at = datetime.now(UTC) - timedelta(minutes=5)
        refresh.finished_at = datetime.now(UTC)
    with TestClient(imported_app) as client:
        cooldown = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        )
        hidden = client.get(
            f"/capability-refreshes/{queued['refresh_id']}",
            headers={
                "X-HCAM-Actor": "outside-viewer",
                "X-HCAM-Roles": "camera.viewer",
                "X-HCAM-Departments": "operations",
            },
        )
    assert cooldown.status_code == 429
    assert int(cooldown.headers["retry-after"]) >= 1
    assert hidden.status_code == 404

    with imported_app.state.database.session_factory.begin() as session:
        refresh = session.get(StreamCapabilityRefresh, queued["refresh_id"])
        assert refresh is not None
        refresh.finished_at = datetime.now(UTC) - timedelta(minutes=2)
    with TestClient(imported_app) as client:
        resumed = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        )
    assert resumed.status_code == 202
    assert resumed.json()["deduplicated"] is False


def test_capability_refresh_conflict_reuses_winning_active_job(
    imported_app,
    editor_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)

    winner_id = "cpr_0000000000000000000000000000c001"
    queued_at = datetime.now(UTC) - timedelta(minutes=2)
    with imported_app.state.database.session_factory.begin() as session:
        session.add(
            StreamCapabilityRefresh(
                refresh_id=winner_id,
                stream_id=stream_id,
                status="queued",
                source="manual",
                priority=100,
                requested_by="synthetic-concurrent-winner",
                request_id="synthetic-concurrent-winner",
                audit_reason="Synthetic concurrent queue winner",
                attempt_count=0,
                max_attempts=3,
                next_attempt_at=queued_at,
                queued_at=queued_at,
                updated_at=queued_at,
            )
        )

    original_active_refresh = CapabilityService._active_refresh
    call_count = 0

    def stale_first_read(
        service: CapabilityService, candidate_stream_id: str
    ) -> StreamCapabilityRefresh | None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return None
        return original_active_refresh(service, candidate_stream_id)

    monkeypatch.setattr(CapabilityService, "_active_refresh", stale_first_read)
    with TestClient(imported_app) as client:
        response = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        )

    assert response.status_code == 202, response.text
    assert response.json()["refresh_id"] == winner_id
    assert response.json()["deduplicated"] is True
    assert call_count >= 2
    with imported_app.state.database.session_factory() as session:
        active_count = session.scalar(
            select(func.count())
            .select_from(StreamCapabilityRefresh)
            .where(
                StreamCapabilityRefresh.stream_id == stream_id,
                StreamCapabilityRefresh.status.in_(("queued", "running")),
            )
        )
    assert active_count == 1


def test_worker_persists_latest_snapshot_and_deduplicates_unchanged_results(
    imported_app,
    editor_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        refresh_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]
    engine = _StaticEngine(_result())
    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        engine,  # type: ignore[arg-type]
        worker_id="capability-worker-1",
    )
    assert worker.run_once() is True

    with TestClient(imported_app) as client:
        completed = client.get(
            f"/capability-refreshes/{refresh_id}", headers=viewer_headers
        )
        latest = client.get(
            f"/streams/{stream_id}/capabilities", headers=viewer_headers
        )
        history = client.get(
            f"/streams/{stream_id}/capability-snapshots", headers=viewer_headers
        )
    assert completed.json()["status"] == "succeeded"
    assert completed.json()["completeness"] == "complete"
    assert latest.status_code == 200
    assert latest.json()["fresh"] is True
    assert latest.json()["device"]["model"] == "Synthetic One"
    assert history.json()["total"] == 1

    with imported_app.state.database.session_factory.begin() as session:
        first = session.get(StreamCapabilityRefresh, refresh_id)
        assert first is not None
        first.queued_at = datetime.now(UTC) - timedelta(minutes=2)
        first.finished_at = datetime.now(UTC) - timedelta(minutes=2)
    with TestClient(imported_app) as client:
        second_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]
    assert worker.run_once() is True
    with imported_app.state.database.session_factory() as session:
        snapshot_count = session.scalar(
            select(func.count())
            .select_from(StreamCapabilitySnapshot)
            .where(StreamCapabilitySnapshot.stream_id == stream_id)
        )
        second = session.get(StreamCapabilityRefresh, second_id)
    assert snapshot_count == 1
    assert second is not None and second.snapshot_id == completed.json()["snapshot_id"]


def test_worker_creates_change_history_event_and_retries_transient_failure(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        refresh_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]
    failing = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        _FailingEngine(CapabilityDiscoveryError("unreachable", retryable=True)),  # type: ignore[arg-type]
        worker_id="capability-worker-retry",
    )
    assert failing.run_once() is True
    with imported_app.state.database.session_factory.begin() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        assert refresh is not None
        assert refresh.status == "queued"
        assert refresh.attempt_count == 1
        assert refresh.reason_code == "unreachable"
        refresh.next_attempt_at = datetime.now(UTC) - timedelta(seconds=1)

    succeeding = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        _StaticEngine(_result(model="Changed Model")),  # type: ignore[arg-type]
        worker_id="capability-worker-retry",
    )
    assert succeeding.run_once() is True
    with imported_app.state.database.session_factory() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        changed_events = session.scalars(
            select(StreamEventOutbox).where(
                StreamEventOutbox.stream_id == stream_id,
                StreamEventOutbox.event_type == "hcam.stream.capabilities.changed.v1",
            )
        ).all()
        audits = session.scalars(
            select(AuditEvent).where(
                AuditEvent.target_id == refresh_id,
                AuditEvent.action == "stream.capability_refresh.retry",
            )
        ).all()
    assert refresh is not None and refresh.status == "succeeded"
    assert refresh.attempt_count == 2
    assert len(changed_events) == 1
    assert len(audits) == 1


def test_worker_does_not_retry_terminal_failure_and_recovers_expired_lease(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        refresh_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]
    with imported_app.state.database.session_factory.begin() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        assert refresh is not None
        refresh.status = "running"
        refresh.lease_owner = "dead-worker"
        refresh.lease_until = datetime.now(UTC) - timedelta(seconds=1)
    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        _FailingEngine(CapabilityDiscoveryError("unauthorized", retryable=False)),  # type: ignore[arg-type]
        worker_id="replacement-worker",
    )
    assert worker.run_once() is True
    with imported_app.state.database.session_factory() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        recovery_audit = session.scalar(
            select(AuditEvent).where(
                AuditEvent.target_id == refresh_id,
                AuditEvent.action == "stream.capability_refresh.lease_recovered",
            )
        )
    assert refresh is not None
    assert refresh.status == "failed"
    assert refresh.reason_code == "unauthorized"
    assert refresh.attempt_count == 1
    assert refresh.lease_owner is None
    assert recovery_audit is not None
    assert recovery_audit.actor_id is None
    assert recovery_audit.source == "hcam.capability-worker"
    assert {
        key: recovery_audit.context[key]
        for key in ("stream_id", "camera_id", "source", "attempt_count")
    } == {
        "stream_id": stream_id,
        "camera_id": "synthetic:cctv-002",
        "source": "manual",
        "attempt_count": 1,
    }
    assert isinstance(recovery_audit.context["request_id"], str)


def test_worker_prunes_expired_capability_history_but_keeps_latest_inventory(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        current_refresh_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]

    now = datetime.now(UTC) + timedelta(minutes=1)
    older_at = now - timedelta(days=100)
    latest_at = now - timedelta(days=95)
    older_snapshot_id = "cps_0000000000000000000000000000d001"
    tied_snapshot_id = "cps_0000000000000000000000000000d002"
    latest_snapshot_id = "cps_0000000000000000000000000000d003"
    old_refresh_id = "cpr_0000000000000000000000000000d001"
    with imported_app.state.database.session_factory.begin() as session:
        session.add_all(
            [
                StreamCapabilitySnapshot(
                    snapshot_id=older_snapshot_id,
                    stream_id=stream_id,
                    fingerprint="a" * 64,
                    source="device_and_media",
                    completeness="complete",
                    payload=_result(model="Expired History").payload,
                    first_observed_at=older_at,
                    last_observed_at=older_at,
                    created_at=older_at,
                ),
                StreamCapabilitySnapshot(
                    snapshot_id=tied_snapshot_id,
                    stream_id=stream_id,
                    fingerprint="b" * 64,
                    source="device_and_media",
                    completeness="complete",
                    payload=_result(model="Expired Tied History").payload,
                    first_observed_at=latest_at,
                    last_observed_at=latest_at,
                    created_at=latest_at,
                ),
                StreamCapabilitySnapshot(
                    snapshot_id=latest_snapshot_id,
                    stream_id=stream_id,
                    fingerprint="c" * 64,
                    source="device_and_media",
                    completeness="complete",
                    payload=_result(model="Latest Stale Inventory").payload,
                    first_observed_at=latest_at,
                    last_observed_at=latest_at,
                    created_at=latest_at,
                ),
            ]
        )
        session.flush()
        session.add(
            StreamCapabilityRefresh(
                refresh_id=old_refresh_id,
                stream_id=stream_id,
                status="succeeded",
                source="manual",
                priority=100,
                requested_by="retention-test",
                request_id="retention-test-old",
                audit_reason="Synthetic expired refresh",
                attempt_count=1,
                max_attempts=3,
                next_attempt_at=older_at,
                duration_ms=1.0,
                result_completeness="complete",
                snapshot_id=older_snapshot_id,
                queued_at=older_at,
                started_at=older_at,
                finished_at=older_at,
                created_at=older_at,
                updated_at=older_at,
            )
        )

    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        _FailingEngine(CapabilityDiscoveryError("unauthorized", retryable=False)),  # type: ignore[arg-type]
        worker_id="capability-retention-worker",
        clock=lambda: now,
    )
    assert worker.run_once() is True

    with imported_app.state.database.session_factory() as session:
        assert session.get(StreamCapabilitySnapshot, older_snapshot_id) is None
        assert session.get(StreamCapabilitySnapshot, tied_snapshot_id) is None
        latest = session.get(StreamCapabilitySnapshot, latest_snapshot_id)
        assert session.get(StreamCapabilityRefresh, old_refresh_id) is None
        current = session.get(StreamCapabilityRefresh, current_refresh_id)
        snapshot_count = session.scalar(
            select(func.count())
            .select_from(StreamCapabilitySnapshot)
            .where(StreamCapabilitySnapshot.stream_id == stream_id)
        )
    assert latest is not None
    assert latest.payload["device"]["model"] == "Latest Stale Inventory"
    assert current is not None and current.status == "failed"
    assert snapshot_count == 1


def test_worker_fails_closed_when_stream_is_disabled_after_queue(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        refresh_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]
    with imported_app.state.database.session_factory.begin() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        assert endpoint is not None
        assert refresh is not None
        endpoint.enabled = False
        refresh.status = "running"
        refresh.attempt_count = 1
        refresh.lease_owner = "expired-disabled-worker"
        refresh.lease_until = datetime.now(UTC) - timedelta(seconds=1)

    engine = _CountingEngine()
    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        engine,  # type: ignore[arg-type]
        worker_id="disabled-stream-worker",
    )
    assert worker.run_once() is True

    with imported_app.state.database.session_factory() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        audit = session.scalar(
            select(AuditEvent).where(
                AuditEvent.target_id == refresh_id,
                AuditEvent.action == "stream.capability_refresh.fail",
            )
        )
    assert refresh is not None
    assert refresh.status == "failed"
    assert refresh.reason_code == "stream_disabled"
    assert refresh.attempt_count == 1
    assert refresh.finished_at is not None
    assert refresh.lease_owner is None
    assert refresh.lease_until is None
    assert audit is not None
    expected_context = {
        "stream_id": stream_id,
        "camera_id": "synthetic:cctv-002",
        "source": "manual",
        "reason_code": "stream_disabled",
        "attempt_count": 1,
    }
    assert {key: audit.context[key] for key in expected_context} == expected_context
    assert isinstance(audit.context["request_id"], str)
    assert engine.calls == 0


def test_worker_audits_missing_stream_preflight_without_contacting_engine(
    imported_app,
    editor_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        refresh_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]

    original_get = Session.get

    def missing_stream_get(session: Session, entity, ident, **kwargs):
        if entity is StreamEndpoint:
            return None
        return original_get(session, entity, ident, **kwargs)

    monkeypatch.setattr(Session, "get", missing_stream_get)
    engine = _CountingEngine()
    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        engine,  # type: ignore[arg-type]
        worker_id="missing-stream-worker",
    )
    assert worker.run_once() is True

    with imported_app.state.database.session_factory() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        audit = session.scalar(
            select(AuditEvent).where(
                AuditEvent.target_id == refresh_id,
                AuditEvent.action == "stream.capability_refresh.fail",
            )
        )
    assert refresh is not None
    assert refresh.status == "failed"
    assert refresh.reason_code == "stream_not_found"
    assert refresh.lease_owner is None
    assert refresh.lease_until is None
    assert audit is not None
    expected_context = {
        "stream_id": stream_id,
        "source": "manual",
        "reason_code": "stream_not_found",
        "attempt_count": 0,
    }
    assert {key: audit.context[key] for key in expected_context} == expected_context
    assert isinstance(audit.context["request_id"], str)
    assert engine.calls == 0


def test_scheduled_refresh_is_opt_in_and_jitter_is_bounded(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        response = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=_onvif_payload(capability_refresh_enabled=True),
            headers=editor_headers,
        )
        assert response.status_code == 201
        stream_id = response.json()["stream_id"]
    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        _StaticEngine(_result()),  # type: ignore[arg-type]
        worker_id="scheduled-worker",
    )
    assert worker.run_once() is True
    with imported_app.state.database.session_factory() as session:
        refresh = session.scalar(
            select(StreamCapabilityRefresh).where(
                StreamCapabilityRefresh.stream_id == stream_id
            )
        )
        endpoint = session.get(StreamEndpoint, stream_id)
        assert refresh is not None
        queue_audit = session.scalar(
            select(AuditEvent).where(
                AuditEvent.target_id == refresh.refresh_id,
                AuditEvent.action == "stream.capability_refresh.queue",
            )
        )
    assert refresh is not None and refresh.source == "scheduled"
    assert refresh.status == "succeeded"
    assert endpoint is not None and endpoint.capability_due_at is not None
    assert queue_audit is not None
    assert queue_audit.actor_id is None
    assert queue_audit.source == "hcam.capability-worker"
    assert queue_audit.context == {
        "stream_id": stream_id,
        "camera_id": "synthetic:cctv-002",
        "source": "scheduled",
    }
    now = datetime.now(UTC)
    next_due = next_capability_due(now, stream_id)
    assert now + timedelta(hours=22) <= next_due <= now + timedelta(hours=26)


def test_scheduled_refresh_fails_closed_when_queue_audit_is_unavailable(
    imported_app,
    editor_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(imported_app) as client:
        response = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=_onvif_payload(
                name="scheduled-audit-failure",
                capability_refresh_enabled=True,
            ),
            headers=editor_headers,
        )
        assert response.status_code == 201
        stream_id = response.json()["stream_id"]
    with imported_app.state.database.session_factory() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        original_due_at = endpoint.capability_due_at

    def fail_audit(*_args, **_kwargs):
        raise SQLAlchemyError("synthetic audit outage")

    monkeypatch.setattr(
        "hcam.streams.capability_worker.AuditRepository.record",
        fail_audit,
    )
    engine = _CountingEngine()
    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        engine,  # type: ignore[arg-type]
        worker_id="scheduled-audit-failure-worker",
    )

    with pytest.raises(SQLAlchemyError):
        worker.run_once()

    with imported_app.state.database.session_factory() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        refresh_count = session.scalar(
            select(func.count())
            .select_from(StreamCapabilityRefresh)
            .where(StreamCapabilityRefresh.stream_id == stream_id)
        )
    assert endpoint is not None and endpoint.capability_due_at == original_due_at
    assert refresh_count == 0
    assert engine.calls == 0


def test_expired_lease_recovery_fails_closed_when_audit_is_unavailable(
    imported_app,
    editor_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        refresh_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]
    with imported_app.state.database.session_factory.begin() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        assert refresh is not None
        refresh.status = "running"
        refresh.lease_owner = "expired-worker"
        refresh.lease_until = datetime.now(UTC) - timedelta(seconds=1)

    def fail_audit(*_args, **_kwargs):
        raise SQLAlchemyError("synthetic audit outage")

    monkeypatch.setattr(
        "hcam.streams.capability_worker.AuditRepository.record",
        fail_audit,
    )
    engine = _CountingEngine()
    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        engine,  # type: ignore[arg-type]
        worker_id="replacement-worker",
    )

    with pytest.raises(SQLAlchemyError):
        worker.run_once()

    with imported_app.state.database.session_factory() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
    assert refresh is not None
    assert refresh.status == "running"
    assert refresh.lease_owner == "expired-worker"
    assert refresh.attempt_count == 0
    assert engine.calls == 0


def test_scheduled_capability_load_processes_50_streams(imported_app) -> None:
    now = datetime.now(UTC)
    with imported_app.state.database.session_factory.begin() as session:
        for number in range(50):
            session.add(
                StreamEndpoint(
                    stream_id=f"str_{number + 1000:032x}",
                    camera_id="synthetic:cctv-002",
                    name=f"scheduled-load-{number:02d}",
                    adapter_kind="onvif",
                    protocol="http",
                    locator="http://127.0.0.1:8081/onvif/media_service",
                    management_locator=("http://127.0.0.1:8081/onvif/device_service"),
                    capability_refresh_enabled=True,
                    capability_due_at=now,
                    transport="tcp",
                    is_primary=False,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )

    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        _StaticEngine(_result()),  # type: ignore[arg-type]
        worker_id="scheduled-load-worker",
    )
    assert all(worker.run_once() for _ in range(50))
    assert worker.run_once() is False

    with imported_app.state.database.session_factory() as session:
        succeeded = session.scalar(
            select(func.count())
            .select_from(StreamCapabilityRefresh)
            .where(
                StreamCapabilityRefresh.source == "scheduled",
                StreamCapabilityRefresh.status == "succeeded",
            )
        )
        snapshots = session.scalar(
            select(func.count()).select_from(StreamCapabilitySnapshot)
        )
    assert succeeded == 50
    assert snapshots == 50


def test_capability_worker_handles_empty_active_and_runtime_failure_paths(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    idle = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        _StaticEngine(_result()),  # type: ignore[arg-type]
        worker_id="idle-worker",
    )
    assert idle.run_once() is False

    with TestClient(imported_app) as client:
        scheduled = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=_onvif_payload(
                name="scheduled-active",
                capability_refresh_enabled=True,
            ),
            headers=editor_headers,
        ).json()
        refresh_id = client.post(
            f"/streams/{scheduled['stream_id']}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]
    with imported_app.state.database.session_factory.begin() as session:
        refresh = session.get(StreamCapabilityRefresh, refresh_id)
        assert refresh is not None
        refresh.next_attempt_at = datetime.now(UTC) + timedelta(hours=1)
    assert idle.run_once() is False

    with TestClient(imported_app) as client:
        runtime_stream = _create_managed_stream(client, editor_headers)
        runtime_refresh = client.post(
            f"/streams/{runtime_stream}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]

    class BrokenEngine:
        def discover(self, _endpoint):
            raise TypeError("synthetic runtime defect")

    broken = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        BrokenEngine(),  # type: ignore[arg-type]
        worker_id="broken-worker",
    )
    with pytest.raises(CapabilityWorkerRuntimeError):
        broken.run_once()
    with imported_app.state.database.session_factory() as session:
        refresh = session.get(StreamCapabilityRefresh, runtime_refresh)
    assert refresh is not None
    assert refresh.status == "queued"
    assert refresh.reason_code == "capability_worker_error"


def test_capability_worker_detects_lost_lease(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        stream_id = _create_managed_stream(client, editor_headers)
        refresh_id = client.post(
            f"/streams/{stream_id}/capability-refreshes",
            headers=editor_headers,
        ).json()["refresh_id"]
    worker = CapabilityRefreshWorker(
        imported_app.state.database.session_factory,
        _StaticEngine(_result()),  # type: ignore[arg-type]
        worker_id="not-the-owner",
    )
    with pytest.raises(CapabilityWorkerLeaseError):
        worker._record_success(refresh_id, _result())
