from __future__ import annotations

from hcam.operations.platform.contracts import DegradationDecisionV1, ErrorBudgetStateV1, HealthProjectionV1


def decide_degradation(
    budget: ErrorBudgetStateV1,
    health: HealthProjectionV1,
    *,
    optional_lanes: list[str],
) -> DegradationDecisionV1:
    if health.state == "stopped":
        state, reasons = "stopped", ["degradation.service_stopped"]
    elif health.state == "unknown" or budget.status == "unknown":
        state, reasons = "constrained", ["degradation.unknown_state"]
    elif health.state == "degraded" or budget.status == "exhausted":
        state, reasons = "degraded", ["degradation.error_budget_exhausted"]
    elif budget.status == "at_risk":
        state, reasons = "constrained", ["degradation.error_budget_at_risk"]
    else:
        state, reasons = "normal", ["degradation.within_budget"]
    bypassed = sorted(set(optional_lanes)) if state in {"constrained", "degraded", "stopped"} else []
    return DegradationDecisionV1(
        state=state,
        optional_lanes_bypassed=bypassed,
        reasons=reasons,
    )
