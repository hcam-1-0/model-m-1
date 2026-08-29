from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator


_MAX_CONFIG_FILE_BYTES = 256 * 1024
_CAMERA_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
_HOST_PATTERN = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
)
_STREAM_SCHEMES = frozenset({"rtsp", "rtsps", "http", "https"})


class AdapterConfigurationError(ValueError):
    """Raised when a local adapter configuration is unsafe or unusable."""


def _host_from_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in _STREAM_SCHEMES or not parsed.hostname:
        raise ValueError("stream URL must use rtsp, rtsps, http, or https with a host")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("stream URL must not include embedded credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("stream URL must not include a query string or fragment")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError("stream URL port must be between 1 and 65535")
    return parsed.hostname.lower().rstrip(".")


def redact_stream_url(value: str) -> str:
    """Return a display-safe stream URL that never includes a credential or path."""
    parsed = urlsplit(value)
    host = parsed.hostname or "invalid-host"
    port = f":{parsed.port}" if parsed.port is not None else ""
    scheme = parsed.scheme or "unknown"
    return f"{scheme}://{host}{port}/…"


class StreamConfig(BaseModel):
    """One explicitly authorized camera source and its local recording identity."""

    camera_id: str = Field(description="Stable HCAM camera_id, also used as folder name")
    rtsp_url: str = Field(description="RTSP or HLS URL; credentials belong only in ignored local config")
    enabled: bool = True
    transport: Literal["tcp", "udp"] = "tcp"
    location_label: str | None = None
    department: str | None = None

    @field_validator("camera_id")
    @classmethod
    def camera_id_is_safe_path_component(cls, value: str) -> str:
        if _CAMERA_ID_PATTERN.fullmatch(value) is None:
            raise ValueError(
                "camera_id must contain only letters, numbers, dots, underscores, or hyphens"
            )
        return value

    @field_validator("rtsp_url")
    @classmethod
    def stream_url_is_supported(cls, value: str) -> str:
        _host_from_url(value)
        return value

    @property
    def host(self) -> str:
        return _host_from_url(self.rtsp_url)


class CatalogConfig(BaseModel):
    """Read-only catalog source. It never performs discovery beyond this exact URL."""

    url: str = Field(description="Exact HTTPS catalog URL that has been authorized for this adapter")
    enabled: bool = False
    source_kind: Literal["hls", "rtsp", "whep"] = "hls"
    max_cameras: int = Field(default=3, ge=1, le=32)
    camera_id_prefix: str = Field(default="catalog_", min_length=1, max_length=80)
    timeout_seconds: float = Field(default=10.0, ge=1.0, le=30.0)
    viewer_enabled: bool = False
    viewer_session_ttl_seconds: int = Field(default=900, ge=60, le=3600)

    @field_validator("url")
    @classmethod
    def catalog_must_use_https(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme.lower() != "https" or not parsed.hostname:
            raise ValueError("catalog URL must be an absolute HTTPS URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("catalog URL must not include embedded credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("catalog URL must not include a query string or fragment")
        return value

    @field_validator("camera_id_prefix")
    @classmethod
    def catalog_prefix_is_safe(cls, value: str) -> str:
        if _CAMERA_ID_PATTERN.fullmatch(f"{value}camera") is None:
            raise ValueError("camera_id_prefix contains unsupported characters")
        return value

    @property
    def host(self) -> str:
        return _host_from_url(self.url)


class AdapterConfig(BaseModel):
    """Top-level local Cam-Adapter configuration.

    Streams are deliberately opt-in: an adapter can start only when each source
    host has been allow-listed in the same local configuration file.
    """

    drive_base: Path = Field(default=Path("/content/drive/MyDrive/cctv-h/camera_recordings"))
    local_fallback_base: Path = Field(default=Path("./camera_recordings"))

    segment_time_seconds: int = Field(default=300, ge=30, le=3600)
    segment_format: Literal["mp4"] = "mp4"

    sample_interval_seconds: float = Field(default=2.0, ge=0.5, le=60)
    yolo_model: str = Field(default="yolov8n.pt")
    yolo_conf: float = Field(default=0.35, ge=0.1, le=0.95)
    yolo_classes: list[int] | None = None
    yolo_device: str = "0"

    max_reconnect_attempts: int = Field(default=0, ge=0)
    backoff_base_seconds: float = Field(default=1.0, ge=0.2)
    backoff_max_seconds: float = Field(default=60.0, ge=5)
    backoff_jitter: float = Field(default=0.4, ge=0, le=1)
    telemetry_interval_seconds: float = Field(default=30.0, ge=5, le=300)

    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    rtsp_transport: Literal["tcp", "udp"] = "tcp"
    extra_ffmpeg_input_args: list[str] = Field(default_factory=list)
    extra_ffmpeg_output_args: list[str] = Field(default_factory=list)

    allowed_source_hosts: list[str] = Field(default_factory=list)
    streams: list[StreamConfig] = Field(default_factory=list)
    catalog: CatalogConfig | None = None

    @field_validator("allowed_source_hosts")
    @classmethod
    def allowed_hosts_are_exact(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            host = value.strip().lower().rstrip(".")
            if not host or "*" in host or ":" in host or _HOST_PATTERN.fullmatch(host) is None:
                raise ValueError("allowed_source_hosts must contain exact host names only")
            if host not in normalized:
                normalized.append(host)
        return normalized

    @model_validator(mode="after")
    def catalog_host_is_allowlisted(self) -> "AdapterConfig":
        if self.catalog is not None and self.allowed_source_hosts:
            if self.catalog.host not in self.allowed_source_hosts:
                raise ValueError("catalog host must appear in allowed_source_hosts")
        return self

    @classmethod
    def from_file(cls, value: str | Path) -> "AdapterConfig":
        path = Path(value).expanduser().resolve()
        try:
            if not path.is_file() or path.stat().st_size > _MAX_CONFIG_FILE_BYTES:
                raise AdapterConfigurationError("adapter config must be a small regular file")
            payload = json.loads(path.read_text(encoding="utf-8"))
        except AdapterConfigurationError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AdapterConfigurationError("adapter config could not be read as JSON") from exc
        if not isinstance(payload, dict):
            raise AdapterConfigurationError("adapter config must contain a JSON object")
        try:
            parsed = cls.model_validate(payload)
        except ValueError as exc:
            raise AdapterConfigurationError("adapter config is invalid") from exc
        return parsed.with_paths_relative_to(path.parent)

    def with_paths_relative_to(self, directory: Path) -> "AdapterConfig":
        def resolve(path: Path) -> Path:
            return path.expanduser().resolve() if path.is_absolute() else (directory / path).resolve()

        def resolve_executable(value: str) -> str:
            candidate = Path(value).expanduser()
            if candidate.is_absolute() or "/" in value or "\\" in value:
                return str(resolve(candidate))
            return value

        return self.model_copy(
            update={
                "drive_base": resolve(self.drive_base),
                "local_fallback_base": resolve(self.local_fallback_base),
                "ffmpeg_bin": resolve_executable(self.ffmpeg_bin),
                "ffprobe_bin": resolve_executable(self.ffprobe_bin),
            }
        )

    def assert_activatable(self, streams: list[StreamConfig] | None = None) -> None:
        active_streams = [stream for stream in (streams or self.streams) if stream.enabled]
        if not active_streams:
            raise AdapterConfigurationError("adapter start requires at least one enabled authorized stream")
        if not self.allowed_source_hosts:
            raise AdapterConfigurationError(
                "adapter start requires explicit allowed_source_hosts"
            )
        disallowed = sorted({stream.host for stream in active_streams} - set(self.allowed_source_hosts))
        if disallowed:
            raise AdapterConfigurationError(
                f"configured stream hosts are not allow-listed: {', '.join(disallowed)}"
            )

    def assert_viewer_activatable(self) -> None:
        """Require an explicit, low-latency live-viewer configuration.

        The live viewer never starts the recorder and only supports WHEP.  This
        keeps browser playback on the upstream's live WebRTC path rather than
        treating a downloadable/progressive asset as a live feed.
        """
        if self.catalog is None or not self.catalog.viewer_enabled:
            raise AdapterConfigurationError("live viewer is not enabled in the local adapter config")
        if self.catalog.source_kind != "whep":
            raise AdapterConfigurationError("live viewer requires catalog source_kind 'whep'")
        if not self.allowed_source_hosts or self.catalog.host not in self.allowed_source_hosts:
            raise AdapterConfigurationError("live viewer catalog host is not allow-listed")

    def drive_camera_dir(self, camera_id: str) -> Path:
        StreamConfig(camera_id=camera_id, rtsp_url="https://validation.invalid/stream")
        return self.effective_base() / camera_id

    def effective_base(self) -> Path:
        if self.drive_base.parent.exists() or self.drive_base.exists():
            return self.drive_base
        return self.local_fallback_base
