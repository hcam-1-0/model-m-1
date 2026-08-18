from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from hcam.audit.models import AuditEvent
from hcam.streams.models import StreamEndpoint, StreamHealthCurrent


def stream_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "primary",
        "adapter_kind": "synthetic",
        "protocol": "rtsp",
        "locator": "rtsp://mediamtx:8554/synthetic-002",
        "transport": "tcp",
        "is_primary": True,
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def test_registry_import_creates_legacy_primary_stream(
    imported_app, viewer_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        response = client.get("/streams", headers=viewer_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    stream = payload["items"][0]
    assert stream["camera_id"] == "synthetic:cctv-001"
    assert stream["adapter_kind"] == "legacy"
    assert stream["is_primary"] is True
    assert stream["locator"] == "https://camera.example.invalid/streams/1"
    assert stream["secret_configured"] is False
    assert stream["health"]["state"] == "unknown"


def test_editor_creates_primary_stream_and_projection(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        response = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(),
            headers=editor_headers,
        )
        camera_response = client.get(
            "/cameras/synthetic:cctv-002", headers=editor_headers
        )

    assert response.status_code == 201
    assert response.headers["etag"] == '"1"'
    stream = response.json()
    assert stream["stream_id"].startswith("str_")
    assert response.headers["location"] == f"/streams/{stream['stream_id']}"
    assert stream["health"]["state"] == "unknown"
    assert camera_response.json()["stream"]["selected_url"] == stream["locator"]

    with imported_app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.endpoint.create",
                AuditEvent.outcome == "success",
            )
        ).one()
    assert event.target_id == stream["stream_id"]
    assert "locator" not in event.context


def test_stream_locator_rejects_credentials_and_records_safe_failure(
    imported_app, editor_headers: dict[str, str]
) -> None:
    payload = stream_payload(
        locator="rtsp://operator:secret@mediamtx:8554/camera?token=private"
    )
    with TestClient(imported_app) as client:
        response = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=payload,
            headers=editor_headers,
        )

    assert response.status_code == 422
    assert "secret" not in response.text
    assert "private" not in response.text
    with imported_app.state.database.session_factory() as session:
        event = session.scalars(
            select(AuditEvent).where(
                AuditEvent.action == "stream.endpoint.create",
                AuditEvent.outcome == "failure",
            )
        ).one()
    assert event.context["error_type"] == "StreamValidationError"


def test_viewer_cannot_create_or_queue_stream(
    imported_app, viewer_headers: dict[str, str]
) -> None:
    headers = {
        **viewer_headers,
        "X-HCAM-Reason": "Viewer cannot mutate stream state",
    }
    with TestClient(imported_app) as client:
        create_response = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(),
            headers=headers,
        )
        stream_id = client.get("/streams", headers=viewer_headers).json()["items"][0][
            "stream_id"
        ]
        queue_response = client.post(
            f"/streams/{stream_id}/probe", headers=headers
        )

    assert create_response.status_code == 403
    assert queue_response.status_code == 403


def test_stream_update_requires_etag_and_promotes_new_primary(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        create_response = client.post(
            "/cameras/synthetic:cctv-001/streams",
            json=stream_payload(
                name="secondary",
                locator="rtsp://mediamtx:8554/synthetic-secondary",
                is_primary=False,
            ),
            headers=editor_headers,
        )
        stream = create_response.json()
        missing_etag = client.patch(
            f"/streams/{stream['stream_id']}",
            json={"is_primary": True},
            headers=editor_headers,
        )
        promoted = client.patch(
            f"/streams/{stream['stream_id']}",
            json={"is_primary": True},
            headers={**editor_headers, "If-Match": create_response.headers["etag"]},
        )
        streams = client.get(
            "/streams?camera_id=synthetic:cctv-001", headers=editor_headers
        ).json()["items"]

    assert missing_etag.status_code == 428
    assert promoted.status_code == 200
    assert promoted.headers["etag"] == '"2"'
    assert promoted.json()["is_primary"] is True
    assert sum(item["is_primary"] for item in streams) == 1


def test_queue_probe_and_read_empty_history(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        stream_id = client.get("/streams", headers=editor_headers).json()["items"][0][
            "stream_id"
        ]
        queued = client.post(
            f"/streams/{stream_id}/probe", headers=editor_headers
        )
        history = client.get(
            f"/streams/{stream_id}/probes", headers=editor_headers
        )
        health = client.get(
            f"/streams/{stream_id}/health", headers=editor_headers
        )

    assert queued.status_code == 202
    assert queued.json()["status"] == "queued"
    assert history.status_code == 200
    assert history.json()["total"] == 0
    assert health.json()["state"] == "unknown"


def test_department_scope_hides_streams(imported_app) -> None:
    headers = {
        "X-HCAM-Actor": "operations-viewer",
        "X-HCAM-Roles": "camera.viewer",
        "X-HCAM-Departments": "operations",
    }
    with TestClient(imported_app) as client:
        response = client.get("/streams", headers=headers)

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_stream_tables_have_current_health_for_every_endpoint(imported_app) -> None:
    with imported_app.state.database.session_factory() as session:
        endpoint_ids = set(session.scalars(select(StreamEndpoint.stream_id)).all())
        health_ids = set(session.scalars(select(StreamHealthCurrent.stream_id)).all())
    assert endpoint_ids
    assert endpoint_ids == health_ids
