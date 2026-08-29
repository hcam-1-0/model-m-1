from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from starlette.responses import HTMLResponse, RedirectResponse

from hcam.security.auth import (
    CAMERA_VIEWER,
    PLATFORM_ADMIN,
    Principal,
    RoleGuard,
    get_current_principal,
)

from .catalog import CatalogLoadError, CatalogPreview
from .config import StreamConfig, redact_stream_url
from .dashboard_ui import ADAPTER_BACKEND_DASHBOARD_HTML
from .monitoring_ui import CAMERA_MONITORING_DASHBOARD_HTML
from .runtime import AdapterRuntime, AdapterRuntimeError, AdapterRuntimeStatus
from .viewer import LiveCamera


router = APIRouter(prefix="/cam-adapter", tags=["cam-adapter"])
dashboard_router = APIRouter(tags=["adapter-backend-dashboard"])
monitoring_dashboard_router = APIRouter(tags=["camera-monitoring-dashboard"])
_LIVE_VIEWER_COOKIE = "hcam_live_viewer"
_PLAYBACK_SESSION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{20,80}$")


class AdapterStatus(BaseModel):
    config_loaded: bool
    config_file: str | None
    configuration_error: str | None
    running: bool
    base: str | None
    segment_time: int | None
    streams_configured: int
    streams_enabled: int
    active_workers: list[str]
    yolo_model: str | None
    sample_interval: float | None
    catalog_configured: bool
    catalog_enabled: bool
    live_viewer_configured: bool
    live_viewer_enabled: bool
    live_viewer_camera_limit: int | None


class AdapterStream(BaseModel):
    camera_id: str
    enabled: bool
    location_label: str | None
    department: str | None
    url_redacted: str


class CatalogPreviewResponse(BaseModel):
    catalog_host: str
    total_entries: int
    selected_streams: list[AdapterStream]


class SourceValidation(BaseModel):
    camera_id: str
    reachable: bool


class LiveViewerLaunch(BaseModel):
    launch_path: str
    expires_in_seconds: int


class LiveCameraResponse(BaseModel):
    camera_id: str
    location_label: str | None
    department: str | None


class LiveCameraList(BaseModel):
    cameras: list[LiveCameraResponse]


class AdapterBackendDashboardData(BaseModel):
    adapter: AdapterStatus
    live_cameras: list[LiveCameraResponse]
    live_cameras_available: bool
    live_cameras_message: str | None = None


def _get_adapter_runtime(request: Request) -> AdapterRuntime:
    return request.app.state.adapter_runtime


def _status_response(snapshot: AdapterRuntimeStatus) -> AdapterStatus:
    return AdapterStatus(
        config_loaded=snapshot.config_loaded,
        config_file=snapshot.config_file,
        configuration_error=snapshot.configuration_error,
        running=snapshot.running,
        base=snapshot.base,
        segment_time=snapshot.segment_time,
        streams_configured=snapshot.streams_configured,
        streams_enabled=snapshot.streams_enabled,
        active_workers=list(snapshot.active_workers),
        yolo_model=snapshot.yolo_model,
        sample_interval=snapshot.sample_interval,
        catalog_configured=snapshot.catalog_configured,
        catalog_enabled=snapshot.catalog_enabled,
        live_viewer_configured=snapshot.live_viewer_configured,
        live_viewer_enabled=snapshot.live_viewer_enabled,
        live_viewer_camera_limit=snapshot.live_viewer_camera_limit,
    )


def _stream_response(stream: StreamConfig) -> AdapterStream:
    return AdapterStream(
        camera_id=stream.camera_id,
        enabled=stream.enabled,
        location_label=stream.location_label,
        department=stream.department,
        url_redacted=redact_stream_url(stream.rtsp_url),
    )


def _runtime_failure(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Camera adapter action was not completed. Check its local configuration and status.",
    )


def _live_viewer_failure(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Live viewer action was not completed. Check the local adapter status and try again.",
    )


def _authorized_live_viewer(
    request: Request,
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> AdapterRuntime:
    if runtime.has_live_viewer_session(request.cookies.get(_LIVE_VIEWER_COOKIE)):
        return runtime
    principal = get_current_principal(request)
    if principal.roles.isdisjoint({CAMERA_VIEWER, PLATFORM_ADMIN}):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return runtime


def _live_camera_response(camera: LiveCamera) -> LiveCameraResponse:
    return LiveCameraResponse(
        camera_id=camera.camera_id,
        location_label=camera.location_label,
        department=camera.department,
    )


def _browser_launch_redirect(
    runtime: AdapterRuntime,
    launch_token: str,
    destination: str,
) -> RedirectResponse:
    try:
        redeemed = runtime.redeem_live_viewer_session(launch_token)
    except AdapterRuntimeError as exc:
        raise _live_viewer_failure(exc) from exc
    if redeemed is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Dashboard launch link expired")
    cookie_token, max_age = redeemed
    response = RedirectResponse(url=destination, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=_LIVE_VIEWER_COOKIE,
        value=cookie_token,
        max_age=max_age,
        httponly=True,
        samesite="strict",
        secure=False,
        path="/",
    )
    return response


@router.get("/status", response_model=AdapterStatus)
def adapter_status(
    principal: Principal = Depends(RoleGuard(CAMERA_VIEWER, PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> AdapterStatus:
    return _status_response(runtime.status())


@router.get("/streams", response_model=list[AdapterStream])
def adapter_streams(
    principal: Principal = Depends(RoleGuard(CAMERA_VIEWER, PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> list[AdapterStream]:
    return [_stream_response(stream) for stream in runtime.streams()]


@router.post("/reload", response_model=AdapterStatus)
def reload_adapter_config(
    principal: Principal = Depends(RoleGuard(PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> AdapterStatus:
    try:
        return _status_response(runtime.reload())
    except AdapterRuntimeError as exc:
        raise _runtime_failure(exc) from exc


@router.post("/start", response_model=AdapterStatus)
def start_adapter(
    principal: Principal = Depends(RoleGuard(PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> AdapterStatus:
    try:
        return _status_response(runtime.start())
    except AdapterRuntimeError as exc:
        raise _runtime_failure(exc) from exc


@router.post("/stop", response_model=AdapterStatus)
def stop_adapter(
    principal: Principal = Depends(RoleGuard(PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> AdapterStatus:
    return _status_response(runtime.stop())


@router.post("/catalog/preview", response_model=CatalogPreviewResponse)
def preview_catalog(
    principal: Principal = Depends(RoleGuard(PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> CatalogPreviewResponse:
    try:
        preview: CatalogPreview = runtime.catalog_preview()
    except (AdapterRuntimeError, CatalogLoadError) as exc:
        raise _runtime_failure(exc) from exc
    return CatalogPreviewResponse(
        catalog_host=preview.catalog_host,
        total_entries=preview.total_entries,
        selected_streams=[_stream_response(stream) for stream in preview.selected_streams],
    )


@router.post("/validate", response_model=list[SourceValidation])
def validate_configured_sources(
    principal: Principal = Depends(RoleGuard(PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> list[SourceValidation]:
    try:
        return [SourceValidation.model_validate(result) for result in runtime.validate_configured_sources()]
    except AdapterRuntimeError as exc:
        raise _runtime_failure(exc) from exc


@router.post("/live/session", response_model=LiveViewerLaunch)
def create_live_viewer_session(
    principal: Principal = Depends(RoleGuard(PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> LiveViewerLaunch:
    """Create a one-time local browser launch link for the authenticated admin."""
    try:
        launch_token, expires_in_seconds = runtime.issue_live_viewer_session()
    except AdapterRuntimeError as exc:
        raise _live_viewer_failure(exc) from exc
    return LiveViewerLaunch(
        launch_path=f"/cam-adapter/live?launch={launch_token}",
        expires_in_seconds=expires_in_seconds,
    )


@router.post("/dashboard/session", response_model=LiveViewerLaunch)
def create_adapter_backend_dashboard_session(
    principal: Principal = Depends(RoleGuard(PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> LiveViewerLaunch:
    """Create a one-time local browser launch link for the basic dashboard."""
    try:
        launch_token, expires_in_seconds = runtime.issue_live_viewer_session()
    except AdapterRuntimeError as exc:
        raise _live_viewer_failure(exc) from exc
    return LiveViewerLaunch(
        launch_path=f"/adapter-backend-dashboard?launch={launch_token}",
        expires_in_seconds=expires_in_seconds,
    )


@router.post("/monitoring-dashboard/session", response_model=LiveViewerLaunch)
def create_camera_monitoring_dashboard_session(
    principal: Principal = Depends(RoleGuard(PLATFORM_ADMIN)),
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> LiveViewerLaunch:
    """Create a one-time launch link for the monitoring-center extension."""
    try:
        launch_token, expires_in_seconds = runtime.issue_live_viewer_session()
    except AdapterRuntimeError as exc:
        raise _live_viewer_failure(exc) from exc
    return LiveViewerLaunch(
        launch_path=f"/camera-monitoring-dashboard?launch={launch_token}",
        expires_in_seconds=expires_in_seconds,
    )


@router.get("/live", include_in_schema=False)
def live_viewer_page(
    request: Request,
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> Response:
    launch_token = request.query_params.get("launch")
    if launch_token:
        response = _browser_launch_redirect(runtime, launch_token, "/adapter-backend-dashboard")
    else:
        _authorized_live_viewer(request, runtime)
        response = RedirectResponse(url="/adapter-backend-dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.get("/live/cameras", response_model=LiveCameraList)
def list_live_cameras(
    runtime: AdapterRuntime = Depends(_authorized_live_viewer),
) -> LiveCameraList:
    try:
        return LiveCameraList(cameras=[_live_camera_response(camera) for camera in runtime.live_cameras()])
    except AdapterRuntimeError as exc:
        raise _live_viewer_failure(exc) from exc


@router.post("/live/whep/{camera_id}")
async def negotiate_live_whep(
    camera_id: str,
    request: Request,
    runtime: AdapterRuntime = Depends(_authorized_live_viewer),
) -> Response:
    offer_bytes = await request.body()
    if len(offer_bytes) > 64 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Live offer is too large")
    try:
        offer_sdp = offer_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Live offer is invalid") from exc
    try:
        answer = runtime.negotiate_whep(camera_id, offer_sdp)
    except AdapterRuntimeError as exc:
        raise _live_viewer_failure(exc) from exc
    headers = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
    if answer.playback_session_id is not None:
        headers["X-HCAM-Playback-Session"] = answer.playback_session_id
    return Response(content=answer.answer_sdp, media_type="application/sdp", headers=headers)


@router.delete("/live/whep/{playback_session_id}", status_code=status.HTTP_204_NO_CONTENT)
def close_live_whep(
    playback_session_id: str,
    runtime: AdapterRuntime = Depends(_authorized_live_viewer),
) -> Response:
    if _PLAYBACK_SESSION_PATTERN.fullmatch(playback_session_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Live playback session not found")
    try:
        runtime.close_whep(playback_session_id)
    except AdapterRuntimeError as exc:
        raise _live_viewer_failure(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers={"Cache-Control": "no-store"})


@router.get("/dashboard/data", response_model=AdapterBackendDashboardData)
def adapter_backend_dashboard_data(
    runtime: AdapterRuntime = Depends(_authorized_live_viewer),
) -> AdapterBackendDashboardData:
    snapshot = _status_response(runtime.status())
    try:
        cameras = [_live_camera_response(camera) for camera in runtime.live_cameras()]
    except AdapterRuntimeError:
        return AdapterBackendDashboardData(
            adapter=snapshot,
            live_cameras=[],
            live_cameras_available=False,
            live_cameras_message="Live camera catalogue is unavailable. Adapter status remains available.",
        )
    return AdapterBackendDashboardData(
        adapter=snapshot,
        live_cameras=cameras,
        live_cameras_available=True,
    )


@dashboard_router.get("/adapter-backend-dashboard", include_in_schema=False)
def adapter_backend_dashboard_page(
    request: Request,
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> Response:
    launch_token = request.query_params.get("launch")
    if launch_token:
        response = _browser_launch_redirect(runtime, launch_token, "/adapter-backend-dashboard")
    else:
        _authorized_live_viewer(request, runtime)
        response = HTMLResponse(ADAPTER_BACKEND_DASHBOARD_HTML)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@monitoring_dashboard_router.get("/camera-monitoring-dashboard", include_in_schema=False)
def camera_monitoring_dashboard_page(
    request: Request,
    runtime: AdapterRuntime = Depends(_get_adapter_runtime),
) -> Response:
    launch_token = request.query_params.get("launch")
    if launch_token:
        response = _browser_launch_redirect(runtime, launch_token, "/camera-monitoring-dashboard")
    else:
        _authorized_live_viewer(request, runtime)
        response = HTMLResponse(CAMERA_MONITORING_DASHBOARD_HTML)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
