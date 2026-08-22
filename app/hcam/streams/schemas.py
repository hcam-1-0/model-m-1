from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator


StreamId = Annotated[str, Field(pattern=r"^str_[0-9a-f]{32}$")]
StreamName = Annotated[str, Field(min_length=1, max_length=120)]
AdapterKind = Literal["rtsp", "hls", "http", "onvif", "synthetic", "legacy"]
StreamProtocol = Literal["rtsp", "rtsps", "hls", "http", "https"]
Transport = Literal["tcp", "udp", "auto"]
OnvifAuthMode = Literal[
    "none",
    "wsse_password_digest",
    "http_digest",
    "wsse_and_http_digest",
]
HealthState = Literal[
    "unknown",
    "healthy",
    "degraded",
    "offline",
    "unauthorized",
    "misconfigured",
    "unsupported",
]
_SECRET_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")


class StreamEndpointCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StreamName
    adapter_kind: AdapterKind
    protocol: StreamProtocol
    locator: Annotated[str, Field(min_length=1, max_length=4096)]
    secret_ref: Annotated[str, Field(max_length=255)] | None = None
    management_locator: Annotated[str, Field(min_length=1, max_length=4096)] | None = None
    onvif_auth_mode: OnvifAuthMode = "none"
    capability_refresh_enabled: bool = False
    onvif_control_enabled: bool = False
    onvif_max_velocity: Annotated[float, Field(gt=0, le=1)] = 0.5
    onvif_max_move_seconds: Annotated[float, Field(ge=0.1, le=10)] = 2.0
    transport: Transport = "tcp"
    is_primary: bool = False
    enabled: bool = True

    @model_validator(mode="after")
    def validate_secret_reference(self) -> StreamEndpointCreate:
        if self.secret_ref is not None and _SECRET_REF.fullmatch(self.secret_ref) is None:
            raise ValueError("secret_ref must be an opaque path-like identifier")
        if self.protocol not in {"rtsp", "rtsps"} and self.transport != "tcp":
            raise ValueError("non-RTSP endpoints require TCP transport")
        if self.adapter_kind != "onvif" and (
            self.management_locator is not None
            or self.onvif_auth_mode != "none"
            or self.capability_refresh_enabled
            or self.onvif_control_enabled
        ):
            raise ValueError("ONVIF management settings require an ONVIF adapter")
        if self.management_locator is not None:
            _validate_management_locator(self.management_locator)
        if self.onvif_auth_mode != "none" and self.secret_ref is None:
            raise ValueError("authenticated ONVIF access requires secret_ref")
        if self.capability_refresh_enabled and self.management_locator is None:
            raise ValueError(
                "scheduled capability refresh requires management_locator"
            )
        if self.onvif_control_enabled and self.management_locator is None:
            raise ValueError("ONVIF control requires management_locator")
        return self


class StreamEndpointPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StreamName | None = None
    locator: Annotated[str, Field(min_length=1, max_length=4096)] | None = None
    secret_ref: Annotated[str, Field(max_length=255)] | None = None
    management_locator: Annotated[str, Field(min_length=1, max_length=4096)] | None = None
    onvif_auth_mode: OnvifAuthMode | None = None
    capability_refresh_enabled: bool | None = None
    onvif_control_enabled: bool | None = None
    onvif_max_velocity: Annotated[float, Field(gt=0, le=1)] | None = None
    onvif_max_move_seconds: Annotated[float, Field(ge=0.1, le=10)] | None = None
    transport: Transport | None = None
    is_primary: bool | None = None
    enabled: bool | None = None

    @model_validator(mode="after")
    def contains_change(self) -> StreamEndpointPatch:
        if not self.model_fields_set:
            raise ValueError("at least one stream field must be supplied")
        if "secret_ref" in self.model_fields_set and self.secret_ref is not None:
            if _SECRET_REF.fullmatch(self.secret_ref) is None:
                raise ValueError("secret_ref must be an opaque path-like identifier")
        if "management_locator" in self.model_fields_set and self.management_locator:
            _validate_management_locator(self.management_locator)
        return self


def _validate_management_locator(locator: str) -> None:
    normalized = locator.strip()
    parsed = urlsplit(normalized)
    if (
        normalized != locator
        or parsed.scheme.lower() not in {"http", "https"}
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "management_locator must be a credential-free HTTP(S) URL "
            "without query parameters or fragments"
        )


class StreamHealthResponse(BaseModel):
    state: HealthState
    reason_code: str | None
    observed_at: datetime | None
    consecutive_successes: int
    consecutive_failures: int
    probe_latency_ms: float | None
    codec: str | None
    container: str | None
    width: int | None
    height: int | None
    frame_rate: float | None
    last_success_at: datetime | None
    last_failure_at: datetime | None


class StreamEndpointResponse(BaseModel):
    stream_id: StreamId
    camera_id: str
    version: int
    name: str
    adapter_kind: AdapterKind
    protocol: StreamProtocol
    locator: str
    secret_configured: bool
    management_locator: str | None
    onvif_auth_mode: OnvifAuthMode
    capability_refresh_enabled: bool
    capability_due_at: datetime | None
    onvif_control_enabled: bool
    onvif_max_velocity: float
    onvif_max_move_seconds: float
    transport: Transport
    is_primary: bool
    enabled: bool
    health: StreamHealthResponse
    created_at: datetime
    updated_at: datetime


class StreamEndpointListResponse(BaseModel):
    items: list[StreamEndpointResponse]
    total: int
    limit: int
    offset: int


class StreamProbeResponse(BaseModel):
    probe_id: str
    stream_id: StreamId
    worker_id: str
    started_at: datetime
    finished_at: datetime
    outcome: Literal["success", "failure"]
    reason_code: str | None
    latency_ms: float
    media: dict[str, object]


class StreamProbeListResponse(BaseModel):
    items: list[StreamProbeResponse]
    total: int
    limit: int
    offset: int


class ProbeQueuedResponse(BaseModel):
    stream_id: StreamId
    status: Literal["queued"] = "queued"
    probe_due_at: datetime


class OnvifMediaProfileResponse(BaseModel):
    token: Annotated[str, Field(min_length=1, max_length=255)]
    name: Annotated[str, Field(max_length=255)] | None
    fixed: bool | None
    video_encoding: Annotated[str, Field(max_length=255)] | None
    width: Annotated[int, Field(ge=1, le=1_000_000)] | None
    height: Annotated[int, Field(ge=1, le=1_000_000)] | None
    frame_rate_limit: Annotated[int, Field(ge=1, le=1_000_000)] | None
    audio_encoding: Annotated[str, Field(max_length=255)] | None
    video_source_token: Annotated[str, Field(max_length=255)] | None = None
    ptz_configured: bool
    analytics_configured: bool
    metadata_configured: bool


class OnvifMediaCapabilitiesResponse(BaseModel):
    snapshot_uri: bool | None
    rotation: bool | None
    video_source_mode: bool | None
    osd: bool | None
    temporary_osd_text: bool | None
    exi_compression: bool | None
    maximum_profiles: Annotated[int, Field(ge=1, le=1_000_000)] | None
    profiles: Annotated[list[OnvifMediaProfileResponse], Field(max_length=64)]


class CameraCapabilityDiscoveryResponse(BaseModel):
    stream_id: StreamId
    camera_id: str
    discovered_at: datetime
    source: Literal["onvif_media_service"] = "onvif_media_service"
    media: OnvifMediaCapabilitiesResponse


class CapabilityRefreshResponse(BaseModel):
    refresh_id: Annotated[str, Field(pattern=r"^cpr_[0-9a-f]{32}$")]
    stream_id: StreamId
    status: Literal["queued", "running", "succeeded", "failed"]
    source: Literal["manual", "scheduled"]
    attempt_count: int
    max_attempts: int
    reason_code: str | None
    completeness: Literal["complete", "partial"] | None
    snapshot_id: str | None
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    next_attempt_at: datetime
    deduplicated: bool = False


class CapabilityDeviceResponse(BaseModel):
    manufacturer: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    serial_number: str | None = None
    hardware_id: str | None = None
    clock_offset_seconds: float | None = None


class CapabilitySnapshotResponse(BaseModel):
    snapshot_id: str
    stream_id: StreamId
    camera_id: str
    source: Literal["device_and_media", "media_only"]
    completeness: Literal["complete", "partial"]
    fresh: bool
    observed_at: datetime
    stale_at: datetime
    device: CapabilityDeviceResponse | None = None
    services: list[dict[str, object]] = Field(default_factory=list, max_length=64)
    media: OnvifMediaCapabilitiesResponse | None = None
    warnings: list[str] = Field(default_factory=list, max_length=16)


class CapabilitySnapshotListResponse(BaseModel):
    items: list[CapabilitySnapshotResponse]
    total: int
    limit: int
    offset: int


OnvifPtzAction = Literal[
    "stop",
    "continuous",
    "relative",
    "absolute",
    "goto_preset",
]


class OnvifImagingInspectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_token: Annotated[str, Field(min_length=1, max_length=255)]


class OnvifImagingInspectionResponse(BaseModel):
    operation_id: Annotated[str, Field(pattern=r"^ovf_[0-9a-f]{32}$")]
    stream_id: StreamId
    camera_id: str
    profile_token: str
    video_source_token: str
    brightness: float | None = None
    color_saturation: float | None = None
    contrast: float | None = None
    sharpness: float | None = None
    exposure_mode: str | None = None
    observed_at: datetime


class OnvifEventPullRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_limit: Annotated[int, Field(ge=1, le=32)] = 16
    timeout_seconds: Annotated[float, Field(ge=0.1, le=5)] = 1.0


class OnvifEventMessageResponse(BaseModel):
    topic: Annotated[str, Field(max_length=500)] | None = None
    utc_time: datetime | None = None
    property_operation: Annotated[str, Field(max_length=64)] | None = None
    data: dict[str, str] = Field(default_factory=dict)


class OnvifEventPullResponse(BaseModel):
    operation_id: Annotated[str, Field(pattern=r"^ovf_[0-9a-f]{32}$")]
    stream_id: StreamId
    camera_id: str
    subscription_terminated: bool
    messages: Annotated[list[OnvifEventMessageResponse], Field(max_length=32)]
    observed_at: datetime


class OnvifPtzCommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: OnvifPtzAction
    profile_token: Annotated[str, Field(min_length=1, max_length=255)]
    pan: Annotated[float, Field(ge=-1, le=1)] | None = None
    tilt: Annotated[float, Field(ge=-1, le=1)] | None = None
    zoom: Annotated[float, Field(ge=-1, le=1)] | None = None
    speed: Annotated[float, Field(gt=0, le=1)] | None = None
    duration_seconds: Annotated[float, Field(ge=0.1, le=10)] | None = None
    preset_token: Annotated[str, Field(min_length=1, max_length=255)] | None = None

    @model_validator(mode="after")
    def validate_action_fields(self) -> OnvifPtzCommandRequest:
        components = (self.pan, self.tilt, self.zoom)
        if self.action in {"continuous", "relative", "absolute"} and all(
            value is None for value in components
        ):
            raise ValueError(f"{self.action} requires pan, tilt, or zoom")
        if self.action == "continuous" and self.duration_seconds is None:
            raise ValueError("continuous move requires duration_seconds")
        if self.action == "goto_preset" and self.preset_token is None:
            raise ValueError("goto_preset requires preset_token")
        if self.action != "goto_preset" and self.preset_token is not None:
            raise ValueError("preset_token is valid only for goto_preset")
        if self.action != "continuous" and self.duration_seconds is not None:
            raise ValueError("duration_seconds is valid only for continuous move")
        if self.action == "stop" and any(value is not None for value in components):
            raise ValueError("stop does not accept movement components")
        return self


class OnvifPtzCommandResponse(BaseModel):
    operation_id: Annotated[str, Field(pattern=r"^ovf_[0-9a-f]{32}$")]
    stream_id: StreamId
    camera_id: str
    action: OnvifPtzAction
    outcome: Literal["success"] = "success"
    auto_stopped: bool
    started_at: datetime
    finished_at: datetime


class OnvifDiscoveryMatchResponse(BaseModel):
    endpoint_reference: Annotated[str, Field(max_length=500)] | None = None
    types: list[Annotated[str, Field(max_length=255)]] = Field(
        default_factory=list, max_length=16
    )
    scopes: list[Annotated[str, Field(max_length=500)]] = Field(
        default_factory=list, max_length=32
    )
    xaddrs: list[Annotated[str, Field(max_length=4096)]] = Field(
        default_factory=list, max_length=16
    )


class OnvifDiscoveryResponse(BaseModel):
    operation_id: Annotated[str, Field(pattern=r"^ovf_[0-9a-f]{32}$")]
    interface_address: str
    result_count: int
    matches: Annotated[list[OnvifDiscoveryMatchResponse], Field(max_length=64)]
    observed_at: datetime


class PlaybackSessionResponse(BaseModel):
    session_id: Annotated[str, Field(pattern=r"^pbs_[0-9a-f]{32}$")]
    stream_id: StreamId
    playback_url: str
    access_token: str
    token_type: Literal["Bearer"]
    expires_at: datetime
