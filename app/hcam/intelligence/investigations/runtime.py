from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeneratedInvestigationRuntime:
    enabled: bool = False
    environment: str = "development"

    def __post_init__(self) -> None:
        environment = self.environment.strip().lower()
        if environment not in {"development", "test", "production"}:
            raise ValueError("environment must be development, test, or production")
        if environment == "production" and self.enabled:
            raise ValueError("the generated P4.5 runtime is forbidden in production")
        object.__setattr__(self, "environment", environment)

    def require_enabled(self) -> None:
        if not self.enabled:
            raise RuntimeError("the generated P4.5 runtime is disabled")
