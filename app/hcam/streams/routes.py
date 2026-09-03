from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from hcam.database import get_session
from hcam.observability import request_id_from_scope
from hcam.security.auth import (
    CAMERA_CONTROLLER,
    CAMERA_EDITOR,
    CAMERA_VIEWER,
    PLATFORM_ADMIN,
    Principal,
    RoleGuard,
)
from hcam.streams.repository import StreamFilters, StreamRepository, stream_to_response
from hcam.streams.capabilities import (
    CapabilityCooldownError,
    CapabilityDiscoveryError,
    CapabilityNotFoundError,
    CapabilityService,
    CapabilityValidationError,
    build_capability_discovery_engine,
    capability_refresh_to_response,
)
from hcam.streams.onvif_discovery import (
    OnvifDiscoveryDisabledError,
    OnvifDiscoveryRuntimeError,
    OnvifDiscoveryService,
)
from hcam.streams.onvif_operations import (
    OnvifOperationConflictError,
    OnvifOperationError,
    OnvifOperationNotFoundError,
    OnvifOperationService,
    OnvifOperationValidationError,
)
from hcam.streams.playback import (
    PlaybackConfigurationError,
    PlaybackService,
    PlaybackSigner,
    PlaybackUnavailableError,
)
from hcam.streams.schemas import (
    CameraCapabilityDiscoveryResponse,
    CapabilityRefreshResponse,
    CapabilitySnapshotListResponse,
    CapabilitySnapshotResponse,
    OnvifDiscoveryResponse,
    OnvifEventPullRequest,
    OnvifEventPullResponse,
    OnvifImagingInspectionRequest,
    OnvifImagingInspectionResponse,
    OnvifPtzCommandRequest,
    OnvifPtzCommandResponse,
    PlaybackSessionResponse,
    ProbeQueuedResponse,
    StreamEndpointCreate,
    StreamEndpointListResponse,
    StreamEndpointPatch,
    StreamEndpointResponse,
    StreamHealthResponse,
    StreamProbeListResponse,
)
from hcam.streams.service import (
    StreamCapabilityDiscoveryError,
    StreamConflictError,
    StreamNotFoundError,
    StreamPreconditionError,
    StreamService,
    StreamValidationError,
)


router = APIRouter(tags=["stream-management"])
SessionDependency = Annotated[Session, Depends(get_session)]
ViewerPrincipal = Annotated[
    Principal, Depends(RoleGuard(CAMERA_VIEWER, CAMERA_EDITOR, PLATFORM_ADMIN))
]
EditorPrincipal = Annotated[
    Principal, Depends(RoleGuard(CAMERA_EDITOR, PLATFORM_ADMIN))
]
ControllerPrincipal = Annotated[
    Principal, Depends(RoleGuard(CAMERA_CONTROLLER, PLATFORM_ADMIN))
]
AdminPrincipal = Annotated[Principal, Depends(RoleGuard(PLATFORM_ADMIN))]
ReasonHeader = Annotated[
    str,
    Header(alias="X-HCAM-Reason", min_length=8, max_length=500, pattern=r".*\S.*"),
]
_ETAG_PATTERN = re.compile(r'^"([1-9][0-9]*)"$')


def _etag(version: int) -> str:
    return f'"{version}"'


def _expected_version(if_match: str | None) -> int:
    if if_match is None:
        raise HTTPException(428, "If-Match stream version is required")
    match = _ETAG_PATTERN.fullmatch(if_match.strip())
    if match is None:
        raise HTTPException(400, "If-Match must contain a stream version ETag")
    return int(match.group(1))


def _raise_service_error(error: RuntimeError) -> None:
    if isinstance(error, OnvifOperationNotFoundError):
        raise HTTPException(404, "Stream not found") from error
    if isinstance(error, OnvifOperationConflictError):
        raise HTTPException(409, str(error)) from error
    if isinstance(error, OnvifOperationValidationError):
        raise HTTPException(422, str(error)) from error
    if isinstance(error, OnvifOperationError):
        raise HTTPException(
            502, f"ONVIF operation failed ({error.reason_code})"
        ) from error
    if isinstance(error, CapabilityNotFoundError):
        raise HTTPException(404, str(error)) from error
    if isinstance(error, CapabilityValidationError):
        raise HTTPException(422, str(error)) from error
    if isinstance(error, CapabilityDiscoveryError):
        if error.reason_code in {
            "network_policy_denied",
            "credentials_unavailable",
            "camera_secret_provider_unconfigured",
            "camera_secret_invalid_reference",
            "camera_secret_invalid_file",
            "camera_secret_invalid_payload",
            "camera_secret_unavailable",
        }:
            raise HTTPException(
                422,
                f"ONVIF capability configuration failed ({error.reason_code})",
            ) from error
        raise HTTPException(
            502,
            f"ONVIF capability discovery failed ({error.reason_code})",
        ) from error
    if isinstance(error, StreamNotFoundError):
        raise HTTPException(404, "Stream not found") from error
    if isinstance(error, StreamPreconditionError):
        raise HTTPException(412, str(error)) from error
    if isinstance(error, StreamConflictError):
        raise HTTPException(409, str(error)) from error
    if isinstance(error, StreamValidationError):
        raise HTTPException(422, str(error)) from error
    if isinstance(error, StreamCapabilityDiscoveryError):
        raise HTTPException(
            502,
            f"ONVIF capability discovery failed ({error.reason_code})",
        ) from error
    raise error


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.get("/streams", response_model=StreamEndpointListResponse)
def list_streams(
    session: SessionDependency,
    principal: ViewerPrincipal,
    camera_id: Annotated[str | None, Query(max_length=160)] = None,
    protocol: Annotated[str | None, Query(max_length=16)] = None,
    state: Annotated[str | None, Query(max_length=32)] = None,
    enabled: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StreamEndpointListResponse:
    return StreamRepository(session).list(
        filters=StreamFilters(
            camera_id=camera_id,
            protocol=protocol,
            state=state,
            enabled=enabled,
            allowed_departments=principal.allowed_departments,
        ),
        limit=limit,
        offset=offset,
    )


@router.post(
    "/cameras/{camera_id}/streams",
    response_model=StreamEndpointResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stream(
    camera_id: str,
    payload: StreamEndpointCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> StreamEndpointResponse:
    try:
        endpoint, health = StreamService(session).create(
            camera_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["ETag"] = _etag(endpoint.version_id)
    response.headers["Location"] = f"/streams/{endpoint.stream_id}"
    return stream_to_response(endpoint, health)


@router.get("/streams/{stream_id}", response_model=StreamEndpointResponse)
def get_stream(
    stream_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> StreamEndpointResponse:
    row = StreamRepository(session).get(
        stream_id, allowed_departments=principal.allowed_departments
    )
    if row is None:
        raise HTTPException(404, "Stream not found")
    endpoint, health = row
    response.headers["ETag"] = _etag(endpoint.version_id)
    return stream_to_response(endpoint, health)


@router.patch("/streams/{stream_id}", response_model=StreamEndpointResponse)
def update_stream(
    stream_id: str,
    payload: StreamEndpointPatch,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> StreamEndpointResponse:
    try:
        endpoint, health = StreamService(session).update(
            stream_id,
            payload,
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["ETag"] = _etag(endpoint.version_id)
    return stream_to_response(endpoint, health)


@router.get("/streams/{stream_id}/health", response_model=StreamHealthResponse)
def get_stream_health(
    stream_id: str,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> StreamHealthResponse:
    row = StreamRepository(session).get(
        stream_id, allowed_departments=principal.allowed_departments
    )
    if row is None:
        raise HTTPException(404, "Stream not found")
    return stream_to_response(*row).health


@router.get("/streams/{stream_id}/probes", response_model=StreamProbeListResponse)
def list_stream_probes(
    stream_id: str,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StreamProbeListResponse:
    repository = StreamRepository(session)
    if repository.get(
        stream_id, allowed_departments=principal.allowed_departments
    ) is None:
        raise HTTPException(404, "Stream not found")
    return repository.list_probes(stream_id, limit=limit, offset=offset)


@router.post(
    "/streams/{stream_id}/probe",
    response_model=ProbeQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_stream_probe(
    stream_id: str,
    request: Request,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> ProbeQueuedResponse:
    try:
        endpoint = StreamService(session).queue_probe(
            stream_id,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    return ProbeQueuedResponse(stream_id=endpoint.stream_id, probe_due_at=endpoint.probe_due_at)


@router.post(
    "/streams/{stream_id}/capabilities/discover",
    response_model=CameraCapabilityDiscoveryResponse,
)
def discover_camera_capabilities(
    stream_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> CameraCapabilityDiscoveryResponse:
    settings = request.app.state.settings
    try:
        result = CapabilityService(session).discover_synchronously(
            stream_id,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
            engine=build_capability_discovery_engine(settings),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = (
        f'</streams/{stream_id}/capability-refreshes>; rel="successor-version"'
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return result


@router.post(
    "/streams/{stream_id}/capability-refreshes",
    response_model=CapabilityRefreshResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_capability_refresh(
    stream_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> CapabilityRefreshResponse:
    try:
        refresh, deduplicated = CapabilityService(session).queue_refresh(
            stream_id,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except CapabilityCooldownError as exc:
        raise HTTPException(
            429,
            str(exc),
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["Location"] = f"/capability-refreshes/{refresh.refresh_id}"
    response.headers["Cache-Control"] = "no-store"
    return capability_refresh_to_response(refresh, deduplicated=deduplicated)


@router.get(
    "/capability-refreshes/{refresh_id}",
    response_model=CapabilityRefreshResponse,
)
def get_capability_refresh(
    refresh_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> CapabilityRefreshResponse:
    try:
        refresh = CapabilityService(session).get_refresh(
            refresh_id,
            principal=principal,
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["Cache-Control"] = "no-store"
    return capability_refresh_to_response(refresh)


@router.get(
    "/streams/{stream_id}/capabilities",
    response_model=CapabilitySnapshotResponse,
)
def get_latest_capabilities(
    stream_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> CapabilitySnapshotResponse:
    try:
        result = CapabilityService(session).latest_snapshot(
            stream_id,
            principal=principal,
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get(
    "/streams/{stream_id}/capability-snapshots",
    response_model=CapabilitySnapshotListResponse,
)
def list_capability_snapshots(
    stream_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CapabilitySnapshotListResponse:
    try:
        result = CapabilityService(session).list_snapshots(
            stream_id,
            principal=principal,
            limit=limit,
            offset=offset,
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["Cache-Control"] = "no-store"
    return result


@router.post(
    "/streams/{stream_id}/onvif/imaging-inspections",
    response_model=OnvifImagingInspectionResponse,
)
def inspect_onvif_imaging(
    stream_id: str,
    payload: OnvifImagingInspectionRequest,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> OnvifImagingInspectionResponse:
    try:
        result = OnvifOperationService(
            session, request.app.state.settings
        ).inspect_imaging(
            stream_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    _no_store(response)
    return result


@router.post(
    "/streams/{stream_id}/onvif/event-pulls",
    response_model=OnvifEventPullResponse,
)
def pull_onvif_events(
    stream_id: str,
    payload: OnvifEventPullRequest,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> OnvifEventPullResponse:
    try:
        result = OnvifOperationService(
            session, request.app.state.settings
        ).pull_events(
            stream_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    _no_store(response)
    return result


@router.post(
    "/streams/{stream_id}/onvif/ptz-commands",
    response_model=OnvifPtzCommandResponse,
)
def execute_onvif_ptz_command(
    stream_id: str,
    payload: OnvifPtzCommandRequest,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ControllerPrincipal,
    reason: ReasonHeader,
) -> OnvifPtzCommandResponse:
    try:
        result = OnvifOperationService(
            session, request.app.state.settings
        ).execute_ptz(
            stream_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    _no_store(response)
    return result


@router.post(
    "/onvif/discovery-runs",
    response_model=OnvifDiscoveryResponse,
)
def run_onvif_discovery(
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: AdminPrincipal,
    reason: ReasonHeader,
) -> OnvifDiscoveryResponse:
    try:
        result = OnvifDiscoveryService(
            session, request.app.state.settings
        ).run(
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except OnvifDiscoveryDisabledError as exc:
        raise HTTPException(409, str(exc)) from exc
    except OnvifDiscoveryRuntimeError as exc:
        raise HTTPException(
            502, f"ONVIF WS-Discovery failed ({exc.reason_code})"
        ) from exc
    _no_store(response)
    return result


@router.post(
    "/streams/{stream_id}/playback-sessions",
    response_model=PlaybackSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_playback_session(
    stream_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    reason: ReasonHeader,
) -> PlaybackSessionResponse:
    try:
        result = PlaybackService(session, request.app.state.settings).create_session(
            stream_id,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except PlaybackConfigurationError as exc:
        raise HTTPException(503, "Playback signing is not configured") from exc
    except PlaybackUnavailableError as exc:
        code = 404 if str(exc) == "Stream not found" else 409
        raise HTTPException(code, str(exc)) from exc
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return result


@router.get("/internal/playback-jwks.json", include_in_schema=False)
def playback_jwks(request: Request, response: Response) -> dict[str, object]:
    try:
        signer = PlaybackSigner.from_settings(request.app.state.settings)
    except PlaybackConfigurationError as exc:
        raise HTTPException(503, "Playback signing is not configured") from exc
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return signer.jwks()
