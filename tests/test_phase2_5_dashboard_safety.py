from __future__ import annotations

import asyncio
import json
from urllib.parse import urlsplit

import httpx
import pytest

from hcam.labs.sentinel import dashboard
from hcam.labs.sentinel.adapter import CatalogAdapterError
from hcam.labs.sentinel.dashboard import DashboardSettings
from hcam.labs.sentinel.fixtures import generated_catalog_document
from hcam.labs.sentinel.lab_adapters import (
    LAB1_HIGH_ADAPTER,
    LabAdapterStateError,
)
from hcam.labs.sentinel.models import CatalogValidationError, normalize_catalog_document


def generated_document(**updates) -> dict[str, object]:
    document: dict[str, object] = {
        "classification": "generated-only",
        "fixture_count": 50,
        "parallelism": 4,
        "total_bytes": 1024,
        "accelerator": {"h264": {"accelerator": "nvidia"}},
        "fixtures": [],
    }
    document.update(updates)
    return document


def write_json(path, document) -> None:
    path.write_text(json.dumps(document), encoding="ascii")


def test_dashboard_settings_and_exact_generated_policy(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HCAM_PHASE2_5_STATE_PATH", str(tmp_path / "catalog.db"))
    monkeypatch.setenv("HCAM_PHASE2_5_MEDIA_EVIDENCE", str(tmp_path / "media.json"))
    monkeypatch.setenv(
        "HCAM_PHASE2_5_ADAPTER_STATE_PATH", str(tmp_path / "adapter.json")
    )
    monkeypatch.setenv(
        "HCAM_PHASE2_5_PUBLISHER_STATE_PATH", str(tmp_path / "publisher.json")
    )
    monkeypatch.setenv("HCAM_PHASE2_5_REQUIRE_PUBLISHER_STATE", "true")
    monkeypatch.setenv("HCAM_PHASE2_5_REFRESH_INTERVAL_SECONDS", "120")

    settings = DashboardSettings.from_environment()

    assert settings.state_path == tmp_path / "catalog.db"
    assert settings.media_evidence_path == tmp_path / "media.json"
    assert settings.adapter_state_path == tmp_path / "adapter.json"
    assert settings.publisher_state_path == tmp_path / "publisher.json"
    assert settings.require_publisher_state is True
    assert settings.refresh_interval_seconds == 120
    policy = dashboard.generated_lab_policy()
    policy.validate(
        "rtsp://mediamtx:8554/hcam/generated",
        origin="http://catalog-simulator:8090/api/ingest",
        role="inference",
    )
    with pytest.raises(CatalogValidationError):
        policy.validate(
            "https://external.invalid/camera",
            origin="http://catalog-simulator:8090/api/ingest",
            role="inference",
        )


def test_generated_media_evidence_fails_closed(tmp_path) -> None:
    missing = tmp_path / "missing.json"
    assert dashboard._generated_media_evidence(None) is None
    assert dashboard._generated_media_evidence(missing) is None

    missing.write_text("not-json", encoding="ascii")
    assert dashboard._generated_media_evidence(missing) is None
    write_json(missing, {"classification": "external"})
    assert dashboard._generated_media_evidence(missing) is None
    missing.write_bytes(b"x" * (1024 * 1024 + 1))
    assert dashboard._generated_media_evidence(missing) is None

    write_json(missing, generated_document(accelerator="invalid"))
    safe = dashboard._safe_media_evidence(missing)
    assert safe == {
        "fixture_count": 50,
        "parallelism": 4,
        "total_bytes": 1024,
        "accelerator": None,
    }


@pytest.mark.parametrize(
    "document",
    [
        "not-json",
        [],
        {"classification": "external"},
        {
            "classification": "generated-only",
            "adapter_id": "unknown",
            "active_stream_count": 30,
        },
        {
            "classification": "generated-only",
            "adapter_id": "lab1highadapter",
            "active_stream_count": 0,
        },
    ],
)
def test_publisher_state_parser_rejects_untrusted_documents(tmp_path, document) -> None:
    path = tmp_path / "publisher-state.json"
    if isinstance(document, str):
        path.write_text(document, encoding="ascii")
    else:
        write_json(path, document)
    assert dashboard._safe_publisher_state(path) is None


def test_publisher_state_requires_explicit_no_downgrade_and_exact_profile(
    tmp_path,
) -> None:
    path = tmp_path / "publisher-state.json"
    write_json(
        path,
        {
            "classification": "generated-only",
            "adapter_id": "lab1highadapter",
            "active_stream_count": 30,
            "stream_copy": True,
            "quality_downgraded": False,
        },
    )
    assert dashboard._safe_publisher_state(path) == {
        "adapter_id": "lab1highadapter",
        "active_stream_count": 30,
        "stream_copy": True,
        "quality_downgraded": False,
    }
    ready = asyncio.run(
        dashboard._await_publisher_profile(path, LAB1_HIGH_ADAPTER, timeout_seconds=0)
    )
    assert ready["active_stream_count"] == 30

    write_json(
        path,
        {
            "classification": "generated-only",
            "adapter_id": "lab1highadapter",
            "active_stream_count": 30,
            "stream_copy": False,
            "quality_downgraded": True,
        },
    )
    with pytest.raises(LabAdapterStateError, match="publisher_not_ready"):
        asyncio.run(
            dashboard._await_publisher_profile(
                path, LAB1_HIGH_ADAPTER, timeout_seconds=0
            )
        )


def test_observed_media_accepts_only_bounded_generated_probe_data(tmp_path) -> None:
    path = tmp_path / "media.json"
    write_json(path, generated_document(fixtures="invalid"))
    assert dashboard._observed_media(path) == {}
    write_json(path, generated_document(fixtures=[{}] * 51))
    assert dashboard._observed_media(path) == {}

    fixtures = [
        "invalid",
        {"camera_id": "../../C01", "probe": {}},
        {"camera_id": "C01", "probe": {"codec": "vp9"}},
        {"camera_id": "C02", "probe": {"codec": "h264"}},
        {
            "camera_id": "C03",
            "probe": {
                "codec": "h264",
                "width": "1280",
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
                "fps": 30,
                "has_b_frames": 2,
            },
        },
    ]
    write_json(path, generated_document(fixtures=fixtures))
    observed = dashboard._observed_media(path)
    assert set(observed) == {"C03", "C04"}
    assert observed["C03"]["preview_compatible"] is True
    assert observed["C04"]["preview_compatible"] is False

    active = {
        "external_camera_id": "C03",
        "advertised_live": True,
        "lifecycle_state": "active",
    }
    inactive = {**active, "lifecycle_state": "inactive"}
    assert (
        dashboard._with_observed_media(active, observed)["preview_compatible"] is True
    )
    assert (
        dashboard._with_observed_media(inactive, observed)["preview_compatible"]
        is False
    )


def test_adapter_catalog_locator_replaces_path_without_leaking_query() -> None:
    locator = dashboard._adapter_catalog_locator(
        "http://catalog-simulator:8090/legacy?token=forbidden", LAB1_HIGH_ADAPTER
    )
    assert locator == "http://catalog-simulator:8090/api/ingest/lab1highadapter"
    with pytest.raises(ValueError, match=r"HTTP\(S\) absolute"):
        dashboard._adapter_catalog_locator("/relative", LAB1_HIGH_ADAPTER)


class FakeHealthResponse:
    def __init__(self, *, status_code=200, document=None, content=b"{}") -> None:
        self.status_code = status_code
        self.document = document
        self.content = content

    def json(self):
        if isinstance(self.document, Exception):
            raise self.document
        return self.document


class FakeHealthClient:
    response = FakeHealthResponse(document={"items": []})
    error: Exception | None = None

    def __init__(self, **_kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def get(self, url: str):
        assert url == "http://mediamtx:9997/v3/paths/list"
        if self.error is not None:
            raise self.error
        return self.response


def normalized_low_catalog():
    return normalize_catalog_document(
        generated_catalog_document(mode="low"),
        origin="http://catalog-simulator:8090/api/ingest/lab2lowadapter",
        network_policy=dashboard.generated_lab_policy(),
    )


def test_candidate_health_maps_only_ready_generated_paths(monkeypatch) -> None:
    catalog = normalized_low_catalog()
    first_inference = next(
        endpoint
        for endpoint in catalog.cameras[0].endpoints
        if endpoint.role == "inference"
    )
    path = urlsplit(first_inference.locator).path.lstrip("/")
    FakeHealthClient.error = None
    FakeHealthClient.response = FakeHealthResponse(
        document={
            "items": [
                {"name": path, "ready": True},
                {"name": "ignored", "ready": False},
                "invalid",
            ]
        }
    )
    monkeypatch.setattr(dashboard.httpx, "AsyncClient", FakeHealthClient)

    health = asyncio.run(
        dashboard._candidate_health(catalog, mediamtx_api_url="http://mediamtx:9997/")
    )

    assert health["C01"] is True
    assert health["C02"] is False
    assert health["C05"] is True


@pytest.mark.parametrize(
    "response",
    [
        FakeHealthResponse(status_code=503, document={"items": []}),
        FakeHealthResponse(document={"items": []}, content=b"x" * (1024 * 1024 + 1)),
        FakeHealthResponse(document=ValueError("invalid json")),
        FakeHealthResponse(document={"items": "invalid"}),
    ],
)
def test_candidate_health_fails_closed(monkeypatch, response) -> None:
    FakeHealthClient.error = None
    FakeHealthClient.response = response
    monkeypatch.setattr(dashboard.httpx, "AsyncClient", FakeHealthClient)
    with pytest.raises(CatalogAdapterError):
        asyncio.run(
            dashboard._candidate_health(
                normalized_low_catalog(), mediamtx_api_url="http://mediamtx:9997"
            )
        )

    FakeHealthClient.error = httpx.ConnectError("generated upstream unavailable")
    with pytest.raises(CatalogAdapterError, match="candidate_health_unavailable"):
        asyncio.run(
            dashboard._candidate_health(
                normalized_low_catalog(), mediamtx_api_url="http://mediamtx:9997"
            )
        )
    FakeHealthClient.error = None


def test_dashboard_main_requires_explicit_non_loopback_and_starts_uvicorn(
    monkeypatch,
) -> None:
    assert dashboard.main(["--bind", "0.0.0.0"]) == 2
    calls = []
    monkeypatch.setattr(
        dashboard.uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    assert dashboard.main(["--bind", "0.0.0.0", "--allow-non-loopback"]) == 0
    assert calls[0][1] == {"host": "0.0.0.0", "port": 8091, "access_log": False}
