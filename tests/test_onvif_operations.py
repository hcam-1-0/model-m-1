from __future__ import annotations

import ipaddress
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from fastapi.testclient import TestClient
from sqlalchemy import select

from hcam.audit.models import AuditEvent
from hcam.camera_registry.importer import RegistryImporter
from hcam.main import create_app
from hcam.settings import Settings
from hcam.streams.models import OnvifControlLease, OnvifOperationRun
from hcam.streams.network import OnvifEgressRule
from hcam.streams.onvif_simulator import handler_for


def _headers(role: str) -> dict[str, str]:
    return {
        "X-HCAM-Actor": f"test-{role.replace('.', '-')}",
        "X-HCAM-Roles": role,
        "X-HCAM-Departments": "*",
        "X-HCAM-Reason": "Authorized isolated ONVIF operation test",
    }


def _build_app(tmp_path: Path, seed_file: Path, port: int):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'operations.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            onvif_egress_rules=(
                OnvifEgressRule(
                    scheme="http",
                    host="127.0.0.1",
                    port=port,
                    approved_addresses=(ipaddress.ip_network("127.0.0.1/32"),),
                ),
            ),
            onvif_lab_http_enabled=True,
            onvif_control_enabled=True,
        )
    )
    app.state.database.create_schema()
    RegistryImporter(app.state.database.session_factory).import_file(seed_file)
    return app


def _stream_payload(port: int, *, control: bool = True) -> dict[str, object]:
    return {
        "name": "controlled-onvif",
        "adapter_kind": "onvif",
        "protocol": "http",
        "locator": f"http://127.0.0.1:{port}/onvif/media_service",
        "management_locator": f"http://127.0.0.1:{port}/onvif/device_service",
        "onvif_control_enabled": control,
        "onvif_max_velocity": 0.5,
        "onvif_max_move_seconds": 0.25,
        "is_primary": True,
    }


def test_onvif_operations_execute_against_synthetic_services(
    tmp_path: Path, seed_file: Path
) -> None:
    handler = handler_for("rtsp://127.0.0.1:8554/synthetic-01")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    app = _build_app(tmp_path, seed_file, port)
    try:
        with TestClient(app) as client:
            created = client.post(
                "/cameras/synthetic:cctv-002/streams",
                json=_stream_payload(port),
                headers=_headers("platform.admin"),
            )
            assert created.status_code == 201, created.text
            stream_id = created.json()["stream_id"]

            imaging = client.post(
                f"/streams/{stream_id}/onvif/imaging-inspections",
                json={"profile_token": "hcam-main"},
                headers=_headers("camera.editor"),
            )
            events = client.post(
                f"/streams/{stream_id}/onvif/event-pulls",
                json={"message_limit": 4, "timeout_seconds": 0.1},
                headers=_headers("camera.editor"),
            )
            ptz = client.post(
                f"/streams/{stream_id}/onvif/ptz-commands",
                json={
                    "action": "continuous",
                    "profile_token": "hcam-main",
                    "pan": 0.2,
                    "duration_seconds": 0.1,
                },
                headers=_headers("camera.controller"),
            )
            ptz_stop = client.post(
                f"/streams/{stream_id}/onvif/ptz-commands",
                json={"action": "stop", "profile_token": "hcam-main"},
                headers=_headers("camera.controller"),
            )
            ptz_relative = client.post(
                f"/streams/{stream_id}/onvif/ptz-commands",
                json={
                    "action": "relative",
                    "profile_token": "hcam-main",
                    "pan": 0.3,
                    "tilt": 0.2,
                    "zoom": 0.1,
                    "speed": 0.4,
                },
                headers=_headers("camera.controller"),
            )
            ptz_absolute = client.post(
                f"/streams/{stream_id}/onvif/ptz-commands",
                json={
                    "action": "absolute",
                    "profile_token": "hcam-main",
                    "pan": 0.8,
                    "speed": 0.4,
                },
                headers=_headers("camera.controller"),
            )
            ptz_preset = client.post(
                f"/streams/{stream_id}/onvif/ptz-commands",
                json={
                    "action": "goto_preset",
                    "profile_token": "hcam-main",
                    "preset_token": "preset-01",
                },
                headers=_headers("camera.controller"),
            )
            ptz_bad_profile = client.post(
                f"/streams/{stream_id}/onvif/ptz-commands",
                json={"action": "stop", "profile_token": "missing"},
                headers=_headers("camera.controller"),
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert imaging.status_code == 200, imaging.text
    assert imaging.headers["cache-control"] == "no-store"
    assert imaging.json()["video_source_token"] == "source-main"
    assert imaging.json()["brightness"] == 52
    assert imaging.json()["exposure_mode"] == "AUTO"
    assert events.status_code == 200, events.text
    assert events.json()["subscription_terminated"] is True
    assert events.json()["messages"][0]["data"] == {"State": "true"}
    assert ptz.status_code == 200, ptz.text
    assert ptz.json()["auto_stopped"] is True
    assert handler.operation_counts["ContinuousMove"] == 1
    assert handler.operation_counts["Stop"] == 2
    assert handler.operation_counts["RelativeMove"] == 1
    assert handler.operation_counts["AbsoluteMove"] == 1
    assert handler.operation_counts["GotoPreset"] == 1
    assert all(
        response.status_code == 200
        for response in (ptz_stop, ptz_relative, ptz_absolute, ptz_preset)
    )
    assert ptz_bad_profile.status_code == 422

    with app.state.database.session_factory() as session:
        runs = session.scalars(
            select(OnvifOperationRun).order_by(OnvifOperationRun.requested_at)
        ).all()
        leases = session.scalars(select(OnvifControlLease)).all()
        audits = session.scalars(
            select(AuditEvent).where(AuditEvent.action.like("stream.onvif.%"))
        ).all()
    assert [run.operation_type for run in runs] == [
        "imaging_inspect",
        "event_pull",
        "ptz_continuous",
        "ptz_stop",
        "ptz_relative",
        "ptz_absolute",
        "ptz_goto_preset",
        "ptz_stop",
    ]
    assert [run.outcome for run in runs] == ["success"] * 7 + ["failure"]
    assert leases == []
    assert len(audits) == 16
    assert sum(event.outcome == "pending" for event in audits) == 8
    assert sum(event.outcome in {"success", "failure"} for event in audits) == 8
    assert all("locator" not in event.context for event in audits)
    app.state.database.dispose()


def test_onvif_control_requires_admin_enablement_and_controller_role(
    tmp_path: Path, seed_file: Path
) -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        handler_for("rtsp://127.0.0.1:8554/synthetic-01"),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    app = _build_app(tmp_path, seed_file, port)
    try:
        with TestClient(app) as client:
            editor_create = client.post(
                "/cameras/synthetic:cctv-002/streams",
                json=_stream_payload(port),
                headers=_headers("camera.editor"),
            )
            created = client.post(
                "/cameras/synthetic:cctv-002/streams",
                json=_stream_payload(port, control=False),
                headers=_headers("platform.admin"),
            )
            stream_id = created.json()["stream_id"]
            editor_control = client.post(
                f"/streams/{stream_id}/onvif/ptz-commands",
                json={"action": "stop", "profile_token": "hcam-main"},
                headers=_headers("camera.editor"),
            )
            controller_control = client.post(
                f"/streams/{stream_id}/onvif/ptz-commands",
                json={"action": "stop", "profile_token": "hcam-main"},
                headers=_headers("camera.controller"),
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        app.state.database.dispose()

    assert editor_create.status_code == 422
    assert editor_control.status_code == 403
    assert controller_control.status_code == 422
    assert "not enabled" in controller_control.text


def test_ptz_rejects_per_stream_velocity_and_duration_limits() -> None:
    from hcam.streams.onvif_operations import (
        OnvifEndpointConfig,
        OnvifOperationValidationError,
        _validate_ptz_limits,
    )
    from hcam.streams.schemas import OnvifPtzCommandRequest
    import pytest

    config = OnvifEndpointConfig(
        stream_id="str_" + "a" * 32,
        camera_id="synthetic:test",
        management_locator="http://127.0.0.1/onvif/device_service",
        onvif_auth_mode="none",
        secret_ref=None,
        onvif_control_enabled=True,
        onvif_max_velocity=0.25,
        onvif_max_move_seconds=1,
    )
    with pytest.raises(OnvifOperationValidationError, match="velocity"):
        _validate_ptz_limits(
            OnvifPtzCommandRequest(
                action="continuous",
                profile_token="main",
                pan=0.5,
                duration_seconds=0.5,
            ),
            config,
        )
    with pytest.raises(OnvifOperationValidationError, match="duration"):
        _validate_ptz_limits(
            OnvifPtzCommandRequest(
                action="continuous",
                profile_token="main",
                pan=0.2,
                duration_seconds=2,
            ),
            config,
        )
