from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from hcam.audit.models import AuditEvent
from hcam.main import create_app
from hcam.settings import Settings
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


def _application(tmp_path: Path, *, enabled: bool) -> FastAPI:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / ('enabled.db' if enabled else 'disabled.db')).as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
            intelligence_generated_control_plane_enabled=enabled,
        )
    )
    application.state.database.create_schema()
    with application.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=2)
    return application


def _headers(
    role: str = "intelligence.editor",
    department: str = "Engineering Lab",
    *,
    reason: str | None = "Authorized generated Phase 4 control-plane test",
) -> dict[str, str]:
    headers = {
        "X-HCAM-Actor": "phase40-test-operator",
        "X-HCAM-Roles": role,
        "X-HCAM-Departments": department,
    }
    if reason is not None:
        headers["X-HCAM-Reason"] = reason
    return headers


def _rule_payload(*, department: str = "Engineering Lab") -> dict[str, object]:
    return {
        "department": department,
        "rule_key": "generated.restricted-zone-sequence",
        "version": 1,
        "graph": {
            "nodes": [
                {"node_id": "event_enter", "kind": "event", "inputs": []},
                {
                    "node_id": "predicate_zone",
                    "kind": "predicate",
                    "inputs": ["event_enter"],
                    "field": "event.zone_code",
                    "operator": "eq",
                    "value": "synthetic-zone-a",
                },
                {
                    "node_id": "window_short",
                    "kind": "window",
                    "inputs": ["predicate_zone"],
                    "duration_ms": 30_000,
                },
            ],
            "output_node_id": "window_short",
        },
        "intended_use": "Validate generated-only draft rule control-plane behavior",
        "policy_version": "sha256:" + "a" * 64,
        "retention_class": "derived.intelligence.standard",
    }


def _provider_payload(*, department: str = "Engineering Lab") -> dict[str, object]:
    return {
        "department": department,
        "provider_key": "generated.reference-catalogue",
        "policy_ref": "ref_" + "a" * 32,
        "destination_policy_ref": "ref_" + "b" * 32,
        "allowed_fields": ["record.external_id", "record.status_code"],
    }


def test_intelligence_routes_are_absent_when_control_plane_is_disabled(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path, enabled=False)
    try:
        with TestClient(application) as client:
            assert client.get("/intelligence-health").status_code == 404
            assert (
                client.post(
                    f"/streams/{synthetic_stream_id(1)}/intelligence-rules",
                    json=_rule_payload(),
                    headers=_headers(),
                ).status_code
                == 404
            )
    finally:
        application.state.database.dispose()


def test_intelligence_health_is_explicit_and_never_operational(tmp_path: Path) -> None:
    application = _application(tmp_path, enabled=True)
    try:
        with TestClient(application) as client:
            response = client.get("/intelligence-health")
            assert response.status_code == 200
            assert response.json() == {
                "control_plane_enabled": True,
                "runtime_state": "disabled",
                "provider_transport_state": "absent",
                "data_state": "generated_only",
                "operational_alerting": False,
                "reason_code": "p4_0_runtime_disabled",
            }
            assert response.headers["cache-control"] == "no-store"
    finally:
        application.state.database.dispose()


def test_rule_lifecycle_is_etag_guarded_audited_and_unpublished(tmp_path: Path) -> None:
    application = _application(tmp_path, enabled=True)
    try:
        with TestClient(application) as client:
            created = client.post(
                f"/streams/{synthetic_stream_id(1)}/intelligence-rules",
                json=_rule_payload(),
                headers=_headers(),
            )
            assert created.status_code == 201, created.text
            body = created.json()
            assert body["status"] == "draft"
            assert body["authority_class"] == "mandatory_review"
            assert body["operational"] is False
            assert body["generated_only"] is True
            assert body["runtime_state"] == "disabled"
            assert created.headers["etag"] == '"1"'
            assert created.headers["location"].endswith(body["rule_record_id"])
            assert created.headers["cache-control"] == "no-store"

            listed = client.get("/intelligence-rules", headers=_headers("intelligence.viewer"))
            assert listed.status_code == 200
            assert listed.json()["total"] == 1
            assert listed.json()["items"][0]["rule_id"] == body["rule_id"]

            fetched = client.get(
                f"/intelligence-rules/{body['rule_record_id']}",
                headers=_headers("intelligence.reviewer"),
            )
            assert fetched.status_code == 200
            assert fetched.headers["etag"] == '"1"'

            no_precondition = client.patch(
                f"/intelligence-rules/{body['rule_record_id']}",
                json={"status": "validated"},
                headers=_headers(),
            )
            assert no_precondition.status_code == 428
            malformed = client.patch(
                f"/intelligence-rules/{body['rule_record_id']}",
                json={"status": "validated"},
                headers={**_headers(), "If-Match": "1"},
            )
            assert malformed.status_code == 400

            updated = client.patch(
                f"/intelligence-rules/{body['rule_record_id']}",
                json={"status": "validated"},
                headers={**_headers("intelligence.approver"), "If-Match": '"1"'},
            )
            assert updated.status_code == 200, updated.text
            assert updated.json()["status"] == "validated"
            assert updated.headers["etag"] == '"2"'

            stale = client.patch(
                f"/intelligence-rules/{body['rule_record_id']}",
                json={"status": "retired"},
                headers={**_headers(), "If-Match": '"1"'},
            )
            assert stale.status_code == 412
            illegal = client.patch(
                f"/intelligence-rules/{body['rule_record_id']}",
                json={"status": "validated"},
                headers={**_headers(), "If-Match": '"2"'},
            )
            assert illegal.status_code == 409

        with application.state.database.session_factory() as session:
            actions = set(session.scalars(select(AuditEvent.action)).all())
            assert "intelligence.rule.create" in actions
            assert "intelligence.rule.status.update" in actions
            assert session.scalar(
                select(func.count()).select_from(StreamEventOutbox).where(
                    StreamEventOutbox.event_type
                    == "hcam.intelligence.rule.changed.v1",
                    StreamEventOutbox.published_at.is_(None),
                )
            ) == 2
    finally:
        application.state.database.dispose()


def test_rule_conflicts_and_department_isolation_fail_closed(tmp_path: Path) -> None:
    application = _application(tmp_path, enabled=True)
    try:
        with TestClient(application) as client:
            url = f"/streams/{synthetic_stream_id(1)}/intelligence-rules"
            assert client.post(url, json=_rule_payload(), headers=_headers()).status_code == 201
            assert client.post(url, json=_rule_payload(), headers=_headers()).status_code == 409
            hidden = client.post(
                url,
                json=_rule_payload(),
                headers=_headers(department="Another Department"),
            )
            assert hidden.status_code == 404
            missing = client.post(
                "/streams/str_ffffffffffffffffffffffffffffffff/intelligence-rules",
                json=_rule_payload(),
                headers=_headers(),
            )
            assert missing.status_code == 404
            listing = client.get(
                "/intelligence-rules", headers=_headers("intelligence.viewer", "Another Department")
            )
            assert listing.json()["total"] == 0
    finally:
        application.state.database.dispose()


def test_reference_provider_is_metadata_only_disabled_and_scoped(tmp_path: Path) -> None:
    application = _application(tmp_path, enabled=True)
    try:
        with TestClient(application) as client:
            created = client.post(
                "/reference-providers", json=_provider_payload(), headers=_headers()
            )
            assert created.status_code == 201, created.text
            body = created.json()
            assert body["enabled"] is False
            assert body["status"] == "disabled"
            assert body["transport_state"] == "absent"
            assert body["credential_state"] == "none"
            assert body["runtime_state"] == "disabled"
            assert client.post(
                "/reference-providers", json=_provider_payload(), headers=_headers()
            ).status_code == 409
            fetched = client.get(
                f"/reference-providers/{body['provider_id']}",
                headers=_headers("intelligence.viewer"),
            )
            assert fetched.status_code == 200
            hidden = client.get(
                f"/reference-providers/{body['provider_id']}",
                headers=_headers("intelligence.viewer", "Another Department"),
            )
            assert hidden.status_code == 404
            assert client.get(
                "/reference-providers", headers=_headers("intelligence.viewer")
            ).json()["total"] == 1
    finally:
        application.state.database.dispose()


def test_read_models_are_empty_bounded_generated_control_plane_views(tmp_path: Path) -> None:
    application = _application(tmp_path, enabled=True)
    try:
        with TestClient(application) as client:
            headers = _headers("intelligence.viewer")
            for path in ("/correlation-hypotheses", "/alerts", "/investigation-timelines"):
                response = client.get(path, headers=headers)
                assert response.status_code == 200
                assert response.json()["items"] == []
                assert response.headers["cache-control"] == "no-store"
                assert client.get(f"{path}?limit=501", headers=headers).status_code == 422
    finally:
        application.state.database.dispose()


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({}, 401),
        (_headers("camera.viewer"), 403),
        (_headers("not.a.role"), 401),
        (_headers(reason=None), 422),
        (_headers(reason=" invalid reason "), 422),
    ],
)
def test_mutation_authentication_role_and_reason_are_required(
    tmp_path: Path, headers: dict[str, str], expected: int
) -> None:
    application = _application(tmp_path, enabled=True)
    try:
        with TestClient(application) as client:
            response = client.post(
                f"/streams/{synthetic_stream_id(1)}/intelligence-rules",
                json=_rule_payload(),
                headers=headers,
            )
            assert response.status_code == expected
    finally:
        application.state.database.dispose()


def test_provider_request_rejects_destination_and_credential_input(tmp_path: Path) -> None:
    application = _application(tmp_path, enabled=True)
    try:
        with TestClient(application) as client:
            for field in ("url", "credential", "query_schema"):
                payload = _provider_payload()
                payload[field] = "not-accepted"
                response = client.post(
                    "/reference-providers", json=payload, headers=_headers()
                )
                assert response.status_code == 422
    finally:
        application.state.database.dispose()
