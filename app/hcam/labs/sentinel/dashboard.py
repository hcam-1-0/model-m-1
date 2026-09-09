from __future__ import annotations

import asyncio
from time import perf_counter
import json
import os
import re
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

import httpx
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    generate_latest,
)

from hcam.labs.sentinel.adapter import CatalogAdapterError, SentinelCatalogAdapter
from hcam.labs.sentinel.fixtures import generated_stream_id
from hcam.labs.sentinel.hls_relay import HlsRelayError, SentinelHlsRelay
from hcam.labs.sentinel.lab_adapters import (
    LAB_ADAPTERS,
    LabAdapterProfile,
    LabAdapterStateError,
    lab_adapter_profile,
    read_active_lab_adapter,
    write_active_lab_adapter,
)
from hcam.labs.sentinel.observability import LabObservability
from hcam.labs.sentinel.models import ExactNetworkPolicy, NetworkRule
from hcam.labs.sentinel.store import CatalogStore
from hcam.labs.sentinel.whep_proxy import SentinelWhepProxy, WhepProxyError


_CAMERA_ID = re.compile(r"^C([0-4][0-9]|50)$")
_STATIC = Path(__file__).with_name("static")


@dataclass(frozen=True, slots=True)
class DashboardSettings:
    state_path: Path
    source_id: str
    catalog_locator: str
    core_api_url: str
    public_whep_base_url: str
    media_evidence_path: Path | None
    mediamtx_api_url: str = "http://mediamtx:9997"
    refresh_interval_seconds: float = 60
    adapter_state_path: Path | None = None
    publisher_state_path: Path | None = None
    require_publisher_state: bool = False
    catalog_mode: Literal["sentinel-online", "generated-fallback"] = (
        "generated-fallback"
    )
    whep_session_ttl_seconds: int = 60
    sentinel_mediamtx_api_url: str = "http://sentinel-mediamtx:9997"
    sentinel_publish_base_url: str = "rtsp://sentinel-mediamtx:8554/hcam-sentinel"
    sentinel_public_whep_base_url: str = "http://127.0.0.1:8890/hcam-sentinel"

    @classmethod
    def from_environment(cls) -> "DashboardSettings":
        return cls(
            state_path=Path(
                os.getenv("HCAM_PHASE2_5_STATE_PATH", "/tmp/hcam-phase2-5/catalog.db")
            ),
            source_id=os.getenv("HCAM_PHASE2_5_SOURCE_ID", "generated-sentinel"),
            catalog_locator=os.getenv(
                "HCAM_PHASE2_5_CATALOG_URL", "http://catalog-simulator:8090/api/ingest"
            ),
            core_api_url=os.getenv("HCAM_PHASE2_5_CORE_API_URL", "http://api:8000"),
            public_whep_base_url=os.getenv(
                "HCAM_PHASE2_5_PUBLIC_WHEP_URL", "http://127.0.0.1:8889"
            ),
            media_evidence_path=(
                Path(value)
                if (value := os.getenv("HCAM_PHASE2_5_MEDIA_EVIDENCE"))
                else None
            ),
            mediamtx_api_url=os.getenv(
                "HCAM_PHASE2_5_MEDIAMTX_API_URL", "http://mediamtx:9997"
            ),
            refresh_interval_seconds=float(
                os.getenv("HCAM_PHASE2_5_REFRESH_INTERVAL_SECONDS", "60")
            ),
            adapter_state_path=(
                Path(value)
                if (value := os.getenv("HCAM_PHASE2_5_ADAPTER_STATE_PATH"))
                else None
            ),
            publisher_state_path=(
                Path(value)
                if (value := os.getenv("HCAM_PHASE2_5_PUBLISHER_STATE_PATH"))
                else None
            ),
            require_publisher_state=os.getenv(
                "HCAM_PHASE2_5_REQUIRE_PUBLISHER_STATE", "false"
            ).lower()
            in {"1", "true"},
            catalog_mode=os.getenv("HCAM_PHASE2_5_CATALOG_MODE", "sentinel-online"),  # type: ignore[arg-type]
            whep_session_ttl_seconds=int(
                os.getenv("HCAM_PHASE2_5_WHEP_SESSION_TTL_SECONDS", "60")
            ),
            sentinel_mediamtx_api_url=os.getenv(
                "HCAM_PHASE2_5_SENTINEL_MEDIAMTX_API_URL",
                "http://sentinel-mediamtx:9997",
            ),
            sentinel_publish_base_url=os.getenv(
                "HCAM_PHASE2_5_SENTINEL_PUBLISH_URL",
                "rtsp://sentinel-mediamtx:8554/hcam-sentinel",
            ),
            sentinel_public_whep_base_url=os.getenv(
                "HCAM_PHASE2_5_SENTINEL_PUBLIC_WHEP_URL",
                "http://127.0.0.1:8890/hcam-sentinel",
            ),
        )


def generated_lab_policy() -> ExactNetworkPolicy:
    return ExactNetworkPolicy(
        (
            NetworkRule("http", "catalog-simulator", 8090, "/api/ingest"),
            NetworkRule("rtsp", "mediamtx", 8554, "/hcam/"),
            NetworkRule("rtsp", "rtsp-fault-proxy", 8555, "/hcam/"),
            NetworkRule("http", "mediamtx", 8889, "/hcam/"),
            NetworkRule("http", "mediamtx", 8888, "/hcam/"),
        )
    )


def sentinel_online_policy() -> ExactNetworkPolicy:
    return ExactNetworkPolicy(
        (
            NetworkRule("https", "live.corp8.cloud", 443, "/api/ingest"),
            NetworkRule("rtsp", "live.corp8.cloud", 8554, "/stream/"),
            NetworkRule("http", "live.corp8.cloud", 8889, "/stream/"),
            NetworkRule("https", "live.corp8.cloud", 443, "/live/stream/"),
            NetworkRule("http", "live.corp8.cloud", 80, "/live/stream/"),
        )
    )


def _generated_media_evidence(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.is_file() or path.stat().st_size > 1024 * 1024:
        return None
    try:
        document = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if (
        not isinstance(document, dict)
        or document.get("classification") != "generated-only"
    ):
        return None
    return document


def _safe_media_evidence(path: Path | None) -> dict[str, object] | None:
    document = _generated_media_evidence(path)
    if document is None:
        return None
    accelerator = document.get("accelerator")
    if not isinstance(accelerator, dict):
        accelerator = None
    return {
        "fixture_count": document.get("fixture_count"),
        "parallelism": document.get("parallelism"),
        "total_bytes": document.get("total_bytes"),
        "accelerator": accelerator,
    }


def _safe_publisher_state(path: Path) -> dict[str, object] | None:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 16 * 1024:
        return None
    try:
        document = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if (
        not isinstance(document, dict)
        or document.get("classification") != "generated-only"
    ):
        return None
    adapter_id = document.get("adapter_id")
    active_stream_count = document.get("active_stream_count")
    if adapter_id not in {profile.adapter_id for profile in LAB_ADAPTERS}:
        return None
    if not isinstance(active_stream_count, int) or not 1 <= active_stream_count <= 50:
        return None
    return {
        "adapter_id": adapter_id,
        "active_stream_count": active_stream_count,
        "stream_copy": document.get("stream_copy") is True,
        "quality_downgraded": document.get("quality_downgraded") is not False,
    }


async def _await_publisher_profile(
    path: Path,
    profile: LabAdapterProfile,
    *,
    timeout_seconds: float = 20,
) -> dict[str, object]:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while True:
        document = _safe_publisher_state(path)
        if (
            document is not None
            and document["adapter_id"] == profile.adapter_id
            and document["active_stream_count"] == profile.active_stream_count
            and document["stream_copy"] is True
            and document["quality_downgraded"] is False
        ):
            return document
        if asyncio.get_running_loop().time() >= deadline:
            raise LabAdapterStateError("lab_adapter_publisher_not_ready")
        await asyncio.sleep(0.25)


def _adapter_catalog_locator(
    base_locator: str,
    profile: LabAdapterProfile,
    catalog_mode: Literal["sentinel-online", "generated-fallback"] = (
        "generated-fallback"
    ),
) -> str:
    parsed = urlsplit(base_locator)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("catalog locator must be an HTTP(S) absolute URL")
    path = (
        profile.catalog_path
        if catalog_mode == "sentinel-online"
        else profile.generated_catalog_path
    )
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _observed_media(path: Path | None) -> dict[str, dict[str, object]]:
    document = _generated_media_evidence(path)
    if document is None:
        return {}
    fixtures = document.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) > 50:
        return {}
    observed: dict[str, dict[str, object]] = {}
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        camera_id = fixture.get("camera_id")
        probe = fixture.get("probe")
        if not isinstance(camera_id, str) or _CAMERA_ID.fullmatch(camera_id) is None:
            continue
        if not isinstance(probe, dict) or probe.get("codec") not in {"h264", "hevc"}:
            continue
        try:
            media = {
                "codec": probe["codec"],
                "width": int(probe["width"]),
                "height": int(probe["height"]),
                "fps": float(probe["fps"]),
                "has_b_frames": int(probe["has_b_frames"]),
            }
        except (KeyError, TypeError, ValueError):
            continue
        media["preview_compatible"] = (
            media["codec"] == "h264" and media["has_b_frames"] == 0
        )
        observed[camera_id] = media
    return observed


def _with_observed_media(
    camera: dict[str, object],
    observed: dict[str, dict[str, object]],
    *,
    catalog_mode: Literal["sentinel-online", "generated-fallback"] = (
        "generated-fallback"
    ),
) -> dict[str, object]:
    result = dict(camera)
    media = observed.get(str(camera["external_camera_id"]))
    result["observed_media"] = media
    if catalog_mode == "sentinel-online":
        transports = camera.get("transports")
        has_whep = isinstance(transports, list) and any(
            isinstance(item, dict)
            and item.get("role") == "preview"
            and item.get("protocol") in {"http", "https"}
            for item in transports
        )
        result["preview_compatible"] = bool(
            has_whep
            and camera["advertised_live"]
            and camera["lifecycle_state"] == "active"
        )
    else:
        result["preview_compatible"] = bool(
            media
            and media["preview_compatible"]
            and camera["advertised_live"]
            and camera["lifecycle_state"] == "active"
        )
    return result


async def _candidate_health(
    catalog,
    *,
    mediamtx_api_url: str,
) -> dict[str, bool]:
    try:
        async with httpx.AsyncClient(
            timeout=5, follow_redirects=False, trust_env=False
        ) as client:
            response = await client.get(f"{mediamtx_api_url.rstrip('/')}/v3/paths/list")
    except httpx.HTTPError as exc:
        raise CatalogAdapterError("candidate_health_unavailable") from exc
    if response.status_code != 200 or len(response.content) > 1024 * 1024:
        raise CatalogAdapterError("candidate_health_unavailable")
    try:
        document = response.json()
        items = document["items"]
    except (ValueError, KeyError, TypeError) as exc:
        raise CatalogAdapterError("candidate_health_invalid") from exc
    if not isinstance(items, list):
        raise CatalogAdapterError("candidate_health_invalid")
    ready_paths = {
        item.get("name")
        for item in items
        if isinstance(item, dict)
        and item.get("ready") is True
        and isinstance(item.get("name"), str)
    }
    health: dict[str, bool] = {}
    for camera in catalog.cameras:
        inference = next(
            (endpoint for endpoint in camera.endpoints if endpoint.role == "inference"),
            None,
        )
        path = (
            urlsplit(inference.locator).path.lstrip("/")
            if inference is not None
            else None
        )
        health[camera.external_id] = not camera.advertised_live or path in ready_paths
    return health


def create_dashboard_app(settings: DashboardSettings | None = None) -> FastAPI:
    configured = settings or DashboardSettings.from_environment()
    if configured.catalog_mode not in {"sentinel-online", "generated-fallback"}:
        raise ValueError("catalog mode is invalid")
    if not 10 <= configured.refresh_interval_seconds <= 3600:
        raise ValueError("refresh interval must be between 10 and 3600 seconds")
    sentinel_whep = urlsplit(configured.sentinel_public_whep_base_url)
    if (
        sentinel_whep.scheme not in {"http", "https"}
        or sentinel_whep.hostname not in {"127.0.0.1", "localhost"}
        or sentinel_whep.username is not None
        or sentinel_whep.password is not None
    ):
        raise ValueError(
            "Sentinel WHEP endpoint must be an unauthenticated loopback URL"
        )
    sentinel_whep_origin = urlunsplit(
        (sentinel_whep.scheme, sentinel_whep.netloc, "", "", "")
    )
    adapter_state_path = (
        configured.adapter_state_path
        or configured.state_path.with_name("active-lab-adapter.json")
    )
    publisher_state_path = (
        configured.publisher_state_path
        or configured.state_path.with_name("publisher-state.json")
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if configured.catalog_mode == "sentinel-online":
            if os.getenv("HCAM_ALLOW_SENTINEL_SANDBOX", "").lower() not in {
                "1",
                "true",
            }:
                raise RuntimeError("HCAM_ALLOW_SENTINEL_SANDBOX=true is required")
            network_policy = sentinel_online_policy()
        else:
            if os.getenv("HCAM_ALLOW_SYNTHETIC_LAB", "").lower() not in {
                "1",
                "true",
            }:
                raise RuntimeError("HCAM_ALLOW_SYNTHETIC_LAB=true is required")
            network_policy = generated_lab_policy()
        store = CatalogStore(configured.state_path)
        store.initialize()
        try:
            active_profile = read_active_lab_adapter(adapter_state_path)
            if not adapter_state_path.exists():
                write_active_lab_adapter(adapter_state_path, active_profile.adapter_id)
        except LabAdapterStateError as exc:
            raise RuntimeError(exc.code) from exc
        adapters: dict[str, SentinelCatalogAdapter] = {}
        for profile in LAB_ADAPTERS:
            store.upsert_source(
                source_id=profile.adapter_id,
                catalog_locator=_adapter_catalog_locator(
                    configured.catalog_locator, profile, configured.catalog_mode
                ),
                department_scope="Engineering Lab",
                enabled=True,
                auto_apply=True,
            )
            adapters[profile.adapter_id] = SentinelCatalogAdapter(
                store,
                network_policy,
                max_records=profile.catalog_capacity,
                candidate_health_resolver=(
                    (
                        lambda catalog: _candidate_health(
                            catalog, mediamtx_api_url=configured.mediamtx_api_url
                        )
                    )
                    if configured.catalog_mode == "generated-fallback"
                    else None
                ),
            )
        whep_proxy = SentinelWhepProxy(
            network_policy, ttl_seconds=configured.whep_session_ttl_seconds
        )
        hls_relay = SentinelHlsRelay(
            network_policy,
            mediamtx_api_url=configured.sentinel_mediamtx_api_url,
            publish_base_url=configured.sentinel_publish_base_url,
            public_whep_base_url=configured.sentinel_public_whep_base_url,
            ttl_seconds=configured.whep_session_ttl_seconds,
        )
        registry = CollectorRegistry()
        observability = LabObservability(registry, version="phase2-5-lab")
        refresh_counter = Counter(
            "hcam_phase2_5_catalog_refresh_total",
            "Generated Phase 2.5 catalogue refreshes",
            ("adapter", "outcome"),
            registry=registry,
        )
        camera_gauge = Gauge(
            "hcam_phase2_5_catalog_cameras",
            "Generated Phase 2.5 catalogue cameras",
            ("adapter", "state"),
            registry=registry,
        )
        refresh_lock = asyncio.Lock()
        adapter_switch_lock = asyncio.Lock()

        async def perform_refresh(adapter_id: str, reason: str):
            profile = lab_adapter_profile(adapter_id)
            async with refresh_lock:
                correlation_id = observability.correlation_id()
                started = perf_counter()
                try:
                    result = await adapters[profile.adapter_id].refresh(
                        profile.adapter_id,
                        requester="phase2-5-dashboard",
                        reason=reason,
                    )
                except CatalogAdapterError as exc:
                    code = "catalog_schema_rejected" if exc.code in {"invalid_catalog_json", "catalog_schema_invalid"} else "catalog_upstream_failed"
                    observability.observe("provider" if code == "catalog_upstream_failed" else "catalogue", code, "degraded" if code == "catalog_upstream_failed" else "failed", correlation_id)
                    observability.duration.labels(component="catalogue", outcome="failed").observe(perf_counter() - started)
                    refresh_counter.labels(profile.adapter_id, "failed").inc()
                    raise
                refresh_counter.labels(
                    profile.adapter_id,
                    "unchanged" if result.unchanged else "succeeded",
                ).inc()
                if result.record_count == 0:
                    observability.observe("provider", "none", "healthy", correlation_id)
                    observability.observe("catalogue", "catalog_empty", "degraded", correlation_id)
                else:
                    observability.observe("provider", "none", "healthy", correlation_id)
                    observability.observe("catalogue", "none", "healthy", correlation_id)
                observability.duration.labels(component="catalogue", outcome="healthy" if result.record_count else "degraded").observe(perf_counter() - started)
                counts = store.summary(profile.adapter_id)["counts"]
                for state in ("active", "inactive", "missing", "tombstoned"):
                    camera_gauge.labels(profile.adapter_id, state).set(  # type: ignore[index]
                        counts[state]
                    )
                return result

        app.state.catalog_store = store
        app.state.catalog_adapters = adapters
        app.state.perform_catalog_refresh = perform_refresh
        app.state.metrics_registry = registry
        app.state.observability = observability
        app.state.dashboard_settings = configured
        app.state.adapter_state_path = adapter_state_path
        app.state.publisher_state_path = publisher_state_path
        app.state.require_publisher_state = configured.require_publisher_state
        app.state.adapter_switch_lock = adapter_switch_lock
        app.state.whep_proxy = whep_proxy
        app.state.hls_relay = hls_relay
        app.state.initial_refresh_errors = {}
        try:
            if configured.require_publisher_state:
                await _await_publisher_profile(publisher_state_path, active_profile)
            await perform_refresh(
                active_profile.adapter_id,
                f"{configured.catalog_mode} {active_profile.adapter_id} startup refresh",
            )
        except (CatalogAdapterError, LabAdapterStateError) as exc:
            app.state.initial_refresh_errors[active_profile.adapter_id] = exc.code
        stop_event = asyncio.Event()

        async def scheduler() -> None:
            while not stop_event.is_set():
                try:
                    await asyncio.wait_for(
                        stop_event.wait(), timeout=configured.refresh_interval_seconds
                    )
                    continue
                except TimeoutError:
                    pass
                try:
                    profile = read_active_lab_adapter(adapter_state_path)
                    await perform_refresh(
                        profile.adapter_id,
                        f"Scheduled {profile.adapter_id} catalogue refresh",
                    )
                except (CatalogAdapterError, LabAdapterStateError):
                    continue
                await whep_proxy.cleanup_expired()
                await hls_relay.cleanup_expired()

        scheduler_task = asyncio.create_task(
            scheduler(), name="phase2-5-catalog-refresh"
        )
        try:
            yield
        finally:
            stop_event.set()
            scheduler_task.cancel()
            with suppress(asyncio.CancelledError):
                await scheduler_task
            await whep_proxy.close()
            await hls_relay.close()

    app = FastAPI(
        title="H-CAM Phase 2.5 Test Dashboard",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

    def active_profile(request: Request) -> LabAdapterProfile:
        try:
            return read_active_lab_adapter(request.app.state.adapter_state_path)
        except LabAdapterStateError as exc:
            raise HTTPException(
                503, f"Lab adapter state unavailable ({exc.code})"
            ) from exc

    def data_classification() -> str:
        return (
            "sentinel-sandbox"
            if configured.catalog_mode == "sentinel-online"
            else "generated-only"
        )

    def local_ready(request: Request) -> bool:
        return all(hasattr(request.app.state, name) for name in ("catalog_store", "metrics_registry", "observability"))

    def relay_failure_code(code: str) -> str | None:
        return "mediamtx_unavailable" if code in {"hls_relay_start_failed", "hls_relay_health_failed", "whep_upstream_failed", "whep_upstream_timeout"} else None

    def require_lab_confirmation(value: str) -> None:
        if value != data_classification():
            raise HTTPException(403, "Active lab-source confirmation required")

    def bearer_token(request: Request) -> str:
        authorization = request.headers.get("authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if separator != " " or scheme.lower() != "bearer" or not token:
            raise HTTPException(401, "WHEP session authorization required")
        return token

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            f"connect-src 'self' {sentinel_whep_origin} "
            "http://127.0.0.1:8889 http://localhost:8889; "
            "media-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-HCAM-Data-Classification"] = data_classification()
        return response

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(_STATIC / "dashboard.html", media_type="text/html")

    @app.get("/static/dashboard.css", include_in_schema=False)
    def stylesheet() -> FileResponse:
        return FileResponse(_STATIC / "dashboard.css", media_type="text/css")

    @app.get("/static/dashboard.js", include_in_schema=False)
    def script() -> FileResponse:
        return FileResponse(_STATIC / "dashboard.js", media_type="text/javascript")

    @app.get("/health")
    def health(request: Request) -> dict[str, object]:
        profile = active_profile(request)
        return {
            "status": "ok",
            "classification": data_classification(),
            "catalog_mode": configured.catalog_mode,
            "adapter_id": profile.adapter_id,
            "initial_refresh_error": request.app.state.initial_refresh_errors.get(
                profile.adapter_id
            ),
            "checks": request.app.state.observability.health(app_ready=local_ready(request)),
        }

    @app.get("/health/live")
    def health_live() -> dict[str, str]:
        return {"status":"live","dependency":"process"}

    @app.get("/health/ready")
    def health_ready(request: Request) -> dict[str, str]:
        return {"status":"ready" if local_ready(request) else "not_ready","dependency":"local_store_and_metrics"}

    @app.get("/api/support-bundle")
    def support_bundle(request: Request) -> dict[str, object]:
        """LAB-only bounded diagnostic bundle; never includes media/provider data."""
        return request.app.state.observability.support_bundle(app_ready=True)

    @app.get("/metrics", include_in_schema=False)
    def metrics(request: Request) -> Response:
        return Response(
            content=generate_latest(request.app.state.metrics_registry),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.get("/api/status")
    def status(request: Request) -> dict[str, object]:
        profile = active_profile(request)
        store: CatalogStore = request.app.state.catalog_store
        result = store.summary(profile.adapter_id)
        result["classification"] = data_classification()
        result["media_preparation"] = (
            _safe_media_evidence(configured.media_evidence_path)
            if configured.catalog_mode == "generated-fallback"
            else None
        )
        result["adapter"] = profile.document()
        result["adapters"] = [
            {**item.document(), "active": item.adapter_id == profile.adapter_id}
            for item in LAB_ADAPTERS
        ]
        result["publisher"] = (
            _safe_publisher_state(request.app.state.publisher_state_path)
            if configured.catalog_mode == "generated-fallback"
            else None
        )
        result["catalog_mode"] = configured.catalog_mode
        result["runtime_connection_limit"] = profile.active_stream_count
        result["initial_refresh_error"] = request.app.state.initial_refresh_errors.get(
            profile.adapter_id
        )
        result["observability"] = request.app.state.observability.status(app_ready=local_ready(request))
        result["boundaries"] = {
            "test_dashboard_only": True,
            "main_dashboard": False,
            "government_data": False,
            "organizer_sandbox": configured.catalog_mode == "sentinel-online",
            "recording": False,
            "analytics": False,
        }
        return result

    @app.get("/api/cameras")
    def cameras(
        request: Request,
        q: str | None = Query(default=None, max_length=100),
        state: str | None = Query(default=None, max_length=32),
        codec: str | None = Query(default=None, max_length=16),
        limit: int = Query(default=100, ge=1, le=100),
    ) -> dict[str, object]:
        profile = active_profile(request)
        store: CatalogStore = request.app.state.catalog_store
        observed = _observed_media(configured.media_evidence_path)
        items = [
            _with_observed_media(item, observed, catalog_mode=configured.catalog_mode)
            for item in store.list_cameras(profile.adapter_id, limit=100)
        ]
        if q:
            needle = q.casefold()
            items = [
                item
                for item in items
                if needle in str(item["external_camera_id"]).casefold()
                or needle in str(item.get("name") or "").casefold()
                or needle in str(item.get("location") or "").casefold()
            ]
        if state:
            items = [item for item in items if item["lifecycle_state"] == state]
        if codec:
            items = [item for item in items if item["media"]["codec"] == codec]  # type: ignore[index]
        return {"total": len(items), "items": items[:limit]}

    @app.get("/api/events")
    def events(
        request: Request, limit: int = Query(default=20, ge=1, le=100)
    ) -> dict[str, object]:
        profile = active_profile(request)
        store: CatalogStore = request.app.state.catalog_store
        items = store.list_events(profile.adapter_id, limit=limit)
        return {"total": len(items), "items": items}

    @app.post("/api/refresh")
    async def refresh(
        request: Request,
        confirmation: str = Header(alias="X-HCAM-Lab-Confirm"),
        reason: str = Header(alias="X-HCAM-Reason", min_length=8, max_length=240),
    ) -> dict[str, object]:
        require_lab_confirmation(confirmation)
        profile = active_profile(request)
        try:
            result = await request.app.state.perform_catalog_refresh(
                profile.adapter_id, reason
            )
        except CatalogAdapterError as exc:
            raise HTTPException(502, f"Catalogue refresh failed ({exc.code})") from exc
        return {
            "refresh_id": result.refresh_id,
            "status": result.status,
            "record_count": result.record_count,
            "warning_count": result.warning_count,
            "unchanged": result.unchanged,
        }

    @app.post("/api/adapters/{adapter_id}/activate")
    async def activate_adapter(
        adapter_id: str,
        request: Request,
        confirmation: str = Header(alias="X-HCAM-Lab-Confirm"),
        reason: str = Header(alias="X-HCAM-Reason", min_length=8, max_length=240),
    ) -> dict[str, object]:
        require_lab_confirmation(confirmation)
        try:
            profile = lab_adapter_profile(adapter_id)
        except LabAdapterStateError as exc:
            raise HTTPException(404, "Generated lab adapter not found") from exc
        async with request.app.state.adapter_switch_lock:
            try:
                previous = read_active_lab_adapter(request.app.state.adapter_state_path)
            except LabAdapterStateError as exc:
                raise HTTPException(503, "Lab adapter state is invalid") from exc
            try:
                write_active_lab_adapter(
                    request.app.state.adapter_state_path, profile.adapter_id
                )
                if (
                    configured.catalog_mode == "generated-fallback"
                    and request.app.state.require_publisher_state
                ):
                    await _await_publisher_profile(
                        request.app.state.publisher_state_path, profile
                    )
                refresh_result = await request.app.state.perform_catalog_refresh(
                    profile.adapter_id,
                    f"Activate {profile.adapter_id}: {reason}",
                )
            except (CatalogAdapterError, LabAdapterStateError, OSError) as exc:
                with suppress(LabAdapterStateError, OSError):
                    write_active_lab_adapter(
                        request.app.state.adapter_state_path, previous.adapter_id
                    )
                    if (
                        configured.catalog_mode == "generated-fallback"
                        and request.app.state.require_publisher_state
                    ):
                        await _await_publisher_profile(
                            request.app.state.publisher_state_path, previous
                        )
                code = getattr(exc, "code", "lab_adapter_state_unavailable")
                raise HTTPException(503, f"Lab adapter switch failed ({code})") from exc
        return {
            "adapter": profile.document(),
            "status": "active",
            "record_count": refresh_result.record_count,
            "quality_downgraded": False,
        }

    @app.post("/api/cameras/{external_id}/playback")
    async def playback(
        external_id: str,
        request: Request,
        transport: str = Query(default="auto", pattern="^(auto|direct-whep)$"),
    ) -> dict[str, object]:
        if not external_id or len(external_id) > 160:
            raise HTTPException(404, "Lab camera not found")
        match = (
            _CAMERA_ID.fullmatch(external_id)
            if configured.catalog_mode == "generated-fallback"
            else None
        )
        if configured.catalog_mode == "generated-fallback" and match is None:
            raise HTTPException(404, "Generated camera not found")
        profile = active_profile(request)
        store: CatalogStore = request.app.state.catalog_store
        camera = store.get_camera(profile.adapter_id, external_id)
        if (
            camera is None
            or not camera["advertised_live"]
            or camera["lifecycle_state"] != "active"
        ):
            raise HTTPException(409, "Lab camera is not active")
        if configured.catalog_mode == "sentinel-online":
            if transport == "auto":
                fallback = store.get_camera_endpoint(
                    profile.adapter_id, external_id, role="fallback"
                )
                if fallback is None or fallback.protocol not in {"http", "https"}:
                    raise HTTPException(409, "Sentinel HLS fallback is unavailable")
                try:
                    relay = await request.app.state.hls_relay.issue(
                        fallback, limit=profile.preview_session_limit
                    )
                except HlsRelayError as exc:
                    stable=relay_failure_code(exc.code)
                    if stable: request.app.state.observability.observe("relay", stable, "degraded")
                    status_code = 429 if exc.code == "hls_relay_limit_reached" else 502
                    raise HTTPException(
                        status_code, f"Sentinel HLS relay unavailable ({exc.code})"
                    ) from exc
                return {
                    "stream_id": camera["camera_id"],
                    "whep_url": relay.whep_url,
                    "cleanup_url": f"/api/relays/{relay.session_id}",
                    "hls_url": None,
                    "access_token": relay.bearer_token,
                    "token_type": "Bearer",
                    "expires_at": relay.expires_at,
                    "retention": "none",
                    "media_path": "hls-stream-copy-to-local-whep",
                }
            endpoint = store.get_camera_endpoint(
                profile.adapter_id, external_id, role="preview"
            )
            if endpoint is None or endpoint.protocol not in {"http", "https"}:
                raise HTTPException(409, "Sentinel WHEP preview is unavailable")
            try:
                ticket = await request.app.state.whep_proxy.issue(
                    endpoint, limit=profile.preview_session_limit
                )
            except WhepProxyError as exc:
                stable=relay_failure_code(exc.code)
                if stable: request.app.state.observability.observe("relay", stable, "degraded")
                status_code = 429 if exc.code == "whep_session_limit_reached" else 502
                raise HTTPException(
                    status_code, f"Sentinel preview unavailable ({exc.code})"
                ) from exc
            local_whep_url = f"/api/whep/{ticket.session_id}"
            return {
                "stream_id": camera["camera_id"],
                "whep_url": local_whep_url,
                "cleanup_url": local_whep_url,
                "hls_url": None,
                "access_token": ticket.bearer_token,
                "token_type": "Bearer",
                "expires_at": ticket.expires_at,
                "retention": "none",
                "media_path": "direct-webrtc",
            }

        assert match is not None
        observed = _observed_media(configured.media_evidence_path).get(external_id)
        if observed is None or observed["preview_compatible"] is not True:
            raise HTTPException(409, "Generated media is not WHEP preview compatible")
        number = int(match.group(1))
        stream_id = generated_stream_id(number)
        headers = {
            "X-HCAM-Actor": "phase2-5-dashboard",
            "X-HCAM-Roles": "camera.viewer",
            "X-HCAM-Departments": "Engineering Lab",
            "X-HCAM-Reason": "Generated lab operator preview",
        }
        try:
            async with httpx.AsyncClient(
                timeout=10,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                response = await client.post(
                    f"{configured.core_api_url.rstrip('/')}/streams/{stream_id}/playback-sessions",
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise HTTPException(502, "Generated playback service unavailable") from exc
        if response.status_code != 201:
            raise HTTPException(409, "Generated stream is not ready for preview")
        try:
            session = response.json()
            token = session["access_token"]
            expires_at = session["expires_at"]
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(502, "Generated playback response invalid") from exc
        path = f"hcam/{stream_id}"
        return {
            "stream_id": stream_id,
            "whep_url": f"{configured.public_whep_base_url.rstrip('/')}/{path}/whep",
            "hls_url": session["playback_url"],
            "access_token": token,
            "token_type": "Bearer",
            "expires_at": expires_at,
        }

    def whep_error(exc: WhepProxyError) -> HTTPException:
        status = {
            "whep_session_unauthorized": 401,
            "whep_session_not_found": 404,
            "whep_session_expired": 410,
            "whep_offer_rejected": 413,
            "whep_session_already_used": 409,
        }.get(exc.code, 502)
        return HTTPException(status, f"WHEP signaling failed ({exc.code})")

    @app.post("/api/whep/{session_id}")
    async def whep_negotiate(session_id: str, request: Request) -> Response:
        if configured.catalog_mode != "sentinel-online":
            raise HTTPException(404, "Sentinel WHEP proxy is disabled")
        if request.headers.get("content-type", "").split(";", 1)[0].lower() != (
            "application/sdp"
        ):
            raise HTTPException(415, "WHEP offer must be application/sdp")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > request.app.state.whep_proxy.max_offer_bytes:
                raise HTTPException(413, "WHEP offer exceeds the lab limit")
        try:
            answer, _external_resource = await request.app.state.whep_proxy.negotiate(
                session_id, bearer_token(request), bytes(body)
            )
        except WhepProxyError as exc:
            stable=relay_failure_code(exc.code)
            if exc.code == "whep_upstream_timeout": request.app.state.observability.observe("preview", "preview_timeout", "failed")
            elif stable: request.app.state.observability.observe("relay", stable, "degraded")
            raise whep_error(exc) from exc
        return Response(
            content=answer,
            status_code=201,
            media_type="application/sdp",
            headers={"Location": f"/api/whep/{session_id}/resource"},
        )

    @app.delete("/api/whep/{session_id}", status_code=204)
    @app.delete("/api/whep/{session_id}/resource", status_code=204)
    async def whep_delete(session_id: str, request: Request) -> Response:
        if configured.catalog_mode != "sentinel-online":
            raise HTTPException(404, "Sentinel WHEP proxy is disabled")
        try:
            await request.app.state.whep_proxy.delete(session_id, bearer_token(request))
        except WhepProxyError as exc:
            request.app.state.observability.observe("cleanup", "cleanup_failed", "failed")
            raise whep_error(exc) from exc
        return Response(status_code=204)

    @app.delete("/api/relays/{session_id}", status_code=204)
    async def relay_delete(session_id: str, request: Request) -> Response:
        if configured.catalog_mode != "sentinel-online":
            raise HTTPException(404, "Sentinel HLS relay is disabled")
        try:
            await request.app.state.hls_relay.delete(session_id, bearer_token(request))
        except HlsRelayError as exc:
            request.app.state.observability.observe("cleanup", "cleanup_failed", "failed")
            status = 401 if exc.code == "hls_relay_unauthorized" else 404
            raise HTTPException(
                status, f"HLS relay cleanup failed ({exc.code})"
            ) from exc
        return Response(status_code=204)

    return app


app = create_dashboard_app()


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="H-CAM Phase 2.5 generated lab dashboard"
    )
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--allow-non-loopback", action="store_true")
    args = parser.parse_args(argv)
    if (
        args.bind not in {"127.0.0.1", "::1", "localhost"}
        and not args.allow_non_loopback
    ):
        return 2
    uvicorn.run(app, host=args.bind, port=args.port, access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
