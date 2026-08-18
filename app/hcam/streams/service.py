from __future__ import annotations

from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera, utc_now
from hcam.security.auth import Principal
from hcam.streams.locator import sanitize_stream_reference
from hcam.streams.models import StreamEndpoint, StreamHealthCurrent
from hcam.streams.schemas import StreamEndpointCreate, StreamEndpointPatch


class StreamNotFoundError(RuntimeError):
    pass


class StreamAccessError(RuntimeError):
    pass


class StreamConflictError(RuntimeError):
    pass


class StreamPreconditionError(RuntimeError):
    pass


class StreamValidationError(RuntimeError):
    pass


def _validate_locator(locator: str, protocol: str) -> str:
    normalized = locator.strip()
    sanitized = sanitize_stream_reference(normalized)
    if sanitized is None:
        raise StreamValidationError("Stream locator is invalid or unsupported")
    if sanitized != normalized:
        raise StreamValidationError(
            "Stream locator cannot contain credentials, query parameters, or fragments"
        )
    parsed = urlsplit(sanitized)
    allowed_schemes = {
        "rtsp": {"rtsp"},
        "rtsps": {"rtsps"},
        "hls": {"http", "https"},
        "http": {"http"},
        "https": {"https"},
    }
    if parsed.hostname is None or parsed.scheme.lower() not in allowed_schemes[protocol]:
        raise StreamValidationError("Stream locator does not match its protocol")
    return sanitized


def _sync_camera_projection(
    camera: Camera, endpoint: StreamEndpoint, health: StreamHealthCurrent
) -> None:
    if not endpoint.is_primary:
        return
    camera.selected_url = endpoint.locator
    camera.delivery_type = endpoint.protocol
    camera.reachability = health.state
    camera.last_checked_at = health.observed_at
    camera.codec = health.codec
    camera.container = health.container
    camera.updated_at = utc_now()


def ensure_primary_endpoint_from_camera(session: Session, camera: Camera) -> None:
    locator = camera.selected_url or camera.hls_path or camera.stream_path
    if locator is None:
        return
    existing = session.scalar(
        select(StreamEndpoint).where(
            StreamEndpoint.camera_id == camera.camera_id,
            StreamEndpoint.is_primary.is_(True),
        )
    )
    protocol = urlsplit(locator).scheme.lower()
    if protocol in {"http", "https"} and camera.delivery_type == "hls":
        protocol = "hls"
    if protocol not in {"rtsp", "rtsps", "hls", "http", "https"}:
        return
    if existing is None:
        endpoint = StreamEndpoint(
            stream_id=f"str_{uuid4().hex}",
            camera_id=camera.camera_id,
            name="primary",
            adapter_kind="legacy",
            protocol=protocol,
            locator=locator,
            transport="tcp",
            is_primary=True,
            enabled=True,
            probe_due_at=utc_now(),
        )
        health = StreamHealthCurrent(
            stream_id=endpoint.stream_id,
            state=(camera.reachability or "unknown")
            if camera.reachability in {
                "unknown",
                "healthy",
                "degraded",
                "offline",
                "unauthorized",
                "misconfigured",
                "unsupported",
            }
            else "unknown",
            observed_at=camera.last_checked_at,
            codec=camera.codec,
            container=camera.container,
        )
        session.add_all([endpoint, health])
        return
    existing.locator = locator
    existing.protocol = protocol
    existing.probe_due_at = utc_now()


class StreamService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        camera_id: str,
        payload: StreamEndpointCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> tuple[StreamEndpoint, StreamHealthCurrent]:
        stream_id = f"str_{uuid4().hex}"
        try:
            locator = _validate_locator(payload.locator, payload.protocol)
            with self.session.begin():
                camera = self.session.get(Camera, camera_id)
                if camera is None or not principal.can_access_department(
                    camera.department
                ):
                    raise StreamNotFoundError("Camera not found")
                primary = self.session.scalar(
                    select(StreamEndpoint).where(
                        StreamEndpoint.camera_id == camera_id,
                        StreamEndpoint.is_primary.is_(True),
                    )
                )
                is_primary = payload.is_primary or primary is None
                if payload.is_primary and primary is not None:
                    raise StreamConflictError("Camera already has a primary stream")
                endpoint = StreamEndpoint(
                    stream_id=stream_id,
                    camera_id=camera_id,
                    name=payload.name.strip(),
                    adapter_kind=payload.adapter_kind,
                    protocol=payload.protocol,
                    locator=locator,
                    secret_ref=payload.secret_ref,
                    transport=payload.transport,
                    is_primary=is_primary,
                    enabled=payload.enabled,
                    probe_due_at=utc_now() if payload.enabled else None,
                )
                health = StreamHealthCurrent(stream_id=stream_id)
                self.session.add_all([endpoint, health])
                if is_primary:
                    _sync_camera_projection(camera, endpoint, health)
                self.session.flush()
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.endpoint.create",
                    target_type="stream_endpoint",
                    target_id=stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="success",
                    context={
                        "camera_id": camera_id,
                        "adapter_kind": endpoint.adapter_kind,
                        "protocol": endpoint.protocol,
                        "is_primary": endpoint.is_primary,
                    },
                    request_id=request_id,
                )
            return endpoint, health
        except (
            StreamNotFoundError,
            StreamConflictError,
            StreamValidationError,
        ) as exc:
            self._record_failure(
                principal, "stream.endpoint.create", stream_id, reason, exc, request_id
            )
            raise
        except IntegrityError as exc:
            error = StreamConflictError("Stream endpoint conflicts with existing data")
            self._record_failure(
                principal, "stream.endpoint.create", stream_id, reason, error, request_id
            )
            raise error from exc

    def update(
        self,
        stream_id: str,
        payload: StreamEndpointPatch,
        *,
        expected_version: int,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> tuple[StreamEndpoint, StreamHealthCurrent]:
        try:
            with self.session.begin():
                endpoint = self.session.get(StreamEndpoint, stream_id)
                if endpoint is None:
                    raise StreamNotFoundError("Stream not found")
                camera = self.session.get(Camera, endpoint.camera_id)
                if camera is None or not principal.can_access_department(
                    camera.department
                ):
                    raise StreamNotFoundError("Stream not found")
                if endpoint.version_id != expected_version:
                    raise StreamPreconditionError("Stream version does not match")
                before = (
                    endpoint.name,
                    endpoint.locator,
                    endpoint.secret_ref,
                    endpoint.transport,
                    endpoint.is_primary,
                    endpoint.enabled,
                )
                changes = payload.model_dump(exclude_unset=True)
                if "name" in changes:
                    endpoint.name = payload.name.strip() if payload.name else ""
                if "locator" in changes and payload.locator is not None:
                    endpoint.locator = _validate_locator(
                        payload.locator, endpoint.protocol
                    )
                if "secret_ref" in changes:
                    endpoint.secret_ref = payload.secret_ref
                if "transport" in changes and payload.transport is not None:
                    if endpoint.protocol not in {"rtsp", "rtsps"} and payload.transport != "tcp":
                        raise StreamValidationError(
                            "Non-RTSP endpoints require TCP transport"
                        )
                    endpoint.transport = payload.transport
                if "enabled" in changes and payload.enabled is not None:
                    endpoint.enabled = payload.enabled
                    endpoint.probe_due_at = utc_now() if payload.enabled else None
                    if not payload.enabled:
                        endpoint.lease_owner = None
                        endpoint.lease_until = None
                if "is_primary" in changes and payload.is_primary is not None:
                    if not payload.is_primary and endpoint.is_primary:
                        raise StreamValidationError(
                            "Promote another stream instead of removing the primary stream"
                        )
                    if payload.is_primary and not endpoint.is_primary:
                        current_primary = self.session.scalar(
                            select(StreamEndpoint).where(
                                StreamEndpoint.camera_id == endpoint.camera_id,
                                StreamEndpoint.is_primary.is_(True),
                            )
                        )
                        if current_primary is not None:
                            current_primary.is_primary = False
                            current_primary.updated_at = utc_now()
                            self.session.flush()
                        endpoint.is_primary = True

                after = (
                    endpoint.name,
                    endpoint.locator,
                    endpoint.secret_ref,
                    endpoint.transport,
                    endpoint.is_primary,
                    endpoint.enabled,
                )
                if before == after:
                    raise StreamValidationError("Stream update does not change data")
                endpoint.updated_at = utc_now()
                health = self.session.get(StreamHealthCurrent, stream_id)
                if health is None:
                    raise StreamConflictError("Stream health projection is missing")
                _sync_camera_projection(camera, endpoint, health)
                self.session.flush()
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.endpoint.update",
                    target_type="stream_endpoint",
                    target_id=stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="success",
                    context={
                        "camera_id": endpoint.camera_id,
                        "changed_fields": sorted(changes),
                        "previous_version": expected_version,
                        "version": endpoint.version_id,
                    },
                    request_id=request_id,
                )
            return endpoint, health
        except (
            StreamConflictError,
            StreamNotFoundError,
            StreamPreconditionError,
            StreamValidationError,
        ) as exc:
            self._record_failure(
                principal, "stream.endpoint.update", stream_id, reason, exc, request_id
            )
            raise
        except StaleDataError as exc:
            error = StreamPreconditionError("Stream changed during the update")
            self._record_failure(
                principal, "stream.endpoint.update", stream_id, reason, error, request_id
            )
            raise error from exc
        except IntegrityError as exc:
            error = StreamConflictError("Stream update conflicts with existing data")
            self._record_failure(
                principal, "stream.endpoint.update", stream_id, reason, error, request_id
            )
            raise error from exc

    def queue_probe(
        self,
        stream_id: str,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> StreamEndpoint:
        now = utc_now()
        try:
            with self.session.begin():
                endpoint = self.session.get(StreamEndpoint, stream_id)
                if endpoint is None:
                    raise StreamNotFoundError("Stream not found")
                camera = self.session.get(Camera, endpoint.camera_id)
                if camera is None or not principal.can_access_department(
                    camera.department
                ):
                    raise StreamNotFoundError("Stream not found")
                if not endpoint.enabled:
                    raise StreamValidationError("Disabled streams cannot be probed")
                if endpoint.lease_until is not None and endpoint.lease_until > now:
                    raise StreamConflictError("Stream probe is already running")
                endpoint.probe_due_at = now
                endpoint.lease_owner = None
                endpoint.lease_until = None
                endpoint.updated_at = now
                self.session.flush()
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.probe.queue",
                    target_type="stream_endpoint",
                    target_id=stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="success",
                    context={"camera_id": endpoint.camera_id},
                    request_id=request_id,
                )
            return endpoint
        except (StreamConflictError, StreamNotFoundError, StreamValidationError) as exc:
            self._record_failure(
                principal, "stream.probe.queue", stream_id, reason, exc, request_id
            )
            raise

    def _record_failure(
        self,
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
                    target_type="stream_endpoint",
                    target_id=target_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="failure",
                    context={"error_type": type(error).__name__},
                    request_id=request_id,
                )
        except SQLAlchemyError:
            return
