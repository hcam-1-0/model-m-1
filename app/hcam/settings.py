from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


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
        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "database_url", self.database_url.strip())
        object.__setattr__(self, "service_name", self.service_name.strip())

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
            database_url=_environment_value_or_file(
                "HCAM_DATABASE_URL",
                "HCAM_DATABASE_URL_FILE",
                defaults.database_url,
            ),
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
        )
