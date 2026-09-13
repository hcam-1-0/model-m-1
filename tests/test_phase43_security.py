from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from hcam.intelligence.alerts.metrics import AlertMetrics
from hcam.intelligence.alerts.persistence import (
    AlertConflictError,
    AlertDisabledError,
    AlertNotFoundError,
    AlertPolicyError,
    AlertPreconditionError,
)
from hcam.intelligence.alerts.runtime import GeneratedAlertRuntime
from hcam.intelligence.alerts.service import problem_for
from hcam.settings import Settings
from tests.test_phase43_api import command, headers
from tests.test_phase43_persistence import application, seed_alert


def test_generated_alert_routes_require_auth_role_scope_reason_and_actor_binding(tmp_path) -> None:
    app = application(tmp_path)
    try:
        alert, _ = seed_alert(app)
        path = f"/generated-alerts/{alert.alert_id}"
        with TestClient(app) as client:
            assert client.get(path).status_code == 401
            assert client.get(path, headers=headers("camera.viewer")).status_code == 403
            scoped = headers("intelligence.viewer")
            scoped["X-HCAM-Departments"] = "Other Department"
            assert client.get(path, headers=scoped).status_code == 404

            missing_reason = headers(version=1)
            missing_reason.pop("X-HCAM-Reason")
            assert client.post(path + "/lifecycle", json=command("queue_review", 1), headers=missing_reason).status_code == 422

            mismatch = headers(version=1)
            mismatch["X-HCAM-Reason"] = "Different generated lifecycle reason"
            assert client.post(path + "/lifecycle", json=command("queue_review", 1), headers=mismatch).status_code == 400

            wrong_actor = command("queue_review", 1, actor="another-actor")
            response = client.post(
                path + "/lifecycle",
                json=wrong_actor,
                headers=headers(version=1),
            )
            assert response.status_code == 422
            assert response.headers["content-type"].startswith("application/problem+json")
            assert response.json()["reason_code"] == "alert_policy_denied"
    finally:
        app.state.database.dispose()


def test_if_match_is_mandatory_and_must_bind_the_body_version(tmp_path) -> None:
    app = application(tmp_path)
    try:
        alert, _ = seed_alert(app)
        path = f"/generated-alerts/{alert.alert_id}/lifecycle"
        with TestClient(app) as client:
            assert client.post(
                path, json=command("queue_review", 1), headers=headers()
            ).status_code == 422
            mismatch = client.post(
                path,
                json=command("queue_review", 1),
                headers=headers(version=2),
            )
            assert mismatch.status_code == 412
            assert mismatch.json()["reason_code"] == "alert_precondition_failed"
    finally:
        app.state.database.dispose()


def test_runtime_metrics_problem_taxonomy_and_production_gate_are_bounded() -> None:
    disabled = GeneratedAlertRuntime()
    with pytest.raises(RuntimeError, match="disabled"):
        disabled.executor()
    with pytest.raises(ValueError, match="forbidden in production"):
        GeneratedAlertRuntime(enabled=True, environment="production")
    assert GeneratedAlertRuntime(enabled=True, environment="test").executor() is not None
    with pytest.raises(ValueError, match="forbidden in production"):
        Settings(
            environment="production",
            database_url="postgresql+psycopg://generated:generated@localhost/hcam",
            intelligence_generated_alert_lifecycle_enabled=True,
        )
    with pytest.raises(ValueError, match="between 1 and 5"):
        Settings(environment="test", intelligence_generated_high_impact_quorum=6)

    metrics = AlertMetrics()
    metrics.record("proposal", "created")
    metrics.record("timer", "stale")
    assert metrics.snapshot() == {"proposal:created": 1, "timer:stale": 1}
    with pytest.raises(ValueError, match="outcome"):
        metrics.record("proposal", "camera-id-value")
    with pytest.raises(ValueError, match="operation"):
        metrics.record("camera-id-value", "created")

    expected = (
        (AlertConflictError("x"), 409),
        (AlertNotFoundError("x"), 404),
        (AlertDisabledError("x"), 503),
        (AlertPreconditionError("x"), 412),
        (AlertPolicyError("x"), 422),
    )
    for error, status in expected:
        problem = problem_for(error)
        assert problem.status == status
        assert problem.type.endswith(error.reason_code)
