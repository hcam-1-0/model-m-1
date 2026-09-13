from __future__ import annotations

from dataclasses import dataclass

from hcam.operations.platform.contracts import MetricDefinitionV1
from hcam.operations.platform.registry import METRIC_DEFINITIONS, METRIC_LABEL_VALUES, validate_registry


def metric_contracts() -> tuple[MetricDefinitionV1, ...]:
    validate_registry()
    return tuple(
        MetricDefinitionV1(
            name=name,
            kind=kind,
            unit=unit,
            labels=labels,
            description=f"Generated H-CAM platform metric for {name}.",
        )
        for name, (kind, unit, labels) in sorted(METRIC_DEFINITIONS.items())
    )


def validate_labels(metric_name: str, labels: dict[str, str]) -> None:
    definition = METRIC_DEFINITIONS.get(metric_name)
    if definition is None:
        raise ValueError("metric is not registered")
    expected = set(definition[2])
    if set(labels) != expected:
        raise ValueError("metric labels do not match the registry")
    if any(value not in METRIC_LABEL_VALUES[label] for label, value in labels.items()):
        raise ValueError("metric label value is not allowlisted")


@dataclass(frozen=True, slots=True)
class OpenTelemetryProjectionAdapter:
    enabled: bool = False
    endpoint_configured: bool = False

    def __post_init__(self) -> None:
        if self.enabled or self.endpoint_configured:
            raise ValueError("OpenTelemetry export remains disabled in P4.6")

    def project(self, name: str, labels: dict[str, str], value: float) -> dict[str, object]:
        validate_labels(name, labels)
        return {"name": name, "labels": dict(sorted(labels.items())), "value": value, "exported": False}
