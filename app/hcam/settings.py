from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from hcam.streams.network import parse_allowed_hosts


_MAX_SECRET_FILE_BYTES = 16 * 1024
_BEARER_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._~+/=-]{32,256}$")


def _environment_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _positive_environment_integer(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if parsed < 1:
        raise ValueError(f"{name} must be a positive integer")
    return parsed


def _positive_environment_number(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive number") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be a positive number")
    return parsed


def _read_secret_file(name: str) -> str | None:
    configured_path = os.getenv(name)
    if configured_path is None:
        return None
    if not configured_path.strip():
        raise ValueError(f"{name} must identify a readable secret file")
    path = Path(configured_path).expanduser()
    try:
        if not path.is_file() or path.stat().st_size > _MAX_SECRET_FILE_BYTES:
            raise ValueError(f"{name} must identify a small regular file")
        payload = path.read_bytes()
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError(f"{name} could not be read") from exc
    try:
        value = payload.decode("utf-8").rstrip("\r\n")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name} must contain UTF-8 text") from exc
    if not value or "\n" in value or "\r" in value or "\x00" in value:
        raise ValueError(f"{name} must contain exactly one non-empty text value")
    return value


def _read_pem_secret_file(name: str) -> str | None:
    configured_path = os.getenv(name)
    if configured_path is None:
        return None
    if not configured_path.strip():
        raise ValueError(f"{name} must identify a readable PEM file")
    path = Path(configured_path).expanduser()
    try:
        if not path.is_file() or path.stat().st_size > 64 * 1024:
            raise ValueError(f"{name} must identify a small regular file")
        value = path.read_text(encoding="ascii")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"{name} could not be read as ASCII PEM") from exc
    if "-----BEGIN" not in value or "PRIVATE KEY-----" not in value:
        raise ValueError(f"{name} must contain a private key PEM")
    return value


def _environment_value_or_file(
    value_name: str,
    file_name: str,
    default: str,
) -> str:
    direct_value = os.getenv(value_name)
    file_value = _read_secret_file(file_name)
    if direct_value is not None and file_value is not None:
        raise ValueError(f"{value_name} and {file_name} are mutually exclusive")
    if file_value is not None:
        return file_value
    if direct_value is not None:
        return direct_value
    return default


def database_url_from_environment(default: str) -> str:
    return _environment_value_or_file(
        "HCAM_DATABASE_URL",
        "HCAM_DATABASE_URL_FILE",
        default,
    )


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = field(default="sqlite:///./var/hcam.db", repr=False)
    create_schema: bool = False
    dev_auth_enabled: bool = False
    service_name: str = "H-CAM Core"
    environment: str = "development"
    max_request_body_bytes: int = 8 * 1024 * 1024
    access_log_enabled: bool = True
    metrics_enabled: bool = False
    metrics_token: str | None = field(default=None, repr=False)
    ffprobe_executable: str = "ffprobe"
    stream_probe_timeout_seconds: float = 8.0
    stream_probe_allowed_hosts: frozenset[str] = frozenset()
    stream_probe_token: str | None = field(default=None, repr=False)
    playback_signing_key: str | None = field(default=None, repr=False)
    playback_public_base_url: str = "http://127.0.0.1:8888"
    playback_token_ttl_seconds: int = 60
    playback_issuer: str = "hcam-core"
    playback_audience: str = "mediamtx"

    def __post_init__(self) -> None:
        environment = self.environment.strip().lower()
        if environment not in {"development", "test", "production"}:
            raise ValueError(
                "HCAM_ENVIRONMENT must be development, test, or production"
            )
        if not self.database_url.strip():
            raise ValueError("HCAM_DATABASE_URL must not be empty")
        if not self.service_name.strip():
            raise ValueError("HCAM_SERVICE_NAME must not be empty")
        if self.max_request_body_bytes < 1:
            raise ValueError("HCAM_MAX_REQUEST_BODY_BYTES must be a positive integer")
        if self.metrics_enabled and self.metrics_token is None:
            raise ValueError(
                "HCAM_METRICS_TOKEN_FILE is required when metrics are enabled"
            )
        if self.metrics_token is not None and _BEARER_TOKEN_PATTERN.fullmatch(
            self.metrics_token
        ) is None:
            raise ValueError(
                "metrics token must be 32 to 256 bearer-safe characters"
            )
        if not self.ffprobe_executable.strip():
            raise ValueError("HCAM_FFPROBE_EXECUTABLE must not be empty")
        if self.stream_probe_timeout_seconds <= 0:
            raise ValueError("HCAM_STREAM_PROBE_TIMEOUT_SECONDS must be positive")
        playback_url = urlsplit(self.playback_public_base_url)
        if (
            playback_url.scheme not in {"http", "https"}
            or playback_url.hostname is None
            or playback_url.query
            or playback_url.fragment
        ):
            raise ValueError("HCAM_PLAYBACK_PUBLIC_BASE_URL must be an HTTP(S) base URL")
        if not 10 <= self.playback_token_ttl_seconds <= 300:
            raise ValueError("HCAM_PLAYBACK_TOKEN_TTL_SECONDS must be between 10 and 300")
        if not self.playback_issuer.strip() or not self.playback_audience.strip():
            raise ValueError("playback issuer and audience must not be empty")
        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "database_url", self.database_url.strip())
        object.__setattr__(self, "service_name", self.service_name.strip())
        object.__setattr__(self, "ffprobe_executable", self.ffprobe_executable.strip())
        object.__setattr__(
            self, "playback_public_base_url", self.playback_public_base_url.rstrip("/")
        )
        object.__setattr__(self, "playback_issuer", self.playback_issuer.strip())
        object.__setattr__(self, "playback_audience", self.playback_audience.strip())

    @classmethod
    def from_environment(cls) -> Settings:
        defaults = cls()
        environment = os.getenv("HCAM_ENVIRONMENT", defaults.environment)
        if (
            environment.strip().lower() == "production"
            and os.getenv("HCAM_DATABASE_URL") is None
            and os.getenv("HCAM_DATABASE_URL_FILE") is None
        ):
            raise ValueError(
                "HCAM_DATABASE_URL or HCAM_DATABASE_URL_FILE is required in production"
            )
        return cls(
            database_url=database_url_from_environment(defaults.database_url),
            create_schema=_environment_flag("HCAM_CREATE_SCHEMA"),
            dev_auth_enabled=_environment_flag("HCAM_DEV_AUTH_ENABLED"),
            service_name=os.getenv("HCAM_SERVICE_NAME", defaults.service_name),
            environment=environment,
            max_request_body_bytes=_positive_environment_integer(
                "HCAM_MAX_REQUEST_BODY_BYTES",
                defaults.max_request_body_bytes,
            ),
            access_log_enabled=_environment_flag(
                "HCAM_ACCESS_LOG_ENABLED",
                defaults.access_log_enabled,
            ),
            metrics_enabled=_environment_flag(
                "HCAM_METRICS_ENABLED",
                defaults.metrics_enabled,
            ),
            metrics_token=_read_secret_file("HCAM_METRICS_TOKEN_FILE"),
            ffprobe_executable=os.getenv(
                "HCAM_FFPROBE_EXECUTABLE", defaults.ffprobe_executable
            ),
            stream_probe_timeout_seconds=_positive_environment_number(
                "HCAM_STREAM_PROBE_TIMEOUT_SECONDS",
                defaults.stream_probe_timeout_seconds,
            ),
            stream_probe_allowed_hosts=parse_allowed_hosts(
                os.getenv("HCAM_STREAM_PROBE_ALLOWED_HOSTS")
            ),
            stream_probe_token=_read_secret_file("HCAM_STREAM_PROBE_TOKEN_FILE"),
            playback_signing_key=_read_pem_secret_file(
                "HCAM_PLAYBACK_SIGNING_KEY_FILE"
            ),
            playback_public_base_url=os.getenv(
                "HCAM_PLAYBACK_PUBLIC_BASE_URL", defaults.playback_public_base_url
            ),
            playback_token_ttl_seconds=_positive_environment_integer(
                "HCAM_PLAYBACK_TOKEN_TTL_SECONDS",
                defaults.playback_token_ttl_seconds,
            ),
            playback_issuer=os.getenv(
                "HCAM_PLAYBACK_ISSUER", defaults.playback_issuer
            ),
            playback_audience=os.getenv(
                "HCAM_PLAYBACK_AUDIENCE", defaults.playback_audience
            ),
        )
