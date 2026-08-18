from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


StreamId = Annotated[str, Field(pattern=r"^str_[0-9a-f]{32}$")]
StreamName = Annotated[str, Field(min_length=1, max_length=120)]
AdapterKind = Literal["rtsp", "hls", "http", "onvif", "synthetic", "legacy"]
StreamProtocol = Literal["rtsp", "rtsps", "hls", "http", "https"]
Transport = Literal["tcp", "udp", "auto"]
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
    transport: Transport = "tcp"
    is_primary: bool = False
    enabled: bool = True

    @model_validator(mode="after")
    def validate_secret_reference(self) -> StreamEndpointCreate:
        if self.secret_ref is not None and _SECRET_REF.fullmatch(self.secret_ref) is None:
            raise ValueError("secret_ref must be an opaque path-like identifier")
        if self.protocol not in {"rtsp", "rtsps"} and self.transport != "tcp":
            raise ValueError("non-RTSP endpoints require TCP transport")
        return self


class StreamEndpointPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StreamName | None = None
    locator: Annotated[str, Field(min_length=1, max_length=4096)] | None = None
    secret_ref: Annotated[str, Field(max_length=255)] | None = None
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
        return self


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
