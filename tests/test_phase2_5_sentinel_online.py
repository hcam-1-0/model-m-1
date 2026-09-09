from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from prometheus_client import generate_latest

from hcam.labs.sentinel import dashboard
from hcam.labs.sentinel.dashboard import (
    DashboardSettings,
    create_dashboard_app,
    sentinel_online_policy,
)
from hcam.labs.sentinel.hls_relay import HlsRelayError, SentinelHlsRelay
from hcam.labs.sentinel.models import CatalogEndpoint, normalize_catalog_document
from hcam.labs.sentinel.whep_proxy import SentinelWhepProxy, WhepProxyError


def sentinel_catalog_document() -> dict[str, object]:
    return {
        "cameras": [
            {
                "id": "1",
                "number": 1,
                "name": "Camera 1",
                "location": "Sentinel Lab Zone 1",
                "codec": "h264",
                "live": True,
                "width": 1920,
                "height": 1080,
                "fps": 25,
                "bitrate_kbps": 2000,
                "bits_per_pixel": 0.04,
                "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/1",
                "webrtc_url": "http://live.corp8.cloud:8889/stream/1/whep",
                "hls_live_url": "/live/stream/1/index.m3u8",
            },
            {
                "id": "2",
                "number": 2,
                "name": "Camera 2",
                "location": "Sentinel Lab Zone 2",
                "codec": "",
                "live": True,
                "width": 0,
                "height": 0,
                "fps": 0,
                "bitrate_kbps": 0,
                "bits_per_pixel": 0,
                "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/2",
                "webrtc_url": "http://live.corp8.cloud:8889/stream/2/whep",
                "hls_live_url": "/live/stream/2/index.m3u8",
            },
        ]
    }


class FakeOnlineAdapter:
    locators: list[str] = []

    def __init__(self, store, network_policy, **kwargs) -> None:
        self.store = store
        self.network_policy = network_policy
        assert kwargs["max_records"] == 50

    async def refresh(self, source_id: str, *, requester: str, reason: str):
        assert requester == "phase2-5-dashboard"
        assert len(reason) >= 8
        source = self.store.get_source_config(source_id)
        assert source is not None
        self.locators.append(source.catalog_locator)
        catalog = normalize_catalog_document(
            sentinel_catalog_document(),
            origin=source.catalog_locator,
            network_policy=self.network_policy,
            max_records=50,
        )
        result = self.store.apply_snapshot(source_id, catalog)
        return SimpleNamespace(
            refresh_id="p25r_sentinel",
            status="succeeded",
            record_count=len(catalog.cameras),
            warning_count=catalog.warning_count,
            unchanged=False,
            snapshot_id=result["snapshot_id"],
        )


def online_settings(tmp_path) -> DashboardSettings:
    return DashboardSettings(
        state_path=tmp_path / "sentinel-online.db",
        source_id="sentinel-online",
        catalog_locator="https://live.corp8.cloud/api/ingest",
        core_api_url="http://api:8000",
        public_whep_base_url="http://127.0.0.1:8889",
        media_evidence_path=None,
        catalog_mode="sentinel-online",
    )


def test_both_lab_profiles_use_same_online_catalogue_with_different_limits(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SENTINEL_SANDBOX", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeOnlineAdapter)
    FakeOnlineAdapter.locators = []

    def whep_handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            assert request.url == "http://live.corp8.cloud:8889/stream/1/whep"
            assert request.headers["content-type"] == "application/sdp"
            return httpx.Response(
                201,
                headers={
                    "Content-Type": "application/sdp",
                    "Location": "/stream/1/session/test-session",
                },
                content=b"v=0\r\n",
            )
        assert request.method == "DELETE"
        assert request.url.path == "/stream/1/session/test-session"
        return httpx.Response(204)

    with TestClient(create_dashboard_app(online_settings(tmp_path))) as client:
        client.app.state.whep_proxy.transport = httpx.MockTransport(whep_handler)
        high = client.get("/api/status")
        cameras = client.get("/api/cameras")
        playback = client.post("/api/cameras/1/playback?transport=direct-whep")
        session = playback.json()
        offer = client.post(
            session["whep_url"],
            headers={
                "Authorization": f"Bearer {session['access_token']}",
                "Content-Type": "application/sdp",
            },
            content=b"v=0\r\n",
        )
        closed = client.delete(
            offer.headers["location"],
            headers={"Authorization": f"Bearer {session['access_token']}"},
        )
        switched = client.post(
            "/api/adapters/lab2lowadapter/activate",
            headers={
                "X-HCAM-Lab-Confirm": "sentinel-sandbox",
                "X-HCAM-Reason": "Switch to bounded low resource profile",
            },
        )
        low = client.get("/api/status")

    assert high.json()["classification"] == "sentinel-sandbox"
    assert high.json()["counts"]["total"] == 2
    assert high.json()["runtime_connection_limit"] == 30
    assert high.json()["adapter"]["preview_session_limit"] == 4
    assert high.headers["x-hcam-data-classification"] == "sentinel-sandbox"
    assert cameras.json()["total"] == 2
    assert all(item["preview_compatible"] for item in cameras.json()["items"])
    assert all("locator" not in str(item) for item in cameras.json()["items"])
    assert playback.status_code == 200
    assert session["whep_url"].startswith("/api/whep/")
    assert "live.corp8.cloud" not in str(session)
    assert offer.status_code == 201
    assert offer.text == "v=0\r\n"
    assert closed.status_code == 204
    assert switched.status_code == 200
    assert low.json()["counts"]["total"] == 2
    assert low.json()["runtime_connection_limit"] == 4
    assert low.json()["adapter"]["preview_session_limit"] == 1
    assert FakeOnlineAdapter.locators == [
        "https://live.corp8.cloud/api/ingest",
        "https://live.corp8.cloud/api/ingest",
    ]


def test_whep_proxy_is_bounded_authenticated_and_zero_retention() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.method == "POST":
            return httpx.Response(
                201,
                headers={
                    "Content-Type": "application/sdp; charset=utf-8",
                    "Location": "/stream/1/session/abc",
                },
                content=b"v=0\r\n",
            )
        return httpx.Response(204)

    proxy = SentinelWhepProxy(
        sentinel_online_policy(), transport=httpx.MockTransport(handler)
    )
    endpoint = CatalogEndpoint(
        role="preview",
        protocol="http",
        locator="http://live.corp8.cloud:8889/stream/1/whep",
    )

    async def scenario() -> None:
        ticket = await proxy.issue(endpoint, limit=1)
        with pytest.raises(WhepProxyError, match="whep_session_limit_reached"):
            await proxy.issue(endpoint, limit=1)
        with pytest.raises(WhepProxyError, match="whep_session_unauthorized"):
            await proxy.negotiate(ticket.session_id, "wrong", b"v=0\r\n")
        answer, resource = await proxy.negotiate(
            ticket.session_id, ticket.bearer_token, b"v=0\r\n"
        )
        assert answer == b"v=0\r\n"
        assert resource == "http://live.corp8.cloud:8889/stream/1/session/abc"
        await proxy.delete(ticket.session_id, ticket.bearer_token)
        await proxy.close()

    asyncio.run(scenario())
    assert calls == [
        ("POST", "/stream/1/whep"),
        ("DELETE", "/stream/1/session/abc"),
    ]


def _runtime_whep_session(client: TestClient) -> dict[str, str]:
    response = client.post("/api/cameras/1/playback?transport=direct-whep")
    assert response.status_code == 200
    return response.json()


def _runtime_errors(client: TestClient) -> list[dict[str, str]]:
    response = client.get("/api/status")
    assert response.status_code == 200
    return response.json()["observability"]["errors"]


def test_whep_preview_timeout_is_observed_through_runtime_route(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SENTINEL_SANDBOX", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeOnlineAdapter)

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("controlled timeout", request=request)

    with TestClient(create_dashboard_app(online_settings(tmp_path))) as client:
        client.app.state.whep_proxy.transport = httpx.MockTransport(timeout_handler)
        session = _runtime_whep_session(client)
        response = client.post(
            session["whep_url"],
            headers={
                "Authorization": f"Bearer {session['access_token']}",
                "Content-Type": "application/sdp",
            },
            content=b"v=0\r\n",
        )

        assert response.status_code == 502
        assert _runtime_errors(client) == [
            {"component": "preview", "error_code": "preview_timeout"}
        ]
        event = client.app.state.observability.events[-1]
        assert event.component == "preview"
        assert event.error_code == "preview_timeout"
        assert len(event.correlation_id) == 32
        metrics = generate_latest(client.app.state.metrics_registry).decode("utf-8")
        assert 'hcam_phase2_5_failures_total{component="preview",error_code="preview_timeout"} 1.0' in metrics


def test_whep_transport_failure_is_relay_unavailable_but_rejection_is_not(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SENTINEL_SANDBOX", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeOnlineAdapter)

    def network_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("controlled connection refusal", request=request)

    with TestClient(create_dashboard_app(online_settings(tmp_path))) as client:
        client.app.state.whep_proxy.transport = httpx.MockTransport(network_handler)
        session = _runtime_whep_session(client)
        unavailable = client.post(
            session["whep_url"],
            headers={
                "Authorization": f"Bearer {session['access_token']}",
                "Content-Type": "application/sdp",
            },
            content=b"v=0\r\n",
        )
        assert unavailable.status_code == 502
        assert _runtime_errors(client) == [
            {"component": "relay", "error_code": "mediamtx_unavailable"}
        ]

        client.app.state.whep_proxy.transport = httpx.MockTransport(
            lambda request: httpx.Response(502, request=request)
        )
        rejected_session = _runtime_whep_session(client)
        rejected = client.post(
            rejected_session["whep_url"],
            headers={
                "Authorization": f"Bearer {rejected_session['access_token']}",
                "Content-Type": "application/sdp",
            },
            content=b"v=0\r\n",
        )
        assert rejected.status_code == 502
        assert _runtime_errors(client) == [
            {"component": "relay", "error_code": "mediamtx_unavailable"}
        ]


def test_whep_cleanup_failure_is_observed_through_runtime_route(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("HCAM_ALLOW_SENTINEL_SANDBOX", "true")
    monkeypatch.setattr(dashboard, "SentinelCatalogAdapter", FakeOnlineAdapter)

    def negotiate_then_fail_cleanup(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                201,
                headers={
                    "Content-Type": "application/sdp",
                    "Location": "/stream/1/session/cleanup-test",
                },
                content=b"v=0\r\n",
                request=request,
            )
        raise httpx.ConnectError("controlled cleanup refusal", request=request)

    with TestClient(create_dashboard_app(online_settings(tmp_path))) as client:
        client.app.state.whep_proxy.transport = httpx.MockTransport(
            negotiate_then_fail_cleanup
        )
        session = _runtime_whep_session(client)
        offer = client.post(
            session["whep_url"],
            headers={
                "Authorization": f"Bearer {session['access_token']}",
                "Content-Type": "application/sdp",
            },
            content=b"v=0\r\n",
        )
        assert offer.status_code == 201
        cleanup = client.delete(
            offer.headers["location"],
            headers={"Authorization": f"Bearer {session['access_token']}"},
        )

        assert cleanup.status_code == 502
        assert _runtime_errors(client) == [
            {"component": "cleanup", "error_code": "cleanup_failed"}
        ]
        event = client.app.state.observability.events[-1]
        assert event.component == "cleanup"
        assert event.error_code == "cleanup_failed"
        assert len(event.correlation_id) == 32


def test_hls_relay_uses_stream_copy_and_terminates_without_media_files(
    monkeypatch,
) -> None:
    command: tuple[object, ...] = ()

    class FakeProcess:
        returncode = None
        terminated = False

        def terminate(self) -> None:
            self.terminated = True
            self.returncode = 0

        async def wait(self) -> int:
            return 0

        def kill(self) -> None:
            self.returncode = -9

    process = FakeProcess()

    async def create_process(*args, **kwargs):
        nonlocal command
        command = args
        assert kwargs["stdin"] == asyncio.subprocess.DEVNULL
        assert kwargs["stdout"] == asyncio.subprocess.DEVNULL
        assert kwargs["stderr"] == asyncio.subprocess.DEVNULL
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_process)
    relay = SentinelHlsRelay(
        sentinel_online_policy(),
        mediamtx_api_url="http://sentinel-mediamtx:9997",
        publish_base_url="rtsp://sentinel-mediamtx:8554/hcam-sentinel",
        public_whep_base_url="http://127.0.0.1:8890/hcam-sentinel",
    )

    async def ready(_relay) -> None:
        return None

    monkeypatch.setattr(relay, "_wait_ready", ready)
    endpoint = CatalogEndpoint(
        role="fallback",
        protocol="https",
        locator="https://live.corp8.cloud/live/stream/1/index.m3u8",
    )

    async def scenario() -> None:
        ticket = await relay.issue(endpoint, limit=1)
        with pytest.raises(HlsRelayError, match="hls_relay_limit_reached"):
            await relay.issue(endpoint, limit=1)
        with pytest.raises(HlsRelayError, match="hls_relay_unauthorized"):
            await relay.delete(ticket.session_id, "wrong")
        await relay.delete(ticket.session_id, ticket.bearer_token)
        assert ticket.whep_url.startswith("http://127.0.0.1:8890/hcam-sentinel/")

    asyncio.run(scenario())
    assert "-c:v" in command
    assert command[command.index("-c:v") + 1] == "copy"
    assert command[command.index("-reconnect") + 1] == "1"
    assert command[command.index("-http_persistent") + 1] == "0"
    assert "https://live.corp8.cloud/live/stream/1/index.m3u8?cookieCheck=1" in command
    assert not any(str(item).endswith((".mp4", ".mkv", ".ts")) for item in command)
    assert process.terminated is True
