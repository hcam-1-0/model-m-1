from __future__ import annotations

from datetime import datetime

from hcam.intelligence.investigations.canonical import stable_id
from hcam.intelligence.investigations.contracts import (
    HoldOverlayV1,
    RetentionEvaluationV1,
    RetentionPolicyReferenceV1,
)


def evaluate_retention(
    *,
    timeline_id: str,
    department: str,
    policy: RetentionPolicyReferenceV1,
    holds: list[HoldOverlayV1],
    policy_available: bool,
    evaluated_at: datetime,
) -> RetentionEvaluationV1:
    if any(hold.timeline_id != timeline_id or hold.department != department for hold in holds):
        raise ValueError("hold scope does not match the timeline")
    active = [hold for hold in holds if hold.state == "simulated_active"]
    if active:
        outcome = "retain"
        reasons = ["retention.generated_hold"]
    elif not policy_available:
        outcome = "unknown"
        reasons = ["retention.policy_unavailable"]
    else:
        outcome = "eligible_for_simulation"
        reasons = ["retention.generated_policy_allows_simulation"]
    return RetentionEvaluationV1(
        evaluation_id=stable_id(
            "ipev", timeline_id, policy.policy_ref, evaluated_at.isoformat()
        ),
        timeline_id=timeline_id,
        department=department,
        policy=policy,
        hold_refs=[hold.hold_ref for hold in active],
        outcome=outcome,
        reason_codes=reasons,
        evaluated_at=evaluated_at,
    )
