from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from time import monotonic
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera, utc_now
from hcam.security.auth import Principal
from hcam.streams.models import (
    OnvifOperationRun,
    StreamCapabilityRefresh,
    StreamCapabilitySnapshot,
    StreamEndpoint,
    StreamEventOutbox,
)
from hcam.streams.network import OnvifNetworkPolicy, StreamNetworkPolicyError
from hcam.streams.onvif import (
    HttpxOnvifTransport,
    OnvifCapabilityDiscovery,
    OnvifDeviceInformation,
    OnvifMediaCapabilities,
    OnvifResolutionError,
    OnvifService,
    OnvifSoapClient,
    get_device_clock_offset,
    get_device_information,
    get_services,
)
from hcam.streams.schemas import (
    CameraCapabilityDiscoveryResponse,
    CapabilityDeviceResponse,
    CapabilityRefreshResponse,
    CapabilitySnapshotListResponse,
    CapabilitySnapshotResponse,
    OnvifMediaCapabilitiesResponse,
)
from hcam.streams.secrets import (
    CameraSecretError,
    CameraSecretProvider,
    build_camera_secret_provider,
)


_MEDIA_NAMESPACE = "http://www.onvif.org/ver10/media/wsdl"
_REFRESH_COOLDOWN = timedelta(seconds=60)
_STALE_AFTER = timedelta(hours=36)
_HISTORY_RETENTION = timedelta(days=90)
_SYNC_DISCOVERY_OPERATION = "capability_discover_sync"


class CapabilityNotFoundError(RuntimeError):
    pass


class CapabilityValidationError(RuntimeError):
    pass


class CapabilityCooldownError(RuntimeError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("capability refresh cooldown is active")
        self.retry_after = retry_after


class CapabilityDiscoveryError(RuntimeError):
    def __init__(self, reason_code: str, *, retryable: bool) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class CapabilityEndpointConfig:
    stream_id: str
    camera_id: str
    locator: str
    protocol: str
    management_locator: str | None
    onvif_auth_mode: str
    secret_ref: str | None

    @classmethod
    def from_endpoint(cls, endpoint: StreamEndpoint) -> CapabilityEndpointConfig:
        return cls(
            stream_id=endpoint.stream_id,
            camera_id=endpoint.camera_id,
            locator=endpoint.locator,
            protocol=endpoint.protocol,
            management_locator=endpoint.management_locator,
            onvif_auth_mode=endpoint.onvif_auth_mode,
            secret_ref=endpoint.secret_ref,
        )


@dataclass(frozen=True, slots=True)
class CapabilityDiscoveryResult:
    source: str
    completeness: str
    payload: dict[str, object]
    duration_ms: float


@dataclass(frozen=True, slots=True)
class CapabilityDiscoveryEngine:
    network_policy: OnvifNetworkPolicy
    secret_provider: CameraSecretProvider
    transport: HttpxOnvifTransport

    def discover(self, endpoint: CapabilityEndpointConfig) -> CapabilityDiscoveryResult:
        started = monotonic()
        credentials = None
        if endpoint.onvif_auth_mode != "none":
            if endpoint.secret_ref is None:
                raise CapabilityDiscoveryError(
                    "credentials_unavailable", retryable=False
                )
            try:
                credentials = self.secret_provider.get(endpoint.secret_ref)
            except CameraSecretError as exc:
                raise CapabilityDiscoveryError(
                    exc.reason_code, retryable=False
                ) from exc
        client = OnvifSoapClient(
            transport=self.transport.with_network_policy(self.network_policy),
            credentials=credentials,
            auth_mode=endpoint.onvif_auth_mode,
        )
        warnings: list[str] = []
        device: OnvifDeviceInformation | None = None
        services: tuple[OnvifService, ...] = ()
        clock_offset: float | None = None
        media: OnvifMediaCapabilities | None = None
        successful_sections = 0

        if endpoint.management_locator is not None:
            self._validate_url(endpoint.management_locator)
            try:
                device = get_device_information(client, endpoint.management_locator)
                successful_sections += 1
            except OnvifResolutionError as exc:
                self._handle_section_error(exc, warnings)
            try:
                services = get_services(client, endpoint.management_locator)
                successful_sections += 1
            except OnvifResolutionError as exc:
                self._handle_section_error(exc, warnings)
            try:
                clock_offset = get_device_clock_offset(
                    client,
                    endpoint.management_locator,
                    observed_at=utc_now(),
                )
                successful_sections += 1
            except OnvifResolutionError as exc:
                self._handle_section_error(exc, warnings)

        media_url = self._media_url(endpoint, services, warnings)
        if media_url is not None:
            try:
                self._validate_url(media_url)
                media = OnvifCapabilityDiscovery(
                    timeout_seconds=self.transport.timeout_seconds,
                    max_response_bytes=self.transport.max_response_bytes,
                    soap_client=client,
                ).discover(media_url)
                successful_sections += 1
            except StreamNetworkPolicyError:
                warnings.append("network_policy_denied")
            except OnvifResolutionError as exc:
                self._handle_section_error(exc, warnings)
        else:
            warnings.append("onvif_media_service_unavailable")

        if successful_sections == 0:
            reason = warnings[0] if warnings else "onvif_no_capabilities"
            raise CapabilityDiscoveryError(
                reason,
                retryable=_retryable_reason(reason),
            )
        source = (
            "device_and_media"
            if endpoint.management_locator is not None
            else "media_only"
        )
        expected_sections = 4 if endpoint.management_locator is not None else 1
        completeness = (
            "complete"
            if successful_sections == expected_sections and not warnings
            else "partial"
        )
        payload: dict[str, object] = {
            "device": _device_payload(device, clock_offset),
            "services": [
                {"namespace": item.namespace, "version": item.version}
                for item in sorted(services, key=lambda service: service.namespace)
            ],
            "media": _media_payload(media),
            "warnings": list(dict.fromkeys(warnings))[:16],
        }
        return CapabilityDiscoveryResult(
            source=source,
            completeness=completeness,
            payload=payload,
            duration_ms=max(0.0, (monotonic() - started) * 1000),
        )

    def _validate_url(self, locator: str) -> None:
        try:
            self.network_policy.validate(locator)
        except StreamNetworkPolicyError as exc:
            raise CapabilityDiscoveryError(
                "network_policy_denied", retryable=False
            ) from exc

    def _media_url(
        self,
        endpoint: CapabilityEndpointConfig,
        services: tuple[OnvifService, ...],
        warnings: list[str],
    ) -> str | None:
        advertised = next(
            (
                service.xaddr
                for service in services
                if service.namespace == _MEDIA_NAMESPACE
            ),
            None,
        )
        if advertised is not None:
            try:
                self.network_policy.validate(advertised)
            except StreamNetworkPolicyError:
                warnings.append("onvif_advertised_service_denied")
            else:
                return advertised
        if urlsplit(endpoint.locator).scheme.lower() in {"http", "https"}:
            return endpoint.locator
        return None

    @staticmethod
    def _handle_section_error(
        error: OnvifResolutionError,
        warnings: list[str],
    ) -> None:
        if error.reason_code in {"unauthorized", "credentials_unavailable"}:
            raise CapabilityDiscoveryError(
                error.reason_code, retryable=False
            ) from error
        warnings.append(error.reason_code)


def build_capability_discovery_engine(settings) -> CapabilityDiscoveryEngine:
    network_policy = OnvifNetworkPolicy(
        rules=settings.onvif_egress_rules,
        environment=settings.environment,
        lab_http_enabled=settings.onvif_lab_http_enabled,
    )
    return CapabilityDiscoveryEngine(
        network_policy=network_policy,
        secret_provider=build_camera_secret_provider(
            settings.camera_secret_provider,
            settings.camera_secret_root,
        ),
        transport=HttpxOnvifTransport(
            timeout_seconds=settings.stream_probe_timeout_seconds,
            ca_bundle=settings.onvif_ca_bundle,
            network_policy=network_policy,
        ),
    )


def _retryable_reason(reason_code: str) -> bool:
    return reason_code in {"unreachable", "onvif_http_error"}


def _device_payload(
    device: OnvifDeviceInformation | None,
    clock_offset: float | None,
) -> dict[str, object] | None:
    if device is None and clock_offset is None:
        return None
    payload: dict[str, object] = asdict(device) if device is not None else {}
    payload["clock_offset_seconds"] = clock_offset
    return payload


def _media_payload(media: OnvifMediaCapabilities | None) -> dict[str, object] | None:
    if media is None:
        return None
    payload = asdict(media)
    payload["profiles"] = [asdict(profile) for profile in media.profiles]
    return payload


def _stable_fingerprint(payload: dict[str, object]) -> str:
    stable = copy.deepcopy(payload)
    stable.pop("warnings", None)
    device = stable.get("device")
    if isinstance(device, dict):
        device.pop("clock_offset_seconds", None)
    encoded = json.dumps(
        stable,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def store_capability_snapshot(
    session: Session,
    endpoint: StreamEndpoint,
    result: CapabilityDiscoveryResult,
    *,
    observed_at: datetime,
) -> tuple[StreamCapabilitySnapshot, bool]:
    latest = session.scalar(
        select(StreamCapabilitySnapshot)
        .where(StreamCapabilitySnapshot.stream_id == endpoint.stream_id)
        .order_by(
            StreamCapabilitySnapshot.last_observed_at.desc(),
            StreamCapabilitySnapshot.created_at.desc(),
            StreamCapabilitySnapshot.snapshot_id.desc(),
        )
        .limit(1)
    )
    fingerprint = _stable_fingerprint(result.payload)
    changed = latest is None or latest.fingerprint != fingerprint
    if latest is not None and not changed:
        latest.last_observed_at = observed_at
        latest.source = result.source
        latest.completeness = result.completeness
        latest.payload = result.payload
        snapshot = latest
    else:
        snapshot = StreamCapabilitySnapshot(
            snapshot_id=f"cps_{uuid4().hex}",
            stream_id=endpoint.stream_id,
            fingerprint=fingerprint,
            source=result.source,
            completeness=result.completeness,
            payload=result.payload,
            first_observed_at=observed_at,
            last_observed_at=observed_at,
            created_at=observed_at,
        )
        session.add(snapshot)
        session.flush()
        session.add(
            StreamEventOutbox(
                event_id=f"evt_{uuid4().hex}",
                event_type="hcam.stream.capabilities.changed.v1",
                schema_version=1,
                stream_id=endpoint.stream_id,
                camera_id=endpoint.camera_id,
                occurred_at=observed_at,
                payload={
                    "stream_id": endpoint.stream_id,
                    "camera_id": endpoint.camera_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "previous_snapshot_id": latest.snapshot_id if latest else None,
                    "source": result.source,
                    "completeness": result.completeness,
                    "observed_at": observed_at.isoformat(),
                },
            )
        )
    session.execute(
        delete(StreamCapabilitySnapshot).where(
            StreamCapabilitySnapshot.stream_id == endpoint.stream_id,
            StreamCapabilitySnapshot.last_observed_at
            < observed_at - _HISTORY_RETENTION,
            StreamCapabilitySnapshot.snapshot_id != snapshot.snapshot_id,
        )
    )
    return snapshot, changed


def capability_refresh_to_response(
    refresh: StreamCapabilityRefresh,
    *,
    deduplicated: bool = False,
) -> CapabilityRefreshResponse:
    return CapabilityRefreshResponse(
        refresh_id=refresh.refresh_id,
        stream_id=refresh.stream_id,
        status=refresh.status,
        source=refresh.source,
        attempt_count=refresh.attempt_count,
        max_attempts=refresh.max_attempts,
        reason_code=refresh.reason_code,
        completeness=refresh.result_completeness,
        snapshot_id=refresh.snapshot_id,
        queued_at=refresh.queued_at,
        started_at=refresh.started_at,
        finished_at=refresh.finished_at,
        next_attempt_at=refresh.next_attempt_at,
        deduplicated=deduplicated,
    )


def capability_snapshot_to_response(
    snapshot: StreamCapabilitySnapshot,
    *,
    camera_id: str,
    now: datetime | None = None,
) -> CapabilitySnapshotResponse:
    observed_at = snapshot.last_observed_at
    stale_at = observed_at + _STALE_AFTER
    payload = snapshot.payload
    return CapabilitySnapshotResponse(
        snapshot_id=snapshot.snapshot_id,
        stream_id=snapshot.stream_id,
        camera_id=camera_id,
        source=snapshot.source,
        completeness=snapshot.completeness,
        fresh=(now or utc_now()) < stale_at,
        observed_at=observed_at,
        stale_at=stale_at,
        device=(
            CapabilityDeviceResponse.model_validate(payload["device"])
            if isinstance(payload.get("device"), dict)
            else None
        ),
        services=(
            payload["services"] if isinstance(payload.get("services"), list) else []
        ),
        media=(
            OnvifMediaCapabilitiesResponse.model_validate(payload["media"])
            if isinstance(payload.get("media"), dict)
            else None
        ),
        warnings=(
            payload["warnings"] if isinstance(payload.get("warnings"), list) else []
        ),
    )


class CapabilityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def queue_refresh(
        self,
        stream_id: str,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> tuple[StreamCapabilityRefresh, bool]:
        now = utc_now()
        try:
            with self.session.begin():
                endpoint, _camera = self._authorized_endpoint(stream_id, principal)
                _validate_capability_endpoint(endpoint)
                active = self._active_refresh(stream_id)
                if active is not None:
                    return active, True
                previous = self.session.scalar(
                    select(StreamCapabilityRefresh)
                    .where(StreamCapabilityRefresh.stream_id == stream_id)
                    .order_by(StreamCapabilityRefresh.queued_at.desc())
                    .limit(1)
                )
                cooldown_anchor = None
                if previous is not None:
                    cooldown_anchor = previous.finished_at or previous.queued_at
                if (
                    cooldown_anchor is not None
                    and cooldown_anchor + _REFRESH_COOLDOWN > now
                ):
                    remaining = cooldown_anchor + _REFRESH_COOLDOWN - now
                    raise CapabilityCooldownError(
                        max(1, int(remaining.total_seconds()) + 1)
                    )
                refresh = StreamCapabilityRefresh(
                    refresh_id=f"cpr_{uuid4().hex}",
                    stream_id=stream_id,
                    status="queued",
                    source="manual",
                    priority=100,
                    requested_by=principal.actor_id,
                    request_id=request_id,
                    audit_reason=reason.strip(),
                    attempt_count=0,
                    max_attempts=3,
                    next_attempt_at=now,
                    queued_at=now,
                    created_at=now,
                    updated_at=now,
                )
                self.session.add(refresh)
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.capability_refresh.queue",
                    target_type="stream_capability_refresh",
                    target_id=refresh.refresh_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="success",
                    context={"stream_id": stream_id, "camera_id": endpoint.camera_id},
                    request_id=request_id,
                )
                self.session.flush()
            return refresh, False
        except IntegrityError as exc:
            self.session.rollback()
            with self.session.begin():
                endpoint, _camera = self._authorized_endpoint(stream_id, principal)
                _validate_capability_endpoint(endpoint)
                active = self._active_refresh(stream_id)
                if active is not None:
                    return active, True
            raise CapabilityValidationError(
                "capability refresh conflicted with another request"
            ) from exc

    def _active_refresh(self, stream_id: str) -> StreamCapabilityRefresh | None:
        return self.session.scalar(
            select(StreamCapabilityRefresh)
            .where(
                StreamCapabilityRefresh.stream_id == stream_id,
                StreamCapabilityRefresh.status.in_(("queued", "running")),
            )
            .order_by(StreamCapabilityRefresh.queued_at.desc())
            .limit(1)
        )

    def discover_synchronously(
        self,
        stream_id: str,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
        engine: CapabilityDiscoveryEngine,
    ) -> CameraCapabilityDiscoveryResponse:
        operation_id = f"ovf_{uuid4().hex}"
        requested_at = utc_now()
        started = monotonic()
        with self.session.begin():
            endpoint, _camera = self._authorized_endpoint(stream_id, principal)
            _validate_capability_endpoint(endpoint)
            config = CapabilityEndpointConfig.from_endpoint(endpoint)
        self._begin_synchronous_discovery(
            operation_id,
            config,
            principal,
            reason,
            request_id,
            requested_at,
        )
        try:
            result = engine.discover(config)
            media_payload = result.payload.get("media")
            if not isinstance(media_payload, dict):
                raise CapabilityDiscoveryError(
                    "onvif_media_service_unavailable", retryable=False
                )
            response = CameraCapabilityDiscoveryResponse(
                stream_id=stream_id,
                camera_id=config.camera_id,
                discovered_at=utc_now(),
                media=OnvifMediaCapabilitiesResponse.model_validate(media_payload),
            )
        except (
            CapabilityDiscoveryError,
            CapabilityNotFoundError,
            CapabilityValidationError,
        ) as exc:
            reason_code = (
                exc.reason_code
                if isinstance(exc, CapabilityDiscoveryError)
                else type(exc).__name__
            )
            self._complete_synchronous_discovery_failure(
                operation_id,
                config,
                principal,
                reason,
                request_id,
                started,
                reason_code=reason_code,
                error_type=type(exc).__name__,
            )
            raise
        except Exception as exc:
            error = CapabilityDiscoveryError(
                "capability_discovery_error", retryable=False
            )
            self._complete_synchronous_discovery_failure(
                operation_id,
                config,
                principal,
                reason,
                request_id,
                started,
                reason_code=error.reason_code,
                error_type=type(error).__name__,
            )
            raise error from exc

        profiles = response.media.profiles
        configured_features = sorted(
            {
                feature
                for profile in profiles
                for feature, configured in (
                    ("audio", profile.audio_encoding is not None),
                    ("ptz", profile.ptz_configured),
                    ("analytics", profile.analytics_configured),
                    ("metadata", profile.metadata_configured),
                )
                if configured
            }
        )
        finished_at = utc_now()
        duration_ms = max(0.0, (monotonic() - started) * 1000)
        try:
            with self.session.begin():
                endpoint = self.session.get(StreamEndpoint, stream_id)
                if endpoint is None:
                    raise CapabilityNotFoundError("Stream not found")
                store_capability_snapshot(
                    self.session,
                    endpoint,
                    result,
                    observed_at=response.discovered_at,
                )
                run = self._pending_synchronous_discovery(
                    operation_id, config, principal
                )
                run.outcome = "success"
                run.reason_code = None
                run.finished_at = finished_at
                run.duration_ms = duration_ms
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.capabilities.discover",
                    target_type="stream_endpoint",
                    target_id=stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="success",
                    context={
                        "camera_id": config.camera_id,
                        "profile_count": len(profiles),
                        "configured_features": configured_features,
                        "compatibility_endpoint": True,
                        "operation_id": operation_id,
                    },
                    request_id=request_id,
                )
        except SQLAlchemyError as audit_exc:
            self.session.rollback()
            raise CapabilityDiscoveryError(
                "capability_audit_unavailable", retryable=False
            ) from audit_exc
        except CapabilityNotFoundError as exc:
            self._complete_synchronous_discovery_failure(
                operation_id,
                config,
                principal,
                reason,
                request_id,
                started,
                reason_code=type(exc).__name__,
                error_type=type(exc).__name__,
            )
            raise
        return response

    def _begin_synchronous_discovery(
        self,
        operation_id: str,
        config: CapabilityEndpointConfig,
        principal: Principal,
        reason: str,
        request_id: str | None,
        requested_at: datetime,
    ) -> None:
        try:
            with self.session.begin():
                self.session.add(
                    OnvifOperationRun(
                        operation_id=operation_id,
                        stream_id=config.stream_id,
                        actor_id=principal.actor_id,
                        operation_type=_SYNC_DISCOVERY_OPERATION,
                        outcome="pending",
                        reason_code=None,
                        parameters={"compatibility_endpoint": True},
                        audit_reason=reason.strip(),
                        request_id=request_id,
                        requested_at=requested_at,
                        finished_at=None,
                        duration_ms=None,
                    )
                )
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.capabilities.discover.requested",
                    target_type="stream_endpoint",
                    target_id=config.stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="pending",
                    context={
                        "camera_id": config.camera_id,
                        "compatibility_endpoint": True,
                        "operation_id": operation_id,
                    },
                    request_id=request_id,
                )
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise CapabilityDiscoveryError(
                "capability_audit_unavailable", retryable=False
            ) from exc

    def _pending_synchronous_discovery(
        self,
        operation_id: str,
        config: CapabilityEndpointConfig,
        principal: Principal,
    ) -> OnvifOperationRun:
        run = self.session.get(OnvifOperationRun, operation_id)
        if (
            run is None
            or run.stream_id != config.stream_id
            or run.actor_id != principal.actor_id
            or run.operation_type != _SYNC_DISCOVERY_OPERATION
            or run.outcome != "pending"
        ):
            raise CapabilityDiscoveryError(
                "capability_audit_unavailable", retryable=False
            )
        return run

    def _complete_synchronous_discovery_failure(
        self,
        operation_id: str,
        config: CapabilityEndpointConfig,
        principal: Principal,
        reason: str,
        request_id: str | None,
        started: float,
        *,
        reason_code: str,
        error_type: str,
    ) -> None:
        safe_reason = reason_code[:64]
        try:
            with self.session.begin():
                run = self._pending_synchronous_discovery(
                    operation_id, config, principal
                )
                run.outcome = "failure"
                run.reason_code = safe_reason
                run.finished_at = utc_now()
                run.duration_ms = max(0.0, (monotonic() - started) * 1000)
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.capabilities.discover",
                    target_type="stream_endpoint",
                    target_id=config.stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="failure",
                    context={
                        "error_type": error_type,
                        "reason_code": safe_reason,
                        "compatibility_endpoint": True,
                        "operation_id": operation_id,
                    },
                    request_id=request_id,
                )
        except SQLAlchemyError as audit_exc:
            self.session.rollback()
            raise CapabilityDiscoveryError(
                "capability_audit_unavailable", retryable=False
            ) from audit_exc

    def get_refresh(
        self,
        refresh_id: str,
        *,
        principal: Principal,
    ) -> StreamCapabilityRefresh:
        query = (
            select(StreamCapabilityRefresh)
            .join(
                StreamEndpoint,
                StreamEndpoint.stream_id == StreamCapabilityRefresh.stream_id,
            )
            .join(Camera, Camera.camera_id == StreamEndpoint.camera_id)
            .where(StreamCapabilityRefresh.refresh_id == refresh_id)
        )
        if principal.allowed_departments is not None:
            if not principal.allowed_departments:
                raise CapabilityNotFoundError("Capability refresh not found")
            query = query.where(Camera.department.in_(principal.allowed_departments))
        refresh = self.session.scalar(query)
        if refresh is None:
            raise CapabilityNotFoundError("Capability refresh not found")
        return refresh

    def latest_snapshot(
        self,
        stream_id: str,
        *,
        principal: Principal,
    ) -> CapabilitySnapshotResponse:
        endpoint, _camera = self._authorized_endpoint(stream_id, principal)
        snapshot = self.session.scalar(
            select(StreamCapabilitySnapshot)
            .where(StreamCapabilitySnapshot.stream_id == stream_id)
            .order_by(
                StreamCapabilitySnapshot.last_observed_at.desc(),
                StreamCapabilitySnapshot.created_at.desc(),
                StreamCapabilitySnapshot.snapshot_id.desc(),
            )
            .limit(1)
        )
        if snapshot is None:
            raise CapabilityNotFoundError("Capability snapshot not found")
        return capability_snapshot_to_response(
            snapshot,
            camera_id=endpoint.camera_id,
        )

    def list_snapshots(
        self,
        stream_id: str,
        *,
        principal: Principal,
        limit: int,
        offset: int,
    ) -> CapabilitySnapshotListResponse:
        endpoint, _camera = self._authorized_endpoint(stream_id, principal)
        query = select(StreamCapabilitySnapshot).where(
            StreamCapabilitySnapshot.stream_id == stream_id
        )
        total = int(
            self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
        snapshots = self.session.scalars(
            query.order_by(
                StreamCapabilitySnapshot.last_observed_at.desc(),
                StreamCapabilitySnapshot.created_at.desc(),
                StreamCapabilitySnapshot.snapshot_id.desc(),
            )
            .limit(limit)
            .offset(offset)
        ).all()
        return CapabilitySnapshotListResponse(
            items=[
                capability_snapshot_to_response(
                    snapshot,
                    camera_id=endpoint.camera_id,
                )
                for snapshot in snapshots
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    def store_legacy_media_result(
        self,
        response: CameraCapabilityDiscoveryResponse,
    ) -> StreamCapabilitySnapshot:
        result = CapabilityDiscoveryResult(
            source="media_only",
            completeness="complete",
            payload={
                "device": None,
                "services": [],
                "media": response.media.model_dump(mode="json"),
                "warnings": [],
            },
            duration_ms=0,
        )
        with self.session.begin():
            endpoint = self.session.get(StreamEndpoint, response.stream_id)
            if endpoint is None:
                raise CapabilityNotFoundError("Stream not found")
            snapshot, _changed = store_capability_snapshot(
                self.session,
                endpoint,
                result,
                observed_at=response.discovered_at,
            )
        return snapshot

    def _authorized_endpoint(
        self,
        stream_id: str,
        principal: Principal,
    ) -> tuple[StreamEndpoint, Camera]:
        query = (
            select(StreamEndpoint, Camera)
            .join(Camera, Camera.camera_id == StreamEndpoint.camera_id)
            .where(StreamEndpoint.stream_id == stream_id)
        )
        if principal.allowed_departments is not None:
            if not principal.allowed_departments:
                raise CapabilityNotFoundError("Stream not found")
            query = query.where(Camera.department.in_(principal.allowed_departments))
        row = self.session.execute(query).one_or_none()
        if row is None:
            raise CapabilityNotFoundError("Stream not found")
        return row


def _validate_capability_endpoint(endpoint: StreamEndpoint) -> None:
    if endpoint.adapter_kind != "onvif":
        raise CapabilityValidationError("Capability refresh requires an ONVIF stream")
    if not endpoint.enabled:
        raise CapabilityValidationError("Disabled streams cannot refresh capabilities")
    if endpoint.management_locator is None and endpoint.protocol not in {
        "http",
        "https",
    }:
        raise CapabilityValidationError(
            "Capability refresh requires HTTP(S) management or media service URL"
        )
    if endpoint.onvif_auth_mode == "none" and endpoint.secret_ref is not None:
        raise CapabilityValidationError(
            "ONVIF credentials are not available unless authentication mode is enabled"
        )
    if endpoint.onvif_auth_mode != "none" and endpoint.secret_ref is None:
        raise CapabilityValidationError(
            "Authenticated ONVIF access requires a secret reference"
        )
