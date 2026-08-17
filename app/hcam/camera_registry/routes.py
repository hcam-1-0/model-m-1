from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from hcam.camera_registry.repository import (
    CameraFilters,
    CameraRepository,
    camera_to_response,
)
from hcam.camera_registry.schemas import CameraListResponse, CameraResponse
from hcam.database import get_session


router = APIRouter(prefix="/cameras", tags=["camera-registry"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=CameraListResponse)
def list_cameras(
    session: SessionDependency,
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
        ),
        limit=limit,
        offset=offset,
    )


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: str, session: SessionDependency) -> CameraResponse:
    camera = CameraRepository(session).get(camera_id)
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found",
        )
    return camera_to_response(camera)
