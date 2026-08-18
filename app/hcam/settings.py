from __future__ import annotations

import os
from dataclasses import dataclass


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


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = "sqlite:///./var/hcam.db"
    create_schema: bool = False
    dev_auth_enabled: bool = False
    service_name: str = "H-CAM Core"
    environment: str = "development"
    max_request_body_bytes: int = 8 * 1024 * 1024
    access_log_enabled: bool = True

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
        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "database_url", self.database_url.strip())
        object.__setattr__(self, "service_name", self.service_name.strip())

    @classmethod
    def from_environment(cls) -> Settings:
        defaults = cls()
        return cls(
            database_url=os.getenv("HCAM_DATABASE_URL", defaults.database_url),
            create_schema=_environment_flag("HCAM_CREATE_SCHEMA"),
            dev_auth_enabled=_environment_flag("HCAM_DEV_AUTH_ENABLED"),
            service_name=os.getenv("HCAM_SERVICE_NAME", defaults.service_name),
            environment=os.getenv("HCAM_ENVIRONMENT", "development"),
            max_request_body_bytes=_positive_environment_integer(
                "HCAM_MAX_REQUEST_BODY_BYTES",
                defaults.max_request_body_bytes,
            ),
            access_log_enabled=_environment_flag(
                "HCAM_ACCESS_LOG_ENABLED",
                defaults.access_log_enabled,
            ),
        )
