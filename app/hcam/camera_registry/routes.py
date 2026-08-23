from __future__ import annotations

import re
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from hcam.camera_registry.repository import (
    CameraFilters,
    CameraRepository,
    camera_to_response,
)
from hcam.camera_registry.schemas import (
    CameraCreate,
    CameraListResponse,
    CameraPatch,
    CameraResponse,
)
from hcam.camera_registry.service import (
    CameraAccessError,
    CameraConflictError,
    CameraNotFoundError,
    CameraPreconditionError,
    CameraService,
    CameraValidationError,
)
from hcam.database import get_session
from hcam.observability import request_id_from_scope
from hcam.security.auth import (
    CAMERA_EDITOR,
    CAMERA_VIEWER,
    PLATFORM_ADMIN,
    Principal,
    RoleGuard,
)


router = APIRouter(prefix="/cameras", tags=["camera-registry"])
SessionDependency = Annotated[Session, Depends(get_session)]
ViewerPrincipal = Annotated[
    Principal,
    Depends(RoleGuard(CAMERA_VIEWER, CAMERA_EDITOR, PLATFORM_ADMIN)),
]
EditorPrincipal = Annotated[
    Principal,
    Depends(RoleGuard(CAMERA_EDITOR, PLATFORM_ADMIN)),
]
ReasonHeader = Annotated[
    str,
    Header(
        alias="X-HCAM-Reason",
        min_length=8,
        max_length=500,
        pattern=r".*\S.*",
    ),
]
_ETAG_PATTERN = re.compile(r'^"([1-9][0-9]*)"$')


def _etag(version: int) -> str:
    return f'"{version}"'


def _expected_version(if_match: str | None) -> int:
    if if_match is None:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="If-Match camera version is required",
        )
    match = _ETAG_PATTERN.fullmatch(if_match.strip())
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If-Match must contain a camera version ETag",
        )
    return int(match.group(1))


def _raise_service_error(error: RuntimeError) -> None:
    if isinstance(error, CameraNotFoundError):
        raise HTTPException(status_code=404, detail="Camera not found") from error
    if isinstance(error, CameraAccessError):
        raise HTTPException(status_code=403, detail=str(error)) from error
    if isinstance(error, CameraPreconditionError):
        raise HTTPException(status_code=412, detail=str(error)) from error
    if isinstance(error, CameraConflictError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, CameraValidationError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    raise error


@router.get("", response_model=CameraListResponse)
def list_cameras(
    session: SessionDependency,
    principal: ViewerPrincipal,
    source: Annotated[str | None, Query(max_length=64)] = None,
    department: Annotated[str | None, Query(max_length=120)] = None,
    camera_type: Annotated[str | None, Query(max_length=80)] = None,
    health_status: Annotated[str | None, Query(max_length=80)] = None,
    operational_status: Annotated[
        str | None, Query(alias="status", max_length=80)
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CameraListResponse:
    return CameraRepository(session).list(
        filters=CameraFilters(
            source=source,
            department=department,
            camera_type=camera_type,
            health_status=health_status,
            operational_status=operational_status,
            allowed_departments=principal.allowed_departments,
        ),
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(
    payload: CameraCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> CameraResponse:
    try:
        camera = CameraService(session).create(
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["ETag"] = _etag(camera.version_id)
    response.headers["Location"] = f"/cameras/{camera.camera_id}"
    return camera_to_response(camera)


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(
    camera_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> CameraResponse:
    camera = CameraRepository(session).get(camera_id)
    if camera is None or not principal.can_access_department(camera.department):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )
    response.headers["ETag"] = _etag(camera.version_id)
    return camera_to_response(camera)


@router.patch("/{camera_id}", response_model=CameraResponse)
def update_camera(
    camera_id: str,
    payload: CameraPatch,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> CameraResponse:
    try:
        camera = CameraService(session).update(
            camera_id,
            payload,
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["ETag"] = _etag(camera.version_id)
    return camera_to_response(camera)
