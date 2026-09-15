import pytest
from fastapi.testclient import TestClient

from hcam.main import create_app
from hcam.operations.platform.runtime import GeneratedPlatformRuntime
from hcam.security.auth import OPERATIONS_PLATFORM_ROLES, PLATFORM_AUTHENTICATION_ROLES
from hcam.settings import Settings


HEADERS = {
    "X-HCAM-Actor": "generated:reader",
    "X-HCAM-Roles": "operations.platform.read",
    "X-HCAM-Departments": "Generated Department",
}


def _app(database_url: str, enabled: bool = True):
    return create_app(
        Settings(
            database_url=database_url,
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            access_log_enabled=False,
            operations_generated_platform_enabled=enabled,
        )
    )


def test_platform_read_api_is_bounded_no_store_and_generated_only(tmp_path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'api.db').as_posix()}"
    with TestClient(_app(database_url)) as client:
        response = client.get("/platform/operations/summary", headers=HEADERS)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["generated_only"] is True
        assert response.json()["available_views"] == ["objectives", "budgets", "degradation"]
        assert response.json()["unified_search_enabled"] is False
        view = client.get("/platform/operations/objectives?limit=20", headers=HEADERS)
        assert view.status_code == 200
        assert view.json() == {"view": "objectives", "items": [], "count": 0, "generated_only": True}
        assert client.get("/platform/operations/capacity", headers=HEADERS).status_code == 403


def test_platform_specialized_roles_are_view_scoped(tmp_path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'scoped.db').as_posix()}"
    with TestClient(_app(database_url)) as client:
        capacity_headers = {**HEADERS, "X-HCAM-Roles": "operations.capacity.read"}
        summary = client.get("/platform/operations/summary", headers=capacity_headers)
        assert summary.status_code == 200
        assert summary.json()["available_views"] == ["capacity"]
        assert summary.json()["counts"] == {"capacity": 0}
        assert client.get("/platform/operations/capacity", headers=capacity_headers).status_code == 200
        assert client.get("/platform/operations/security", headers=capacity_headers).status_code == 403


def test_platform_api_requires_role_and_is_absent_when_disabled(tmp_path) -> None:
    with TestClient(_app(f"sqlite:///{(tmp_path / 'enabled.db').as_posix()}")) as client:
        assert client.get("/platform/operations/summary").status_code == 401
        denied = {**HEADERS, "X-HCAM-Roles": "camera.viewer"}
        assert client.get("/platform/operations/summary", headers=denied).status_code == 403
    with TestClient(_app(f"sqlite:///{(tmp_path / 'disabled.db').as_posix()}", False)) as client:
        assert client.get("/platform/operations/summary", headers=HEADERS).status_code == 404


def test_external_adapters_and_production_runtime_fail_closed() -> None:
    for field in (
        "operations_unified_search_enabled",
        "operations_otel_export_enabled",
        "operations_external_broker_enabled",
        "operations_kubernetes_execution_enabled",
    ):
        try:
            Settings(**{field: True})
        except ValueError as exc:
            assert "remain disabled" in str(exc)
        else:
            raise AssertionError(f"{field} was unexpectedly enabled")
    try:
        Settings(environment="production", database_url="postgresql://generated", operations_generated_platform_enabled=True)
    except ValueError as exc:
        assert "forbidden in production" in str(exc)
    else:
        raise AssertionError("P4.6 production runtime was unexpectedly enabled")


def test_generated_runtime_normalizes_environment_and_stays_explicitly_disabled() -> None:
    runtime = GeneratedPlatformRuntime(enabled=True, environment=" TEST ")
    assert runtime.environment == "test"
    runtime.require_enabled()
    with pytest.raises(RuntimeError):
        GeneratedPlatformRuntime().require_enabled()
    with pytest.raises(ValueError):
        GeneratedPlatformRuntime(environment="staging")
    with pytest.raises(ValueError):
        GeneratedPlatformRuntime(enabled=True, environment="production")


def test_operations_roles_extend_the_platform_authentication_registry() -> None:
    assert OPERATIONS_PLATFORM_ROLES
    assert OPERATIONS_PLATFORM_ROLES <= PLATFORM_AUTHENTICATION_ROLES
