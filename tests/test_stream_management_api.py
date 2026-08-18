from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm.exc import StaleDataError

from hcam.audit.models import AuditEvent
from hcam.security.auth import Principal
from hcam.streams.models import StreamEndpoint, StreamHealthCurrent
from hcam.streams.service import StreamConflictError, StreamService


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


def test_stream_routes_enforce_lookup_etag_and_primary_invariants(
    imported_app, editor_headers: dict[str, str]
) -> None:
    missing_id = "str_" + "f" * 32
    with TestClient(imported_app) as client:
        listed = client.get("/streams", headers=editor_headers).json()["items"]
        primary = listed[0]
        stream_id = primary["stream_id"]

        assert client.get(f"/streams/{missing_id}", headers=editor_headers).status_code == 404
        assert (
            client.get(f"/streams/{missing_id}/health", headers=editor_headers).status_code
            == 404
        )
        assert (
            client.get(f"/streams/{missing_id}/probes", headers=editor_headers).status_code
            == 404
        )

        malformed = client.patch(
            f"/streams/{stream_id}",
            json={"name": "changed"},
            headers={**editor_headers, "If-Match": "1"},
        )
        stale = client.patch(
            f"/streams/{stream_id}",
            json={"name": "changed"},
            headers={**editor_headers, "If-Match": '"99"'},
        )
        no_change = client.patch(
            f"/streams/{stream_id}",
            json={"name": primary["name"]},
            headers={**editor_headers, "If-Match": '"1"'},
        )
        demote = client.patch(
            f"/streams/{stream_id}",
            json={"is_primary": False},
            headers={**editor_headers, "If-Match": '"1"'},
        )

    assert malformed.status_code == 400
    assert stale.status_code == 412
    assert no_change.status_code == 422
    assert demote.status_code == 422


def test_stream_mutations_reject_conflicts_disabled_probes_and_bad_locators(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        existing = client.get("/streams", headers=editor_headers).json()["items"][0]
        stream_id = existing["stream_id"]
        duplicate_primary = client.post(
            "/cameras/synthetic:cctv-001/streams",
            json=stream_payload(locator="rtsp://mediamtx:8554/duplicate"),
            headers=editor_headers,
        )
        missing_camera = client.post(
            "/cameras/missing-camera/streams",
            json=stream_payload(),
            headers=editor_headers,
        )
        protocol_mismatch = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(protocol="hls", locator="rtsp://mediamtx/live"),
            headers=editor_headers,
        )
        disabled = client.patch(
            f"/streams/{stream_id}",
            json={"enabled": False},
            headers={**editor_headers, "If-Match": '"1"'},
        )
        queue_disabled = client.post(
            f"/streams/{stream_id}/probe", headers=editor_headers
        )

    assert duplicate_primary.status_code == 409
    assert missing_camera.status_code == 404
    assert protocol_mismatch.status_code == 422
    assert disabled.status_code == 200
    assert queue_disabled.status_code == 422

    with imported_app.state.database.session_factory.begin() as session:
        endpoint = session.get(StreamEndpoint, stream_id)
        assert endpoint is not None
        endpoint.enabled = True
        endpoint.lease_owner = "worker-active"
        endpoint.lease_until = datetime.now(UTC) + timedelta(minutes=1)

    with TestClient(imported_app) as client:
        busy = client.post(f"/streams/{stream_id}/probe", headers=editor_headers)
        filtered = client.get(
            "/streams?protocol=hls&state=unknown&enabled=true",
            headers=editor_headers,
        )
    assert busy.status_code == 409
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 0


def test_hls_stream_update_requires_tcp_and_matching_locator(
    imported_app, editor_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        created = client.post(
            "/cameras/synthetic:cctv-002/streams",
            json=stream_payload(
                adapter_kind="hls",
                protocol="hls",
                locator="https://media.example.invalid/live.m3u8",
                is_primary=False,
            ),
            headers=editor_headers,
        )
        assert created.status_code == 201
        stream_id = created.json()["stream_id"]
        etag = created.headers["etag"]
        bad_transport = client.patch(
            f"/streams/{stream_id}",
            json={"transport": "udp"},
            headers={**editor_headers, "If-Match": etag},
        )
        bad_locator = client.patch(
            f"/streams/{stream_id}",
            json={"locator": "rtsp://media.example.invalid/live"},
            headers={**editor_headers, "If-Match": etag},
        )
    assert bad_transport.status_code == 422
    assert bad_locator.status_code == 422


def test_queue_probe_normalizes_worker_version_race_to_conflict() -> None:
    class BeginRaisesStaleData:
        def __enter__(self):
            raise StaleDataError("simulated worker race")

        def __exit__(self, *_args) -> None:
            return None

    class SessionStub:
        def begin(self) -> BeginRaisesStaleData:
            return BeginRaisesStaleData()

    service = StreamService(SessionStub())  # type: ignore[arg-type]
    service._record_failure = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    principal = Principal(
        actor_id="test-editor",
        roles=frozenset({"camera.editor"}),
        departments=frozenset({"*"}),
        authentication_method="test",
    )
    with pytest.raises(StreamConflictError, match="queueing"):
        service.queue_probe(
            "str_" + "a" * 32,
            principal=principal,
            reason="Authorized synthetic probe race",
            request_id="request-test",
        )
