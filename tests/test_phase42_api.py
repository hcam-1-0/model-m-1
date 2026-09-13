from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from hcam.audit.models import AuditEvent
from hcam.intelligence.models import (
    IntelligenceRuleCompilation,
    IntelligenceRuleLifecycleEvent,
    IntelligenceRuleScopeMember,
)
from hcam.intelligence.rules.compiler import compile_rule
from hcam.intelligence.rules.contracts import RuleInputV1, VisualRuleDocumentV1
from hcam.intelligence.rules.runtime import run_and_store_generated_evidence
from hcam.main import create_app
from hcam.settings import Settings
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id
from hcam.streams.models import StreamEventOutbox


FIXTURE = Path("contracts/phase-4/p4-2/fixtures/generated-rule-documents-v1.json")


def _document() -> dict[str, object]:
    return deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8"))["documents"][0])


def _payload() -> dict[str, object]:
    return {"document": _document(), "scope_stream_ids": [synthetic_stream_id(1)]}


def _headers(
    role: str = "intelligence.editor", department: str = "Engineering Lab"
) -> dict[str, str]:
    return {
        "X-HCAM-Actor": "phase42-generated-operator",
        "X-HCAM-Roles": role,
        "X-HCAM-Departments": department,
        "X-HCAM-Reason": "Authorized generated Phase 4.2 rule control test",
    }


def _application(tmp_path: Path, *, enabled: bool = True) -> FastAPI:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'phase42-api.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
            intelligence_generated_control_plane_enabled=enabled,
            intelligence_generated_rule_evaluation_enabled=enabled,
        )
    )
    application.state.database.create_schema()
    with application.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=2)
    return application


def test_compile_preview_is_nonpersistent_bounded_and_no_store(tmp_path: Path) -> None:
    application = _application(tmp_path)
    document = _document()
    document["department"] = "Engineering Lab"
    try:
        with TestClient(application) as client:
            response = client.post(
                "/intelligence-rules/compile-preview",
                json={"document": document},
                headers=_headers(),
            )
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "no-store"
            assert response.json()["operational"] is False
            assert response.json()["canonical_ast"]["output_node_id"].startswith("n")
        with application.state.database.session_factory() as session:
            assert (
                session.scalar(
                    select(func.count()).select_from(IntelligenceRuleCompilation)
                )
                == 0
            )
    finally:
        application.state.database.dispose()


def test_rule_create_read_versions_and_lifecycle_are_immutable_and_audited(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    payload = _payload()
    payload["document"]["department"] = "Engineering Lab"
    try:
        with TestClient(application) as client:
            created = client.post(
                "/intelligence-rules", json=payload, headers=_headers()
            )
            assert created.status_code == 201, created.text
            body = created.json()
            record_id = body["rule_record_id"]
            assert body["status"] == "draft"
            assert body["runtime_state"] == "generated_evidence_only"
            assert body["operational"] is False and body["generated_only"] is True
            assert created.headers["etag"] == '"1"'

            fetched = client.get(
                f"/intelligence-rules/{record_id}",
                headers=_headers("intelligence.viewer"),
            )
            assert fetched.status_code == 200
            assert fetched.json()["semantic_digest"] == body["semantic_digest"]
            legacy_patch = client.patch(
                f"/intelligence-rules/{record_id}",
                json={"status": "validated"},
                headers={**_headers(), "If-Match": '"1"'},
            )
            assert legacy_patch.status_code == 409

            versions = client.get(
                f"/intelligence-rules/{record_id}/versions",
                headers=_headers("intelligence.viewer"),
            )
            assert versions.status_code == 200
            assert versions.json()["total"] == 1

            version_two = deepcopy(payload)
            version_two["document"]["version"] = 2
            created_two = client.post(
                "/intelligence-rules",
                json=version_two,
                headers=_headers(),
            )
            assert created_two.status_code == 201, created_two.text
            versions = client.get(
                f"/intelligence-rules/{record_id}/versions",
                headers=_headers("intelligence.viewer"),
            )
            assert [item["version"] for item in versions.json()["items"]] == [1, 2]

            compilation = client.get(
                f"/intelligence-rule-compilations/{body['compilation_id']}",
                headers=_headers("intelligence.viewer"),
            )
            assert compilation.status_code == 200, compilation.text
            assert compilation.json()["ast_digest"] == body["semantic_digest"]

            current_etag = '"1"'
            for action, role, status in (
                ("validate", "intelligence.editor", "validated"),
                ("approve", "intelligence.approver", "approved"),
                ("mark-shadow-eligible", "intelligence.approver", "shadow"),
                ("suspend", "intelligence.editor", "suspended"),
                ("retire", "intelligence.editor", "retired"),
            ):
                response = client.post(
                    f"/intelligence-rules/{record_id}/{action}",
                    headers={**_headers(role), "If-Match": current_etag},
                )
                assert response.status_code == 200, response.text
                assert response.json()["status"] == status
                assert response.json()["semantic_digest"] == body["semantic_digest"]
                current_etag = response.headers["etag"]
            assert current_etag == '"6"'

            assert (
                client.post(
                    f"/intelligence-rules/{record_id}/approve",
                    headers={
                        **_headers("intelligence.approver"),
                        "If-Match": current_etag,
                    },
                ).status_code
                == 409
            )

            evaluations = client.get(
                f"/intelligence-rules/{record_id}/evaluations",
                headers=_headers("intelligence.viewer"),
            )
            assert evaluations.status_code == 200 and evaluations.json()["items"] == []

        with application.state.database.session_factory() as session:
            assert (
                session.scalar(
                    select(func.count()).select_from(IntelligenceRuleCompilation)
                )
                == 2
            )
            assert (
                session.scalar(
                    select(func.count()).select_from(IntelligenceRuleScopeMember)
                )
                == 2
            )
            assert (
                session.scalar(
                    select(func.count()).select_from(IntelligenceRuleLifecycleEvent)
                )
                == 5
            )
            assert (
                session.scalar(select(func.count()).select_from(StreamEventOutbox)) == 7
            )
            actions = set(session.scalars(select(AuditEvent.action)).all())
            assert "intelligence.rule.p42.create" in actions
            assert "intelligence.rule.p42.approved" in actions
    finally:
        application.state.database.dispose()


def test_p42_control_is_default_off_scoped_and_requires_rbac_etag_reason(
    tmp_path: Path,
) -> None:
    disabled = _application(tmp_path, enabled=False)
    payload = _payload()
    payload["document"]["department"] = "Engineering Lab"
    try:
        with TestClient(disabled) as client:
            assert (
                client.post(
                    "/intelligence-rules", json=payload, headers=_headers()
                ).status_code
                == 404
            )
    finally:
        disabled.state.database.dispose()

    application = _application(tmp_path)
    try:
        with TestClient(application) as client:
            assert client.post("/intelligence-rules", json=payload).status_code == 401
            assert (
                client.post(
                    "/intelligence-rules",
                    json=payload,
                    headers=_headers("camera.viewer"),
                ).status_code
                == 403
            )
            wrong_scope = deepcopy(payload)
            wrong_scope["document"]["department"] = "Another Department"
            assert (
                client.post(
                    "/intelligence-rules", json=wrong_scope, headers=_headers()
                ).status_code
                == 404
            )
            created = client.post(
                "/intelligence-rules", json=payload, headers=_headers()
            )
            record_id = created.json()["rule_record_id"]
            assert (
                client.post(
                    f"/intelligence-rules/{record_id}/validate", headers=_headers()
                ).status_code
                == 428
            )
            assert (
                client.get(
                    f"/intelligence-rules/{record_id}",
                    headers=_headers("intelligence.viewer", "Another Department"),
                ).status_code
                == 404
            )
    finally:
        application.state.database.dispose()


def test_public_api_has_no_evaluation_start_activation_alert_or_action_route(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    try:
        paths = application.openapi()["paths"]
        assert set(paths["/intelligence-rules/{record_id}/evaluations"]) == {"get"}
        p42_paths = {
            path: value
            for path, value in paths.items()
            if path.startswith("/intelligence-rule")
        }
        serialized = json.dumps(p42_paths).lower()
        for prohibited in (
            "/activate",
            "evaluation-start",
            "dispatch",
            "enforcement",
            "provider-call",
            "notification-send",
        ):
            assert prohibited not in serialized
    finally:
        application.state.database.dispose()


def test_generated_runtime_stores_revision_for_read_only_api_projection(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    payload = _payload()
    payload["document"]["department"] = "Engineering Lab"
    observed_at = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
    try:
        with TestClient(application) as client:
            created = client.post(
                "/intelligence-rules", json=payload, headers=_headers()
            )
            assert created.status_code == 201, created.text
            record_id = created.json()["rule_record_id"]
            compiled = compile_rule(
                VisualRuleDocumentV1.model_validate(payload["document"])
            )
            rule_input = RuleInputV1(
                input_id="generated-runtime-input",
                input_kind="event",
                type_code="generated.vehicle.observed",
                department="Engineering Lab",
                partition_digest="sha256:" + "2" * 64,
                stream_id=synthetic_stream_id(1),
                occurred_at=observed_at,
                watermark_at=observed_at + timedelta(minutes=1),
                values={
                    "event_kind": "generated.vehicle.observed",
                    "object_class": "vehicle.car",
                    "confidence": 0.95,
                    "uncertainty": 0.05,
                    "direction": "forward",
                    "count": 1,
                    "rate": 1.0,
                    "chronology_complete": True,
                    "contradiction": False,
                },
            )
            with application.state.database.session_factory() as session:
                stored = run_and_store_generated_evidence(
                    session,
                    rule_record_id=record_id,
                    compiled=compiled,
                    inputs=[rule_input],
                    interval_start=observed_at,
                    recorded_at=observed_at + timedelta(minutes=2),
                )
            assert stored.state == "matched"
            response = client.get(
                f"/intelligence-rules/{record_id}/evaluations",
                headers=_headers("intelligence.viewer"),
            )
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "no-store"
            assert response.json()["total"] == 1
            assert response.json()["items"] == [stored.model_dump(mode="json")]

            shadow = client.get(
                f"/intelligence-rules/{record_id}/shadow-comparisons",
                headers=_headers("intelligence.viewer"),
            )
            assert shadow.status_code == 200
            assert shadow.json()["total"] == 0
            assert shadow.json()["items"] == []
    finally:
        application.state.database.dispose()


def test_rule_mutations_fail_closed_for_duplicate_scope_and_stale_version(
    tmp_path: Path,
) -> None:
    application = _application(tmp_path)
    payload = _payload()
    payload["document"]["department"] = "Engineering Lab"
    try:
        with TestClient(application) as client:
            missing_scope = deepcopy(payload)
            missing_scope["scope_stream_ids"] = ["str_" + "f" * 32]
            assert (
                client.post(
                    "/intelligence-rules", json=missing_scope, headers=_headers()
                ).status_code
                == 404
            )

            created = client.post(
                "/intelligence-rules", json=payload, headers=_headers()
            )
            assert created.status_code == 201, created.text
            record_id = created.json()["rule_record_id"]
            assert (
                client.post(
                    "/intelligence-rules", json=payload, headers=_headers()
                ).status_code
                == 409
            )
            assert (
                client.post(
                    f"/intelligence-rules/{record_id}/validate",
                    headers={**_headers(), "If-Match": '"99"'},
                ).status_code
                == 412
            )
            assert (
                client.get(
                    "/intelligence-rules/irlr_" + "f" * 32 + "/versions",
                    headers=_headers("intelligence.viewer"),
                ).status_code
                == 404
            )
    finally:
        application.state.database.dispose()
