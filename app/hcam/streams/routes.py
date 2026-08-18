from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from hcam.database import get_session
from hcam.observability import request_id_from_scope
from hcam.security.auth import CAMERA_EDITOR, CAMERA_VIEWER, PLATFORM_ADMIN, Principal, RoleGuard
from hcam.streams.repository import StreamFilters, StreamRepository, stream_to_response
from hcam.streams.playback import (
    PlaybackConfigurationError,
    PlaybackService,
    PlaybackSigner,
    PlaybackUnavailableError,
)
from hcam.streams.schemas import (
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
    if isinstance(error, StreamNotFoundError):
        raise HTTPException(404, "Stream not found") from error
    if isinstance(error, StreamPreconditionError):
        raise HTTPException(412, str(error)) from error
    if isinstance(error, StreamConflictError):
        raise HTTPException(409, str(error)) from error
    if isinstance(error, StreamValidationError):
        raise HTTPException(422, str(error)) from error
    raise error


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
