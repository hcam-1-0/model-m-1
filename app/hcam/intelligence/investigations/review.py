from __future__ import annotations

from datetime import datetime

from hcam.intelligence.investigations.canonical import stable_id
from hcam.intelligence.investigations.contracts import ReviewDecisionV1


def record_review(
    *,
    timeline_id: str,
    department: str,
    target_ref: str,
    decision: str,
    disposition: str,
    revision: int,
    supersedes_review_id: str | None,
    reviewer_id: str,
    reason: str,
    evidence_digest: str,
    recorded_at: datetime,
) -> ReviewDecisionV1:
    return ReviewDecisionV1(
        review_id=stable_id("irev", timeline_id, target_ref, revision, evidence_digest),
        timeline_id=timeline_id,
        department=department,
        target_ref=target_ref,
        decision=decision,
        disposition=disposition,
        revision=revision,
        supersedes_review_id=supersedes_review_id,
        reviewer_id=reviewer_id,
        reason=reason,
        evidence_digest=evidence_digest,
        recorded_at=recorded_at,
    )


def latest_review(reviews: list[ReviewDecisionV1]) -> ReviewDecisionV1:
    if not reviews:
        raise ValueError("at least one review is required")
    target_refs = {review.target_ref for review in reviews}
    if len(target_refs) != 1:
        raise ValueError("reviews must share a target")
    ordered = sorted(reviews, key=lambda review: (review.revision, review.review_id))
    if [review.revision for review in ordered] != list(range(1, len(ordered) + 1)):
        raise ValueError("review revisions must be contiguous")
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.supersedes_review_id != previous.review_id:
            raise ValueError("review supersession chain is broken")
    return ordered[-1]
