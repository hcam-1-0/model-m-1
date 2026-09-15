from __future__ import annotations

from datetime import datetime

from hcam.intelligence.investigations.canonical import stable_id
from hcam.intelligence.investigations.contracts import (
    EvidenceReferenceV2,
    IntegrityAssessmentV1,
)


def assess_generated_digest(
    reference: EvidenceReferenceV2,
    *,
    observed_digest: str | None,
    outcome: str,
    assessed_by: str,
    assessed_at: datetime,
) -> IntegrityAssessmentV1:
    allowed = {"matched", "mismatched", "unavailable", "denied", "unverifiable"}
    if outcome not in allowed:
        raise ValueError("integrity outcome is not allowlisted")
    return IntegrityAssessmentV1(
        assessment_id=stable_id(
            "iasm", reference.reference_id, outcome, assessed_at.isoformat()
        ),
        reference_id=reference.reference_id,
        timeline_id=reference.timeline_id,
        department=reference.department,
        state=outcome,
        algorithm="sha256",
        expected_digest=reference.content_digest,
        observed_digest=observed_digest,
        assessed_by=assessed_by,
        reason_code=f"integrity.{outcome}",
        assessed_at=assessed_at,
    )
