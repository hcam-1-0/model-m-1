from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from hcam.labs.sentinel import dashboard
from hcam.labs.sentinel.adapter import CatalogAdapterError
from hcam.labs.sentinel.dashboard import DashboardSettings, create_dashboard_app
from hcam.labs.sentinel.fixtures import generated_catalog_document
from hcam.labs.sentinel.models import normalize_catalog_document
from hcam.labs.sentinel.simulator import create_simulator_app


def test_generated_catalogue_simulator_supports_etag_and_modes(monkeypatch) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    with TestClient(create_simulator_app()) as client:
        first = client.get("/api/ingest")
        unchanged = client.get(
            "/api/ingest", headers={"If-None-Match": first.headers["etag"]}
        )
        compatibility = client.get("/api/ingest?mode=compatibility")
        empty = client.get("/api/ingest?scenario=empty")
        added = client.get("/api/ingest?mode=compatibility&scenario=new")
        malformed = client.get("/api/ingest?scenario=malformed")
        hostile = client.get("/api/ingest?scenario=unsupported")
        high = client.get("/api/ingest/lab1highadapter")
        low = client.get("/api/ingest/lab2lowadapter")

    assert first.status_code == 200
    assert len(first.json()["cameras"]) == 50
    assert sum(camera["live"] for camera in first.json()["cameras"]) == 30
    assert unchanged.status_code == 304
    assert len(compatibility.json()["cameras"]) == 12
    assert empty.json()["cameras"] == []
    assert len(added.json()["cameras"]) == 13
    assert malformed.json()["cameras"][0]["live"] == "yes"
    assert hostile.status_code == 422
    assert len(high.json()["cameras"]) == 50
    assert sum(camera["live"] for camera in high.json()["cameras"]) == 30
    assert high.headers["x-hcam-lab-adapter"] == "lab1highadapter"
    assert len(low.json()["cameras"]) == 12
    assert sum(camera["live"] for camera in low.json()["cameras"]) == 4
    assert low.headers["x-hcam-lab-adapter"] == "lab2lowadapter"
    assert first.headers["x-hcam-data-classification"] == "generated-only"


class FakeAdapter:
    def __init__(self, store, network_policy, **_kwargs) -> None:
        self.store = store
        self.network_policy = network_policy

    async def refresh(self, source_id: str, *, requester: str, reason: str):
        assert requester == "phase2-5-dashboard"
        assert len(reason) >= 8
        mode = "low" if source_id == "lab2lowadapter" else "default"
        catalog = normalize_catalog_document(
            generated_catalog_document(mode=mode),  # type: ignore[arg-type]
            origin="http://catalog-simulator:8090/api/ingest",
            network_policy=self.network_policy,
        )
        result = self.store.apply_snapshot(source_id, catalog)
        return SimpleNamespace(
            refresh_id="p25r_generated",
            status="succeeded",
            record_count=len(catalog.cameras),
            warning_count=catalog.warning_count,
            unchanged=False,
            snapshot_id=result["snapshot_id"],
        )


class FakePlaybackClient:
    def __init__(self, **_kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def post(self, _url: str, *, headers: dict[str, str]):
        assert headers["X-HCAM-Roles"] == "camera.viewer"
        return SimpleNamespace(
            status_code=201,
            json=lambda: {
                "access_token": "generated-token",
                "expires_at": "2030-01-01T00:00:00Z",
                "playback_url": "http://127.0.0.1:8888/hcam/generated/index.m3u8",
            },
        )


def write_media_evidence(path) -> None:
    path.write_text(
        json.dumps(
            {
                "classification": "generated-only",
                "fixture_count": 2,
                "parallelism": 1,
                "total_bytes": 1024,
                "accelerator": {"h264": {"accelerator": "cpu"}},
                "fixtures": [
                    {
                        "camera_id": "C01",
                        "probe": {
                            "codec": "h264",
                            "width": 1280,
                            "height": 720,
                            "fps": 25,
                            "has_b_frames": 0,
                        },
                    },
                    {
                        "camera_id": "C04",
                        "probe": {
                            "codec": "hevc",
                            "width": 1920,
                            "height": 1080,
                            "fps": 25,
                            "has_b_frames": 2,
                        },
                    },
                ],
            }
        ),
        encoding="ascii",
    )


def test_dashboard_is_separate_generated_only_surface(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeAdapter)
    media_evidence = tmp_path / "fixture-evidence.json"
    write_media_evidence(media_evidence)
    settings = DashboardSettings(
        state_path=tmp_path / "catalog.db",
        source_id="generated-sentinel",
        catalog_locator="http://catalog-simulator:8090/api/ingest",
        core_api_url="http://api:8000",
        public_whep_base_url="http://127.0.0.1:8889",
        media_evidence_path=media_evidence,
    )
    with TestClient(create_dashboard_app(settings)) as client:
        page = client.get("/")
        status = client.get("/api/status")
        cameras = client.get("/api/cameras?q=C01")
        incompatible_camera = client.get("/api/cameras?q=C04")
        denied_refresh = client.post(
            "/api/refresh",
            headers={
                "X-HCAM-Lab-Confirm": "wrong",
                "X-HCAM-Reason": "Generated refresh rejected",
            },
        )
        refreshed = client.post(
            "/api/refresh",
            headers={
                "X-HCAM-Lab-Confirm": "generated-only",
                "X-HCAM-Reason": "Generated refresh accepted",
            },
        )
        inactive_preview = client.post("/api/cameras/C31/playback")
        incompatible_preview = client.post("/api/cameras/C04/playback")
        metrics = client.get("/metrics")

        assert page.status_code == 200

        dashboard_script = client.get("/static/dashboard.js")
        assert dashboard_script.status_code == 200
        assert "trustedWhepResource" in dashboard_script.text
        assert "resource.origin !== base.origin" in dashboard_script.text
        assert "resource.pathname.startsWith(sessionPrefix)" in dashboard_script.text
        assert 'peer.connectionState === "connected"' in dashboard_script.text
        assert "Negotiating WHEP live feed" in dashboard_script.text
        assert "ensureLiveFeed" in dashboard_script.text
        assert "state.autoStartAttempted = true" in dashboard_script.text
        assert "video.play().catch" in dashboard_script.text
        assert "const cleanupTargets = []" in dashboard_script.text
        assert "if (state.cleanupUrl) cleanupTargets.push" in dashboard_script.text
        assert "else if (state.resource) cleanupTargets.push" in dashboard_script.text
        assert "function autoPreviewCamera()" in dashboard_script.text
        assert "leftPixels - rightPixels" in dashboard_script.text
        assert "state.pendingPreview" in dashboard_script.text
        assert "state.startAbortController.abort()" in dashboard_script.text
        assert "schedulePreviewReconnect" in dashboard_script.text
        assert "expiresAt - Date.now() - 10000" in dashboard_script.text
    assert "H-CAM CORP8 Camera Grid" in page.text
    assert "CORP8 Camera Grid" in page.text
    assert "controls" in page.text
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    assert status.json()["boundaries"] == {
        "test_dashboard_only": True,
        "main_dashboard": False,
        "government_data": False,
        "organizer_sandbox": False,
        "recording": False,
        "analytics": False,
    }
    assert status.json()["counts"]["total"] == 50
    assert status.json()["adapter"]["adapter_id"] == "lab1highadapter"
    assert len(status.json()["adapters"]) == 2
    assert status.json()["observed_health_counts"] == {"offline": 20, "unknown": 30}
    assert cameras.json()["total"] == 1
    assert cameras.json()["items"][0]["observed_media"]["codec"] == "h264"
    assert cameras.json()["items"][0]["preview_compatible"] is True
    assert incompatible_camera.json()["items"][0]["media"]["codec"] == "h264"
    assert incompatible_camera.json()["items"][0]["observed_media"]["codec"] == "hevc"
    assert incompatible_camera.json()["items"][0]["preview_compatible"] is False
    assert denied_refresh.status_code == 403
    assert refreshed.status_code == 200
    assert inactive_preview.status_code == 409
    assert incompatible_preview.status_code == 409
    assert "hcam_phase2_5_catalog_refresh_total" in metrics.text


def test_dashboard_switches_durable_lab_profiles_without_touching_main_adapter(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeAdapter)
    adapter_state = tmp_path / "active-lab-adapter.json"
    settings = DashboardSettings(
        state_path=tmp_path / "catalog.db",
        source_id="legacy-generated-sentinel",
        catalog_locator="http://catalog-simulator:8090/api/ingest",
        core_api_url="http://api:8000",
        public_whep_base_url="http://127.0.0.1:8889",
        media_evidence_path=None,
        adapter_state_path=adapter_state,
    )

    with TestClient(create_dashboard_app(settings)) as client:
        high = client.get("/api/status")
        denied = client.post(
            "/api/adapters/lab2lowadapter/activate",
            headers={
                "X-HCAM-Lab-Confirm": "wrong",
                "X-HCAM-Reason": "Generated low profile switch",
            },
        )
        switched = client.post(
            "/api/adapters/lab2lowadapter/activate",
            headers={
                "X-HCAM-Lab-Confirm": "generated-only",
                "X-HCAM-Reason": "Generated low profile switch",
            },
        )
        low = client.get("/api/status")
        low_cameras = client.get("/api/cameras")

    assert high.json()["counts"]["total"] == 50
    assert high.json()["counts"]["advertised_live"] == 30
    assert denied.status_code == 403
    assert switched.status_code == 200
    assert switched.json()["quality_downgraded"] is False
    assert low.json()["adapter"]["adapter_id"] == "lab2lowadapter"
    assert low.json()["counts"]["total"] == 12
    assert low.json()["counts"]["advertised_live"] == 4
    assert low_cameras.json()["total"] == 12
    assert "legacy-generated-sentinel" not in adapter_state.read_text(encoding="ascii")


def test_dashboard_allows_only_observed_whep_compatible_media(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeAdapter)
    monkeypatch.setattr(dashboard.httpx, "AsyncClient", FakePlaybackClient)
    media_evidence = tmp_path / "fixture-evidence.json"
    write_media_evidence(media_evidence)
    settings = DashboardSettings(
        state_path=tmp_path / "catalog.db",
        source_id="generated-sentinel",
        catalog_locator="http://catalog-simulator:8090/api/ingest",
        core_api_url="http://api:8000",
        public_whep_base_url="http://127.0.0.1:8889",
        media_evidence_path=media_evidence,
    )

    with TestClient(create_dashboard_app(settings)) as client:
        allowed = client.post("/api/cameras/C01/playback")
        denied = client.post("/api/cameras/C04/playback")

    assert allowed.status_code == 200
    assert allowed.json()["whep_url"].endswith(
        "/hcam/str_00000000000000000000000000000001/whep"
    )
    assert denied.status_code == 409


def test_generated_document_does_not_copy_external_identity() -> None:
    rendered = str(generated_catalog_document())

    assert "sentinel.gujarat.gov.in" not in rendered
    assert "corp8.cloud" not in rendered
    assert "Government" not in rendered


class FailingAdapter(FakeAdapter):
    async def refresh(self, source_id: str, *, requester: str, reason: str):
        raise CatalogAdapterError("generated_catalog_unavailable")


class LowFailingAdapter(FakeAdapter):
    async def refresh(self, source_id: str, *, requester: str, reason: str):
        if source_id == "lab2lowadapter":
            raise CatalogAdapterError("generated_low_catalog_unavailable")
        return await super().refresh(source_id, requester=requester, reason=reason)


def dashboard_settings(tmp_path, *, media_evidence_path=None, **updates):
    values = {
        "state_path": tmp_path / "catalog.db",
        "source_id": "generated-sentinel",
        "catalog_locator": "http://catalog-simulator:8090/api/ingest",
        "core_api_url": "http://api:8000",
        "public_whep_base_url": "http://127.0.0.1:8889",
        "media_evidence_path": media_evidence_path,
    }
    values.update(updates)
    return DashboardSettings(**values)


def test_dashboard_auxiliary_routes_filters_and_invalid_identifiers(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeAdapter)
    with TestClient(create_dashboard_app(dashboard_settings(tmp_path))) as client:
        css = client.get("/static/dashboard.css")
        health = client.get("/health")
        active = client.get("/api/cameras?state=active")
        h264 = client.get("/api/cameras?codec=h264")
        events = client.get("/api/events?limit=5")
        unknown_adapter = client.post(
            "/api/adapters/main-adapter/activate",
            headers={
                "X-HCAM-Lab-Confirm": "generated-only",
                "X-HCAM-Reason": "Reject unknown generated adapter",
            },
        )
        invalid_camera = client.post("/api/cameras/not-a-camera/playback")

    assert css.status_code == 200
    assert health.json()["adapter_id"] == "lab1highadapter"
    assert active.json()["total"] == 30
    assert h264.json()["total"] == 25
    assert events.status_code == 200
    assert unknown_adapter.status_code == 404
    assert invalid_camera.status_code == 404


def test_dashboard_startup_and_refresh_fail_closed(tmp_path, monkeypatch) -> None:
    with pytest.raises(ValueError, match="refresh interval"):
        create_dashboard_app(dashboard_settings(tmp_path, refresh_interval_seconds=1))

    monkeypatch.delenv("HCAM_ALLOW_SYNTHETIC_LAB", raising=False)
    with pytest.raises(RuntimeError, match="HCAM_ALLOW_SYNTHETIC_LAB"):
        with TestClient(create_dashboard_app(dashboard_settings(tmp_path))):
            pass

    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    invalid_state = tmp_path / "invalid-adapter-state.json"
    invalid_state.write_text("not-json", encoding="ascii")
    with pytest.raises(RuntimeError, match="lab_adapter_state_invalid"):
        with TestClient(
            create_dashboard_app(
                dashboard_settings(tmp_path, adapter_state_path=invalid_state)
            )
        ):
            pass

    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FailingAdapter)
    with TestClient(create_dashboard_app(dashboard_settings(tmp_path))) as client:
        health = client.get("/health")
        refresh = client.post(
            "/api/refresh",
            headers={
                "X-HCAM-Lab-Confirm": "generated-only",
                "X-HCAM-Reason": "Generated refresh dependency failure",
            },
        )
    assert health.json()["initial_refresh_error"] == "generated_catalog_unavailable"
    assert refresh.status_code == 502


def test_dashboard_switch_waits_for_publisher_and_rolls_back_on_refresh_failure(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", LowFailingAdapter)
    readiness_checks = []

    async def ready(_path, profile, *, timeout_seconds=20):
        readiness_checks.append((profile.adapter_id, timeout_seconds))
        return {
            "adapter_id": profile.adapter_id,
            "active_stream_count": profile.active_stream_count,
            "stream_copy": True,
            "quality_downgraded": False,
        }

    monkeypatch.setattr(dashboard, "_await_publisher_profile", ready)
    adapter_state = tmp_path / "active-adapter.json"
    with TestClient(
        create_dashboard_app(
            dashboard_settings(
                tmp_path,
                adapter_state_path=adapter_state,
                publisher_state_path=tmp_path / "publisher.json",
                require_publisher_state=True,
            )
        )
    ) as client:
        failed = client.post(
            "/api/adapters/lab2lowadapter/activate",
            headers={
                "X-HCAM-Lab-Confirm": "generated-only",
                "X-HCAM-Reason": "Generated switch rollback validation",
            },
        )
        status = client.get("/api/status")

    assert failed.status_code == 503
    assert "generated_low_catalog_unavailable" in failed.json()["detail"]
    assert status.json()["adapter"]["adapter_id"] == "lab1highadapter"
    assert [item[0] for item in readiness_checks] == [
        "lab1highadapter",
        "lab2lowadapter",
        "lab1highadapter",
    ]


class PlaybackFailureClient:
    mode = "transport"

    def __init__(self, **_kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def post(self, _url: str, *, headers: dict[str, str]):
        assert headers["X-HCAM-Roles"] == "camera.viewer"
        if self.mode == "transport":
            raise httpx.ConnectError("generated playback unavailable")
        if self.mode == "not-ready":
            return SimpleNamespace(status_code=409)
        return SimpleNamespace(status_code=201, json=lambda: {"unexpected": True})


@pytest.mark.parametrize(
    ("mode", "expected_status"),
    [("transport", 502), ("not-ready", 409), ("invalid-response", 502)],
)
def test_dashboard_playback_dependency_failures_are_sanitized(
    tmp_path, monkeypatch, mode, expected_status
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SYNTHETIC_LAB", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeAdapter)
    PlaybackFailureClient.mode = mode
    monkeypatch.setattr(dashboard.httpx, "AsyncClient", PlaybackFailureClient)
    media_evidence = tmp_path / "fixture-evidence.json"
    write_media_evidence(media_evidence)
    with TestClient(
        create_dashboard_app(
            dashboard_settings(tmp_path, media_evidence_path=media_evidence)
        )
    ) as client:
        response = client.post("/api/cameras/C01/playback")
    assert response.status_code == expected_status
