from __future__ import annotations

from dataclasses import dataclass

from hcam.intelligence.alerts.adapters import GeneratedWorkflowExecutor


@dataclass(frozen=True, slots=True)
class GeneratedAlertRuntime:
    enabled: bool = False
    environment: str = "development"

    def __post_init__(self) -> None:
        if self.environment == "production" and self.enabled:
            raise ValueError("the generated P4.3 runtime is forbidden in production")

    def executor(self) -> GeneratedWorkflowExecutor:
        if not self.enabled:
            raise RuntimeError("the generated P4.3 runtime is disabled")
        return GeneratedWorkflowExecutor()
