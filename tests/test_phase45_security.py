from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hcam.intelligence.investigations.service import (
    InvestigationDisabledError,
    InvestigationError,
    InvestigationService,
)
from hcam.main import create_app
from hcam.security.auth import Principal
from hcam.security.auth import (
    AUTHENTICATION_ROLES,
    CURRENT_AUTHENTICATION_ROLES,
    INVESTIGATION_ROLES,
)
from hcam.settings import Settings


def test_runtime_is_default_off_and_production_forbidden(tmp_path) -> None:
    app = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'disabled.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
        )
    )
    with TestClient(app) as client:
        response = client.get(
            "/investigations/health",
            headers={
                "X-HCAM-Actor": "generated.reader",
                "X-HCAM-Roles": "investigation.read",
                "X-HCAM-Departments": "Generated-Department-0",
            },
        )
        assert response.status_code == 404
    with pytest.raises(ValueError, match="forbidden in production"):
        Settings(
            database_url="postgresql+psycopg://generated.invalid/hcam",
            environment="production",
            intelligence_generated_investigations_enabled=True,
        )


def test_api_enforces_role_and_department_scope(
    p45_app, p45_headers: dict[str, str], p45_context: dict
) -> None:
    with TestClient(p45_app) as client:
        created = client.post(
            "/investigations/timelines",
            headers=p45_headers,
            json=p45_context["command"].model_dump(mode="json"),
        )
        assert created.status_code == 201
        denied_role = client.get(
            f"/investigations/timelines/{p45_context['timeline_id']}",
            headers={
                "X-HCAM-Actor": "generated.viewer",
                "X-HCAM-Roles": "camera.viewer",
                "X-HCAM-Departments": p45_context["department"],
            },
        )
        assert denied_role.status_code == 403
        hidden_department = client.get(
            f"/investigations/timelines/{p45_context['timeline_id']}",
            headers={
                "X-HCAM-Actor": "generated.viewer",
                "X-HCAM-Roles": "investigation.read",
                "X-HCAM-Departments": "Generated-Department-Other",
            },
        )
    assert hidden_department.status_code == 404


def test_investigation_roles_extend_the_historical_authentication_registry() -> None:
    assert INVESTIGATION_ROLES
    assert INVESTIGATION_ROLES.isdisjoint(AUTHENTICATION_ROLES)
    assert CURRENT_AUTHENTICATION_ROLES == AUTHENTICATION_ROLES | INVESTIGATION_ROLES


def test_service_fails_closed_for_disabled_runtime_and_actor_mismatch(
    p45_app, p45_context: dict
) -> None:
    principal = Principal(
        actor_id="generated.other",
        roles=frozenset({"platform.admin"}),
        departments=frozenset({"*"}),
        authentication_method="generated-test",
    )
    with p45_app.state.database.session_factory() as session:
        with pytest.raises(InvestigationDisabledError):
            InvestigationService(
                session,
                enabled=False,
                environment="test",
            ).timelines(principal=principal)
        with pytest.raises(InvestigationError, match="does not match"):
            InvestigationService(
                session,
                enabled=True,
                environment="test",
            ).create_timeline(p45_context["command"], principal=principal)


def test_runtime_validates_environment() -> None:
    from hcam.intelligence.investigations.runtime import GeneratedInvestigationRuntime

    with pytest.raises(ValueError, match="environment"):
        GeneratedInvestigationRuntime(environment="invalid")
    with pytest.raises(ValueError, match="forbidden"):
        GeneratedInvestigationRuntime(enabled=True, environment="production")
    with pytest.raises(RuntimeError, match="disabled"):
        GeneratedInvestigationRuntime().require_enabled()
