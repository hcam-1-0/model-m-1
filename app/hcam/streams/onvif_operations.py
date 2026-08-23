from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import monotonic
from uuid import uuid4
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera, utc_now
from hcam.security.auth import Principal
from hcam.settings import Settings
from hcam.streams.models import OnvifControlLease, OnvifOperationRun, StreamEndpoint
from hcam.streams.network import OnvifNetworkPolicy, StreamNetworkPolicyError
from hcam.streams.onvif import (
    HttpxOnvifTransport,
    OnvifResolutionError,
    OnvifService,
    OnvifSoapClient,
    get_profiles,
    get_services,
)
from hcam.streams.schemas import (
    OnvifEventMessageResponse,
    OnvifEventPullRequest,
    OnvifEventPullResponse,
    OnvifImagingInspectionRequest,
    OnvifImagingInspectionResponse,
    OnvifPtzCommandRequest,
    OnvifPtzCommandResponse,
)
from hcam.streams.secrets import (
    CameraSecretError,
    CameraSecretProvider,
    build_camera_secret_provider,
)


_MEDIA_NAMESPACE = "http://www.onvif.org/ver10/media/wsdl"
_IMAGING_NAMESPACE = "http://www.onvif.org/ver20/imaging/wsdl"
_EVENTS_NAMESPACE = "http://www.onvif.org/ver10/events/wsdl"
_PTZ_NAMESPACE = "http://www.onvif.org/ver20/ptz/wsdl"
_WSA_NAMESPACE = "http://www.w3.org/2005/08/addressing"
_MAX_TEXT = 500


class OnvifOperationNotFoundError(RuntimeError):
    pass


class OnvifOperationValidationError(RuntimeError):
    pass


class OnvifOperationConflictError(RuntimeError):
    pass


class OnvifOperationError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class OnvifEndpointConfig:
    stream_id: str
    camera_id: str
    management_locator: str
    onvif_auth_mode: str
    secret_ref: str | None
    onvif_control_enabled: bool
    onvif_max_velocity: float
    onvif_max_move_seconds: float

    @classmethod
    def from_endpoint(cls, endpoint: StreamEndpoint) -> OnvifEndpointConfig:
        if endpoint.management_locator is None:
            raise OnvifOperationValidationError(
                "ONVIF operations require a management locator"
            )
        return cls(
            stream_id=endpoint.stream_id,
            camera_id=endpoint.camera_id,
            management_locator=endpoint.management_locator,
            onvif_auth_mode=endpoint.onvif_auth_mode,
            secret_ref=endpoint.secret_ref,
            onvif_control_enabled=endpoint.onvif_control_enabled,
            onvif_max_velocity=endpoint.onvif_max_velocity,
            onvif_max_move_seconds=endpoint.onvif_max_move_seconds,
        )


@dataclass(frozen=True, slots=True)
class OnvifOperationEngine:
    network_policy: OnvifNetworkPolicy
    secret_provider: CameraSecretProvider
    transport: HttpxOnvifTransport

    def inspect_imaging(
        self,
        endpoint: OnvifEndpointConfig,
        payload: OnvifImagingInspectionRequest,
        *,
        operation_id: str,
    ) -> OnvifImagingInspectionResponse:
        client, services = self._client_and_services(endpoint)
        media_url = self._service_url(services, _MEDIA_NAMESPACE)
        imaging_url = self._service_url(services, _IMAGING_NAMESPACE)
        profile = next(
            (
                item
                for item in get_profiles(client, media_url)
                if item.token == payload.profile_token
            ),
            None,
        )
        if profile is None:
            raise OnvifOperationValidationError("ONVIF media profile was not found")
        if profile.video_source_token is None:
            raise OnvifOperationValidationError(
                "ONVIF profile does not expose a video source token"
            )
        root = client.request(
            imaging_url,
            (
                '<timg:GetImagingSettings xmlns:timg="http://www.onvif.org/ver20/imaging/wsdl">'
                f"<timg:VideoSourceToken>{escape(profile.video_source_token)}</timg:VideoSourceToken>"
                "</timg:GetImagingSettings>"
            ),
            action=f"{_IMAGING_NAMESPACE}/GetImagingSettings",
        )
        settings = _first(root, "ImagingSettings")
        if settings is None:
            raise OnvifOperationError("onvif_invalid_imaging_settings")
        return OnvifImagingInspectionResponse(
            operation_id=operation_id,
            stream_id=endpoint.stream_id,
            camera_id=endpoint.camera_id,
            profile_token=profile.token,
            video_source_token=profile.video_source_token,
            brightness=_number(settings, "Brightness"),
            color_saturation=_number(settings, "ColorSaturation"),
            contrast=_number(settings, "Contrast"),
            sharpness=_number(settings, "Sharpness"),
            exposure_mode=_text(_first(_first(settings, "Exposure"), "Mode")),
            observed_at=utc_now(),
        )

    def pull_events(
        self,
        endpoint: OnvifEndpointConfig,
        payload: OnvifEventPullRequest,
        *,
        operation_id: str,
    ) -> OnvifEventPullResponse:
        client, services = self._client_and_services(endpoint)
        events_url = self._service_url(services, _EVENTS_NAMESPACE)
        created = client.request(
            events_url,
            (
                '<tev:CreatePullPointSubscription '
                'xmlns:tev="http://www.onvif.org/ver10/events/wsdl" />'
            ),
            action=f"{_EVENTS_NAMESPACE}/EventPortType/CreatePullPointSubscriptionRequest",
        )
        address = _text(_first(_first(created, "SubscriptionReference"), "Address"))
        if address is None:
            raise OnvifOperationError("onvif_invalid_subscription_reference")
        self._validate_url(address)
        subscription_terminated = False
        try:
            pulled = client.request(
                address,
                (
                    '<tev:PullMessages xmlns:tev="http://www.onvif.org/ver10/events/wsdl">'
                    f"<tev:Timeout>PT{payload.timeout_seconds:g}S</tev:Timeout>"
                    f"<tev:MessageLimit>{payload.message_limit}</tev:MessageLimit>"
                    "</tev:PullMessages>"
                ),
                action=f"{_EVENTS_NAMESPACE}/PullPointSubscription/PullMessagesRequest",
                extra_header_xml=_addressing_header(address),
            )
            messages = _parse_events(pulled, payload.message_limit)
        finally:
            try:
                client.request(
                    address,
                    '<wsnt:Unsubscribe xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2" />',
                    action=(
                        "http://docs.oasis-open.org/wsn/bw-2/"
                        "SubscriptionManager/UnsubscribeRequest"
                    ),
                    extra_header_xml=_addressing_header(address),
                )
                subscription_terminated = True
            except OnvifResolutionError:
                subscription_terminated = False
        return OnvifEventPullResponse(
            operation_id=operation_id,
            stream_id=endpoint.stream_id,
            camera_id=endpoint.camera_id,
            subscription_terminated=subscription_terminated,
            messages=messages,
            observed_at=utc_now(),
        )

    def execute_ptz(
        self,
        endpoint: OnvifEndpointConfig,
        payload: OnvifPtzCommandRequest,
        *,
        operation_id: str,
    ) -> OnvifPtzCommandResponse:
        started_at = utc_now()
        client, services = self._client_and_services(endpoint)
        media_url = self._service_url(services, _MEDIA_NAMESPACE)
        ptz_url = self._service_url(services, _PTZ_NAMESPACE)
        profile = next(
            (
                item
                for item in get_profiles(client, media_url)
                if item.token == payload.profile_token
            ),
            None,
        )
        if profile is None or not profile.ptz_configured:
            raise OnvifOperationValidationError(
                "ONVIF profile does not expose PTZ control"
            )
        auto_stopped = False
        if payload.action == "stop":
            self._stop(client, ptz_url, payload.profile_token)
        elif payload.action == "continuous":
            duration = min(
                payload.duration_seconds or endpoint.onvif_max_move_seconds,
                endpoint.onvif_max_move_seconds,
            )
            try:
                client.request(
                    ptz_url,
                    _ptz_move_body("ContinuousMove", payload, endpoint),
                    action=f"{_PTZ_NAMESPACE}/ContinuousMove",
                )
                time.sleep(duration)
            finally:
                self._stop(client, ptz_url, payload.profile_token)
                auto_stopped = True
        elif payload.action in {"relative", "absolute"}:
            operation = "RelativeMove" if payload.action == "relative" else "AbsoluteMove"
            client.request(
                ptz_url,
                _ptz_move_body(operation, payload, endpoint),
                action=f"{_PTZ_NAMESPACE}/{operation}",
            )
        else:
            client.request(
                ptz_url,
                (
                    '<tptz:GotoPreset xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">'
                    f"<tptz:ProfileToken>{escape(payload.profile_token)}</tptz:ProfileToken>"
                    f"<tptz:PresetToken>{escape(payload.preset_token or '')}</tptz:PresetToken>"
                    "</tptz:GotoPreset>"
                ),
                action=f"{_PTZ_NAMESPACE}/GotoPreset",
            )
        return OnvifPtzCommandResponse(
            operation_id=operation_id,
            stream_id=endpoint.stream_id,
            camera_id=endpoint.camera_id,
            action=payload.action,
            auto_stopped=auto_stopped,
            started_at=started_at,
            finished_at=utc_now(),
        )

    def _stop(
        self,
        client: OnvifSoapClient,
        ptz_url: str,
        profile_token: str,
    ) -> None:
        client.request(
            ptz_url,
            (
                '<tptz:Stop xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl">'
                f"<tptz:ProfileToken>{escape(profile_token)}</tptz:ProfileToken>"
                "<tptz:PanTilt>true</tptz:PanTilt><tptz:Zoom>true</tptz:Zoom>"
                "</tptz:Stop>"
            ),
            action=f"{_PTZ_NAMESPACE}/Stop",
        )

    def _client_and_services(
        self, endpoint: OnvifEndpointConfig
    ) -> tuple[OnvifSoapClient, tuple[OnvifService, ...]]:
        self._validate_url(endpoint.management_locator)
        credentials = None
        if endpoint.onvif_auth_mode != "none":
            if endpoint.secret_ref is None:
                raise OnvifOperationError("credentials_unavailable")
            try:
                credentials = self.secret_provider.get(endpoint.secret_ref)
            except CameraSecretError as exc:
                raise OnvifOperationError(exc.reason_code) from exc
        client = OnvifSoapClient(
            transport=self.transport.with_network_policy(self.network_policy),
            credentials=credentials,
            auth_mode=endpoint.onvif_auth_mode,
        )
        try:
            services = get_services(client, endpoint.management_locator)
        except OnvifResolutionError as exc:
            raise OnvifOperationError(exc.reason_code) from exc
        return client, services

    def _service_url(
        self, services: tuple[OnvifService, ...], namespace: str
    ) -> str:
        url = next(
            (service.xaddr for service in services if service.namespace == namespace),
            None,
        )
        if url is None:
            raise OnvifOperationValidationError(
                f"Camera does not advertise {namespace.rsplit('/', 2)[-2]} service"
            )
        self._validate_url(url)
        return url

    def _validate_url(self, locator: str) -> None:
        try:
            self.network_policy.validate(locator)
        except StreamNetworkPolicyError as exc:
            raise OnvifOperationError("network_policy_denied") from exc


def build_onvif_operation_engine(settings: Settings) -> OnvifOperationEngine:
    network_policy = OnvifNetworkPolicy(
        rules=settings.onvif_egress_rules,
        environment=settings.environment,
        lab_http_enabled=settings.onvif_lab_http_enabled,
    )
    return OnvifOperationEngine(
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


class OnvifOperationService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.engine = build_onvif_operation_engine(settings)

    def inspect_imaging(
        self,
        stream_id: str,
        payload: OnvifImagingInspectionRequest,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> OnvifImagingInspectionResponse:
        return self._execute(
            stream_id,
            operation_type="imaging_inspect",
            parameters={"profile_token": payload.profile_token},
            principal=principal,
            reason=reason,
            request_id=request_id,
            callback=lambda config, operation_id: self.engine.inspect_imaging(
                config, payload, operation_id=operation_id
            ),
        )

    def pull_events(
        self,
        stream_id: str,
        payload: OnvifEventPullRequest,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> OnvifEventPullResponse:
        return self._execute(
            stream_id,
            operation_type="event_pull",
            parameters={
                "message_limit": payload.message_limit,
                "timeout_seconds": payload.timeout_seconds,
            },
            principal=principal,
            reason=reason,
            request_id=request_id,
            callback=lambda config, operation_id: self.engine.pull_events(
                config, payload, operation_id=operation_id
            ),
        )

    def execute_ptz(
        self,
        stream_id: str,
        payload: OnvifPtzCommandRequest,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> OnvifPtzCommandResponse:
        config = self._authorized_config(stream_id, principal)
        return self._execute_with_config(
            config,
            operation_type=f"ptz_{payload.action}",
            parameters=_safe_ptz_parameters(payload),
            principal=principal,
            reason=reason,
            request_id=request_id,
            callback=lambda operation_id: self._execute_ptz_with_lease(
                config, payload, principal, operation_id
            ),
        )

    def _execute_ptz_with_lease(
        self,
        config: OnvifEndpointConfig,
        payload: OnvifPtzCommandRequest,
        principal: Principal,
        operation_id: str,
    ) -> OnvifPtzCommandResponse:
        if not self.settings.onvif_control_enabled or not config.onvif_control_enabled:
            raise OnvifOperationValidationError("ONVIF control is not enabled")
        _validate_ptz_limits(payload, config)
        lease_id = None
        if payload.action != "stop":
            lease_id = self._acquire_control_lease(config, principal)
        try:
            return self.engine.execute_ptz(
                config, payload, operation_id=operation_id
            )
        finally:
            if lease_id is not None:
                self._release_control_lease(config.stream_id, lease_id)

    def _execute(
        self,
        stream_id: str,
        *,
        operation_type: str,
        parameters: dict[str, object],
        principal: Principal,
        reason: str,
        request_id: str | None,
        callback,
    ):
        config = self._authorized_config(stream_id, principal)
        return self._execute_with_config(
            config,
            operation_type=operation_type,
            parameters=parameters,
            principal=principal,
            reason=reason,
            request_id=request_id,
            callback=lambda operation_id: callback(config, operation_id),
        )

    def _execute_with_config(
        self,
        config: OnvifEndpointConfig,
        *,
        operation_type: str,
        parameters: dict[str, object],
        principal: Principal,
        reason: str,
        request_id: str | None,
        callback,
    ):
        operation_id = f"ovf_{uuid4().hex}"
        started = monotonic()
        requested_at = utc_now()
        self._begin_record(
            operation_id,
            config,
            operation_type,
            parameters,
            principal,
            reason,
            request_id,
            requested_at,
        )
        try:
            result = callback(operation_id)
        except OnvifResolutionError as exc:
            error = OnvifOperationError(exc.reason_code)
            self._complete_record(
                operation_id,
                config,
                operation_type,
                "failure",
                error.reason_code,
                parameters,
                principal,
                reason,
                request_id,
                requested_at,
                started,
            )
            raise error from exc
        except (
            OnvifOperationError,
            OnvifOperationValidationError,
            OnvifOperationConflictError,
        ) as exc:
            self._complete_record(
                operation_id,
                config,
                operation_type,
                "failure",
                getattr(exc, "reason_code", type(exc).__name__),
                parameters,
                principal,
                reason,
                request_id,
                requested_at,
                started,
            )
            raise
        except Exception as exc:
            error = OnvifOperationError("onvif_operation_error")
            self._complete_record(
                operation_id,
                config,
                operation_type,
                "failure",
                error.reason_code,
                parameters,
                principal,
                reason,
                request_id,
                requested_at,
                started,
            )
            raise error from exc
        self._complete_record(
            operation_id,
            config,
            operation_type,
            "success",
            None,
            parameters,
            principal,
            reason,
            request_id,
            requested_at,
            started,
        )
        return result

    def _authorized_config(
        self, stream_id: str, principal: Principal
    ) -> OnvifEndpointConfig:
        query = (
            select(StreamEndpoint, Camera)
            .join(Camera, Camera.camera_id == StreamEndpoint.camera_id)
            .where(StreamEndpoint.stream_id == stream_id)
        )
        if principal.allowed_departments is not None:
            if not principal.allowed_departments:
                raise OnvifOperationNotFoundError("Stream not found")
            query = query.where(Camera.department.in_(principal.allowed_departments))
        row = self.session.execute(query).one_or_none()
        if row is None:
            self.session.rollback()
            raise OnvifOperationNotFoundError("Stream not found")
        endpoint, _camera = row
        if endpoint.adapter_kind != "onvif" or not endpoint.enabled:
            self.session.rollback()
            raise OnvifOperationValidationError(
                "ONVIF operations require an enabled ONVIF stream"
            )
        config = OnvifEndpointConfig.from_endpoint(endpoint)
        self.session.rollback()
        return config

    def _acquire_control_lease(
        self, config: OnvifEndpointConfig, principal: Principal
    ) -> str:
        lease_id = f"ovl_{uuid4().hex}"
        now = utc_now()
        expires_at = now + timedelta(
            seconds=max(config.onvif_max_move_seconds + 5, 10)
        )
        try:
            with self.session.begin():
                self.session.execute(
                    delete(OnvifControlLease).where(
                        OnvifControlLease.stream_id == config.stream_id,
                        OnvifControlLease.expires_at <= now,
                    )
                )
                self.session.add(
                    OnvifControlLease(
                        stream_id=config.stream_id,
                        lease_id=lease_id,
                        actor_id=principal.actor_id,
                        acquired_at=now,
                        expires_at=expires_at,
                    )
                )
        except IntegrityError as exc:
            self.session.rollback()
            raise OnvifOperationConflictError(
                "Another PTZ command is active for this stream"
            ) from exc
        return lease_id

    def _release_control_lease(self, stream_id: str, lease_id: str) -> None:
        try:
            with self.session.begin():
                self.session.execute(
                    delete(OnvifControlLease).where(
                        OnvifControlLease.stream_id == stream_id,
                        OnvifControlLease.lease_id == lease_id,
                    )
                )
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OnvifOperationError("control_lease_release_failed") from exc

    def _begin_record(
        self,
        operation_id: str,
        config: OnvifEndpointConfig,
        operation_type: str,
        parameters: dict[str, object],
        principal: Principal,
        reason: str,
        request_id: str | None,
        requested_at,
    ) -> None:
        try:
            with self.session.begin():
                self.session.add(
                    OnvifOperationRun(
                        operation_id=operation_id,
                        stream_id=config.stream_id,
                        actor_id=principal.actor_id,
                        operation_type=operation_type,
                        outcome="pending",
                        reason_code=None,
                        parameters=parameters,
                        audit_reason=reason.strip(),
                        request_id=request_id,
                        requested_at=requested_at,
                        finished_at=None,
                        duration_ms=None,
                    )
                )
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action=f"stream.onvif.{operation_type}.requested",
                    target_type="stream_endpoint",
                    target_id=config.stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="pending",
                    context={
                        "camera_id": config.camera_id,
                        "operation_id": operation_id,
                        "parameters": parameters,
                    },
                    request_id=request_id,
                )
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OnvifOperationError("operation_audit_unavailable") from exc

    def _complete_record(
        self,
        operation_id: str,
        config: OnvifEndpointConfig,
        operation_type: str,
        outcome: str,
        reason_code: str | None,
        parameters: dict[str, object],
        principal: Principal,
        reason: str,
        request_id: str | None,
        requested_at,
        started: float,
    ) -> None:
        finished_at = utc_now()
        duration_ms = max(0.0, (monotonic() - started) * 1000)
        safe_reason = reason_code[:64] if reason_code is not None else None
        try:
            with self.session.begin():
                run = self.session.get(OnvifOperationRun, operation_id)
                if (
                    run is None
                    or run.stream_id != config.stream_id
                    or run.actor_id != principal.actor_id
                    or run.operation_type != operation_type
                    or run.outcome != "pending"
                ):
                    raise OnvifOperationError("operation_audit_unavailable")
                run.outcome = outcome
                run.reason_code = safe_reason
                run.finished_at = finished_at
                run.duration_ms = duration_ms
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action=f"stream.onvif.{operation_type}.completed",
                    target_type="stream_endpoint",
                    target_id=config.stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome=outcome,
                    context={
                        "camera_id": config.camera_id,
                        "operation_id": operation_id,
                        "reason_code": safe_reason,
                        "parameters": parameters,
                    },
                    request_id=request_id,
                )
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OnvifOperationError("operation_audit_unavailable") from exc


def _validate_ptz_limits(
    payload: OnvifPtzCommandRequest, config: OnvifEndpointConfig
) -> None:
    velocity_components = (
        (payload.pan, payload.tilt, payload.zoom, payload.speed)
        if payload.action == "continuous"
        else (payload.speed,)
    )
    movement_values = [abs(value) for value in velocity_components if value is not None]
    if movement_values and max(movement_values) > config.onvif_max_velocity:
        raise OnvifOperationValidationError(
            "PTZ movement exceeds the configured per-stream velocity limit"
        )
    if (
        payload.duration_seconds is not None
        and payload.duration_seconds > config.onvif_max_move_seconds
    ):
        raise OnvifOperationValidationError(
            "PTZ movement exceeds the configured per-stream duration limit"
        )


def _safe_ptz_parameters(payload: OnvifPtzCommandRequest) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.model_dump().items()
        if value is not None
    }


def _ptz_move_body(
    operation: str,
    payload: OnvifPtzCommandRequest,
    config: OnvifEndpointConfig,
) -> str:
    vector_name = {
        "ContinuousMove": "Velocity",
        "RelativeMove": "Translation",
        "AbsoluteMove": "Position",
    }[operation]
    attributes = []
    if payload.pan is not None:
        attributes.append(f'x="{payload.pan:g}"')
    if payload.tilt is not None:
        attributes.append(f'y="{payload.tilt:g}"')
    pan_tilt = (
        f'<tt:PanTilt {" ".join(attributes)} />' if attributes else ""
    )
    zoom = f'<tt:Zoom x="{payload.zoom:g}" />' if payload.zoom is not None else ""
    speed = min(payload.speed or config.onvif_max_velocity, config.onvif_max_velocity)
    speed_xml = ""
    if operation in {"RelativeMove", "AbsoluteMove"}:
        speed_xml = (
            f'<tptz:Speed><tt:PanTilt x="{speed:g}" y="{speed:g}" />'
            f'<tt:Zoom x="{speed:g}" /></tptz:Speed>'
        )
    return (
        f'<tptz:{operation} xmlns:tptz="{_PTZ_NAMESPACE}" '
        'xmlns:tt="http://www.onvif.org/ver10/schema">'
        f"<tptz:ProfileToken>{escape(payload.profile_token)}</tptz:ProfileToken>"
        f"<tptz:{vector_name}>{pan_tilt}{zoom}</tptz:{vector_name}>"
        f"{speed_xml}</tptz:{operation}>"
    )


def _addressing_header(address: str) -> str:
    return (
        f'<wsa:To xmlns:wsa="{_WSA_NAMESPACE}">{escape(address)}</wsa:To>'
        f'<wsa:MessageID xmlns:wsa="{_WSA_NAMESPACE}">urn:uuid:{uuid4()}</wsa:MessageID>'
    )


def _local_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _first(
    element: ElementTree.Element | None, local_name: str
) -> ElementTree.Element | None:
    if element is None:
        return None
    return next(
        (item for item in element.iter() if _local_name(item) == local_name),
        None,
    )


def _text(element: ElementTree.Element | None) -> str | None:
    value = (element.text or "").strip() if element is not None else ""
    if not value:
        return None
    if len(value) > _MAX_TEXT:
        raise OnvifOperationError("onvif_response_value_too_large")
    return value


def _number(element: ElementTree.Element, local_name: str) -> float | None:
    value = _text(_first(element, local_name))
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise OnvifOperationError("onvif_invalid_numeric_value") from exc


def _parse_events(
    root: ElementTree.Element, message_limit: int
) -> list[OnvifEventMessageResponse]:
    responses: list[OnvifEventMessageResponse] = []
    notifications = [
        item for item in root.iter() if _local_name(item) == "NotificationMessage"
    ][:message_limit]
    for notification in notifications:
        message = _first(notification, "Message")
        data: dict[str, str] = {}
        if message is not None:
            for item in message.iter():
                if _local_name(item) != "SimpleItem" or len(data) >= 64:
                    continue
                name = item.attrib.get("Name", "")[:128]
                value = item.attrib.get("Value", "")[:_MAX_TEXT]
                if name:
                    data[name] = value
        utc_time = None
        utc_value = message.attrib.get("UtcTime") if message is not None else None
        if utc_value:
            try:
                utc_time = datetime.fromisoformat(utc_value.replace("Z", "+00:00"))
            except ValueError:
                utc_time = None
        responses.append(
            OnvifEventMessageResponse(
                topic=_text(_first(notification, "Topic")),
                utc_time=utc_time,
                property_operation=(
                    message.attrib.get("PropertyOperation", "")[:64] or None
                    if message is not None
                    else None
                ),
                data=data,
            )
        )
    return responses
