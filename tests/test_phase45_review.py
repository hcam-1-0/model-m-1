from __future__ import annotations

import pytest

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.review import latest_review, record_review


def test_review_history_is_attributable_and_append_only(p45_context: dict) -> None:
    target = stable_id("ref", "review-target")
    first = record_review(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        target_ref=target,
        decision="request_information",
        disposition="review_pending",
        revision=1,
        supersedes_review_id=None,
        reviewer_id=p45_context["actor"],
        reason=p45_context["reason"],
        evidence_digest=digest({"evidence": 1}),
        recorded_at=p45_context["now"],
    )
    second = record_review(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        target_ref=target,
        decision="no_conclusion",
        disposition="reviewed",
        revision=2,
        supersedes_review_id=first.review_id,
        reviewer_id=p45_context["actor"],
        reason=p45_context["reason"],
        evidence_digest=digest({"evidence": 2}),
        recorded_at=p45_context["now"],
    )
    assert latest_review([second, first]) == second


def test_review_chain_rejects_mixed_targets(p45_context: dict) -> None:
    kwargs = {
        "timeline_id": p45_context["timeline_id"],
        "department": p45_context["department"],
        "decision": "support",
        "disposition": "reviewed",
        "revision": 1,
        "supersedes_review_id": None,
        "reviewer_id": p45_context["actor"],
        "reason": p45_context["reason"],
        "evidence_digest": digest({"evidence": 1}),
        "recorded_at": p45_context["now"],
    }
    first = record_review(target_ref=stable_id("ref", "one"), **kwargs)
    second = record_review(target_ref=stable_id("ref", "two"), **kwargs)
    with pytest.raises(ValueError, match="share a target"):
        latest_review([first, second])
    with pytest.raises(ValueError, match="at least one"):
        latest_review([])
    broken = first.model_copy(update={"revision": 2, "supersedes_review_id": first.review_id})
    with pytest.raises(ValueError, match="contiguous"):
        latest_review([broken])
