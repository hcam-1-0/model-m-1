from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from hcam.main import create_app
from hcam.security.auth import KNOWN_ROLES
from hcam.settings import Settings
from hcam.streams.lab import seed_synthetic_lab, synthetic_stream_id


def test_intelligence_roles_are_known_without_changing_camera_roles() -> None:
    assert {
        "camera.viewer",
        "camera.editor",
        "camera.controller",
        "platform.admin",
        "intelligence.viewer",
        "intelligence.editor",
        "intelligence.reviewer",
        "intelligence.approver",
    } == KNOWN_ROLES


def test_production_forbids_generated_intelligence_control_plane() -> None:
    with pytest.raises(ValueError, match="intelligence control plane"):
        Settings(
            database_url="postgresql+psycopg://localhost/unused",
            environment="production",
            intelligence_generated_control_plane_enabled=True,
        )


def test_environment_flag_defaults_false_and_parses_explicit_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HCAM_INTELLIGENCE_GENERATED_CONTROL_PLANE_ENABLED", raising=False)
    assert Settings.from_environment().intelligence_generated_control_plane_enabled is False
    monkeypatch.setenv("HCAM_INTELLIGENCE_GENERATED_CONTROL_PLANE_ENABLED", "true")
    assert Settings.from_environment().intelligence_generated_control_plane_enabled is True


def test_database_constraints_block_operational_rule_and_enabled_provider(
    tmp_path: Path,
) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'constraints.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
            intelligence_generated_control_plane_enabled=True,
        )
    )
    application.state.database.create_schema()
    with application.state.database.session_factory() as session:
        seed_synthetic_lab(session, count=1)
    headers = {
        "X-HCAM-Actor": "phase40-security-test",
        "X-HCAM-Roles": "intelligence.editor",
        "X-HCAM-Departments": "Engineering Lab",
        "X-HCAM-Reason": "Create generated records for constraint validation",
    }
    rule = {
        "department": "Engineering Lab",
        "rule_key": "constraint.rule",
        "version": 1,
        "graph": {
            "nodes": [{"node_id": "event", "kind": "event", "inputs": []}],
            "output_node_id": "event",
        },
        "intended_use": "Validate generated database guardrails",
        "policy_version": "sha256:" + "a" * 64,
        "retention_class": "derived.intelligence.standard",
    }
    provider = {
        "department": "Engineering Lab",
        "provider_key": "constraint.provider",
        "policy_ref": "ref_" + "a" * 32,
        "destination_policy_ref": "ref_" + "b" * 32,
        "allowed_fields": ["record.external_id"],
    }
    try:
        with TestClient(application) as client:
            assert client.post(
                f"/streams/{synthetic_stream_id(1)}/intelligence-rules",
                json=rule,
                headers=headers,
            ).status_code == 201
            assert client.post(
                "/reference-providers", json=provider, headers=headers
            ).status_code == 201
        with application.state.database.session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(text("UPDATE intelligence_rules SET operational = 1"))
                session.commit()
            session.rollback()
            with pytest.raises(IntegrityError):
                session.execute(text("UPDATE reference_providers SET enabled = 1"))
                session.commit()
    finally:
        application.state.database.dispose()


def test_openapi_has_no_operational_intelligence_mutation_surface(tmp_path: Path) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'openapi.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
            intelligence_generated_control_plane_enabled=True,
        )
    )
    try:
        paths = application.openapi()["paths"]
        assert "/correlation-hypotheses" in paths
        assert "/alerts" in paths
        assert "/investigation-timelines" in paths
        assert set(paths["/correlation-hypotheses"]) == {"get"}
        assert set(paths["/alerts"]) == {"get"}
        assert set(paths["/investigation-timelines"]) == {"get"}
        serialized = str(paths).lower()
        assert "dispatch" not in serialized
        assert "enforcement" not in serialized
        assert "provider-call" not in serialized
    finally:
        application.state.database.dispose()
