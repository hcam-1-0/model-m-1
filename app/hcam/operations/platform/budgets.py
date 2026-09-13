from __future__ import annotations

from hcam.operations.platform.contracts import ErrorBudgetStateV1, ServiceObjectiveV1
from hcam.operations.platform.objectives import compliance_ratio, data_quality


def calculate_error_budget(objective: ServiceObjectiveV1) -> ErrorBudgetStateV1:
    quality = data_quality(objective)
    if objective.target_state == "unset" or objective.target_ratio is None:
        return ErrorBudgetStateV1(
            objective_id=objective.objective_id,
            target_state=objective.target_state,
            compliance_ratio=None,
            remaining_ratio=None,
            burn_rates=[None for _ in objective.windows],
            data_quality=quality,
            status="unknown",
        )
    ratios = [compliance_ratio(window) for window in objective.windows]
    primary = ratios[0]
    allowed_error = 1.0 - objective.target_ratio
    if primary is None or allowed_error <= 0:
        remaining = 0.0 if primary is not None and primary < 1 else None
        burns = [0.0 if ratio is not None and ratio >= 1 else None for ratio in ratios]
    else:
        consumed = max(0.0, 1.0 - primary)
        remaining = max(0.0, min(1.0, 1.0 - consumed / allowed_error))
        burns = [None if ratio is None else max(0.0, (1.0 - ratio) / allowed_error) for ratio in ratios]
    if remaining is None:
        status = "unknown"
    elif remaining == 0:
        status = "exhausted"
    elif remaining < 0.25 or any(rate is not None and rate > 2 for rate in burns):
        status = "at_risk"
    else:
        status = "within_budget"
    return ErrorBudgetStateV1(
        objective_id=objective.objective_id,
        target_state=objective.target_state,
        compliance_ratio=primary,
        remaining_ratio=remaining,
        burn_rates=burns,
        data_quality=quality,
        status=status,
    )
