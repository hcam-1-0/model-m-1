from __future__ import annotations

import ipaddress
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from threading import Thread

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from hcam.audit.models import AuditEvent
from hcam.audit.repository import AuditRepository
from hcam.security.auth import Principal
from hcam.streams.capabilities import CapabilityDiscoveryEngine
from hcam.streams.models import (
    OnvifOperationRun,
    StreamCapabilitySnapshot,
    StreamEndpoint,
    StreamHealthCurrent,
)
from hcam.streams.network import OnvifEgressRule
from hcam.streams.onvif import OnvifCapabilityDiscovery, OnvifResolutionError
from hcam.streams.onvif_simulator import handler_for
from hcam.streams.service import StreamConflictError, StreamService


def stream_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "primary",
        "adapter_kind": "synthetic",
        "protocol": "rtsp",
        "locator": "rtsp://mediamtx:8554/synthetic-002",
        "transport": "tcp",
        "is_primary": True,
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _allow_loopback_onvif(app, port: int):
    previous = app.state.settings
    app.state.settings = replace(
        previous,
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
    return previous


def test_registry_import_creates_legacy_primary_stream(
    imported_app, viewer_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        response = client.get("/streams", headers=viewer_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    stream = payload["items"][0]
    assert stream["camera_id"] == "synthetic:cctv-001"
    assert stream["adapter_kind"] == "legacy"
    assert stream["is_primary"] is True
    assert stream["locator"] == "https://camera.example.invalid/streams/1"
    assert stream["secret_configured"] is False
    assert stream["health"]["state"] == "unknown"


def test_editor_creates_primary_stream_and_projection(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        response = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(),
            headers=editor_headers,
        )
        camera_response = client.get(
            "/cameras/synthetic:cctv-002", headers=editor_headers
        )

    assert response.status_code == 201
    assert response.headers["etag"] == '"1"'
    stream = response.json()
    assert stream["stream_id"].startswith("str_")
    assert response.headers["location"] == f"/streams/{stream['stream_id']}"
    assert stream["health"]["state"] == "unknown"
    assert camera_response.json()["stream"]["selected_url"] == stream["locator"]

    with imported_app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.endpoint.create",
                AuditEvent.outcome == "success",
            )
        ).one()
    assert event.target_id == stream["stream_id"]
    assert "locator" not in event.context


def test_stream_locator_rejects_credentials_and_records_safe_failure(
    imported_app, editor_headers: dict[str, str]
) -> None:
    payload = stream_payload(
        locator="rtsp://operator:secret@mediamtx:8554/camera?token=private"
    )
    with TestClient(imported_app) as client:
        response = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=payload,
            headers=editor_headers,
        )

    assert response.status_code == 422
    assert "secret" not in response.text
    assert "private" not in response.text
    with imported_app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.endpoint.create",
                AuditEvent.outcome == "failure",
            )
        ).one()
    assert event.context["error_type"] == "StreamValidationError"


def test_viewer_cannot_create_or_queue_stream(
    imported_app, viewer_headers: dict[str, str]
) -> None:
    headers = {
        **viewer_headers,
        "X-HCAM-Reason": "Viewer cannot mutate stream state",
    }
    with TestClient(imported_app) as client:
        create_response = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(),
            headers=headers,
        )
        stream_id = client.get("/streams", headers=viewer_headers).json()["items"][0][
            "stream_id"
        ]
        queue_response = client.post(
            f"/streams/{stream_id}/probe", headers=headers
        )

    assert create_response.status_code == 403
    assert queue_response.status_code == 403


def test_editor_discovers_onvif_camera_capabilities_and_audits(
    imported_app, editor_headers: dict[str, str]
) -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), handler_for("rtsp://127.0.0.1:8554/synthetic-01")
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    previous_settings = _allow_loopback_onvif(imported_app, port)
    try:
        with TestClient(imported_app) as client:
            created = client.post(
                "/cameras/synthetic:cctv-002/streams",
                json=stream_payload(
                    adapter_kind="onvif",
                    protocol="http",
                    locator=f"http://{host}:{port}/onvif/media_service",
                ),
                headers=editor_headers,
            )
            stream_id = created.json()["stream_id"]
            response = client.post(
                f"/streams/{stream_id}/capabilities/discover",
                headers=editor_headers,
            )
    finally:
        imported_app.state.settings = previous_settings
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["stream_id"] == stream_id
    assert payload["camera_id"] == "synthetic:cctv-002"
    assert payload["source"] == "onvif_media_service"
    assert payload["media"]["maximum_profiles"] == 8
    assert len(payload["media"]["profiles"]) == 2
    assert payload["media"]["profiles"][0]["video_encoding"] == "H264"
    assert payload["media"]["profiles"][0]["ptz_configured"] is True

    with imported_app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.capabilities.discover",
                AuditEvent.outcome == "success",
            )
        ).one()
        run = session.scalars(
            select(OnvifOperationRun).where(
                OnvifOperationRun.stream_id == stream_id,
                OnvifOperationRun.operation_type == "capability_discover_sync",
            )
        ).one()
    assert event.target_id == stream_id
    assert event.context["camera_id"] == "synthetic:cctv-002"
    assert event.context["profile_count"] == 2
    assert event.context["configured_features"] == [
        "analytics",
        "audio",
        "metadata",
        "ptz",
    ]
    assert isinstance(event.context["request_id"], str)
    assert event.context["operation_id"] == run.operation_id
    assert run.outcome == "success"
    assert run.reason_code is None
    assert run.finished_at is not None
    assert run.duration_ms is not None
    assert "locator" not in event.context
    with imported_app.state.database.session_factory() as session:
        requested = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.capabilities.discover.requested",
                AuditEvent.outcome == "pending",
            )
        ).one()
    assert requested.target_id == stream_id
    assert requested.context["camera_id"] == "synthetic:cctv-002"
    assert requested.context["operation_id"] == run.operation_id
    assert "locator" not in requested.context


def test_capability_discovery_enforces_role_adapter_and_network_policy(
    imported_app,
    editor_headers: dict[str, str],
    viewer_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        synthetic = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(),
            headers=editor_headers,
        ).json()
        wrong_adapter = client.post(
            f"/streams/{synthetic['stream_id']}/capabilities/discover",
            headers=editor_headers,
        )
        denied = client.post(
            "/cameras/synthetic:cctv-001/streams",
            json=stream_payload(
                name="onvif-unlisted",
                adapter_kind="onvif",
                protocol="http",
                locator="http://unlisted.example.invalid/onvif/media_service",
                is_primary=False,
            ),
            headers=editor_headers,
        ).json()
        network_denied = client.post(
            f"/streams/{denied['stream_id']}/capabilities/discover",
            headers=editor_headers,
        )
        viewer_denied = client.post(
            f"/streams/{denied['stream_id']}/capabilities/discover",
            headers={
                **viewer_headers,
                "X-HCAM-Reason": "Viewer cannot initiate device discovery",
            },
        )

    assert wrong_adapter.status_code == 422
    assert network_denied.status_code == 422
    assert "network_policy_denied" in network_denied.text
    assert viewer_denied.status_code == 403


def test_capability_discovery_requires_reason_and_department_scope(
    imported_app,
    editor_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        traffic_stream = next(
            item
            for item in client.get("/streams", headers=editor_headers).json()["items"]
            if item["camera_id"] == "synthetic:cctv-001"
        )
        missing_reason = client.post(
            f"/streams/{traffic_stream['stream_id']}/capabilities/discover",
            headers={
                key: value
                for key, value in editor_headers.items()
                if key != "X-HCAM-Reason"
            },
        )
        outside_department = client.post(
            f"/streams/{traffic_stream['stream_id']}/capabilities/discover",
            headers={
                "X-HCAM-Actor": "operations-editor",
                "X-HCAM-Roles": "camera.editor",
                "X-HCAM-Departments": "operations",
                "X-HCAM-Reason": "Authorized scoped capability query",
            },
        )

    assert missing_reason.status_code == 422
    assert outside_department.status_code == 404


@pytest.mark.parametrize(
    ("overrides", "detail"),
    [
        (
            {
                "protocol": "rtsp",
                "locator": "rtsp://127.0.0.1:8554/onvif",
            },
            "requires HTTP(S)",
        ),
        (
            {
                "protocol": "http",
                "locator": "http://127.0.0.1:1/onvif/media_service",
                "secret_ref": "vault/camera-002",
            },
            "credentials are not available",
        ),
        (
            {
                "protocol": "http",
                "locator": "http://127.0.0.1:1/onvif/media_service",
                "enabled": False,
            },
            "Disabled streams",
        ),
    ],
)
def test_capability_discovery_rejects_ineligible_onvif_streams(
    imported_app,
    editor_headers: dict[str, str],
    overrides: dict[str, object],
    detail: str,
) -> None:
    with TestClient(imported_app) as client:
        created = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(adapter_kind="onvif", **overrides),
            headers=editor_headers,
        ).json()
        response = client.post(
            f"/streams/{created['stream_id']}/capabilities/discover",
            headers=editor_headers,
        )

    assert response.status_code == 422
    assert detail in response.json()["detail"]


def test_capability_discovery_normalizes_transport_failure_and_audits(
    imported_app,
    editor_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_discovery(
        _discovery: OnvifCapabilityDiscovery, _service_url: str
    ) -> None:
        raise OnvifResolutionError("unreachable")

    monkeypatch.setattr(OnvifCapabilityDiscovery, "discover", fail_discovery)
    previous_settings = _allow_loopback_onvif(imported_app, 1)
    try:
        with TestClient(imported_app) as client:
            created = client.post(
                "/cameras/synthetic:cctv-002/streams",
                json=stream_payload(
                    adapter_kind="onvif",
                    protocol="http",
                    locator="http://127.0.0.1:1/onvif/media_service",
                ),
                headers=editor_headers,
            ).json()
            response = client.post(
                f"/streams/{created['stream_id']}/capabilities/discover",
                headers=editor_headers,
            )
    finally:
        imported_app.state.settings = previous_settings

    assert response.status_code == 502
    assert response.json()["detail"].endswith("(unreachable)")
    with imported_app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.capabilities.discover",
                AuditEvent.outcome == "failure",
            )
        ).one()
        run = session.scalars(
            select(OnvifOperationRun).where(
                OnvifOperationRun.stream_id == created["stream_id"],
                OnvifOperationRun.operation_type == "capability_discover_sync",
            )
        ).one()
    assert event.context["error_type"] == "CapabilityDiscoveryError"
    assert isinstance(event.context["request_id"], str)
    assert event.context["operation_id"] == run.operation_id
    assert run.outcome == "failure"
    assert run.reason_code == "unreachable"
    assert run.finished_at is not None


def test_capability_discovery_fails_closed_before_network_when_intent_audit_fails(
    imported_app,
    editor_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    network_called = False
    original_record = AuditRepository.record

    def fail_requested_audit(self, **kwargs):
        if kwargs["action"] == "stream.capabilities.discover.requested":
            raise SQLAlchemyError("synthetic requested-audit failure")
        return original_record(self, **kwargs)

    def unexpected_discovery(self, endpoint):
        nonlocal network_called
        network_called = True
        raise AssertionError("discovery must not run without durable intent")

    monkeypatch.setattr(AuditRepository, "record", fail_requested_audit)
    monkeypatch.setattr(CapabilityDiscoveryEngine, "discover", unexpected_discovery)

    with TestClient(imported_app) as client:
        created = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(
                adapter_kind="onvif",
                protocol="http",
                locator="http://127.0.0.1:1/onvif/media_service",
            ),
            headers=editor_headers,
        ).json()
        response = client.post(
            f"/streams/{created['stream_id']}/capabilities/discover",
            headers=editor_headers,
        )

    assert response.status_code == 502
    assert response.json()["detail"].endswith("(capability_audit_unavailable)")
    assert network_called is False
    with imported_app.state.database.session_factory() as session:
        runs = session.scalars(
            select(OnvifOperationRun).where(
                OnvifOperationRun.stream_id == created["stream_id"],
                OnvifOperationRun.operation_type == "capability_discover_sync",
            )
        ).all()
    assert runs == []


def test_capability_discovery_sanitizes_unexpected_adapter_failure(
    imported_app,
    editor_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_unexpectedly(self, endpoint):
        raise RuntimeError("camera-password-must-not-leak")

    monkeypatch.setattr(CapabilityDiscoveryEngine, "discover", fail_unexpectedly)
    with TestClient(imported_app) as client:
        created = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(
                adapter_kind="onvif",
                protocol="http",
                locator="http://127.0.0.1:1/onvif/media_service",
            ),
            headers=editor_headers,
        ).json()
        response = client.post(
            f"/streams/{created['stream_id']}/capabilities/discover",
            headers=editor_headers,
        )

    assert response.status_code == 502
    assert response.json()["detail"].endswith("(capability_discovery_error)")
    assert "camera-password-must-not-leak" not in response.text
    with imported_app.state.database.session_factory() as session:
        run = session.scalars(
            select(OnvifOperationRun).where(
                OnvifOperationRun.stream_id == created["stream_id"],
                OnvifOperationRun.operation_type == "capability_discover_sync",
            )
        ).one()
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.capabilities.discover",
                AuditEvent.target_id == created["stream_id"],
            )
        ).one()
    assert run.outcome == "failure"
    assert run.reason_code == "capability_discovery_error"
    assert event.context["error_type"] == "CapabilityDiscoveryError"
    assert "camera-password-must-not-leak" not in str(event.context)


def test_capability_discovery_leaves_pending_intent_when_completion_audit_fails(
    imported_app,
    editor_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), handler_for("rtsp://127.0.0.1:8554/synthetic-01")
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    previous_settings = _allow_loopback_onvif(imported_app, port)
    original_record = AuditRepository.record

    def fail_completion_audit(self, **kwargs):
        if kwargs["action"] == "stream.capabilities.discover":
            raise SQLAlchemyError("synthetic completion-audit failure")
        return original_record(self, **kwargs)

    monkeypatch.setattr(AuditRepository, "record", fail_completion_audit)
    try:
        with TestClient(imported_app) as client:
            created = client.post(
                "/cameras/synthetic:cctv-002/streams",
                json=stream_payload(
                    adapter_kind="onvif",
                    protocol="http",
                    locator=f"http://{host}:{port}/onvif/media_service",
                ),
                headers=editor_headers,
            ).json()
            response = client.post(
                f"/streams/{created['stream_id']}/capabilities/discover",
                headers=editor_headers,
            )
    finally:
        imported_app.state.settings = previous_settings
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert response.status_code == 502
    assert response.json()["detail"].endswith("(capability_audit_unavailable)")
    with imported_app.state.database.session_factory() as session:
        requested = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.capabilities.discover.requested",
                AuditEvent.target_id == created["stream_id"],
            )
        ).one()
        completed = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.capabilities.discover",
                AuditEvent.target_id == created["stream_id"],
            )
        ).all()
        run = session.scalars(
            select(OnvifOperationRun).where(
                OnvifOperationRun.stream_id == created["stream_id"],
                OnvifOperationRun.operation_type == "capability_discover_sync",
            )
        ).one()
        snapshots = session.scalars(
            select(StreamCapabilitySnapshot).where(
                StreamCapabilitySnapshot.stream_id == created["stream_id"]
            )
        ).all()
    assert requested.outcome == "pending"
    assert requested.context["operation_id"] == run.operation_id
    assert run.outcome == "pending"
    assert run.finished_at is None
    assert run.duration_ms is None
    assert snapshots == []
    assert completed == []


def test_stream_update_requires_etag_and_promotes_new_primary(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        create_response = client.post(
            "/cameras/synthetic:cctv-001/streams",
            json=stream_payload(
                name="secondary",
                locator="rtsp://mediamtx:8554/synthetic-secondary",
                is_primary=False,
            ),
            headers=editor_headers,
        )
        stream = create_response.json()
        missing_etag = client.patch(
            f"/streams/{stream['stream_id']}",
            json={"is_primary": True},
            headers=editor_headers,
        )
        promoted = client.patch(
            f"/streams/{stream['stream_id']}",
            json={"is_primary": True},
            headers={**editor_headers, "If-Match": create_response.headers["etag"]},
        )
        streams = client.get(
            "/streams?camera_id=synthetic:cctv-001", headers=editor_headers
        ).json()["items"]

    assert missing_etag.status_code == 428
    assert promoted.status_code == 200
    assert promoted.headers["etag"] == '"2"'
    assert promoted.json()["is_primary"] is True
    assert sum(item["is_primary"] for item in streams) == 1


def test_queue_probe_and_read_empty_history(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        stream_id = client.get("/streams", headers=editor_headers).json()["items"][0][
            "stream_id"
        ]
        queued = client.post(
            f"/streams/{stream_id}/probe", headers=editor_headers
        )
        history = client.get(
            f"/streams/{stream_id}/probes", headers=editor_headers
        )
        health = client.get(
            f"/streams/{stream_id}/health", headers=editor_headers
        )

    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"
    assert history.status_code == 200
    assert history.json()["total"] == 0
    assert health.json()["state"] == "unknown"


def test_department_scope_hides_streams(imported_app) -> None:
    headers = {
        "X-HCAM-Actor": "operations-viewer",
        "X-HCAM-Roles": "camera.viewer",
        "X-HCAM-Departments": "operations",
    }
    with TestClient(imported_app) as client:
        response = client.get("/streams", headers=headers)

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_stream_tables_have_current_health_for_every_endpoint(imported_app) -> None:
    with imported_app.state.database.session_factory() as session:
        endpoint_ids = set(session.scalars(select(StreamEndpoint.stream_id)).all())
        health_ids = set(session.scalars(select(StreamHealthCurrent.stream_id)).all())
    assert endpoint_ids
    assert endpoint_ids == health_ids


def test_stream_routes_enforce_lookup_etag_and_primary_invariants(
    imported_app, editor_headers: dict[str, str]
) -> None:
    missing_id = "str_" + "f" * 32
    with TestClient(imported_app) as client:
        listed = client.get("/streams", headers=editor_headers).json()["items"]
        primary = listed[0]
        stream_id = primary["stream_id"]

        assert client.get(f"/streams/{missing_id}", headers=editor_headers).status_code == 404
        assert (
            client.get(f"/streams/{missing_id}/health", headers=editor_headers).status_code
            == 404
        )
        assert (
            client.get(f"/streams/{missing_id}/probes", headers=editor_headers).status_code
            == 404
        )

        malformed = client.patch(
            f"/streams/{stream_id}",
            json={"name": "changed"},
            headers={**editor_headers, "If-Match": "1"},
        )
        stale = client.patch(
            f"/streams/{stream_id}",
            json={"name": "changed"},
            headers={**editor_headers, "If-Match": '"99"'},
        )
        no_change = client.patch(
            f"/streams/{stream_id}",
            json={"name": primary["name"]},
            headers={**editor_headers, "If-Match": '"1"'},
        )
        demote = client.patch(
            f"/streams/{stream_id}",
            json={"is_primary": False},
            headers={**editor_headers, "If-Match": '"1"'},
        )

    assert malformed.status_code == 400
    assert stale.status_code == 412
    assert no_change.status_code == 422
    assert demote.status_code == 422


def test_stream_mutations_reject_conflicts_disabled_probes_and_bad_locators(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        existing = client.get("/streams", headers=editor_headers).json()["items"][0]
        stream_id = existing["stream_id"]
        duplicate_primary = client.post(
            "/cameras/synthetic:cctv-001/streams",
            json=stream_payload(locator="rtsp://mediamtx:8554/duplicate"),
            headers=editor_headers,
        )
        missing_camera = client.post(
            "/cameras/missing-camera/streams",
            json=stream_payload(),
            headers=editor_headers,
        )
        protocol_mismatch = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(protocol="hls", locator="rtsp://mediamtx/live"),
            headers=editor_headers,
        )
        disabled = client.patch(
            f"/streams/{stream_id}",
            json={"enabled": False},
            headers={**editor_headers, "If-Match": '"1"'},
        )
        queue_disabled = client.post(
            f"/streams/{stream_id}/probe", headers=editor_headers
        )

    assert duplicate_primary.status_code == 409
    assert missing_camera.status_code == 404
    assert protocol_mismatch.status_code == 422
    assert disabled.status_code == 200
    assert queue_disabled.status_code == 422

    with imported_app.state.database.session_factory.begin() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        endpoint.enabled = True
        endpoint.lease_owner = "worker-active"
        endpoint.lease_until = datetime.now(UTC) + timedelta(minutes=1)

    with TestClient(imported_app) as client:
        busy = client.post(f"/streams/{stream_id}/probe", headers=editor_headers)
        filtered = client.get(
            "/streams?protocol=hls&state=unknown&enabled=true",
            headers=editor_headers,
        )
    assert busy.status_code == 409
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 0


def test_hls_stream_update_requires_tcp_and_matching_locator(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        created = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(
                adapter_kind="hls",
                protocol="hls",
                locator="https://media.example.invalid/live.m3u8",
                is_primary=False,
            ),
            headers=editor_headers,
        )
        assert created.status_code == 201
        stream_id = created.json()["stream_id"]
        etag = created.headers["etag"]
        bad_transport = client.patch(
            f"/streams/{stream_id}",
            json={"transport": "udp"},
            headers={**editor_headers, "If-Match": etag},
        )
        bad_locator = client.patch(
            f"/streams/{stream_id}",
            json={"locator": "rtsp://media.example.invalid/live"},
            headers={**editor_headers, "If-Match": etag},
        )
    assert bad_transport.status_code == 422
    assert bad_locator.status_code == 422


def test_queue_probe_normalizes_worker_version_race_to_conflict() -> None:
    class BeginRaisesStaleData:
        def __enter__(self):
            raise StaleDataError("simulated worker race")

        def __exit__(self, *_args) -> None:
            return None

    class SessionStub:
        def begin(self) -> BeginRaisesStaleData:
            return BeginRaisesStaleData()

    service = StreamService(SessionStub())  # type: ignore[arg-type]
    service._record_failure = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    principal = Principal(
        actor_id="test-editor",
        roles=frozenset({"camera.editor"}),
        departments=frozenset({"*"}),
        authentication_method="test",
    )
    with pytest.raises(StreamConflictError, match="queueing"):
        service.queue_probe(
            "str_" + "a" * 32,
            principal=principal,
            reason="Authorized synthetic probe race",
            request_id="request-test",
        )
