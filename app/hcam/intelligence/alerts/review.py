from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from hcam.intelligence.alerts.contracts import (
    AlertReviewDecisionV1,
    ReviewQuorumPolicyV1,
)


class ReviewDenied(ValueError):
    pass


@dataclass(slots=True)
class ReviewQuorum:
    policy: ReviewQuorumPolicyV1
    subject_actor_id: str | None = None
    decisions: list[AlertReviewDecisionV1] = field(default_factory=list)

    def add(self, decision: AlertReviewDecisionV1, *, now: datetime) -> None:
        if decision.department != self.policy.department:
            raise ReviewDenied("review department does not match")
        if decision.policy_id != self.policy.policy_id or decision.policy_version != self.policy.policy_version:
            raise ReviewDenied("review policy binding does not match")
        if decision.evidence_digest != self.policy.evidence_digest:
            raise ReviewDenied("review evidence changed")
        if decision.reviewer_role not in self.policy.permitted_roles:
            raise ReviewDenied("reviewer role is not permitted")
        if self.subject_actor_id is not None and decision.reviewer_id == self.subject_actor_id:
            raise ReviewDenied("subject actor cannot review their own workflow")
        if self.policy.expires_at is not None and now >= self.policy.expires_at:
            raise ReviewDenied("review policy expired")
        if any(item.reviewer_id == decision.reviewer_id for item in self.decisions):
            raise ReviewDenied("reviewer cannot satisfy multiple quorum slots")
        if any(item.decision_id == decision.decision_id for item in self.decisions):
            raise ReviewDenied("review decision already exists")
        self.decisions.append(decision)

    @property
    def outcome(self) -> str:
        binding = [item.decision for item in self.decisions if item.decision in {"approve", "deny"}]
        if "approve" in binding and "deny" in binding:
            return "disagreement"
        if len(binding) < self.policy.required_distinct_reviewers:
            return "pending"
        if all(item == "approve" for item in binding):
            return "approved"
        if all(item == "deny" for item in binding):
            return "rejected"
        return "pending"
