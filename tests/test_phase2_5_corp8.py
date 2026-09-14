from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from hcam.labs.sentinel.corp8 import (
    Corp8CatalogAdapter,
    Corp8PtsClock,
    Corp8StreamPolicy,
    corp8_rtsp_locator,
)
from hcam.labs.sentinel.models import CatalogValidationError
from hcam.labs.sentinel.dashboard import (
    DashboardSettings,
    corp8_online_policy,
    create_dashboard_app,
)
from hcam.labs.sentinel.corp8 import normalize_corp8_catalog_document
from hcam.labs.sentinel.models import CatalogEndpoint
from hcam.labs.sentinel.store import CatalogStore
from hcam.labs.sentinel.whep_proxy import SentinelWhepProxy


def test_corp8_minimal_catalogue_derives_only_exact_documented_transports() -> None:
    catalog = normalize_corp8_catalog_document(
        [{"id": "cam01", "name": "Camera One"}],
        origin="https://cctv.corp8.cloud/cameras.json",
        network_policy=corp8_online_policy(),
    )
    camera = catalog.cameras[0]
    assert camera.external_id == "cam01"
    assert camera.advertised_live is True
    assert [(item.role, item.locator) for item in camera.endpoints] == [
        ("fallback", "https://cctv.corp8.cloud/cam01/index.m3u8"),
        ("inference", "rtsp://103.250.160.189:8554/stream/cam01"),
        ("preview", "http://103.250.160.189:8889/stream/cam01/whep"),
    ]


@pytest.mark.parametrize(
    "payload, code",
    [
        ({"cameras": []}, "corp8_catalog_root_invalid"),
        ([{"id": "camera01", "name": "bad"}], "corp8_camera_id_invalid"),
        ([{"id": "cam01", "name": "a", "url": "https://bad"}], "corp8_camera_record_invalid"),
        ([{"id": "cam01", "name": "a"}, {"id": "cam01", "name": "b"}], "duplicate_camera_id"),
    ],
)
def test_corp8_catalogue_rejects_unexpected_shape_or_identity(
    payload: object, code: str
) -> None:
    with pytest.raises(CatalogValidationError, match=code):
        normalize_corp8_catalog_document(
            payload,
            origin="https://cctv.corp8.cloud/cameras.json",
            network_policy=corp8_online_policy(),
        )


def test_corp8_rtsp_locator_percent_encodes_private_credentials(tmp_path) -> None:
    email_file = tmp_path / "email"
    password_file = tmp_path / "password"
    email_file.write_text("operator@example.test", encoding="utf-8")
    password_file.write_text("pass word/with?reserved", encoding="utf-8")

    locator = corp8_rtsp_locator(
        "rtsp://103.250.160.189:8554/stream/cam01",
        email_file=email_file,
        password_file=password_file,
    )

    assert locator.startswith("rtsp://operator%40example.test:")
    assert locator.endswith("@103.250.160.189:8554/stream/cam01")
    assert "pass%20word%2Fwith%3Freserved" in locator


def test_corp8_rtsp_locator_rejects_non_contract_destination(tmp_path) -> None:
    email_file = tmp_path / "email"
    password_file = tmp_path / "password"
    email_file.write_text("operator@example.test", encoding="utf-8")
    password_file.write_text("password", encoding="utf-8")

    with pytest.raises(Exception, match="corp8_rtsp_locator_invalid"):
        corp8_rtsp_locator(
            "rtsp://outside.example:8554/stream/cam01",
            email_file=email_file,
            password_file=password_file,
        )


def test_corp8_stream_policy_uses_rtsp_tcp_and_bounded_exponential_backoff() -> None:
    policy = Corp8StreamPolicy()

    assert policy.rtsp_transport == "tcp"
    assert policy.timing_source == "pts"
    assert policy.recording_permitted is False
    assert policy.download_permitted is False
    assert [policy.reconnect_delay(attempt) for attempt in range(1, 8)] == [
        2,
        4,
        8,
        16,
        30,
        30,
        30,
    ]


def test_corp8_pts_clock_uses_pts_and_resets_on_discontinuity() -> None:
    clock = Corp8PtsClock()

    first = clock.observe(1000)
    second = clock.observe(1040)
    reset = clock.observe(15)
    clock.reset_for_scene_cut()
    after_cut = clock.observe(2000)

    assert first.delta_ms is None and first.discontinuity is False
    assert second.delta_ms == 40 and second.discontinuity is False
    assert reset.delta_ms is None and reset.discontinuity is True
    assert after_cut.delta_ms is None and after_cut.discontinuity is False


def test_corp8_adapter_uses_an_in_memory_authenticated_session(tmp_path) -> None:
    email_file = tmp_path / "email"
    password_file = tmp_path / "password"
    email_file.write_text("operator@example.test\n", encoding="utf-8")
    password_file.write_text("correct-horse\n", encoding="utf-8")
    store = CatalogStore(tmp_path / "corp8.db")
    store.initialize()
    store.upsert_source(
        source_id="corp8-camera-grid",
        catalog_locator="https://cctv.corp8.cloud/cameras.json",
        auth_mode="none",
        secret_ref=None,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/login":
            if request.method == "GET":
                return httpx.Response(200, request=request)
            assert request.method == "POST"
            assert request.content == b"email=operator%40example.test&password=correct-horse"
            assert request.headers["origin"] == "https://cctv.corp8.cloud"
            assert request.headers["referer"] == "https://cctv.corp8.cloud/auth/login"
            return httpx.Response(
                303,
                headers={
                    "location": "/",
                    "set-cookie": "session=short-lived; Path=/; Secure",
                },
                request=request,
            )
        assert request.url.path == "/cameras.json"
        assert request.headers["cookie"] == "session=short-lived"
        return httpx.Response(
            200,
            content=json.dumps([{"id": "cam01", "name": "Front gate"}]),
            request=request,
        )

    adapter = Corp8CatalogAdapter(
        store,
        corp8_online_policy(),
        email_file=email_file,
        password_file=password_file,
        transport=httpx.MockTransport(handler),
    )
    result = asyncio.run(
        adapter.refresh(
            "corp8-camera-grid", requester="pytest", reason="authenticated catalogue"
        )
    )

    assert result.status == "succeeded"
    assert result.record_count == 1
    stored = store.list_cameras("corp8-camera-grid", limit=5)
    assert stored[0]["external_camera_id"] == "cam01"


def test_corp8_adapter_rejects_form_response_without_an_authenticated_session(tmp_path) -> None:
    email_file = tmp_path / "email"
    password_file = tmp_path / "password"
    email_file.write_text("operator@example.test", encoding="utf-8")
    password_file.write_text("incorrect", encoding="utf-8")
    store = CatalogStore(tmp_path / "corp8.db")
    store.initialize()
    store.upsert_source(
        source_id="corp8-camera-grid",
        catalog_locator="https://cctv.corp8.cloud/cameras.json",
        auth_mode="none",
        secret_ref=None,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/login":
            return httpx.Response(200, request=request)
        raise AssertionError("catalogue must not be requested without a session")

    adapter = Corp8CatalogAdapter(
        store,
        corp8_online_policy(),
        email_file=email_file,
        password_file=password_file,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(Exception, match="catalog_authorization_failed"):
        asyncio.run(adapter.refresh("corp8-camera-grid", requester="pytest", reason="deny"))


def test_corp8_adapter_rejects_a_login_url_outside_the_fixed_origin(tmp_path) -> None:
    email_file = tmp_path / "email"
    password_file = tmp_path / "password"
    email_file.write_text("operator@example.test", encoding="utf-8")
    password_file.write_text("correct-horse", encoding="utf-8")
    store = CatalogStore(tmp_path / "corp8.db")
    store.initialize()
    store.upsert_source(
        source_id="corp8-camera-grid",
        catalog_locator="https://cctv.corp8.cloud/cameras.json",
        auth_mode="none",
        secret_ref=None,
    )
    adapter = Corp8CatalogAdapter(
        store,
        corp8_online_policy(),
        login_url="https://outside.example/auth/login",
        email_file=email_file,
        password_file=password_file,
        transport=httpx.MockTransport(lambda _request: httpx.Response(500)),
    )

    with pytest.raises(Exception, match="corp8_login_url_invalid"):
        asyncio.run(adapter.refresh("corp8-camera-grid", requester="pytest", reason="deny"))


def test_corp8_dashboard_keeps_unimported_cameras_unavailable(tmp_path) -> None:
    settings = DashboardSettings(
        state_path=tmp_path / "catalog.db",
        source_id="corp8-camera-grid",
        catalog_locator="https://cctv.corp8.cloud/cameras.json",
        catalog_mode="corp8-online",
        core_api_url="http://api:8000",
        public_whep_base_url="http://127.0.0.1:8890",
        media_evidence_path=None,
    )
    with TestClient(create_dashboard_app(settings)) as client:
        status = client.get("/api/status")
        switched = client.post(
            "/api/adapters/lab2lowadapter/activate",
            headers={
                "X-HCAM-Lab-Confirm": "corp8-authenticated-grid",
                "X-HCAM-Reason": "Use the lower local resource budget",
            },
        )
        after_switch = client.get("/api/status")
        preview = client.post("/api/cameras/cam01/playback")

    assert status.status_code == 200
    assert status.json()["adapter"]["adapter_id"] == "corp8-camera-grid"
    assert [item["adapter_id"] for item in status.json()["adapters"]] == [
        "lab1highadapter",
        "lab2lowadapter",
    ]
    assert status.json()["resource_profile"]["adapter_id"] == "lab1highadapter"
    assert status.json()["runtime_connection_limit"] == 30
    assert switched.status_code == 200
    assert switched.json()["quality_downgraded"] is True
    assert after_switch.json()["adapter"]["adapter_id"] == "corp8-camera-grid"
    assert after_switch.json()["resource_profile"]["adapter_id"] == "lab2lowadapter"
    assert after_switch.json()["runtime_connection_limit"] == 4
    assert status.json()["boundaries"]["organizer_sandbox"] is True
    assert status.json()["preview_relay_configured"] is False
    assert preview.status_code == 409
    assert preview.json()["detail"] == "Lab camera is not active"


def test_corp8_whep_proxy_uses_private_basic_auth_only_upstream() -> None:
    calls: list[tuple[str, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.headers.get("authorization")))
        if request.method == "POST":
            return httpx.Response(
                201,
                content=b"v=0\r\n",
                headers={
                    "content-type": "application/sdp",
                    "location": "/stream/cam01/session/private",
                },
                request=request,
            )
        return httpx.Response(204, request=request)

    proxy = SentinelWhepProxy(
        corp8_online_policy(), transport=httpx.MockTransport(handler)
    )
    endpoint = CatalogEndpoint(
        role="preview",
        protocol="http",
        locator="http://103.250.160.189:8889/stream/cam01/whep",
    )

    async def scenario() -> None:
        ticket = await proxy.issue(
            endpoint,
            limit=1,
            upstream_auth=httpx.BasicAuth("operator@example.test", "password"),
        )
        _answer, _resource = await proxy.negotiate(
            ticket.session_id, ticket.bearer_token, b"v=0\r\n"
        )
        await proxy.delete(ticket.session_id, ticket.bearer_token)

    asyncio.run(scenario())
    assert calls == [
        ("POST", "Basic b3BlcmF0b3JAZXhhbXBsZS50ZXN0OnBhc3N3b3Jk"),
        ("DELETE", "Basic b3BlcmF0b3JAZXhhbXBsZS50ZXN0OnBhc3N3b3Jk"),
    ]
