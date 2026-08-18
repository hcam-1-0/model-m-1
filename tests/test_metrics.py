from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

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
    try:
        with TestClient(application) as client:
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
    assert 'route="/cameras/{camera_id}"' in body
    assert 'route="&lt;unmatched&gt;"' not in body
    assert 'route="<unmatched>"' in body
    assert 'status_class="2xx"' in body
    assert "synthetic:cctv-001" not in body
    assert "random-sensitive-path-123" not in body
    assert "must-not-appear" not in body
    assert viewer_headers["X-HCAM-Actor"] not in body
    assert METRICS_TOKEN not in body
