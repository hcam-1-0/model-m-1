from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from hcam.audit.models import AuditEvent


def test_admin_can_bulk_import_registry_payload(
    app,
    seed_file: Path,
    admin_headers: dict[str, str],
) -> None:
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    with TestClient(app) as client:
        first = client.post(
            "/camera-imports", json=payload, headers=admin_headers
        )
        second = client.post(
            "/camera-imports", json=payload, headers=admin_headers
        )

    assert first.status_code == 200
    assert first.json()["created"] == 2
    assert second.status_code == 200
    assert second.json()["unchanged"] == 2

    with app.state.database.session_factory() as session:
        events = session.scalars(
            select(AuditEvent)
            .where(AuditEvent.action == "camera_registry.import")
            .order_by(AuditEvent.occurred_at)
        ).all()
    assert len(events) == 2
    assert all(event.actor_id == "test-admin" for event in events)
    assert all(event.reason == "Authorized registry test import" for event in events)


def test_non_admin_cannot_bulk_import(
    app,
    seed_file: Path,
    editor_headers: dict[str, str],
) -> None:
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    with TestClient(app) as client:
        response = client.post(
            "/camera-imports", json=payload, headers=editor_headers
        )

    assert response.status_code == 403
