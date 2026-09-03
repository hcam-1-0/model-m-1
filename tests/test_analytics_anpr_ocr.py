from __future__ import annotations

import json
from dataclasses import replace

import pytest

from hcam.analytics.anpr.contracts import (
    EphemeralLatinOcrHypothesisV1,
    SyntheticAnprExecutionPolicyV1,
)
from hcam.analytics.anpr.generator import synthetic_corpus_plan_fixture
from hcam.analytics.anpr.guardrails import (
    AnprBoundaryViolation,
    canonical_anpr_evidence_json,
)
from hcam.analytics.anpr.ocr import (
    AnprOcrViolation,
    RawLatinOcrEngineResultV1,
    _distribution,
    _draw_line,
    build_ephemeral_latin_hypothesis,
    evaluate_generated_latin_candidate,
    render_generated_latin_crop,
)


POLICY = SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")


class ExactEchoEngine:
    candidate_id = "OCR-L0"
    extracted_inventory_sha256 = "sha256:" + "1" * 64

    def recognize(self, crop):  # type: ignore[no-untyped-def]
        return RawLatinOcrEngineResultV1(crop.ephemeral_token.token, 0.875)


class InvalidScriptEngine:
    candidate_id = "OCR-L1"
    extracted_inventory_sha256 = "sha256:" + "2" * 64

    def recognize(self, crop):  # type: ignore[no-untyped-def]
        del crop
        return RawLatinOcrEngineResultV1("\u8f66\u724c", 0.5)


class ExplodingEngine:
    candidate_id = "OCR-L0"
    extracted_inventory_sha256 = "sha256:" + "3" * 64

    def recognize(self, crop):  # type: ignore[no-untyped-def]
        del crop
        raise RuntimeError("engine detail must not escape")


def _crop(index: int = 0):  # type: ignore[no-untyped-def]
    return render_generated_latin_crop(
        synthetic_corpus_plan_fixture(),
        "development",
        index,
        policy=POLICY,
    )


def test_generated_latin_renderer_is_deterministic_bounded_and_text_visible() -> None:
    first = _crop(0)
    second = _crop(0)

    assert first == second
    assert len(first.bgr_bytes) == first.width * first.height * 3
    assert first.width <= 512
    assert first.height <= 128
    assert first.ephemeral_token.token.startswith("SYN-")
    assert b"SYN-" not in first.bgr_bytes


def test_generated_latin_renderer_covers_both_declared_layouts() -> None:
    layouts = {_crop(index).layout for index in range(8)}

    assert layouts == {"single_line", "two_line"}


def test_generated_crop_rejects_invalid_pixels_dimensions_and_lineage() -> None:
    crop = _crop()

    with pytest.raises(AnprOcrViolation):
        replace(crop, width=0)
    with pytest.raises(AnprOcrViolation):
        replace(crop, bgr_bytes=crop.bgr_bytes[:-1])
    with pytest.raises(AnprOcrViolation):
        replace(crop, generator_version="sha256:" + "0" * 64)


def test_bitmap_renderer_rejects_unknown_glyph_and_impossible_geometry() -> None:
    pixels = bytearray(b"\xff\xff\xff" * (64 * 32))

    with pytest.raises(AnprOcrViolation) as unknown:
        _draw_line(
            pixels,
            canvas_width=64,
            canvas_height=32,
            value="?",
            y=4,
            scale=2,
        )
    with pytest.raises(AnprOcrViolation) as bounds:
        _draw_line(
            pixels,
            canvas_width=8,
            canvas_height=8,
            value="A",
            y=4,
            scale=2,
        )

    assert unknown.value.code == "unsupported_script"
    assert bounds.value.code == "invalid_output"


def test_ephemeral_hypothesis_preserves_exact_raw_output() -> None:
    crop = _crop()
    raw = RawLatinOcrEngineResultV1("sYn-01Ab-cD23", 0.75)

    hypothesis = build_ephemeral_latin_hypothesis(
        crop,
        candidate_id="OCR-L0",
        engine_result=raw,
        latency_ms=12.5,
    )

    assert hypothesis.raw_text == "sYn-01Ab-cD23"
    assert hypothesis.raw_output_mutated is False
    assert hypothesis.retained is False


@pytest.mark.parametrize(
    ("raw_text", "confidence", "expected_code"),
    [
        ("", 0.5, "invalid_output"),
        ("A" * 33, 0.5, "output_too_long"),
        ("SYN TEST", 0.5, "unexpected_whitespace"),
        ("SYN-\u8f66", 0.5, "unsupported_script"),
        ("SYN-\ud800", 0.5, "invalid_output"),
        ("SYN-AAAA-BBBB", float("nan"), "invalid_confidence"),
        ("SYN-AAAA-BBBB", True, "invalid_confidence"),
        (None, None, "no_result"),
    ],
)
def test_malformed_engine_output_fails_with_safe_reason(
    raw_text: object,
    confidence: object,
    expected_code: str,
) -> None:
    with pytest.raises(AnprOcrViolation) as raised:
        build_ephemeral_latin_hypothesis(
            _crop(),
            candidate_id="OCR-L0",
            engine_result=RawLatinOcrEngineResultV1(raw_text, confidence),
            latency_ms=1.0,
        )

    assert raised.value.code == expected_code
    if isinstance(raw_text, str) and raw_text:
        assert raw_text not in str(raised.value)


def test_malformed_alternative_shape_fails_closed() -> None:
    malformed = RawLatinOcrEngineResultV1(
        "SYN-AAAA-BBBB",
        0.5,
        alternatives=(("SYN-BBBB-CCCC",),),  # type: ignore[arg-type]
    )

    with pytest.raises(AnprOcrViolation) as raised:
        build_ephemeral_latin_hypothesis(
            _crop(),
            candidate_id="OCR-L0",
            engine_result=malformed,
            latency_ms=1.0,
        )

    assert raised.value.code == "malformed_result"


@pytest.mark.parametrize("latency_ms", [float("nan"), -1.0, 600_001.0])
def test_invalid_latency_fails_closed(latency_ms: float) -> None:
    with pytest.raises(AnprOcrViolation) as raised:
        build_ephemeral_latin_hypothesis(
            _crop(),
            candidate_id="OCR-L0",
            engine_result=RawLatinOcrEngineResultV1("SYN-AAAA-BBBB", 0.5),
            latency_ms=latency_ms,
        )

    assert raised.value.code == "malformed_result"


def test_alternative_count_and_values_are_bounded() -> None:
    too_many = tuple(("SYN-AAAA-BBBB", 0.5) for _ in range(6))
    with pytest.raises(AnprOcrViolation) as count_error:
        build_ephemeral_latin_hypothesis(
            _crop(),
            candidate_id="OCR-L0",
            engine_result=RawLatinOcrEngineResultV1(
                "SYN-AAAA-BBBB", 0.5, alternatives=too_many
            ),
            latency_ms=1.0,
        )
    with pytest.raises(AnprOcrViolation) as value_error:
        build_ephemeral_latin_hypothesis(
            _crop(),
            candidate_id="OCR-L0",
            engine_result=RawLatinOcrEngineResultV1(
                "SYN-AAAA-BBBB",
                0.5,
                alternatives=(("bad value", 0.5),),
            ),
            latency_ms=1.0,
        )

    assert count_error.value.code == "malformed_result"
    assert value_error.value.code == "unexpected_whitespace"


def test_empty_distribution_and_zero_sample_evaluation_are_rejected() -> None:
    with pytest.raises(ValueError, match="requires at least one"):
        _distribution([])
    with pytest.raises(ValueError, match="outside the local limit"):
        evaluate_generated_latin_candidate(
            synthetic_corpus_plan_fixture(),
            ExactEchoEngine(),
            policy=POLICY,
            sample_count=0,
        )


def test_raw_ocr_hypothesis_is_rejected_by_evidence_guard() -> None:
    hypothesis = build_ephemeral_latin_hypothesis(
        _crop(),
        candidate_id="OCR-L0",
        engine_result=RawLatinOcrEngineResultV1("SYN-AAAA-BBBB", 0.75),
        latency_ms=1.0,
    )

    with pytest.raises(AnprBoundaryViolation) as raised:
        canonical_anpr_evidence_json(hypothesis)

    assert raised.value.code == "plate_text_persistence_prohibited"


def test_exact_echo_evaluation_persists_only_identifier_free_aggregates() -> None:
    evaluation = evaluate_generated_latin_candidate(
        synthetic_corpus_plan_fixture(),
        ExactEchoEngine(),
        policy=POLICY,
        sample_count=12,
    )
    rendered = canonical_anpr_evidence_json(
        evaluation,
        maximum_bytes=64 * 1024,
        maximum_nodes=4_096,
    )
    document = json.loads(rendered)

    assert evaluation.succeeded == 12
    assert evaluation.exact_matches == 12
    assert evaluation.raw_edit_distance == 0
    assert evaluation.replay_output_deterministic is True
    assert {item.layout for item in evaluation.slices} == {
        "single_line",
        "two_line",
    }
    assert document["raw_output_persisted"] is False
    assert "SYN-" not in rendered
    assert '"raw_text"' not in rendered
    assert "sample_id" not in rendered
    assert "region_id" not in rendered


def test_invalid_outputs_are_counted_without_persisting_rejected_values() -> None:
    evaluation = evaluate_generated_latin_candidate(
        synthetic_corpus_plan_fixture(),
        InvalidScriptEngine(),
        policy=POLICY,
        sample_count=4,
    )
    rendered = canonical_anpr_evidence_json(
        evaluation,
        maximum_bytes=64 * 1024,
        maximum_nodes=4_096,
    )

    assert evaluation.failed == 4
    assert evaluation.failure_counts.unsupported_script == 4
    assert evaluation.confidence_distribution is None
    assert "\u8f66\u724c" not in rendered


def test_engine_exceptions_are_reduced_to_safe_aggregate_reason() -> None:
    evaluation = evaluate_generated_latin_candidate(
        synthetic_corpus_plan_fixture(),
        ExplodingEngine(),
        policy=POLICY,
        sample_count=2,
    )
    rendered = canonical_anpr_evidence_json(
        evaluation,
        maximum_bytes=64 * 1024,
        maximum_nodes=4_096,
    )

    assert evaluation.failed == 2
    assert evaluation.failure_counts.engine_error == 2
    assert evaluation.replay_output_deterministic is True
    assert "engine detail" not in rendered


def test_evaluation_never_opens_final_test_samples() -> None:
    with pytest.raises(ValueError, match="cannot open final-test"):
        evaluate_generated_latin_candidate(
            synthetic_corpus_plan_fixture(),
            ExactEchoEngine(),
            policy=POLICY,
            sample_count=13,
        )


def test_candidate_contract_rejects_cross_wired_artifact() -> None:
    evaluation = evaluate_generated_latin_candidate(
        synthetic_corpus_plan_fixture(),
        ExactEchoEngine(),
        policy=POLICY,
        sample_count=4,
    )
    document = evaluation.model_dump(mode="json")
    document["artifact_id"] = "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED"

    with pytest.raises(ValueError, match="exact artifact"):
        EphemeralLatinOcrHypothesisV1.model_validate(
            {
                "result_id": "anprocr_" + "1" * 32,
                "region_id": "anprregion_" + "2" * 32,
                "sample_id": "anprsample_" + "3" * 32,
                "candidate_id": "OCR-L0",
                "artifact_id": document["artifact_id"],
                "artifact_sha256": document["artifact_sha256"],
                "raw_text": "SYN-AAAA-BBBB",
                "raw_confidence": 0.5,
                "latency_ms": 1.0,
            }
        )
