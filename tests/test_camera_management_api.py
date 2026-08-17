from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from hcam.audit.models import AuditEvent


def camera_payload() -> dict:
    return {
        "camera_id": "manual:camera-001",
        "source": "manual-api",
        "external_id": "camera-001",
        "display_name": "Manual Synthetic Camera",
        "location": {
            "label": "Synthetic Junction C",
            "timezone": "Asia/Kolkata",
            "latitude": 23.1,
            "longitude": 72.6,
        },
        "status": {"metadata": "available", "state": "online"},
        "stream": {
            "selected_url": "rtsp://operator:secret@example.invalid/live/1?token=x",
            "delivery": "rtsp",
            "codec": "h264",
            "reachability": "unknown",
        },
        "department": "traffic",
        "ownership": "synthetic-agency",
        "camera_type": "fixed",
        "connectivity_status": "online",
        "storage_status": "metadata-only",
        "health_status": "healthy",
        "maintenance_status": "not-due",
    }


def test_editor_can_create_camera_with_audit_event(
    app, editor_headers: dict[str, str]
) -> None:
    with TestClient(app) as client:
        response = client.post("/cameras", json=camera_payload(), headers=editor_headers)

    assert response.status_code == 201
    assert response.headers["etag"] == '"1"'
    assert response.headers["location"] == "/cameras/manual:camera-001"
    camera = response.json()
    assert camera["version"] == 1
    assert camera["stream"]["selected_url"] == "rtsp://example.invalid/live/1"
    assert "secret" not in response.text
    assert "token" not in response.text

    with app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "camera_registry.camera.create",
                AuditEvent.outcome == "success",
            )
        ).one()
    assert event.actor_id == "test-editor"
    assert event.reason == "Authorized registry test update"


def test_viewer_cannot_create_camera(app, viewer_headers: dict[str, str]) -> None:
    headers = {
        **viewer_headers,
        "X-HCAM-Reason": "Viewer must not write registry data",
    }
    with TestClient(app) as client:
        response = client.post("/cameras", json=camera_payload(), headers=headers)

    assert response.status_code == 403


def test_scoped_editor_create_outside_department_is_rejected_and_audited(
    app,
) -> None:
    headers = {
        "X-HCAM-Actor": "traffic-editor",
        "X-HCAM-Roles": "camera.editor",
        "X-HCAM-Departments": "traffic",
        "X-HCAM-Reason": "Test controlled department boundary",
    }
    payload = camera_payload()
    payload["department"] = "operations"

    with TestClient(app) as client:
        response = client.post("/cameras", json=payload, headers=headers)

    assert response.status_code == 403
    with app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "camera_registry.camera.create",
                AuditEvent.outcome == "failure",
            )
        ).one()
    assert event.actor_id == "traffic-editor"
    assert event.context == {"error_type": "CameraAccessError"}


def test_write_reason_cannot_be_blank(app, editor_headers: dict[str, str]) -> None:
    headers = {**editor_headers, "X-HCAM-Reason": "        "}
    with TestClient(app) as client:
        response = client.post("/cameras", json=camera_payload(), headers=headers)

    assert response.status_code == 422


def test_duplicate_camera_create_returns_conflict(
    app, editor_headers: dict[str, str]
) -> None:
    with TestClient(app) as client:
        first = client.post("/cameras", json=camera_payload(), headers=editor_headers)
        duplicate = client.post("/cameras", json=camera_payload(), headers=editor_headers)

    assert first.status_code == 201
    assert duplicate.status_code == 409

    with app.state.database.session_factory() as session:
        failure = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "camera_registry.camera.create",
                AuditEvent.outcome == "failure",
            )
        ).one()
    assert failure.actor_id == "test-editor"
    assert failure.context == {"error_type": "CameraConflictError"}


def test_update_requires_current_etag_and_increments_version(
    imported_app, viewer_headers: dict[str, str], editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        current = client.get(
            "/cameras/synthetic:cctv-001", headers=viewer_headers
        )
        missing = client.patch(
            "/cameras/synthetic:cctv-001",
            json={"display_name": "Updated Camera"},
            headers=editor_headers,
        )
        stale = client.patch(
            "/cameras/synthetic:cctv-001",
            json={"display_name": "Updated Camera"},
            headers={**editor_headers, "If-Match": '"99"'},
        )
        updated = client.patch(
            "/cameras/synthetic:cctv-001",
            json={
                "display_name": "Updated Camera",
                "stream": {
                    "selected_url": "https://user:pass@example.invalid/new?token=x"
                },
            },
            headers={**editor_headers, "If-Match": current.headers["etag"]},
        )
        repeated_stale = client.patch(
            "/cameras/synthetic:cctv-001",
            json={"display_name": "Another Camera"},
            headers={**editor_headers, "If-Match": current.headers["etag"]},
        )

    assert missing.status_code == 428
    assert stale.status_code == 412
    assert updated.status_code == 200
    assert updated.headers["etag"] == '"2"'
    assert updated.json()["version"] == 2
    assert updated.json()["display_name"] == "Updated Camera"
    assert updated.json()["stream"]["selected_url"] == "https://example.invalid/new"
    assert repeated_stale.status_code == 412

    with imported_app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "camera_registry.camera.update",
                AuditEvent.outcome == "success",
            )
        ).one()
    assert event.actor_id == "test-editor"
    assert event.context["previous_version"] == 1
    assert event.context["version"] == 2


def test_scoped_editor_cannot_move_camera_outside_scope(imported_app) -> None:
    headers = {
        "X-HCAM-Actor": "traffic-editor",
        "X-HCAM-Roles": "camera.editor",
        "X-HCAM-Departments": "traffic",
        "X-HCAM-Reason": "Attempt controlled department transfer",
        "If-Match": '"1"',
    }
    with TestClient(imported_app) as client:
        response = client.patch(
            "/cameras/synthetic:cctv-001",
            json={"department": "operations"},
            headers=headers,
        )

    assert response.status_code == 403

    admin_headers = {
        "X-HCAM-Actor": "test-admin",
        "X-HCAM-Roles": "platform.admin",
        "X-HCAM-Departments": "*",
    }
    with TestClient(imported_app) as client:
        unchanged = client.get(
            "/cameras/synthetic:cctv-001", headers=admin_headers
        )
    assert unchanged.json()["department"] == "traffic"
    assert unchanged.json()["version"] == 1


def test_partial_coordinate_clear_is_rejected(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        response = client.patch(
            "/cameras/synthetic:cctv-001",
            json={"location": {"latitude": None}},
            headers={**editor_headers, "If-Match": '"1"'},
        )

    assert response.status_code == 422


def test_empty_nested_patch_and_weak_etag_are_rejected(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        empty_patch = client.patch(
            "/cameras/synthetic:cctv-001",
            json={"stream": {}},
            headers={**editor_headers, "If-Match": '"1"'},
        )
        weak_etag = client.patch(
            "/cameras/synthetic:cctv-001",
            json={"health_status": "healthy"},
            headers={**editor_headers, "If-Match": 'W/"1"'},
        )

    assert empty_patch.status_code == 422
    assert weak_etag.status_code == 400


def test_malformed_stream_reference_is_discarded_without_server_error(
    app, editor_headers: dict[str, str]
) -> None:
    payload = camera_payload()
    payload["camera_id"] = "manual:camera-malformed"
    payload["external_id"] = "camera-malformed"
    payload["stream"]["selected_url"] = "http://example.invalid:bad/live"

    with TestClient(app) as client:
        response = client.post("/cameras", json=payload, headers=editor_headers)

    assert response.status_code == 201
    assert response.json()["stream"]["selected_url"] is None


def test_oversized_stream_reference_is_rejected(
    app, editor_headers: dict[str, str]
) -> None:
    payload = camera_payload()
    payload["camera_id"] = "manual:camera-oversized"
    payload["external_id"] = "camera-oversized"
    payload["stream"]["selected_url"] = "x" * 4097

    with TestClient(app) as client:
        response = client.post("/cameras", json=payload, headers=editor_headers)

    assert response.status_code == 422


def test_missing_and_no_op_updates_are_rejected_and_audited(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        missing = client.patch(
            "/cameras/synthetic:missing",
            json={"display_name": "Missing Camera"},
            headers={**editor_headers, "If-Match": '"1"'},
        )
        no_op = client.patch(
            "/cameras/synthetic:cctv-001",
            json={"display_name": "Synthetic Junction Camera"},
            headers={**editor_headers, "If-Match": '"1"'},
        )
        current = client.get(
            "/cameras/synthetic:cctv-001",
            headers={
                "X-HCAM-Actor": "test-viewer",
                "X-HCAM-Roles": "camera.viewer",
                "X-HCAM-Departments": "*",
            },
        )

    assert missing.status_code == 404
    assert no_op.status_code == 422
    assert no_op.json() == {"detail": "Camera update does not change registry data"}
    assert current.json()["version"] == 1

    with imported_app.state.database.session_factory() as session:
        failures = session.scalars(
            select(AuditEvent)
            .where(
                AuditEvent.action == "camera_registry.camera.update",
                AuditEvent.outcome == "failure",
            )
            .order_by(AuditEvent.occurred_at)
        ).all()
    assert [event.context["error_type"] for event in failures] == [
        "CameraNotFoundError",
        "CameraValidationError",
    ]
