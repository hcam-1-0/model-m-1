from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from hcam.intelligence.alerts.canonical import digest
from hcam.intelligence.alerts.contracts import AlertBudgetPolicyV1, ProposedAlertCommandV1


@dataclass(frozen=True, slots=True)
class BudgetObservation:
    scope: str
    scope_key: str
    window_started_at: datetime
    observed_count: int


@dataclass(frozen=True, slots=True)
class BudgetDecision:
    admitted: bool
    reason_code: str
    collapse_key: str | None
    represented_alerts: int
    suppressed_alerts: int


def evaluate_budget(
    command: ProposedAlertCommandV1,
    policy: AlertBudgetPolicyV1,
    observations: list[BudgetObservation],
) -> BudgetDecision:
    if command.department != policy.department:
        raise ValueError("budget policy department does not match")
    counts = {(item.scope, item.scope_key): item.observed_count for item in observations}
    exceeded = [
        item
        for item in policy.limits
        if counts.get((item.scope, item.scope_key), 0) >= item.limit
    ]
    if not exceeded:
        return BudgetDecision(True, "within_budget", None, 1, 0)
    collapse_key = digest(
        {
            "contract": "hcam.p4-3.loss-accounted-collapse.v1",
            "department": command.department,
            "incident_key": command.incident_key,
            "policy_digest": policy.policy_digest,
            "exceeded": sorted(f"{item.scope}:{item.scope_key}" for item in exceeded),
        }
    )
    represented = 1 + max(
        counts.get((item.scope, item.scope_key), 0) - item.limit + 1
        for item in exceeded
    )
    return BudgetDecision(False, "collapsed_budget_exceeded", collapse_key, represented, represented - 1)
