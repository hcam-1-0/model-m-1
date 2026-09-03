from __future__ import annotations

import json
from dataclasses import replace

import pytest

from hcam.analytics.anpr.auxiliary import (
    AuxiliaryAnprViolation,
    EphemeralAuxiliarySampleV1,
    RawAuxiliaryOcrEngineResultV1,
    RawRenderedAuxiliaryPixelsV1,
    auxiliary_vocabulary_size,
    build_ephemeral_devanagari_hypothesis,
    derive_ephemeral_auxiliary_sample,
    evaluate_generated_auxiliary_font,
    evaluate_generated_devanagari_candidate,
    render_generated_auxiliary_crop,
    _distribution,
)
from hcam.analytics.anpr.contracts import (
    FONT_D0_ARTIFACT_SHA256,
    FONT_G0_ARTIFACT_SHA256,
    AuxiliaryFontRenderingEvaluationV1,
    SyntheticAnprExecutionPolicyV1,
)
from hcam.analytics.anpr.guardrails import (
    AnprBoundaryViolation,
    canonical_anpr_evidence_json,
)


POLICY = SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")


class FakeRenderer:
    shaping_backend = "basic_freetype_no_raqm"

    def __init__(self, candidate_id: str = "FONT-D0") -> None:
        self.candidate_id = candidate_id
        if candidate_id == "FONT-D0":
            self.artifact_sha256 = FONT_D0_ARTIFACT_SHA256
            self.font_family = "Noto Sans Devanagari"
        else:
            self.artifact_sha256 = FONT_G0_ARTIFACT_SHA256
            self.font_family = "Noto Sans Gujarati"

    def render(self, sample):  # type: ignore[no-untyped-def]
        shade = {
            "clean": b"\x10\x10\x10",
            "low_contrast": b"\x70\x70\x70",
            "downscaled": b"\xa0\xa0\xa0",
        }[sample.degradation]
        return RawRenderedAuxiliaryPixelsV1(
            width=32,
            height=16,
            bgr_bytes=shade * (32 * 16),
        )


class EchoEngine:
    candidate_id = "OCR-D0"
    extracted_inventory_sha256 = "sha256:" + "1" * 64

    def recognize(self, crop):  # type: ignore[no-untyped-def]
        return RawAuxiliaryOcrEngineResultV1(crop.sample.text, 0.875)


class InvalidScriptEngine:
    candidate_id = "OCR-D0"
    extracted_inventory_sha256 = "sha256:" + "2" * 64

    def recognize(self, crop):  # type: ignore[no-untyped-def]
        del crop
        return RawAuxiliaryOcrEngineResultV1("\u0a95\u0aae", 0.5)


class ExplodingEngine:
    candidate_id = "OCR-D0"
    extracted_inventory_sha256 = "sha256:" + "3" * 64

    def recognize(self, crop):  # type: ignore[no-untyped-def]
        del crop
        raise RuntimeError("generated text and implementation detail")


class SelectiveFailRenderer(FakeRenderer):
    def render(self, sample):  # type: ignore[no-untyped-def]
        if sample.degradation == "low_contrast":
            raise AuxiliaryAnprViolation("invalid_output")
        return super().render(sample)


class ExplodingRenderer(FakeRenderer):
    def render(self, sample):  # type: ignore[no-untyped-def]
        del sample
        raise RuntimeError("renderer details")


class MalformedRenderer(FakeRenderer):
    def render(self, sample):  # type: ignore[no-untyped-def]
        del sample
        return object()


def _crop(index: int = 0):  # type: ignore[no-untyped-def]
    return render_generated_auxiliary_crop(
        FakeRenderer(),
        "devanagari",
        index,
        policy=POLICY,
    )


def test_closed_auxiliary_samples_are_deterministic_and_cover_slices() -> None:
    for script in ("devanagari", "gujarati"):
        first = [
            derive_ephemeral_auxiliary_sample(script, index, policy=POLICY)
            for index in range(auxiliary_vocabulary_size(script))
        ]
        second = [
            derive_ephemeral_auxiliary_sample(script, index, policy=POLICY)
            for index in range(auxiliary_vocabulary_size(script))
        ]

        assert first == second
        assert {item.degradation for item in first} == {
            "clean",
            "low_contrast",
            "downscaled",
        }
        assert all(len(item.text) == 4 and not item.text.isascii() for item in first)


def test_auxiliary_generator_rejects_production_and_out_of_range_index() -> None:
    with pytest.raises(AuxiliaryAnprViolation):
        derive_ephemeral_auxiliary_sample(
            "devanagari",
            0,
            policy=SyntheticAnprExecutionPolicyV1(enabled=False),
        )
    with pytest.raises(ValueError, match="outside the closed vocabulary"):
        derive_ephemeral_auxiliary_sample("gujarati", 12, policy=POLICY)
    with pytest.raises(ValueError, match="unsupported auxiliary script"):
        derive_ephemeral_auxiliary_sample("latin", 0, policy=POLICY)  # type: ignore[arg-type]


def test_auxiliary_sample_and_failure_reason_fail_closed() -> None:
    sample = derive_ephemeral_auxiliary_sample("devanagari", 0, policy=POLICY)

    with pytest.raises(AuxiliaryAnprViolation):
        replace(sample, sample_id="unsafe")
    with pytest.raises(AuxiliaryAnprViolation):
        EphemeralAuxiliarySampleV1(
            sample_id="anprauxsample_" + "1" * 32,
            script="latin",  # type: ignore[arg-type]
            degradation="clean",
            text="A",
        )
    assert AuxiliaryAnprViolation("not-a-reason").code == "malformed_result"


def test_auxiliary_crop_is_bounded_and_rejects_cross_wired_font() -> None:
    crop = _crop()

    assert len(crop.bgr_bytes) == crop.width * crop.height * 3
    with pytest.raises(AuxiliaryAnprViolation):
        replace(crop, bgr_bytes=crop.bgr_bytes[:-1])
    with pytest.raises(AuxiliaryAnprViolation):
        render_generated_auxiliary_crop(
            FakeRenderer("FONT-G0"),
            "devanagari",
            0,
            policy=POLICY,
        )
    with pytest.raises(AuxiliaryAnprViolation) as unsupported:
        render_generated_auxiliary_crop(
            FakeRenderer(),
            "latin",  # type: ignore[arg-type]
            0,
            policy=POLICY,
        )
    assert unsupported.value.code == "unsupported_script"


@pytest.mark.parametrize(
    ("renderer", "code"),
    [
        (ExplodingRenderer(), "engine_error"),
        (MalformedRenderer(), "malformed_result"),
    ],
)
def test_auxiliary_renderer_failures_are_bounded(renderer: object, code: str) -> None:
    with pytest.raises(AuxiliaryAnprViolation) as raised:
        render_generated_auxiliary_crop(
            renderer,  # type: ignore[arg-type]
            "devanagari",
            0,
            policy=POLICY,
        )
    assert raised.value.code == code


def test_ephemeral_hypothesis_preserves_raw_devanagari_and_is_not_evidence_safe() -> None:
    crop = _crop()
    hypothesis = build_ephemeral_devanagari_hypothesis(
        crop,
        engine_result=RawAuxiliaryOcrEngineResultV1(crop.sample.text, 0.75),
        latency_ms=1.0,
    )

    assert hypothesis.raw_text == crop.sample.text
    assert hypothesis.modifies_registration_mark is False
    assert hypothesis.transliteration_performed is False
    with pytest.raises(AnprBoundaryViolation) as raised:
        canonical_anpr_evidence_json(hypothesis)
    assert raised.value.code == "plate_text_persistence_prohibited"

    gujarati_crop = render_generated_auxiliary_crop(
        FakeRenderer("FONT-G0"),
        "gujarati",
        0,
        policy=POLICY,
    )
    with pytest.raises(AuxiliaryAnprViolation) as mismatch:
        build_ephemeral_devanagari_hypothesis(
            gujarati_crop,
            engine_result=RawAuxiliaryOcrEngineResultV1(gujarati_crop.sample.text, 0.5),
            latency_ms=1.0,
        )
    assert mismatch.value.code == "unsupported_script"


@pytest.mark.parametrize(
    ("raw_text", "confidence", "code"),
    [
        ("", 0.5, "invalid_output"),
        ("\u0905" * 17, 0.5, "output_too_long"),
        ("\u0905 \u0915", 0.5, "unexpected_whitespace"),
        ("\u0905\u093e", 0.5, "unsupported_script"),
        ("\u0a95", 0.5, "unsupported_script"),
        ("A", 0.5, "unsupported_script"),
        ("\ud800", 0.5, "invalid_output"),
        ("\u0905", float("nan"), "invalid_confidence"),
        ("\u0905", True, "invalid_confidence"),
        (None, None, "no_result"),
    ],
)
def test_auxiliary_ocr_malformed_output_fails_closed(
    raw_text: object,
    confidence: object,
    code: str,
) -> None:
    with pytest.raises(AuxiliaryAnprViolation) as raised:
        build_ephemeral_devanagari_hypothesis(
            _crop(),
            engine_result=RawAuxiliaryOcrEngineResultV1(raw_text, confidence),
            latency_ms=1.0,
        )

    assert raised.value.code == code
    if isinstance(raw_text, str) and raw_text:
        assert raw_text not in str(raised.value)


@pytest.mark.parametrize("latency", [float("nan"), -1.0, 600_001.0])
def test_auxiliary_ocr_rejects_invalid_latency(latency: float) -> None:
    with pytest.raises(AuxiliaryAnprViolation) as raised:
        build_ephemeral_devanagari_hypothesis(
            _crop(),
            engine_result=RawAuxiliaryOcrEngineResultV1(_crop().sample.text, 0.5),
            latency_ms=latency,
        )
    assert raised.value.code == "malformed_result"


def test_exact_echo_evaluation_persists_identifier_free_aggregates_only() -> None:
    evaluation = evaluate_generated_devanagari_candidate(
        FakeRenderer(),
        EchoEngine(),
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
    assert evaluation.reference_grapheme_count == 48
    assert all(item.reference_grapheme_count == 16 for item in evaluation.slices)
    assert evaluation.replay_output_deterministic is True
    assert {item.degradation for item in evaluation.slices} == {
        "clean",
        "low_contrast",
        "downscaled",
    }
    assert document["raw_output_persisted"] is False
    assert '"raw_text"' not in rendered
    assert "anprauxsample_" not in rendered
    assert "anprauxregion_" not in rendered


def test_invalid_script_and_engine_error_are_sanitized_in_aggregates() -> None:
    invalid = evaluate_generated_devanagari_candidate(
        FakeRenderer(),
        InvalidScriptEngine(),
        policy=POLICY,
        sample_count=3,
    )
    exploded = evaluate_generated_devanagari_candidate(
        FakeRenderer(),
        ExplodingEngine(),
        policy=POLICY,
        sample_count=3,
    )
    rendered = canonical_anpr_evidence_json(
        exploded,
        maximum_bytes=64 * 1024,
        maximum_nodes=4_096,
    )

    assert invalid.failure_counts.unsupported_script == 3
    assert exploded.failure_counts.engine_error == 3
    assert "implementation detail" not in rendered


def test_font_evidence_separates_devanagari_ocr_from_gujarati_rendering() -> None:
    devanagari = evaluate_generated_auxiliary_font(
        FakeRenderer("FONT-D0"),
        policy=POLICY,
        sample_count=12,
        ocr_execution_performed=True,
    )
    gujarati = evaluate_generated_auxiliary_font(
        FakeRenderer("FONT-G0"),
        policy=POLICY,
        sample_count=12,
        ocr_execution_performed=False,
    )

    assert devanagari.replay_pixels_deterministic is True
    assert gujarati.replay_pixels_deterministic is True
    assert devanagari.generated_grapheme_count == 48
    assert gujarati.generated_grapheme_count == 48
    assert devanagari.ocr_execution_performed is True
    assert gujarati.ocr_execution_performed is False
    invalid = gujarati.model_dump(mode="json")
    invalid["ocr_execution_performed"] = True
    with pytest.raises(ValueError, match="cross-wired"):
        AuxiliaryFontRenderingEvaluationV1.model_validate(invalid)


def test_font_evaluation_counts_bounded_render_failures() -> None:
    evaluation = evaluate_generated_auxiliary_font(
        SelectiveFailRenderer(),
        policy=POLICY,
        sample_count=6,
        ocr_execution_performed=True,
    )

    assert evaluation.succeeded == 4
    assert evaluation.failed == 2
    assert next(
        item for item in evaluation.slices if item.degradation == "low_contrast"
    ).failed == 2


def test_auxiliary_evaluation_limits_and_candidate_gate_fail_closed() -> None:
    class WrongEngine(EchoEngine):
        candidate_id = "OCR-G0"

    with pytest.raises(ValueError, match="only exact OCR-D0"):
        evaluate_generated_devanagari_candidate(
            FakeRenderer(),
            WrongEngine(),
            policy=POLICY,
            sample_count=1,
        )
    with pytest.raises(ValueError, match="closed vocabulary"):
        evaluate_generated_auxiliary_font(
            FakeRenderer("FONT-G0"),
            policy=POLICY,
            sample_count=13,
            ocr_execution_performed=False,
        )
    with pytest.raises(ValueError, match="font replay"):
        evaluate_generated_auxiliary_font(
            FakeRenderer("FONT-G0"),
            policy=POLICY,
            sample_count=1,
            replay_runs=19,
            ocr_execution_performed=False,
        )
    wrong_font = FakeRenderer()
    wrong_font.candidate_id = "FONT-X"
    with pytest.raises(ValueError, match="only exact W6 fonts"):
        evaluate_generated_auxiliary_font(
            wrong_font,
            policy=POLICY,
            sample_count=1,
            ocr_execution_performed=True,
        )
    with pytest.raises(ValueError, match="OCR replay"):
        evaluate_generated_devanagari_candidate(
            FakeRenderer(),
            EchoEngine(),
            policy=POLICY,
            sample_count=1,
            replay_runs=19,
        )
    with pytest.raises(ValueError, match="closed vocabulary"):
        evaluate_generated_devanagari_candidate(
            FakeRenderer(),
            EchoEngine(),
            policy=POLICY,
            sample_count=13,
        )
    with pytest.raises(ValueError, match="requires at least one"):
        _distribution([])
