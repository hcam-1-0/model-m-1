from __future__ import annotations

from types import MappingProxyType


METRIC_LABEL_VALUES = MappingProxyType(
    {
        "outcome": ("accepted", "denied", "failed", "unknown"),
        "lane": ("operational", "security", "audit", "evidence"),
        "worker_state": ("queued", "leased", "succeeded", "failed", "dead_letter"),
        "circuit_state": ("closed", "open", "half_open"),
        "degradation": ("normal", "constrained", "degraded", "stopped"),
        "capacity_mode": ("latency", "balanced", "throughput"),
        "capacity_scale": ("C1", "C10", "C50"),
        "freshness": ("fresh", "stale", "unknown"),
    }
)

METRIC_DEFINITIONS = MappingProxyType(
    {
        "hcam_platform_requests_total": ("counter", "request", ("outcome",)),
        "hcam_platform_jobs": ("gauge", "job", ("worker_state",)),
        "hcam_platform_job_duration_seconds": ("histogram", "second", ("outcome",)),
        "hcam_platform_circuits": ("gauge", "dependency", ("circuit_state",)),
        "hcam_platform_degradation": ("gauge", "service", ("degradation",)),
        "hcam_platform_capacity_steps": ("counter", "step", ("capacity_scale", "capacity_mode")),
    }
)

FAILURE_REGISTRY = MappingProxyType(
    {
        "authorization.denied": ("authorization", "never"),
        "policy.denied": ("policy", "never"),
        "validation.invalid": ("validation", "never"),
        "integrity.failed": ("integrity", "never"),
        "dependency.timeout": ("dependency", "bounded"),
        "dependency.unavailable": ("dependency", "bounded"),
        "lease.lost": ("concurrency", "never"),
        "capacity.incomplete": ("capacity", "never"),
        "runtime.disabled": ("configuration", "never"),
        "state.unknown": ("unknown", "never"),
    }
)

SERVICE_CLASSES = ("api", "worker", "database", "projection")
WORKER_CLASSES = ("telemetry", "recovery", "capacity", "supply_chain")
RECOVERY_TIERS = ("metadata", "control_state", "derived_state", "reference_only")
CAPACITY_MODES = ("latency", "balanced", "throughput")
CAPACITY_SCALES = {"C1": 1, "C10": 10, "C50": 50}
PLACEMENT_REASONS = (
    "placed",
    "optional_lane_bypassed",
    "mandatory_capability_missing",
    "capacity_exhausted",
    "capability_unknown",
)


def validate_registry() -> None:
    for name, (_, _, labels) in METRIC_DEFINITIONS.items():
        if len(labels) > 8 or any(label not in METRIC_LABEL_VALUES for label in labels):
            raise ValueError(f"metric registry is invalid: {name}")
        series = 1
        for label in labels:
            series *= len(METRIC_LABEL_VALUES[label])
        if series > 32_768:
            raise ValueError(f"metric cardinality is unbounded: {name}")
