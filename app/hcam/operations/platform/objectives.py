from __future__ import annotations

from hcam.operations.platform.contracts import BurnWindowV1, HealthProjectionV1, ServiceObjectiveV1


def compliance_ratio(window: BurnWindowV1) -> float | None:
    if window.valid == 0:
        return None
    return window.good / window.valid


def data_quality(objective: ServiceObjectiveV1) -> str:
    if all(window.valid == 0 and window.unknown > 0 for window in objective.windows):
        return "unknown"
    if any(window.unknown > 0 or window.valid == 0 for window in objective.windows):
        return "partial"
    return "complete"


def health_projection(objective: ServiceObjectiveV1) -> HealthProjectionV1:
    quality = data_quality(objective)
    if objective.target_state == "unset" or quality == "unknown":
        state = "unknown"
        reasons = ["objective.target_unset" if objective.target_state == "unset" else "objective.data_unknown"]
    else:
        ratio = compliance_ratio(objective.windows[0])
        if ratio is None:
            state, reasons = "unknown", ["objective.data_unknown"]
        elif ratio >= (objective.target_ratio or 1.0):
            state, reasons = "healthy", ["objective.within_target"]
        elif ratio > 0:
            state, reasons = "degraded", ["objective.below_target"]
        else:
            state, reasons = "stopped", ["objective.no_good_events"]
    return HealthProjectionV1(service_class=objective.service_class, state=state, reason_codes=reasons)
