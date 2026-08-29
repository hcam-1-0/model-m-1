from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from hcam.cam_adapter.catalog import load_catalog_preview
from hcam.cam_adapter.config import (
    AdapterConfig,
    AdapterConfigurationError,
    CatalogConfig,
    StreamConfig,
)
from hcam.cam_adapter.routes import (
    dashboard_router as adapter_dashboard_router,
)
from hcam.cam_adapter.routes import (
    monitoring_dashboard_router as camera_monitoring_dashboard_router,
)
from hcam.cam_adapter.routes import router as cam_adapter_router
from hcam.cam_adapter.runtime import AdapterRuntime, AdapterRuntimeError
from hcam.security.auth import DevHeaderAuthenticator


def _config(*, streams: list[StreamConfig] | None = None) -> AdapterConfig:
    return AdapterConfig(
        drive_base=Path("recordings"),
        local_fallback_base=Path("recordings"),
        allowed_source_hosts=["live.corp8.cloud"],
        streams=streams or [],
    )


def test_config_file_resolves_recording_and_tool_paths_relative_to_file(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "camera-adapter.json"
    config_file.write_text(
        json.dumps(
            {
                "drive_base": "../recordings",
                "local_fallback_base": "../recordings",
                "ffmpeg_bin": "tools/ffmpeg.exe",
                "ffprobe_bin": "tools/ffprobe.exe",
                "allowed_source_hosts": ["live.corp8.cloud"],
                "streams": [],
            }
        ),
        encoding="utf-8",
    )

    config = AdapterConfig.from_file(config_file)

    assert config.drive_base == (tmp_path.parent / "recordings").resolve()
    assert config.ffmpeg_bin == str((tmp_path / "tools" / "ffmpeg.exe").resolve())
    assert config.ffprobe_bin == str((tmp_path / "tools" / "ffprobe.exe").resolve())


def test_adapter_requires_an_explicit_allow_list_for_enabled_sources() -> None:
    config = AdapterConfig(
        streams=[
            StreamConfig(
                camera_id="cam_1",
                rtsp_url="rtsp://live.corp8.cloud:8554/stream/1",
            )
        ]
    )

    with pytest.raises(AdapterConfigurationError, match="allowed_source_hosts"):
        config.assert_activatable()


def test_adapter_refuses_an_enabled_source_outside_the_allow_list() -> None:
    config = _config(
        streams=[
            StreamConfig(
                camera_id="cam_1",
                rtsp_url="https://unapproved.example/live/index.m3u8",
            )
        ]
    )

    with pytest.raises(AdapterConfigurationError, match="not allow-listed"):
        config.assert_activatable()


def test_catalog_preview_selects_only_live_allowlisted_hls_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "cameras": [
                    {"id": "1", "live": True, "location": "One", "hls_live_url": "/live/stream/1/index.m3u8"},
                    {"id": "2", "live": False, "hls_live_url": "/live/stream/2/index.m3u8"},
                    {"id": "3", "live": True, "hls_live_url": "/live/stream/3/index.m3u8"},
                ]
            }

    monkeypatch.setattr("hcam.cam_adapter.catalog.httpx.get", lambda *_args, **_kwargs: Response())
    config = _config()
    config.catalog = CatalogConfig(
        url="https://live.corp8.cloud/api/ingest",
        source_kind="hls",
        max_cameras=1,
        camera_id_prefix="corp8_",
    )

    preview = load_catalog_preview(config)

    assert preview.catalog_host == "live.corp8.cloud"
    assert preview.total_entries == 3
    assert [stream.camera_id for stream in preview.selected_streams] == ["corp8_1"]
    assert preview.selected_streams[0].rtsp_url == "https://live.corp8.cloud/live/stream/1/index.m3u8"


def test_runtime_stays_stopped_without_a_local_config_file() -> None:
    runtime = AdapterRuntime()

    status = runtime.status()

    assert status.config_loaded is False
    assert status.running is False
    assert status.streams_configured == 0


def test_catalog_preview_selects_allowlisted_whep_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "cameras": [
                    {
                        "id": "1",
                        "live": True,
                        "location": "Approved camera",
                        "webrtc_url": "https://live.corp8.cloud/stream/1/whep",
                    },
                    {
                        "id": "2",
                        "live": True,
                        "webrtc_url": "https://unapproved.example/stream/2/whep",
                    },
                ]
            }

    monkeypatch.setattr("hcam.cam_adapter.catalog.httpx.get", lambda *_args, **_kwargs: Response())
    config = _config()
    config.catalog = CatalogConfig(
        url="https://live.corp8.cloud/api/ingest",
        source_kind="whep",
        max_cameras=3,
        camera_id_prefix="corp8_",
        viewer_enabled=True,
    )

    preview = load_catalog_preview(config)

    assert [stream.camera_id for stream in preview.selected_streams] == ["corp8_1"]
    assert preview.selected_streams[0].rtsp_url.endswith("/stream/1/whep")


def test_live_viewer_issues_one_time_launch_and_negotiates_without_recording(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, admin_headers: dict[str, str]
) -> None:
    config_file = tmp_path / "live-viewer.json"
    config_file.write_text(
        json.dumps(
            {
                "allowed_source_hosts": ["live.corp8.cloud"],
                "catalog": {
                    "url": "https://live.corp8.cloud/api/ingest",
                    "source_kind": "whep",
                    "max_cameras": 1,
                    "camera_id_prefix": "corp8_",
                    "viewer_enabled": True,
                },
                "streams": [],
            }
        ),
        encoding="utf-8",
    )

    class CatalogResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "cameras": [
                    {
                        "id": "1",
                        "live": True,
                        "location": "Approved camera",
                        "department": "operations",
                        "webrtc_url": "https://live.corp8.cloud/stream/1/whep",
                    }
                ]
            }

    class WhepResponse:
        status_code = 201
        content = b"v=0\r\no=- 1 1 IN IP4 127.0.0.1\r\ns=H-CAM\r\n"
        headers = {"Location": "/stream/1/session/approved", "ETag": '"one"'}

    deleted: list[str] = []
    monkeypatch.setattr(
        "hcam.cam_adapter.catalog.httpx.get", lambda *_args, **_kwargs: CatalogResponse()
    )
    monkeypatch.setattr(
        "hcam.cam_adapter.viewer.httpx.post", lambda *_args, **_kwargs: WhepResponse()
    )
    monkeypatch.setattr(
        "hcam.cam_adapter.viewer.httpx.delete",
        lambda url, **_kwargs: deleted.append(url),
    )
    application = FastAPI()
    application.state.adapter_runtime = AdapterRuntime(config_file)
    application.state.authenticator = DevHeaderAuthenticator()
    application.include_router(cam_adapter_router)
    application.include_router(adapter_dashboard_router)
    application.include_router(camera_monitoring_dashboard_router)

    with TestClient(application) as client:
        launch = client.post("/cam-adapter/live/session", headers=admin_headers)
        assert launch.status_code == 200
        launch_path = launch.json()["launch_path"]
        assert "live.corp8.cloud" not in launch_path

        initial = client.get(launch_path, follow_redirects=False)
        assert initial.status_code == 303
        viewer = client.get("/cam-adapter/live")
        assert viewer.status_code == 200
        assert "Adapter Backend Dashboard" in viewer.text
        assert "Live footage" in viewer.text

        cameras = client.get("/cam-adapter/live/cameras")
        assert cameras.status_code == 200
        assert cameras.json() == {
            "cameras": [
                {
                    "camera_id": "corp8_1",
                    "location_label": "Approved camera",
                    "department": "operations",
                }
            ]
        }

        whep = client.post(
            "/cam-adapter/live/whep/corp8_1",
            content=b"v=0\r\no=- 1 1 IN IP4 127.0.0.1\r\ns=H-CAM\r\n",
            headers={"Content-Type": "application/sdp"},
        )
        assert whep.status_code == 200
        assert whep.headers["content-type"].startswith("application/sdp")
        playback_session_id = whep.headers["X-HCAM-Playback-Session"]

        closed = client.delete(f"/cam-adapter/live/whep/{playback_session_id}")
        assert closed.status_code == 204

        dashboard_launch = client.post("/cam-adapter/dashboard/session", headers=admin_headers)
        assert dashboard_launch.status_code == 200
        dashboard_initial = client.get(
            dashboard_launch.json()["launch_path"], follow_redirects=False
        )
        assert dashboard_initial.status_code == 303
        dashboard = client.get("/adapter-backend-dashboard")
        assert dashboard.status_code == 200
        assert "Adapter Backend Dashboard" in dashboard.text
        assert "Live footage" in dashboard.text
        assert "connectCamera" in dashboard.text
        assert "@keyframes" not in dashboard.text
        assert "transition:" not in dashboard.text

        monitoring = client.get("/camera-monitoring-dashboard")
        assert monitoring.status_code == 200
        assert "H-CAM Monitoring Center" in monitoring.text
        assert "Adapter Backend" in monitoring.text
        assert "connectSelectedCamera" in monitoring.text
        assert "No analytics event API is connected" in monitoring.text
        assert "@keyframes" not in monitoring.text
        assert "transition:" not in monitoring.text

        monitoring_launch = client.post(
            "/cam-adapter/monitoring-dashboard/session", headers=admin_headers
        )
        assert monitoring_launch.status_code == 200
        assert monitoring_launch.json()["launch_path"].startswith(
            "/camera-monitoring-dashboard?launch="
        )

        dashboard_data = client.get("/cam-adapter/dashboard/data")
        assert dashboard_data.status_code == 200
        assert dashboard_data.json()["live_cameras_available"] is True
        assert dashboard_data.json()["live_cameras"][0]["camera_id"] == "corp8_1"

        def unavailable_live_cameras() -> tuple[object, ...]:
            raise AdapterRuntimeError("catalogue unavailable")

        monkeypatch.setattr(application.state.adapter_runtime, "live_cameras", unavailable_live_cameras)
        degraded_dashboard = client.get("/cam-adapter/dashboard/data")
        assert degraded_dashboard.status_code == 200
        assert degraded_dashboard.json()["live_cameras_available"] is False
        assert degraded_dashboard.json()["live_cameras"] == []

    assert deleted == ["https://live.corp8.cloud/stream/1/session/approved"]
