from __future__ import annotations

import os
from dataclasses import dataclass


def _environment_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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

    @classmethod
    def from_environment(cls) -> Settings:
        defaults = cls()
        return cls(
            database_url=os.getenv("HCAM_DATABASE_URL", defaults.database_url),
            create_schema=_environment_flag("HCAM_CREATE_SCHEMA"),
            dev_auth_enabled=_environment_flag("HCAM_DEV_AUTH_ENABLED"),
            environment=os.getenv("HCAM_ENVIRONMENT", "development"),
            max_request_body_bytes=_positive_environment_integer(
                "HCAM_MAX_REQUEST_BODY_BYTES",
                defaults.max_request_body_bytes,
            ),
        )
