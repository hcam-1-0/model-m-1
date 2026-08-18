from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from hcam.audit.models import AuditEvent
from hcam.camera_registry.importer import RegistryImporter
from hcam.camera_registry.models import Camera
from hcam.database import Database
from hcam.main import create_app
from hcam.settings import Settings


POSTGRES_TEST_URL = os.getenv("HCAM_POSTGRES_TEST_URL")
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not POSTGRES_TEST_URL,
        reason="HCAM_POSTGRES_TEST_URL is required for PostgreSQL integration",
    ),
]


def test_postgres_migrations_registry_and_audit_contracts(seed_file: Path) -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    try:
        database.check_ready()
        with database.session_factory() as session, session.begin():
            session.execute(delete(AuditEvent))
            session.execute(delete(Camera))
        import_result = RegistryImporter(database.session_factory).import_file(seed_file)
        assert import_result.created == 2

        application = create_app(
            Settings(
                database_url=POSTGRES_TEST_URL,
                dev_auth_enabled=True,
                environment="test",
                access_log_enabled=False,
            )
        )
        viewer_headers = {
            "X-HCAM-Actor": "postgres-viewer",
            "X-HCAM-Roles": "camera.viewer",
            "X-HCAM-Departments": "*",
        }
        editor_headers = {
            "X-HCAM-Actor": "postgres-editor",
            "X-HCAM-Roles": "camera.editor",
            "X-HCAM-Departments": "*",
            "X-HCAM-Reason": "PostgreSQL synthetic integration validation",
            "X-Request-ID": "postgres.integration:001",
        }
        payload = json.loads(seed_file.read_text(encoding="utf-8"))["cameras"][0]
        payload["camera_id"] = "synthetic:postgres-001"
        payload["external_id"] = "postgres-001"
        payload["stream"] = {
            "selected_url": "rtsp://user:password@example.invalid/live?token=secret",
            "delivery": "metadata-only",
        }

        with TestClient(application) as client:
            assert client.get("/health/ready").status_code == 200
            listed = client.get("/cameras", headers=viewer_headers)
            created = client.post("/cameras", json=payload, headers=editor_headers)
            updated = client.patch(
                "/cameras/synthetic:postgres-001",
                json={"health_status": "synthetic-verified"},
                headers={**editor_headers, "If-Match": created.headers["ETag"]},
            )

        assert listed.status_code == 200
        assert listed.json()["total"] == 2
        assert created.status_code == 201
        assert created.json()["stream"]["selected_url"] == (
            "rtsp://example.invalid/live"
        )
        assert updated.status_code == 200
        assert updated.json()["state"]["health"] == "synthetic-verified"

        with database.session_factory() as session:
            assert session.scalar(select(func.count()).select_from(Camera)) == 3
            correlated = session.scalars(
                select(AuditEvent).where(
                    AuditEvent.action.in_(
                        [
                            "camera_registry.camera.create",
                            "camera_registry.camera.update",
                        ]
                    )
                )
            ).all()
        assert len(correlated) == 2
        assert all(
            event.context["request_id"] == "postgres.integration:001"
            for event in correlated
        )
    finally:
        database.dispose()
