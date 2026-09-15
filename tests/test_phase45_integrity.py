from __future__ import annotations

import pytest
from pydantic import ValidationError

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.evidence import register_reference
from hcam.intelligence.investigations.integrity import assess_generated_digest


def _reference(p45_context: dict):
    return register_reference(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        source_system_ref=stable_id("ref", "system"),
        source_object_ref=stable_id("ref", "object"),
        source_version="generated.v1",
        content_digest=digest({"generated": "evidence"}),
        canonicalization_profile="generated.json.v1",
        classification="generated.public",
        registered_by=p45_context["actor"],
        reason=p45_context["reason"],
        registered_at=p45_context["now"],
    )


def test_integrity_is_separate_from_authenticity_custody_and_legal_state(p45_context: dict) -> None:
    reference = _reference(p45_context)
    assessment = assess_generated_digest(
        reference,
        observed_digest=reference.content_digest,
        outcome="matched",
        assessed_by=p45_context["actor"],
        assessed_at=p45_context["now"],
    )
    assert assessment.state == "matched"
    assert assessment.authenticity == assessment.custody == assessment.legal_status == "not_assessed"


def test_integrity_rejects_inconsistent_comparison(p45_context: dict) -> None:
    reference = _reference(p45_context)
    with pytest.raises(ValidationError, match="equal digests"):
        assess_generated_digest(
            reference,
            observed_digest=digest({"different": True}),
            outcome="matched",
            assessed_by=p45_context["actor"],
            assessed_at=p45_context["now"],
        )
    with pytest.raises(ValueError, match="allowlisted"):
        assess_generated_digest(
            reference,
            observed_digest=None,
            outcome="generated-invalid",
            assessed_by=p45_context["actor"],
            assessed_at=p45_context["now"],
        )
