from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hcam.main import create_app
from hcam.settings import Settings


def test_registry_routes_require_identity(app) -> None:
    with TestClient(app) as client:
        response = client.get("/cameras")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "H-CAM-Dev"


def test_registry_fails_closed_without_identity_provider(tmp_path: Path) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'closed.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=False,
            environment="development",
        )
    )
    with TestClient(application) as client:
        response = client.get("/cameras")
        readiness = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication provider is not configured"}
    assert readiness.status_code == 503
    assert readiness.json() == {"detail": "Authentication provider is not ready"}


def test_local_development_auth_is_forbidden_in_production(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="forbidden in production"):
        create_app(
            Settings(
                database_url=f"sqlite:///{(tmp_path / 'production.db').as_posix()}",
                dev_auth_enabled=True,
                environment="production",
            )
        )


def test_automatic_schema_creation_is_forbidden_in_production(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="schema creation is forbidden"):
        create_app(
            Settings(
                database_url=f"sqlite:///{(tmp_path / 'production.db').as_posix()}",
                create_schema=True,
                environment="production",
            )
        )


def test_department_scope_filters_and_hides_records(imported_app) -> None:
    scoped_headers = {
        "X-HCAM-Actor": "traffic-viewer",
        "X-HCAM-Roles": "camera.viewer",
        "X-HCAM-Departments": "traffic",
    }
    with TestClient(imported_app) as client:
        camera_list = client.get("/cameras", headers=scoped_headers)
        hidden_detail = client.get(
            "/cameras/synthetic:cctv-002", headers=scoped_headers
        )

    assert camera_list.status_code == 200
    assert camera_list.json()["total"] == 1
    assert camera_list.json()["items"][0]["camera_id"] == "synthetic:cctv-001"
    assert hidden_detail.status_code == 404


def test_scoped_viewer_without_departments_sees_no_registry_records(
    imported_app,
) -> None:
    headers = {
        "X-HCAM-Actor": "unassigned-viewer",
        "X-HCAM-Roles": "camera.viewer",
    }
    with TestClient(imported_app) as client:
        response = client.get("/cameras", headers=headers)

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_invalid_local_department_scope_is_rejected(app) -> None:
    headers = {
        "X-HCAM-Actor": "test-viewer",
        "X-HCAM-Roles": "camera.viewer",
        "X-HCAM-Departments": "*,traffic",
    }
    with TestClient(app) as client:
        response = client.get("/cameras", headers=headers)

    assert response.status_code == 401
