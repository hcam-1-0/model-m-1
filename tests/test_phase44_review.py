from __future__ import annotations

from hcam.intelligence.integrations.matching import build_candidate_set
from hcam.intelligence.integrations.review import (
    GeneratedHypothesisEvidenceLedger,
    build_review_handoff,
)
from tests.test_phase44_contracts import NOW, intent, manifest


def test_candidate_handoff_is_mandatory_review_and_digest_bound() -> None:
    query = intent(manifest())
    candidate_set = build_candidate_set(
        query_id=query.query_id,
        department=query.department,
        query_fields=dict(query.parameters),
        records=[dict(query.parameters)],
    )
    handoff = build_review_handoff(candidate_set, now=NOW)
    assert handoff.authority_class == "mandatory_review"
    assert handoff.state == "pending_review"
    assert "identity.not_established" in handoff.limitations
    assert "source.generated_only" in handoff.limitations
    assert handoff.operational is False


def test_hypothesis_evidence_history_keeps_support_correction_and_retraction() -> None:
    query = intent(manifest())
    candidate_set = build_candidate_set(
        query_id=query.query_id,
        department=query.department,
        query_fields=dict(query.parameters),
        records=[dict(query.parameters)],
    )
    ledger = GeneratedHypothesisEvidenceLedger()
    hypothesis_id = "hyp_" + "1" * 32
    supporting = ledger.append(
        candidate_set,
        hypothesis_id=hypothesis_id,
        role="supports",
        now=NOW,
    )
    superseding = ledger.append(
        candidate_set,
        hypothesis_id=hypothesis_id,
        role="supersedes",
        supersedes_revision_id=supporting.revision_id,
        now=NOW,
    )
    retraction = ledger.append(
        candidate_set,
        hypothesis_id=hypothesis_id,
        role="retracts",
        supersedes_revision_id=superseding.revision_id,
        now=NOW,
    )
    assert [item.role for item in ledger.history(hypothesis_id)] == [
        "supports",
        "supersedes",
        "retracts",
    ]
    assert retraction.revision == 3
    assert retraction.identity_state == "not_established"
