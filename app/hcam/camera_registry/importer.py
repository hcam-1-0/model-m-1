from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera, utc_now
from hcam.camera_registry.schemas import CameraSeed, RegistryImportResult, RegistrySeed


class RegistryImportError(RuntimeError):
    pass


MAX_STREAM_REFERENCE_LENGTH = 4096


class RegistrySourceAdapter(Protocol):
    @property
    def reference(self) -> str: ...

    def load(self) -> RegistrySeed: ...


class JsonFileRegistryAdapter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @property
    def reference(self) -> str:
        return self.path.name

    def load(self) -> RegistrySeed:
        if not self.path.is_file():
            raise RegistryImportError(f"registry seed file not found: {self.path}")

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RegistryImportError(
                f"registry seed could not be read: {self.path.name}"
            ) from exc

        try:
            return RegistrySeed.model_validate(payload)
        except ValidationError as exc:
            raise RegistryImportError(
                f"registry seed does not match hcam.camera_registry.seed.v1: "
                f"{self.path.name}"
            ) from exc


class PayloadRegistryAdapter:
    def __init__(self, seed: RegistrySeed, reference: str = "api-payload") -> None:
        self.seed = seed
        self._reference = reference

    @property
    def reference(self) -> str:
        return self._reference

    def load(self) -> RegistrySeed:
        return self.seed


def sanitize_stream_reference(value: str | None) -> str | None:
    if not value:
        return None

    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > MAX_STREAM_REFERENCE_LENGTH
        or any(ord(character) < 32 or ord(character) == 127 for character in normalized)
    ):
        return None

    try:
        parsed = urlsplit(normalized)
    except ValueError:
        return None
    if not parsed.scheme and not parsed.netloc:
        return parsed.path or None

    if parsed.scheme.lower() not in {"http", "https", "rtsp", "rtsps"}:
        return None
    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None
    if hostname is None:
        return None

    host = hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if port is not None:
        host = f"{host}:{port}"
    return urlunsplit((parsed.scheme.lower(), host, parsed.path, "", ""))


CAMERA_MUTABLE_FIELDS = (
    "source_id",
    "external_id",
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
    "source_schema",
    "source_generated_at",
    "provenance",
)


def _comparable_value(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(UTC).replace(tzinfo=None)
        return value
    return value


def _camera_values(seed: RegistrySeed, camera: CameraSeed) -> dict[str, Any]:
    selected_url = (
        camera.stream.selected_url
        or camera.stream.hls_url
        or camera.stream.stream_url
    )
    source_details = {
        "adapter": seed.source.adapter,
        "base_url": sanitize_stream_reference(seed.source.base_url),
        "safe_use": seed.source.safe_use,
    }
    return {
        "camera_id": camera.camera_id,
        "source_id": camera.source,
        "external_id": camera.external_id,
        "display_name": camera.display_name,
        "location_label": camera.location.label,
        "timezone_name": camera.location.timezone,
        "latitude": camera.location.latitude,
        "longitude": camera.location.longitude,
        "department": camera.department,
        "ownership": camera.ownership,
        "camera_type": camera.camera_type,
        "connectivity_status": camera.connectivity_status,
        "storage_status": camera.storage_status,
        "health_status": camera.health_status,
        "maintenance_status": camera.maintenance_status,
        "metadata_status": camera.status.metadata,
        "operational_status": camera.status.state,
        "stream_path": sanitize_stream_reference(camera.stream.stream_path),
        "hls_path": sanitize_stream_reference(camera.stream.hls_path),
        "selected_url": sanitize_stream_reference(selected_url),
        "delivery_type": camera.stream.delivery,
        "codec": camera.stream.codec,
        "container": camera.stream.container,
        "duration_seconds": camera.stream.duration_seconds,
        "reachability": camera.stream.reachability,
        "last_checked_at": camera.stream.last_checked_at,
        "source_schema": seed.schema_name,
        "source_generated_at": seed.generated_at,
        "provenance": source_details,
    }


class RegistryImporter:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def import_file(self, path: str | Path) -> RegistryImportResult:
        return self.import_adapter(JsonFileRegistryAdapter(path))

    def import_adapter(
        self,
        adapter: RegistrySourceAdapter,
        *,
        actor_id: str | None = None,
        reason: str = "Phase 1 local registry seed import",
        request_id: str | None = None,
    ) -> RegistryImportResult:
        try:
            seed = adapter.load()
        except Exception as exc:
            self._record_failure(adapter.reference, exc, actor_id, reason, request_id)
            if isinstance(exc, RegistryImportError):
                raise
            raise RegistryImportError("registry adapter failed") from exc

        try:
            return self._persist(seed, adapter.reference, actor_id, reason, request_id)
        except Exception as exc:
            self._record_failure(adapter.reference, exc, actor_id, reason, request_id)
            if isinstance(exc, RegistryImportError):
                raise
            raise RegistryImportError("registry import failed") from exc

    def _persist(
        self,
        seed: RegistrySeed,
        reference: str,
        actor_id: str | None,
        reason: str,
        request_id: str | None,
    ) -> RegistryImportResult:
        created = 0
        updated = 0
        unchanged = 0
        now = utc_now()

        with self.session_factory() as session, session.begin():
            for seed_camera in seed.cameras:
                values = _camera_values(seed, seed_camera)
                camera = session.get(Camera, seed_camera.camera_id)
                if camera is None:
                    session.add(Camera(**values, imported_at=now))
                    created += 1
                    continue

                changed = any(
                    _comparable_value(getattr(camera, field))
                    != _comparable_value(values[field])
                    for field in CAMERA_MUTABLE_FIELDS
                )
                if not changed:
                    unchanged += 1
                    continue

                for field in CAMERA_MUTABLE_FIELDS:
                    setattr(camera, field, values[field])
                camera.imported_at = now
                camera.updated_at = now
                updated += 1

            audit_event = AuditRepository(session).record(
                actor_id=actor_id,
                action="camera_registry.import",
                target_type="camera_registry",
                target_id=seed.source.adapter,
                source="hcam.registry_importer",
                reason=reason,
                outcome="success",
                context={
                    "file": reference,
                    "schema": seed.schema_name,
                    "created": created,
                    "updated": updated,
                    "unchanged": unchanged,
                    "total": len(seed.cameras),
                },
                request_id=request_id,
            )
            audit_event_id = audit_event.event_id

        return RegistryImportResult(
            schema_name=seed.schema_name,
            source=seed.source.adapter,
            created=created,
            updated=updated,
            unchanged=unchanged,
            total=len(seed.cameras),
            audit_event_id=audit_event_id,
        )

    def _record_failure(
        self,
        reference: str,
        error: Exception,
        actor_id: str | None,
        reason: str,
        request_id: str | None,
    ) -> None:
        try:
            with self.session_factory() as session, session.begin():
                AuditRepository(session).record(
                    actor_id=actor_id,
                    action="camera_registry.import",
                    target_type="camera_registry",
                    source="hcam.registry_importer",
                    reason=reason,
                    outcome="failure",
                    context={
                        "file": reference,
                        "error_type": type(error).__name__,
                    },
                    request_id=request_id,
                )
        except SQLAlchemyError:
            # A missing/unavailable database must not hide the original import error.
            return
