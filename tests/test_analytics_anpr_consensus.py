from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from hcam.analytics.anpr import (
    BoundedSyntheticConsensus,
    ConsensusViolation,
    EphemeralConsensusObservationV1,
    EphemeralPlateNormalizationV1,
    SyntheticConsensusPolicyV1,
)
from hcam.analytics.anpr.guardrails import (
    AnprBoundaryViolation,
    canonical_anpr_evidence_json,
)


def _identifier(prefix: str, value: int) -> str:
    return f"{prefix}_{value:032x}"


def _normalization(
    value: str = "SYN-AB12-CD34",
    *,
    confidence: float = 0.8,
    candidate_id: str = "OCR-L0",
) -> EphemeralPlateNormalizationV1:
    return EphemeralPlateNormalizationV1(
        candidate_id=candidate_id,
        script_lane="latin",
        raw_hypothesis_digest=(
            "sha256:" + hashlib.sha256(value.encode("ascii")).hexdigest()
        ),
        nfc_value=value,
        graphemes=tuple(value),
        normalized_display_candidate=value,
        raw_scalar_count=len(value),
        nfc_scalar_count=len(value),
        grapheme_count=len(value),
        format_family="synthetic_non_issuable",
        validation_outcomes=(
            "allowlist_valid",
            "graphemes_segmented",
            "nfc_derived",
            "synthetic_grammar_valid",
            "unicode_scalar_valid",
            "utf8_valid",
        ),
        nfc_transform_performed=False,
        case_transform_performed=False,
        raw_confidence=confidence,
        calibrated_confidence=confidence,
        abstention_reason="quality_threshold_unapproved",
    )


def _observation(
    sequence: int,
    *,
    stream: int = 1,
    epoch: int = 1,
    track: int = 1,
    event_time_ms: int | None = None,
    value: str = "SYN-AB12-CD34",
    confidence: float = 0.8,
) -> EphemeralConsensusObservationV1:
    return EphemeralConsensusObservationV1(
        stream_id=_identifier("str", stream),
        tracker_epoch=_identifier("epoch", epoch),
        track_id=_identifier("trk", track),
        event_time_ms=sequence * 100 if event_time_ms is None else event_time_ms,
        source_sequence=sequence,
        normalization=_normalization(value, confidence=confidence),
    )


def _engine() -> BoundedSyntheticConsensus:
    return BoundedSyntheticConsensus(
        SyntheticConsensusPolicyV1(enabled=True, environment="test")
    )


def test_consensus_is_default_off_and_production_forbidden() -> None:
    with pytest.raises(ConsensusViolation, match="runtime_disabled"):
        BoundedSyntheticConsensus().observe(_observation(1))

    with pytest.raises(ValidationError, match="forbidden in production"):
        SyntheticConsensusPolicyV1(enabled=True, environment="production")


def test_five_observations_close_with_weighted_exact_vote_and_abstain() -> None:
    engine = _engine()
    for sequence in range(1, 5):
        assert engine.observe(_observation(sequence)) == ()

    (result,) = engine.observe(_observation(5))

    assert result.close_reason == "count_limit"
    assert result.observation_count == 5
    assert result.winning_support == 5
    assert result.winning_confidence_weight == 4.0
    assert result.confidence_margin == 4.0
    assert result.thresholds_approved is False
    assert result.abstain is True
    assert result.accepted_value_emitted is False
    assert engine.active_state_count() == 0


def test_rank_order_is_deterministic_for_disagreement_and_ties() -> None:
    first = "SYN-AB12-CD34"
    second = "SYN-EF56-GH78"
    engine = _engine()
    values = (second, first, second, first, second)
    confidences = (0.2, 0.8, 0.2, 0.1, 0.2)
    for sequence, (value, confidence) in enumerate(
        zip(values, confidences, strict=True), start=1
    ):
        results = engine.observe(
            _observation(sequence, value=value, confidence=confidence)
        )

    (result,) = results
    assert result.winning_candidate == first
    assert result.winning_support == 2
    assert result.winning_confidence_weight == 0.9
    assert result.confidence_margin == 0.3

    tied = _engine()
    tied.observe(_observation(1, value=second, confidence=0.5))
    tied.observe(_observation(2, value=first, confidence=0.5))
    (tie_result,) = tied.close_track(
        _identifier("str", 1), _identifier("epoch", 1), _identifier("trk", 1)
    )
    assert tie_result.winning_candidate == first


def test_same_text_never_merges_stream_epoch_or_track_boundaries() -> None:
    engine = _engine()
    observations = (
        _observation(1, stream=1, epoch=1, track=1),
        _observation(1, stream=2, epoch=1, track=1),
        _observation(1, stream=1, epoch=2, track=1),
        _observation(1, stream=1, epoch=1, track=2),
    )
    for observation in observations:
        assert engine.observe(observation) == ()

    assert engine.active_state_count() == 4
    assert engine.active_state_count(_identifier("str", 1)) == 3
    closed = engine.reset_epoch(_identifier("str", 1), _identifier("epoch", 1))
    assert len(closed) == 2
    assert all(result.observation_count == 1 for result in closed)
    assert engine.active_state_count() == 2


def test_event_time_window_closes_without_consuming_late_observation() -> None:
    engine = _engine()
    engine.observe(_observation(1, event_time_ms=1_000))

    (result,) = engine.observe(_observation(2, event_time_ms=3_000))

    assert result.close_reason == "event_time_window"
    assert result.observation_count == 1
    assert result.last_event_time_ms == 1_000
    assert engine.active_state_count() == 0


def test_expire_track_end_and_epoch_reset_close_active_states() -> None:
    engine = _engine()
    engine.observe(_observation(1, track=1, event_time_ms=100))
    engine.observe(_observation(1, track=2, event_time_ms=200))
    (expired,) = engine.expire(_identifier("str", 1), at_event_time_ms=2_100)
    assert expired.close_reason == "event_time_window"
    (ended,) = engine.close_track(
        _identifier("str", 1), _identifier("epoch", 1), _identifier("trk", 2)
    )
    assert ended.close_reason == "track_end"
    assert engine.close_track(
        _identifier("str", 1), _identifier("epoch", 1), _identifier("trk", 2)
    ) == ()

    engine.observe(_observation(1, track=3))
    engine.observe(_observation(1, track=4))
    reset = engine.reset_epoch(_identifier("str", 1), _identifier("epoch", 1))
    assert len(reset) == 2
    assert all(result.close_reason == "epoch_reset" for result in reset)


def test_duplicate_and_out_of_order_observations_fail_closed() -> None:
    engine = _engine()
    engine.observe(_observation(2, event_time_ms=200))

    with pytest.raises(ConsensusViolation, match="duplicate_observation"):
        engine.observe(_observation(2, event_time_ms=201))
    with pytest.raises(ConsensusViolation, match="out_of_order_observation"):
        engine.observe(_observation(1, event_time_ms=300))
    with pytest.raises(ConsensusViolation, match="out_of_order_observation"):
        engine.observe(_observation(3, event_time_ms=100))
    assert engine.active_state_count() == 1


def test_stream_state_capacity_fails_closed_without_evicting_active_tracks() -> None:
    engine = _engine()
    for track in range(1, 257):
        assert engine.observe(_observation(1, track=track)) == ()
    assert engine.active_state_count(_identifier("str", 1)) == 256

    (result,) = engine.observe(_observation(1, track=257))

    assert result.close_reason == "overload"
    assert result.abstention_reason == "overload_fail_closed"
    assert engine.active_state_count(_identifier("str", 1)) == 256


def test_auxiliary_or_unrecognized_normalization_cannot_enter_consensus() -> None:
    document = _observation(1).model_dump(mode="python")
    document["normalization"]["script_lane"] = "devanagari"
    document["normalization"]["candidate_id"] = "OCR-D0"
    document["normalization"]["format_family"] = "unrecognized"
    document["normalization"]["abstention_reason"] = "auxiliary_observation_only"

    with pytest.raises(ValidationError):
        EphemeralConsensusObservationV1.model_validate(document)


def test_ephemeral_consensus_result_is_rejected_by_evidence_boundary() -> None:
    engine = _engine()
    engine.observe(_observation(1))
    (result,) = engine.close_track(
        _identifier("str", 1), _identifier("epoch", 1), _identifier("trk", 1)
    )

    with pytest.raises(
        AnprBoundaryViolation, match="plate_text_persistence_prohibited"
    ):
        canonical_anpr_evidence_json(result)


@pytest.mark.parametrize("field", ["event_time_ms", "source_sequence"])
def test_consensus_observation_metadata_is_rejected_by_evidence_boundary(
    field: str,
) -> None:
    with pytest.raises(
        AnprBoundaryViolation, match="plate_text_persistence_prohibited"
    ):
        canonical_anpr_evidence_json({field: 1})


def test_consensus_result_contract_rejects_forged_rank_and_margin() -> None:
    engine = _engine()
    engine.observe(_observation(1, value="SYN-AB12-CD34", confidence=0.8))
    engine.observe(_observation(2, value="SYN-EF56-GH78", confidence=0.2))
    (result,) = engine.close_track(
        _identifier("str", 1), _identifier("epoch", 1), _identifier("trk", 1)
    )
    document = result.model_dump(mode="python")
    document["ranked_votes"] = tuple(reversed(document["ranked_votes"]))
    document["winning_candidate"] = document["ranked_votes"][0][
        "normalized_display_candidate"
    ]
    document["winning_support"] = document["ranked_votes"][0]["observation_count"]
    document["winning_confidence_weight"] = document["ranked_votes"][0][
        "confidence_weight"
    ]

    with pytest.raises(ValidationError, match="canonical rank order"):
        type(result).model_validate(document)

    document = result.model_dump(mode="python")
    document["confidence_margin"] = 0.0
    with pytest.raises(ValidationError, match="margin is inconsistent"):
        type(result).model_validate(document)


def test_consensus_cannot_build_an_empty_result() -> None:
    with pytest.raises(ValueError, match="empty state"):
        _engine()._build_result((), "track_end")


def test_negative_expiry_time_is_rejected_without_state_change() -> None:
    engine = _engine()
    engine.observe(_observation(1))
    with pytest.raises(ValueError, match="non-negative"):
        engine.expire(_identifier("str", 1), at_event_time_ms=-1)
    assert engine.active_state_count() == 1
