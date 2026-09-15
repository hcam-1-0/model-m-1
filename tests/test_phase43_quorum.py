from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hcam.intelligence.alerts.canonical import stable_id
from hcam.intelligence.alerts.contracts import AlertReviewDecisionV1, ReviewQuorumPolicyV1
from hcam.intelligence.alerts.review import ReviewDenied, ReviewQuorum
from tests.test_phase43_contracts import DIGEST


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def policy(required: int = 2, *, expires=None) -> ReviewQuorumPolicyV1:
    return ReviewQuorumPolicyV1(
        policy_id="generated.quorum",
        policy_version=1,
        department="generated-lab",
        workflow_class="generated_high_impact" if required > 1 else "ordinary",
        required_distinct_reviewers=required,
        permitted_roles=["intelligence.reviewer"],
        evidence_digest=DIGEST,
        effective_at=NOW,
        expires_at=expires,
    )


def vote(index: int, decision: str = "approve", **changes) -> AlertReviewDecisionV1:
    values = {
        "decision_id": stable_id("ardc", index),
        "alert_id": "alt_" + "1" * 32,
        "department": "generated-lab",
        "policy_id": "generated.quorum",
        "policy_version": 1,
        "reviewer_id": f"reviewer-{index}",
        "reviewer_role": "intelligence.reviewer",
        "decision": decision,
        "evidence_digest": DIGEST,
        "reason": "Generated quorum review",
        "recorded_at": NOW,
    }
    values.update(changes)
    return AlertReviewDecisionV1(**values)


def test_distinct_reviewer_quorum_and_disagreement_are_explicit() -> None:
    quorum = ReviewQuorum(policy())
    quorum.add(vote(1), now=NOW)
    assert quorum.outcome == "pending"
    quorum.add(vote(2), now=NOW)
    assert quorum.outcome == "approved"
    split = ReviewQuorum(policy())
    split.add(vote(1), now=NOW)
    split.add(vote(2, "deny"), now=NOW)
    assert split.outcome == "disagreement"
    denied = ReviewQuorum(policy())
    denied.add(vote(1, "deny"), now=NOW)
    denied.add(vote(2, "deny"), now=NOW)
    assert denied.outcome == "rejected"


def test_duplicate_self_stale_role_scope_and_expired_votes_fail_closed() -> None:
    quorum = ReviewQuorum(policy(), subject_actor_id="reviewer-9")
    quorum.add(vote(1), now=NOW)
    with pytest.raises(ReviewDenied):
        quorum.add(vote(2, reviewer_id="reviewer-1"), now=NOW)
    for changes in (
        {"reviewer_id": "reviewer-9"},
        {"department": "other-department"},
        {"evidence_digest": "sha256:" + "f" * 64},
        {"reviewer_role": "camera.viewer"},
    ):
        with pytest.raises(ReviewDenied):
            ReviewQuorum(policy(), subject_actor_id="reviewer-9").add(vote(9, **changes), now=NOW)
    with pytest.raises(ReviewDenied):
        ReviewQuorum(policy(expires=NOW + timedelta(seconds=1))).add(vote(3), now=NOW + timedelta(seconds=1))
    duplicate_id = ReviewQuorum(policy())
    duplicate_id.add(vote(1), now=NOW)
    with pytest.raises(ReviewDenied, match="already exists"):
        duplicate_id.add(
            vote(2).model_copy(update={"decision_id": vote(1).decision_id}),
            now=NOW,
        )
