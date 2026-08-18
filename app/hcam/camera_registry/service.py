from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.importer import sanitize_stream_reference
from hcam.camera_registry.models import Camera, utc_now
from hcam.camera_registry.schemas import (
    CameraCreate,
    CameraPatch,
    CameraStatusSeed,
    LocationSeed,
    StreamSeed,
)
from hcam.security.auth import Principal


class CameraConflictError(RuntimeError):
    pass


class CameraNotFoundError(RuntimeError):
    pass


class CameraAccessError(RuntimeError):
    pass


class CameraPreconditionError(RuntimeError):
    pass


class CameraValidationError(RuntimeError):
    pass


CAMERA_EDITABLE_MODEL_FIELDS = (
    "display_name",
    "location_label",
    "timezone_name",
    "latitude",
    "longitude",
    "department",
    "ownership",
    "camera_type",
    "connectivity_status",
    "storage_status",
    "health_status",
    "maintenance_status",
    "metadata_status",
    "operational_status",
    "stream_path",
    "hls_path",
    "selected_url",
    "delivery_type",
    "codec",
    "container",
    "duration_seconds",
    "reachability",
    "last_checked_at",
)


def _stream_values(stream: StreamSeed) -> dict[str, Any]:
    selected_url = stream.selected_url or stream.hls_url or stream.stream_url
    return {
        "stream_path": sanitize_stream_reference(stream.stream_path),
        "hls_path": sanitize_stream_reference(stream.hls_path),
        "selected_url": sanitize_stream_reference(selected_url),
        "delivery_type": stream.delivery,
        "codec": stream.codec,
        "container": stream.container,
        "duration_seconds": stream.duration_seconds,
        "reachability": stream.reachability,
        "last_checked_at": stream.last_checked_at,
    }


def _create_values(payload: CameraCreate) -> dict[str, Any]:
    now = utc_now()
    return {
        "camera_id": payload.camera_id,
        "source_id": payload.source,
        "external_id": payload.external_id,
        "display_name": payload.display_name,
        "location_label": payload.location.label,
        "timezone_name": payload.location.timezone,
        "latitude": payload.location.latitude,
        "longitude": payload.location.longitude,
        "department": payload.department,
        "ownership": payload.ownership,
        "camera_type": payload.camera_type,
        "connectivity_status": payload.connectivity_status,
        "storage_status": payload.storage_status,
        "health_status": payload.health_status,
        "maintenance_status": payload.maintenance_status,
        "metadata_status": payload.status.metadata,
        "operational_status": payload.status.state,
        **_stream_values(payload.stream),
        "source_schema": "hcam.camera_registry.api.v1",
        "source_generated_at": None,
        "provenance": {
            "adapter": "hcam-api",
            "safe_use": "Authorized camera registry metadata only.",
        },
        "imported_at": now,
        "created_at": now,
        "updated_at": now,
    }


class CameraService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        payload: CameraCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None = None,
    ) -> Camera:
        if not principal.can_access_department(payload.department):
            error = CameraAccessError("Camera department is outside the actor scope")
            self._record_failure(
                principal=principal,
                action="camera_registry.camera.create",
                target_id=payload.camera_id,
                reason=reason,
                error=error,
                request_id=request_id,
            )
            raise error

        try:
            with self.session.begin():
                camera = Camera(**_create_values(payload))
                self.session.add(camera)
                self.session.flush()
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="camera_registry.camera.create",
                    target_type="camera",
                    target_id=camera.camera_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="success",
                    context={
                        "department": camera.department,
                        "source": camera.source_id,
                        "version": camera.version_id,
                    },
                    request_id=request_id,
                )
            return camera
        except IntegrityError as exc:
            error = CameraConflictError("Camera identity already exists")
            self._record_failure(
                principal=principal,
                action="camera_registry.camera.create",
                target_id=payload.camera_id,
                reason=reason,
                error=error,
                request_id=request_id,
            )
            raise error from exc

    def update(
        self,
        camera_id: str,
        payload: CameraPatch,
        *,
        expected_version: int,
        principal: Principal,
        reason: str,
        request_id: str | None = None,
    ) -> Camera:
        try:
            with self.session.begin():
                camera = self.session.get(Camera, camera_id)
                if camera is None or not principal.can_access_department(
                    camera.department
                ):
                    raise CameraNotFoundError("Camera not found")
                if camera.version_id != expected_version:
                    raise CameraPreconditionError("Camera version does not match")

                previous_values = {
                    field: getattr(camera, field)
                    for field in CAMERA_EDITABLE_MODEL_FIELDS
                }
                changed_fields = self._apply_patch(camera, payload)
                if not principal.can_access_department(camera.department):
                    raise CameraAccessError(
                        "Updated camera department is outside the actor scope"
                    )
                current_values = {
                    field: getattr(camera, field)
                    for field in CAMERA_EDITABLE_MODEL_FIELDS
                }
                if previous_values == current_values:
                    raise CameraValidationError(
                        "Camera update does not change registry data"
                    )

                camera.updated_at = utc_now()
                camera.source_schema = "hcam.camera_registry.api.v1"
                provenance = dict(camera.provenance)
                provenance.setdefault("original_adapter", provenance.get("adapter"))
                provenance["adapter"] = "hcam-api"
                provenance["safe_use"] = "Authorized camera registry metadata only."
                camera.provenance = provenance
                self.session.flush()

                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="camera_registry.camera.update",
                    target_type="camera",
                    target_id=camera.camera_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="success",
                    context={
                        "changed_fields": sorted(changed_fields),
                        "previous_version": expected_version,
                        "version": camera.version_id,
                    },
                    request_id=request_id,
                )
            return camera
        except (
            CameraAccessError,
            CameraConflictError,
            CameraNotFoundError,
            CameraPreconditionError,
            CameraValidationError,
        ) as exc:
            self._record_failure(
                principal=principal,
                action="camera_registry.camera.update",
                target_id=camera_id,
                reason=reason,
                error=exc,
                request_id=request_id,
            )
            raise
        except StaleDataError as exc:
            error = CameraPreconditionError("Camera changed during the update")
            self._record_failure(
                principal=principal,
                action="camera_registry.camera.update",
                target_id=camera_id,
                reason=reason,
                error=error,
                request_id=request_id,
            )
            raise error from exc
        except IntegrityError as exc:
            error = CameraConflictError("Camera update conflicts with registry data")
            self._record_failure(
                principal=principal,
                action="camera_registry.camera.update",
                target_id=camera_id,
                reason=reason,
                error=error,
                request_id=request_id,
            )
            raise error from exc

    def _record_failure(
        self,
        *,
        principal: Principal,
        action: str,
        target_id: str,
        reason: str,
        error: Exception,
        request_id: str | None,
    ) -> None:
        try:
            with self.session.begin():
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action=action,
                    target_type="camera",
                    target_id=target_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="failure",
                    context={"error_type": type(error).__name__},
                    request_id=request_id,
                )
        except SQLAlchemyError:
            return

    def _apply_patch(self, camera: Camera, payload: CameraPatch) -> set[str]:
        changes = payload.model_dump(exclude_unset=True)
        changed_fields = set(changes)

        if "display_name" in changes:
            if changes["display_name"] is None:
                raise CameraConflictError("display_name cannot be null")
            camera.display_name = changes["display_name"]

        direct_fields = {
            "department": "department",
            "ownership": "ownership",
            "camera_type": "camera_type",
            "connectivity_status": "connectivity_status",
            "storage_status": "storage_status",
            "health_status": "health_status",
            "maintenance_status": "maintenance_status",
        }
        for input_name, model_name in direct_fields.items():
            if input_name in changes:
                setattr(camera, model_name, changes[input_name])

        if "location" in changes and payload.location is not None:
            location_values = {
                "label": camera.location_label,
                "timezone": camera.timezone_name,
                "latitude": camera.latitude,
                "longitude": camera.longitude,
            }
            location_values.update(payload.location.model_dump(exclude_unset=True))
            try:
                location = LocationSeed.model_validate(location_values)
            except ValidationError as exc:
                raise CameraValidationError("Camera location update is invalid") from exc
            camera.location_label = location.label
            camera.timezone_name = location.timezone
            camera.latitude = location.latitude
            camera.longitude = location.longitude

        if "status" in changes and payload.status is not None:
            status_values = {
                "metadata": camera.metadata_status,
                "state": camera.operational_status,
            }
            status_values.update(payload.status.model_dump(exclude_unset=True))
            camera_status = CameraStatusSeed.model_validate(status_values)
            camera.metadata_status = camera_status.metadata
            camera.operational_status = camera_status.state

        if "stream" in changes and payload.stream is not None:
            stream_values = {
                "stream_path": camera.stream_path,
                "hls_path": camera.hls_path,
                "selected_url": camera.selected_url,
                "delivery": camera.delivery_type,
                "codec": camera.codec,
                "container": camera.container,
                "duration_seconds": camera.duration_seconds,
                "reachability": camera.reachability,
                "last_checked_at": camera.last_checked_at,
            }
            stream_changes = payload.stream.model_dump(exclude_unset=True)
            if "selected_url" not in stream_changes and (
                "hls_url" in stream_changes or "stream_url" in stream_changes
            ):
                stream_values["selected_url"] = None
            stream_values.update(stream_changes)
            try:
                stream = StreamSeed.model_validate(stream_values)
            except ValidationError as exc:
                raise CameraValidationError("Camera stream update is invalid") from exc
            for field, value in _stream_values(stream).items():
                setattr(camera, field, value)

        return changed_fields
