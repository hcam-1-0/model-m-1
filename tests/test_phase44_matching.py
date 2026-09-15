from __future__ import annotations

from hcam.intelligence.integrations.matching import build_candidate_set, compare_field
from tests.test_phase44_contracts import intent, manifest


def test_matching_is_deterministic_bounded_and_never_establishes_identity() -> None:
    query = intent(manifest())
    records = [
        {
            "record_key": "gen_record_001",
            "category": "gen_category_a",
            "region": "gen_region_west",
        },
        {
            "record_key": "gen_record_002",
            "category": "gen_category_b",
            "region": "gen_region_east",
        },
    ]
    result = build_candidate_set(
        query_id=query.query_id,
        department=query.department,
        query_fields=dict(query.parameters),
        records=records,
    )
    assert result.outcome == "candidates"
    assert result.identity_state == "not_established"
    assert result.mandatory_review is True
    assert result.candidates[0].aggregate_score == 1


def test_matching_reports_normalized_approximate_missing_contradiction_and_ambiguity() -> None:
    assert compare_field("category", "gen-a", "GEN A").state == "normalized"
    assert compare_field("category", "gen_alpha", "gen_alphb").state == "approximate"
    assert compare_field("category", "gen_a", None).state == "missing"
    assert (
        compare_field("category", "gen_alpha", "gen_zulu_xray").state
        == "contradicts"
    )
    query = intent(manifest())
    ambiguous = build_candidate_set(
        query_id=query.query_id,
        department=query.department,
        query_fields=dict(query.parameters),
        records=[dict(query.parameters), dict(query.parameters)],
    )
    assert ambiguous.outcome == "ambiguous"
    assert ambiguous.candidates == []
    abstain = build_candidate_set(
        query_id=query.query_id,
        department=query.department,
        query_fields=dict(query.parameters),
        records=[{"record_key": "gen_other", "category": "gen_other"}],
    )
    assert abstain.outcome == "no_match" or abstain.outcome == "abstain"
