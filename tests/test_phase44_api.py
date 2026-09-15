from __future__ import annotations

from fastapi.testclient import TestClient

from hcam.main import create_app
from hcam.settings import Settings
from tests.test_phase44_contracts import intent, manifest


def application(tmp_path, *, enabled: bool = True):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'phase44-api.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            intelligence_generated_reference_integrations_enabled=enabled,
            intelligence_generated_reference_manual_queries_enabled=enabled,
        )
    )
    app.state.database.create_schema()
    return app


def headers(
    role: str,
    *,
    actor: str = "generated-admin",
    department: str = "*",
    reason: str = "Generated-only reference integration test",
) -> dict[str, str]:
    return {
        "X-HCAM-Actor": actor,
        "X-HCAM-Roles": role,
        "X-HCAM-Departments": department,
        "X-HCAM-Reason": reason,
    }


def test_reference_provider_query_control_and_cancel_api(tmp_path) -> None:
    app = application(tmp_path)
    provider = manifest()
    query = intent(provider)
    try:
        with TestClient(app) as client:
            created = client.post(
                "/reference-integrations/providers",
                json=provider.model_dump(mode="json"),
                headers=headers("reference.provider.create_generated"),
            )
            assert created.status_code == 201, created.text
            assert created.headers["cache-control"] == "no-store"
            listed = client.get(
                "/reference-integrations/providers",
                headers=headers("reference.provider.read"),
            )
            assert listed.status_code == 200 and listed.json()["total"] == 1

            control = client.post(
                "/reference-integrations/controls",
                json={
                    "department": provider.department,
                    "scope": "organization",
                    "scope_key": "generated.reference",
                    "state": "enabled_generated",
                },
                headers={
                    **headers("reference.control.manage_generated"),
                    "If-Match": '"0"',
                },
            )
            assert control.status_code == 200, control.text
            assert control.headers["etag"] == '"1"'

            submitted = client.post(
                "/reference-integrations/queries",
                json=query.model_dump(mode="json"),
                headers=headers(
                    "reference.query.submit_generated", reason=query.reason
                ),
            )
            assert submitted.status_code == 202, submitted.text
            assert submitted.headers["location"].startswith(
                "/reference-integrations/queries/"
            )
            job = submitted.json()["job"]
            duplicate = client.post(
                "/reference-integrations/queries",
                json=query.model_dump(mode="json"),
                headers=headers(
                    "reference.query.submit_generated", reason=query.reason
                ),
            )
            assert duplicate.status_code == 202 and duplicate.json()["reused"] is True
            read = client.get(
                f"/reference-integrations/queries/{job['job_id']}",
                headers=headers("reference.query.read"),
            )
            assert read.status_code == 200
            cancelled = client.post(
                f"/reference-integrations/queries/{job['job_id']}/cancel",
                headers={
                    **headers("reference.query.cancel"),
                    "If-Match": '"1"',
                },
            )
            assert cancelled.status_code == 200, cancelled.text
            assert cancelled.json()["state"] == "cancelled"
    finally:
        app.state.database.dispose()


def test_reference_api_is_default_off_and_exposes_no_execution_or_action_route(tmp_path) -> None:
    disabled = application(tmp_path, enabled=False)
    try:
        with TestClient(disabled) as client:
            paths = client.app.openapi()["paths"]
            assert "/reference-integrations/providers" not in paths
            assert "/reference-integrations/queries" not in paths
    finally:
        disabled.state.database.dispose()

    enabled = application(tmp_path)
    try:
        with TestClient(enabled) as client:
            paths = {
                path: methods
                for path, methods in client.app.openapi()["paths"].items()
                if path.startswith("/reference-integrations")
            }
            serialized = str(paths).lower()
            for prohibited in (
                "worker-start",
                "execute-provider",
                "confirm-identity",
                "dispatch",
                "enforcement",
                "runtime_url",
            ):
                assert prohibited not in serialized
    finally:
        enabled.state.database.dispose()
