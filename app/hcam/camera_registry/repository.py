from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import false, func, select
from sqlalchemy.orm import Session

from hcam.camera_registry.models import Camera
from hcam.camera_registry.schemas import (
    CameraListResponse,
    CameraResponse,
    LocationResponse,
    ProvenanceResponse,
    StateResponse,
    StreamResponse,
)


@dataclass(frozen=True, slots=True)
class CameraFilters:
    source: str | None = None
    department: str | None = None
    camera_type: str | None = None
    health_status: str | None = None
    operational_status: str | None = None
    allowed_departments: frozenset[str] | None = None


def camera_to_response(camera: Camera) -> CameraResponse:
    return CameraResponse(
        camera_id=camera.camera_id,
        version=camera.version_id,
        source=camera.source_id,
        external_id=camera.external_id,
        display_name=camera.display_name,
        department=camera.department,
        ownership=camera.ownership,
        camera_type=camera.camera_type,
        location=LocationResponse(
            label=camera.location_label,
            timezone=camera.timezone_name,
            latitude=camera.latitude,
            longitude=camera.longitude,
        ),
        state=StateResponse(
            metadata=camera.metadata_status,
            operational=camera.operational_status,
            connectivity=camera.connectivity_status,
            health=camera.health_status,
            storage=camera.storage_status,
            maintenance=camera.maintenance_status,
        ),
        stream=StreamResponse(
            stream_path=camera.stream_path,
            hls_path=camera.hls_path,
            selected_url=camera.selected_url,
            delivery=camera.delivery_type,
            codec=camera.codec,
            container=camera.container,
            duration_seconds=camera.duration_seconds,
            reachability=camera.reachability,
            last_checked_at=camera.last_checked_at,
        ),
        provenance=ProvenanceResponse(
            schema_name=camera.source_schema,
            adapter=str(camera.provenance.get("adapter", camera.source_id)),
            generated_at=camera.source_generated_at,
            imported_at=camera.imported_at,
            details=camera.provenance,
        ),
        created_at=camera.created_at,
        updated_at=camera.updated_at,
    )


class CameraRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, camera_id: str) -> Camera | None:
        return self.session.get(Camera, camera_id)

    def list(
        self,
        *,
        filters: CameraFilters,
        limit: int,
        offset: int,
    ) -> CameraListResponse:
        conditions = []
        if filters.source is not None:
            conditions.append(Camera.source_id == filters.source)
        if filters.department is not None:
            conditions.append(Camera.department == filters.department)
        if filters.camera_type is not None:
            conditions.append(Camera.camera_type == filters.camera_type)
        if filters.health_status is not None:
            conditions.append(Camera.health_status == filters.health_status)
        if filters.operational_status is not None:
            conditions.append(Camera.operational_status == filters.operational_status)
        if filters.allowed_departments is not None:
            if filters.allowed_departments:
                conditions.append(Camera.department.in_(filters.allowed_departments))
            else:
                conditions.append(false())

        count_statement = select(func.count()).select_from(Camera).where(*conditions)
        total = int(self.session.scalar(count_statement) or 0)
        statement = (
            select(Camera)
            .where(*conditions)
            .order_by(Camera.camera_id)
            .offset(offset)
            .limit(limit)
        )
        cameras = self.session.scalars(statement).all()
        return CameraListResponse(
            items=[camera_to_response(camera) for camera in cameras],
            total=total,
            limit=limit,
            offset=offset,
        )
