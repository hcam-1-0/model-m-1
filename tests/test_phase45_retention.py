from __future__ import annotations

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import (
    HoldOverlayV1,
    RetentionPolicyReferenceV1,
)
from hcam.intelligence.investigations.retention import evaluate_retention


def _policy() -> RetentionPolicyReferenceV1:
    return RetentionPolicyReferenceV1(
        policy_ref=stable_id("ref", "retention-policy"),
        policy_version="generated.v1",
        policy_digest=digest({"policy": "generated"}),
        classification="generated.restricted",
    )


def test_retention_is_advisory_and_hold_does_not_grant_access(p45_context: dict) -> None:
    hold = HoldOverlayV1(
        hold_ref=stable_id("ref", "hold"),
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        state="simulated_active",
        scope_digest=digest({"scope": "timeline"}),
        authority_ref=stable_id("ref", "authority"),
        revision=1,
        recorded_at=p45_context["now"],
    )
    result = evaluate_retention(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        policy=_policy(),
        holds=[hold],
        policy_available=True,
        evaluated_at=p45_context["now"],
    )
    assert result.outcome == "retain"
    assert result.advisory_only is True
    assert result.legal_period_selected is False
    assert hold.grants_access is False


def test_missing_policy_produces_unknown_outcome(p45_context: dict) -> None:
    result = evaluate_retention(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        policy=_policy(),
        holds=[],
        policy_available=False,
        evaluated_at=p45_context["now"],
    )
    assert result.outcome == "unknown"
