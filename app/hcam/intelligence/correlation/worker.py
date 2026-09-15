from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from hcam.intelligence.correlation.bounds import CorrelationBounds
from hcam.intelligence.correlation.contracts import (
    CorrelationBatchResultV1,
    CorrelationIngressEventV1,
    CorrelationProfileV1,
    LaneResultV1,
)
from hcam.intelligence.correlation.metrics import CorrelationMetrics
from hcam.intelligence.correlation.runtime import run_generated_batch


class CorrelationWorkerDisabledError(RuntimeError):
    """Raised when the explicitly disabled P4.1 worker is invoked."""


@dataclass(slots=True)
class GeneratedCorrelationWorker:
    enabled: bool = False
    environment: str = "development"
    bounds: CorrelationBounds = field(default_factory=CorrelationBounds)
    metrics: CorrelationMetrics = field(default_factory=CorrelationMetrics)

    def __post_init__(self) -> None:
        if self.enabled and self.environment.strip().lower() in {"prod", "production"}:
            raise CorrelationWorkerDisabledError(
                "P4.1 generated correlation is forbidden in production"
            )

    def process(
        self,
        events: Sequence[CorrelationIngressEventV1],
        profile: CorrelationProfileV1,
        *,
        optional_results: Mapping[str, Sequence[LaneResultV1]] | None = None,
    ) -> CorrelationBatchResultV1:
        if not self.enabled:
            raise CorrelationWorkerDisabledError(
                "P4.1 generated correlation is disabled by default"
            )
        return run_generated_batch(
            events,
            profile,
            optional_results=optional_results,
            bounds=self.bounds,
            metrics=self.metrics,
        )
