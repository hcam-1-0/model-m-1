from __future__ import annotations

import pytest

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import (
    DeletionIntentV1,
    RetentionPolicyReferenceV1,
)
from hcam.intelligence.investigations.deletion import simulate_deletion
from hcam.intelligence.investigations.retention import evaluate_retention


def test_deletion_is_only_per_target_dry_run_with_residuals(p45_context: dict) -> None:
    target = stable_id("ref", "deletion-target")
    policy = RetentionPolicyReferenceV1(
        policy_ref=stable_id("ref", "policy"),
        policy_version="generated.v1",
        policy_digest=digest({"policy": 1}),
        classification="generated.public",
    )
    evaluation = evaluate_retention(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        policy=policy,
        holds=[],
        policy_available=True,
        evaluated_at=p45_context["now"],
    )
    intent = DeletionIntentV1(
        intent_id=stable_id("idin", "intent"),
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        target_refs=[target],
        policy_evaluation_id=evaluation.evaluation_id,
        requested_by=p45_context["actor"],
        reason=p45_context["reason"],
        requested_at=p45_context["now"],
    )
    receipts = simulate_deletion(
        intent,
        evaluation,
        residuals={target: ["deletion.backup_residual"]},
        recorded_at=p45_context["now"],
    )
    assert receipts[0].outcome == "residual_known"
    assert receipts[0].universal_deletion_proven is False
    assert receipts[0].external_action_executed is False
    clean = simulate_deletion(
        intent,
        evaluation,
        recorded_at=p45_context["now"],
    )
    assert clean[0].outcome == "simulated_deleted"
    blocked = simulate_deletion(
        intent,
        evaluation.model_copy(update={"outcome": "retain"}),
        recorded_at=p45_context["now"],
    )
    assert blocked[0].outcome == "blocked"
    with pytest.raises(ValueError, match="not bound"):
        simulate_deletion(
            intent.model_copy(update={"policy_evaluation_id": stable_id("ipev", "other")}),
            evaluation,
            recorded_at=p45_context["now"],
        )
