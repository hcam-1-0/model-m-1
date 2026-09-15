from __future__ import annotations

from datetime import datetime

from hcam.intelligence.investigations.canonical import stable_id
from hcam.intelligence.investigations.contracts import (
    DeletionIntentV1,
    DeletionReceiptV1,
    RetentionEvaluationV1,
)


def simulate_deletion(
    intent: DeletionIntentV1,
    evaluation: RetentionEvaluationV1,
    *,
    residuals: dict[str, list[str]] | None = None,
    recorded_at: datetime,
) -> list[DeletionReceiptV1]:
    if intent.policy_evaluation_id != evaluation.evaluation_id:
        raise ValueError("deletion intent is not bound to the retention evaluation")
    if intent.timeline_id != evaluation.timeline_id or intent.department != evaluation.department:
        raise ValueError("deletion and retention scope differ")
    residual_map = residuals or {}
    receipts: list[DeletionReceiptV1] = []
    allowed = evaluation.outcome == "eligible_for_simulation"
    for target_ref in intent.target_refs:
        target_residuals = residual_map.get(target_ref, [])
        if not allowed:
            outcome = "blocked"
            target_residuals = ["deletion.retention_blocked"]
        elif target_residuals:
            outcome = "residual_known"
        else:
            outcome = "simulated_deleted"
        receipts.append(
            DeletionReceiptV1(
                receipt_id=stable_id("idel", intent.intent_id, target_ref),
                intent_id=intent.intent_id,
                timeline_id=intent.timeline_id,
                department=intent.department,
                target_ref=target_ref,
                outcome=outcome,
                residual_states=target_residuals,
                recorded_at=recorded_at,
            )
        )
    return receipts
