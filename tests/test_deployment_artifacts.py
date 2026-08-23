from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_container_runtime_is_pinned_non_root_and_health_checked() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.12.12-slim-bookworm@sha256:" in dockerfile
    assert "USER ${HCAM_UID}:${HCAM_GID}" in dockerfile
    assert "ARG HCAM_UID=10001" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "/health/live" in dockerfile
    assert "--no-access-log" in dockerfile
    assert "HCAM_ENVIRONMENT=production" in dockerfile
    assert "COPY pyproject.toml README.md uv.lock ./" in dockerfile
    assert '"uv==${UV_VERSION}"' in dockerfile
    assert "RUN mkdir -p /dist" in dockerfile
    assert "uv sync --locked --extra dev --no-install-project" in dockerfile
    assert "uv export --locked --no-dev --extra postgres --no-emit-project" in dockerfile
    assert "python -m build --no-isolation" in dockerfile
    assert "--wheel --outdir /dist" in dockerfile
    assert "--require-hashes" in dockerfile
    assert "--no-deps /tmp/dist/*.whl" in dockerfile
    assert 'CMD ["python", "-m", "uvicorn"' in dockerfile


def test_docker_context_excludes_unnecessary_or_sensitive_paths() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert dockerignore.startswith("**\n")
    assert "!app/**" in dockerignore
    assert "!migrations/**" in dockerignore
    assert "!uv.lock" in dockerignore
    assert "!.env" not in dockerignore
    assert "!tests" not in dockerignore
    assert "!fixtures" not in dockerignore
    assert "!.git" not in dockerignore


def test_compose_stack_uses_files_for_secrets_and_hardened_api_runtime() -> None:
    compose = (ROOT / "deploy" / "compose.phase1.yaml").read_text(
        encoding="utf-8"
    )

    assert "postgres:18-alpine@sha256:" in compose
    assert "HCAM_DATABASE_URL_FILE: /run/secrets/database_url" in compose
    assert "HCAM_METRICS_TOKEN_FILE: /run/secrets/metrics_token" in compose
    assert "POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password" in compose
    assert "condition: service_completed_successfully" in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "cap_drop:" in compose
    assert "max-size: 10m" in compose
    assert "127.0.0.1:${HCAM_PORT:-8000}:8000" in compose
    assert "POSTGRES_PASSWORD:" not in compose
    assert "phase1-local-postgres-password" not in compose


def test_grafana_dashboard_is_valid_and_uses_bounded_hcam_metrics() -> None:
    path = ROOT / "deploy" / "observability" / "hcam-phase1-overview.json"
    dashboard = json.loads(path.read_text(encoding="utf-8"))
    expressions = [
        target["expr"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    ]

    assert dashboard["uid"] == "hcam-phase1-overview"
    assert dashboard["editable"] is False
    assert len(dashboard["panels"]) == 5
    assert any("hcam_http_requests_total" in expression for expression in expressions)
    assert any(
        "hcam_http_request_duration_seconds_bucket" in expression
        for expression in expressions
    )
    assert "camera_id" not in json.dumps(dashboard)
    assert "synthetic:cctv" not in json.dumps(dashboard)


def test_phase2_dashboard_and_alerts_use_only_bounded_stream_metrics() -> None:
    dashboard_path = (
        ROOT / "deploy" / "observability" / "hcam-phase2-streams.json"
    )
    alerts_path = ROOT / "deploy" / "observability" / "hcam-phase2-alerts.yml"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    alerts = alerts_path.read_text(encoding="utf-8")
    serialized = json.dumps(dashboard)

    assert dashboard["uid"] == "hcam-phase2-streams"
    assert dashboard["editable"] is False
    assert len(dashboard["panels"]) == 8
    assert "hcam_stream_health_state_total" in serialized
    assert "hcam_stream_probe_due_total" in serialized
    assert "hcam_stream_outbox_unpublished_total" in serialized
    assert "hcam_capability_refresh_queue_depth" in serialized
    assert "hcam_capability_snapshot_stale_total" in serialized
    assert "hcam_capability_refresh_expired_leases_total" in serialized
    assert "hcam_capability_refresh_lease_recoveries_recent_total" in serialized
    assert "camera_id" not in serialized + alerts
    assert "stream_id" not in serialized + alerts
    assert "HcamStreamFleetUnhealthy" in alerts
    assert "HcamStreamProbeQueueBacklog" in alerts
    assert "HcamStreamOutboxBacklog" in alerts
    assert "HcamCapabilityWorkerLeaseRecovery" in alerts
    assert "hcam_capability_refresh_lease_recoveries_recent_total" in alerts
