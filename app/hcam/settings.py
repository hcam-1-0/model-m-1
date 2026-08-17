from __future__ import annotations

import os
from dataclasses import dataclass


def _environment_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = "sqlite:///./var/hcam.db"
    create_schema: bool = False
    service_name: str = "H-CAM Core"
    environment: str = "development"

    @classmethod
    def from_environment(cls) -> "Settings":
        defaults = cls()
        return cls(
            database_url=os.getenv("HCAM_DATABASE_URL", defaults.database_url),
            create_schema=_environment_flag("HCAM_CREATE_SCHEMA"),
            environment=os.getenv("HCAM_ENVIRONMENT", "development"),
        )
