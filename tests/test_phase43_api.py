from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from hcam.intelligence.alerts.canonical import stable_id
from tests.test_phase43_persistence import application, seed_alert


def headers(
    role: str = "platform.admin",
    actor: str = "phase43-admin",
    version: int | None = None,
) -> dict[str, str]:
    value = {
        "X-HCAM-Actor": actor,
        "X-HCAM-Roles": role,
        "X-HCAM-Departments": "*",
        "X-HCAM-Reason": "Generated Phase 4.3 lifecycle decision",
    }
    if version is not None:
        value["If-Match"] = f'"{version}"'
    return value


def command(action: str, version: int, *, actor: str = "phase43-admin") -> dict[str, object]:
    return {
        "contract_type": "hcam.p4-3.alert-lifecycle-command.v1",
        "command_id": f"generated.command.{action}.{version}",
        "action": action,
        "expected_version": version,
        "actor_id": actor,
        "reason": "Generated Phase 4.3 lifecycle decision",
        "evidence_digest": None,
        "target_alert_id": None,
        "assignee_id": None,
    }


def test_generated_alert_read_lifecycle_review_and_history_api(tmp_path) -> None:
    app = application(tmp_path)
    try:
        alert, evaluation = seed_alert(app)
        with TestClient(app) as client:
            response = client.get(f"/generated-alerts/{alert.alert_id}", headers=headers("intelligence.viewer"))
            assert response.status_code == 200
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["etag"] == '"1"'

            queued = client.post(
                f"/generated-alerts/{alert.alert_id}/lifecycle",
                json=command("queue_review", 1),
                headers=headers(version=1),
            )
            assert queued.status_code == 200, queued.text
            assert queued.json()["state"] == "queued_review"

            started = client.post(
                f"/generated-alerts/{alert.alert_id}/lifecycle",
                json=command("start_review", 2),
                headers=headers(version=2),
            )
            assert started.status_code == 200, started.text
            assert started.json()["state"] == "under_review"

            policy = client.get(
                f"/generated-alerts/{alert.alert_id}/review-policy",
                headers=headers("intelligence.viewer"),
            )
            assert policy.status_code == 200, policy.text
            policy_body = policy.json()
            review = client.post(
                f"/generated-alerts/{alert.alert_id}/reviews",
                json={
                    "contract_type": "hcam.p4-3.alert-review-decision.v1",
                    "decision_id": stable_id("ardc", alert.alert_id, "approve"),
                    "alert_id": alert.alert_id,
                    "department": alert.department,
                    "policy_id": policy_body["policy_id"],
                    "policy_version": policy_body["policy_version"],
                    "reviewer_id": "phase43-admin",
                    "reviewer_role": "platform.admin",
                    "decision": "approve",
                    "evidence_digest": evaluation.evaluation_digest,
                    "reason": "Generated Phase 4.3 lifecycle decision",
                    "supersedes_decision_id": None,
                    "recorded_at": datetime(2026, 9, 4, 12, 5, tzinfo=UTC).isoformat(),
                    "generated_only": True,
                    "operational": False,
                },
                headers=headers(version=3),
            )
            assert review.status_code == 200, review.text
            assert review.json()["quorum_outcome"] == "approved"
            assert review.json()["alert"]["state"] == "accepted"
            assert review.headers["etag"] == '"4"'

            history = client.get(
                f"/generated-alerts/{alert.alert_id}/lifecycle",
                headers=headers("intelligence.viewer"),
            )
            assert history.status_code == 200
            assert [item["new_state"] for item in history.json()["items"]] == [
                "queued_review",
                "under_review",
                "accepted",
            ]
            listed = client.get("/generated-alerts", headers=headers("intelligence.viewer"))
            assert listed.status_code == 200 and listed.json()["total"] == 1
    finally:
        app.state.database.dispose()


def test_generated_alert_api_is_default_off_and_has_no_operational_routes(tmp_path) -> None:
    disabled = application(tmp_path, enabled=False)
    try:
        with TestClient(disabled) as client:
            assert "/generated-alerts" not in client.app.openapi()["paths"]
    finally:
        disabled.state.database.dispose()

    app = application(tmp_path)
    try:
        generated_paths = {
            path: methods
            for path, methods in app.openapi()["paths"].items()
            if path.startswith("/generated-alerts")
        }
        serialized = str(generated_paths).lower()
        for prohibited in ("dispatch", "enforce", "notify", "provider", "worker-start", "sentinel"):
            assert prohibited not in serialized
    finally:
        app.state.database.dispose()
