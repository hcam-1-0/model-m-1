from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.importer import RegistryImporter
from hcam.main import create_app
from hcam.settings import Settings


METRICS_TOKEN = "phase1-metrics-token-0123456789abcdef"


def test_metrics_endpoint_is_disabled_by_default(app) -> None:
    with TestClient(app) as client:
        response = client.get("/internal/metrics")

    assert response.status_code == 404


def test_metrics_endpoint_requires_bearer_token(tmp_path: Path) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'metrics-auth.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            metrics_enabled=True,
            metrics_token=METRICS_TOKEN,
        )
    )
    application.state.database.create_schema()
    try:
        with TestClient(application) as client:
            missing = client.get("/internal/metrics")
            invalid = client.get(
                "/internal/metrics",
                headers={"Authorization": "Bearer wrong-token"},
            )
    finally:
        application.state.database.dispose()

    assert missing.status_code == 401
    assert missing.headers["WWW-Authenticate"] == "Bearer"
    assert invalid.status_code == 401
    assert METRICS_TOKEN not in missing.text + invalid.text


def test_metrics_use_bounded_route_labels_and_exclude_sensitive_values(
    tmp_path: Path,
    seed_file: Path,
    viewer_headers: dict[str, str],
    editor_headers: dict[str, str],
) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'metrics.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
            metrics_enabled=True,
            metrics_token=METRICS_TOKEN,
        )
    )
    application.state.database.create_schema()
    RegistryImporter(application.state.database.session_factory).import_file(seed_file)
    with application.state.database.session_factory.begin() as session:
        AuditRepository(session).record(
            action="stream.capability_refresh.lease_recovered",
            target_type="stream_capability_refresh",
            target_id="sensitive-refresh-id-must-not-appear",
            source="hcam.capability-worker",
            reason="Expired capability refresh worker lease recovered",
            outcome="success",
            context={"stream_id": "sensitive-stream-id-must-not-appear"},
        )
    try:
        with TestClient(application) as client:
            stream_id = client.get("/streams", headers=viewer_headers).json()[
                "items"
            ][0]["stream_id"]
            assignment = client.post(
                f"/streams/{stream_id}/analytics-assignments",
                json={
                    "capability": "object_detection",
                    "pipeline": {
                        "id": "metrics-pipeline",
                        "version": "sha256:" + "a" * 64,
                    },
                    "models": [
                        {
                            "id": "metrics-detector-must-not-appear",
                            "version": "sha256:" + "b" * 64,
                        }
                    ],
                    "taxonomy_version": "hcam.object.v1",
                    "policy_version": "sha256:" + "c" * 64,
                    "configuration_digest": "sha256:" + "d" * 64,
                    "minimum_confidence": 0.65,
                    "sampling_fps": 5.0,
                    "maximum_queue_age_ms": 2_000,
                    "geometry_refs": [],
                    "retention_class": "derived.analytics.standard",
                    "approval_record_id": "DR-P3.0-METRICS",
                },
                headers={
                    **editor_headers,
                    "X-HCAM-Reason": "Validate bounded analytics metrics",
                },
            )
            rejected_update = client.patch(
                f"/analytics-assignments/{assignment.json()['assignment_id']}",
                json={
                    "minimum_confidence": 0.7,
                    "configuration_digest": "sha256:" + "e" * 64,
                },
                headers={
                    **editor_headers,
                    "If-Match": assignment.headers["ETag"],
                    "X-HCAM-Reason": (
                        "Use https://credential-must-not-appear.invalid/config"
                    ),
                },
            )
            camera = client.get(
                "/cameras/synthetic:cctv-001?token=must-not-appear",
                headers=viewer_headers,
            )
            not_found = client.get("/random-sensitive-path-123")
            metrics = client.get(
                "/internal/metrics",
                headers={"Authorization": f"Bearer {METRICS_TOKEN}"},
            )
    finally:
        application.state.database.dispose()

    assert camera.status_code == 200
    assert assignment.status_code == 201
    assert rejected_update.status_code == 422
    assert "credential-must-not-appear" not in rejected_update.text
    assert not_found.status_code == 404
    assert metrics.status_code == 200
    assert metrics.headers["Cache-Control"] == "no-store"
    assert "text/plain" in metrics.headers["Content-Type"]
    body = metrics.text
    assert "hcam_http_requests_total" in body
    assert "hcam_http_request_duration_seconds_bucket" in body
    assert "hcam_stream_health_state_total" in body
    assert "hcam_stream_probe_due_total" in body
    assert "hcam_stream_outbox_unpublished_total" in body
    assert "hcam_capability_refresh_jobs_retained_total" in body
    assert "hcam_capability_refresh_queue_depth" in body
    assert "hcam_capability_refresh_duration_milliseconds" in body
    assert "hcam_capability_refresh_retries_retained_total" in body
    assert "hcam_capability_snapshot_stale_total" in body
    assert "hcam_capability_refresh_expired_leases_total" in body
    assert "hcam_capability_refresh_lease_recoveries_recent_total 1.0" in body
    assert "hcam_capability_refresh_failures_retained_total" in body
    assert "hcam_onvif_operations_retained_total" in body
    assert (
        'hcam_onvif_operations_retained_total{operation="capability_discover_sync",'
        'outcome="pending"} 0.0'
    ) in body
    assert "hcam_onvif_control_leases_active_total" in body
    assert "hcam_onvif_operation_failures_recent_total" in body
    assert "hcam_analytics_assignments_total 1.0" in body
    assert "hcam_analytics_assignments_blocked_total 1.0" in body
    assert "hcam_analytics_assignment_revisions_retained_total 1.0" in body
    assert "hcam_analytics_outbox_unpublished_total 1.0" in body
    assert (
        'hcam_analytics_assignment_failures_recent_total{operation="create"} 0.0'
        in body
    )
    assert (
        'hcam_analytics_assignment_failures_recent_total{operation="update"} 1.0'
        in body
    )
    assert 'route="/cameras/{camera_id}"' in body
    assert 'route="&lt;unmatched&gt;"' not in body
    assert 'route="<unmatched>"' in body
    assert 'status_class="2xx"' in body
    assert "synthetic:cctv-001" not in body
    assert "random-sensitive-path-123" not in body
    assert "must-not-appear" not in body
    assert "sensitive-refresh-id-must-not-appear" not in body
    assert "sensitive-stream-id-must-not-appear" not in body
    assert "metrics-detector-must-not-appear" not in body
    assert "credential-must-not-appear" not in body
    assert assignment.json()["assignment_id"] not in body
    assert viewer_headers["X-HCAM-Actor"] not in body
    assert METRICS_TOKEN not in body
