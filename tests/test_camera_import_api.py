from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from hcam.audit.models import AuditEvent
from hcam.camera_registry.models import Camera


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
    assert first.headers["cache-control"] == "no-store"
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


def test_bulk_import_rejects_more_than_synchronous_limit(
    app,
    seed_file: Path,
    admin_headers: dict[str, str],
) -> None:
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    template = payload["cameras"][0]
    payload["cameras"] = []
    for index in range(1001):
        camera = json.loads(json.dumps(template))
        camera["camera_id"] = f"synthetic:bulk-{index:04d}"
        camera["external_id"] = f"bulk-{index:04d}"
        payload["cameras"].append(camera)

    with TestClient(app) as client:
        response = client.post(
            "/camera-imports",
            json=payload,
            headers=admin_headers,
        )

    assert response.status_code == 413
    assert response.json() == {
        "detail": "Synchronous camera import is limited to 1000 records"
    }


def test_bulk_import_identity_conflict_rolls_back_and_records_failure(
    app,
    seed_file: Path,
    admin_headers: dict[str, str],
) -> None:
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    with app.state.database.session_factory() as session, session.begin():
        session.add(
            Camera(
                camera_id="synthetic:existing-conflict",
                source_id="synthetic-reference",
                external_id="cctv-001",
                display_name="Existing Synthetic Conflict",
                source_schema="test.v1",
                provenance={"adapter": "test"},
            )
        )

    with TestClient(app) as client:
        response = client.post(
            "/camera-imports",
            json=payload,
            headers=admin_headers,
        )

    assert response.status_code == 409
    with app.state.database.session_factory() as session:
        cameras = session.scalars(select(Camera).order_by(Camera.camera_id)).all()
        failure = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "camera_registry.import",
                AuditEvent.outcome == "failure",
            )
        ).one()
    assert [camera.camera_id for camera in cameras] == [
        "synthetic:existing-conflict"
    ]
    assert failure.context["error_type"] == "IntegrityError"
