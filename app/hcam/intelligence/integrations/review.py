from __future__ import annotations

from datetime import UTC, datetime

from hcam.intelligence.integrations.canonical import digest, stable_id
from hcam.intelligence.integrations.contracts import (
    CandidateSetV1,
    HypothesisEvidenceRevisionV1,
    ReviewHandoffV1,
)


def build_review_handoff(
    candidate_set: CandidateSetV1,
    *,
    now: datetime | None = None,
) -> ReviewHandoffV1:
    limitations = sorted(
        set(
            [
                "identity.not_established",
                "review.mandatory",
                "source.generated_only",
                *candidate_set.reason_codes,
            ]
        )
    )
    return ReviewHandoffV1(
        handoff_id=stable_id("rrev", candidate_set.candidate_set_id),
        candidate_set_id=candidate_set.candidate_set_id,
        department=candidate_set.department,
        limitations=limitations,
        evidence_digest=digest(candidate_set),
        created_at=now or datetime.now(UTC),
    )


class GeneratedHypothesisEvidenceLedger:
    def __init__(self) -> None:
        self._items: list[HypothesisEvidenceRevisionV1] = []

    def append(
        self,
        candidate_set: CandidateSetV1,
        *,
        hypothesis_id: str,
        role: str,
        supersedes_revision_id: str | None = None,
        now: datetime | None = None,
    ) -> HypothesisEvidenceRevisionV1:
        revision = 1 + sum(
            item.hypothesis_id == hypothesis_id for item in self._items
        )
        material = {
            "hypothesis_id": hypothesis_id,
            "candidate_set_id": candidate_set.candidate_set_id,
            "role": role,
            "revision": revision,
            "supersedes_revision_id": supersedes_revision_id,
        }
        item = HypothesisEvidenceRevisionV1(
            revision_id=stable_id("rhev", digest(material)),
            hypothesis_id=hypothesis_id,
            candidate_set_id=candidate_set.candidate_set_id,
            department=candidate_set.department,
            role=role,
            source_digest=candidate_set.candidate_set_digest,
            revision=revision,
            supersedes_revision_id=supersedes_revision_id,
            recorded_at=now or datetime.now(UTC),
        )
        self._items.append(item)
        return item

    def history(self, hypothesis_id: str) -> list[HypothesisEvidenceRevisionV1]:
        return [item for item in self._items if item.hypothesis_id == hypothesis_id]
