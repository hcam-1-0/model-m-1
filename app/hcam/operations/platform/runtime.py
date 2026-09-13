from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeneratedPlatformRuntime:
    enabled: bool = False
    environment: str = "development"
    unified_search_enabled: bool = False
    otel_export_enabled: bool = False
    external_broker_enabled: bool = False
    kubernetes_execution_enabled: bool = False

    def __post_init__(self) -> None:
        environment = self.environment.strip().lower()
        if environment not in {"development", "test", "production"}:
            raise ValueError("environment must be development, test, or production")
        prohibited = (
            self.unified_search_enabled
            or self.otel_export_enabled
            or self.external_broker_enabled
            or self.kubernetes_execution_enabled
        )
        if prohibited:
            raise ValueError("P4.6 external and execution adapters remain disabled")
        if environment == "production" and self.enabled:
            raise ValueError("the generated P4.6 runtime is forbidden in production")
        object.__setattr__(self, "environment", environment)

    def require_enabled(self) -> None:
        if not self.enabled:
            raise RuntimeError("the generated P4.6 runtime is disabled")
