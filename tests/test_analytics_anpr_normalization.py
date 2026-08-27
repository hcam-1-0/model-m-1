from __future__ import annotations

import unicodedata

import pytest
from pydantic import ValidationError

import hcam.analytics.anpr.normalization as normalization_module

from hcam.analytics.anpr import (
    ANPR_PINNED_REGEX_VERSION,
    ANPR_PINNED_UNICODE_VERSION,
    ExactRegexGraphemeSegmenter,
    NormalizationViolation,
    evaluate_generated_calibration,
    measure_generated_normalization,
    normalize_ephemeral_hypothesis,
    segment_generated_reference,
    sequence_edit_distance,
)
from hcam.analytics.anpr.contracts import (
    OCR_L0_ARTIFACT_SHA256,
    EphemeralAuxiliaryOcrHypothesisV1,
    EphemeralCalibrationObservationV1,
    EphemeralLatinOcrHypothesisV1,
    EphemeralPlateNormalizationV1,
)
from hcam.analytics.anpr.guardrails import (
    AnprBoundaryViolation,
    canonical_anpr_evidence_json,
)


class ClosedTestSegmenter:
    regex_version = ANPR_PINNED_REGEX_VERSION
    unicode_version = ANPR_PINNED_UNICODE_VERSION

    def segment(self, value: str) -> tuple[str, ...]:
        clusters: list[str] = []
        for character in value:
            if clusters and unicodedata.category(character).startswith("M"):
                clusters[-1] += character
            else:
                clusters.append(character)
        return tuple(clusters)


class WrongVersionSegmenter(ClosedTestSegmenter):
    regex_version = "0.0.0"


def _latin(raw_text: str, confidence: float = 0.75) -> EphemeralLatinOcrHypothesisV1:
    return EphemeralLatinOcrHypothesisV1(
        result_id="anprocr_11111111111111111111111111111111",
        region_id="anprregion_22222222222222222222222222222222",
        sample_id="anprsample_33333333333333333333333333333333",
        candidate_id="OCR-L0",
        artifact_id="OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
        artifact_sha256=OCR_L0_ARTIFACT_SHA256,
        raw_text=raw_text,
        raw_confidence=confidence,
        latency_ms=0.0,
    )


def _devanagari(raw_text: str, confidence: float = 0.65) -> EphemeralAuxiliaryOcrHypothesisV1:
    return EphemeralAuxiliaryOcrHypothesisV1(
        result_id="anprauxocr_11111111111111111111111111111111",
        region_id="anprauxregion_22222222222222222222222222222222",
        sample_id="anprauxsample_33333333333333333333333333333333",
        raw_text=raw_text,
        raw_confidence=confidence,
        latency_ms=0.0,
    )


def test_latin_normalization_preserves_raw_and_mandatorily_abstains() -> None:
    hypothesis = _latin("syn-a1b2-c3d4")
    raw_before = hypothesis.raw_text

    result = normalize_ephemeral_hypothesis(
        hypothesis,
        segmenter=ClosedTestSegmenter(),
    )

    assert hypothesis.raw_text == raw_before
    assert result.nfc_value == raw_before
    assert result.normalized_display_candidate == "SYN-A1B2-C3D4"
    assert result.format_family == "synthetic_non_issuable"
    assert result.case_transform_performed is True
    assert result.separator_transform_performed is False
    assert result.calibrated_confidence == hypothesis.raw_confidence
    assert result.quality_threshold_approved is False
    assert result.abstain is True
    assert result.abstention_reason == "quality_threshold_unapproved"
    assert result.raw_output_mutated is False


def test_grammar_rejection_does_not_autocorrect_or_insert_separator() -> None:
    hypothesis = _latin("SYN-A1B2C3D4")
    result = normalize_ephemeral_hypothesis(
        hypothesis,
        segmenter=ClosedTestSegmenter(),
    )

    assert result.normalized_display_candidate == hypothesis.raw_text
    assert result.format_family == "unrecognized"
    assert result.abstention_reason == "synthetic_grammar_rejected"
    assert result.separator_transform_performed is False
    assert result.confusable_substitution_performed is False
    assert result.dictionary_completion_performed is False
    assert result.record_lookup_performed is False


def test_devanagari_nfc_and_grapheme_semantics_remain_auxiliary_only() -> None:
    hypothesis = _devanagari("\u0958")
    result = normalize_ephemeral_hypothesis(
        hypothesis,
        segmenter=ClosedTestSegmenter(),
    )

    assert result.nfc_value == unicodedata.normalize("NFC", hypothesis.raw_text)
    assert result.nfc_transform_performed is True
    assert result.grapheme_count == 1
    assert result.format_family == "unrecognized"
    assert result.abstention_reason == "auxiliary_observation_only"
    assert result.transliteration_performed is False
    assert result.abstain is True


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("\u202e", "prohibited_character"),
        ("\u0915A", "unsupported_script"),
        ("\u0915 \u0916", "unexpected_whitespace"),
    ],
)
def test_invalid_unicode_and_script_output_fail_with_safe_codes(
    value: str, code: str
) -> None:
    with pytest.raises(NormalizationViolation) as failure:
        normalize_ephemeral_hypothesis(
            _devanagari(value),
            segmenter=ClosedTestSegmenter(),
        )
    assert failure.value.code == code
    assert value not in str(failure.value)


def test_grapheme_runtime_and_resource_limits_fail_closed() -> None:
    with pytest.raises(NormalizationViolation) as wrong_runtime:
        segment_generated_reference(
            "SYN-A1B2-C3D4",
            "latin",
            segmenter=WrongVersionSegmenter(),
        )
    assert wrong_runtime.value.code == "grapheme_runtime_version_mismatch"

    with pytest.raises(NormalizationViolation) as too_many:
        segment_generated_reference(
            "ABCDEFGHIJKLMNOPQ",
            "latin",
            segmenter=ClosedTestSegmenter(),
        )
    assert too_many.value.code == "grapheme_limit_exceeded"

    with pytest.raises(NormalizationViolation) as too_long:
        segment_generated_reference(
            "A" * 33,
            "latin",
            segmenter=ClosedTestSegmenter(),
        )
    assert too_long.value.code == "output_too_long"


def test_repository_runtime_does_not_silently_replace_exact_regex_runtime() -> None:
    with pytest.raises(NormalizationViolation) as failure:
        ExactRegexGraphemeSegmenter()
    assert failure.value.code in {
        "grapheme_runtime_unavailable",
        "grapheme_runtime_version_mismatch",
    }


def test_codepoint_and_grapheme_metrics_are_reported_separately() -> None:
    result = normalize_ephemeral_hypothesis(
        _devanagari("\u0958"),
        segmenter=ClosedTestSegmenter(),
    )
    metrics = measure_generated_normalization(
        "\u0915\u093c",
        result,
        segmenter=ClosedTestSegmenter(),
    )

    assert metrics.reference_scalar_count == 2
    assert metrics.reference_grapheme_count == 1
    assert metrics.observed_scalar_count == 2
    assert metrics.observed_grapheme_count == 1
    assert metrics.code_point_edit_distance == 0
    assert metrics.grapheme_edit_distance == 0
    assert sequence_edit_distance(("a", "b"), ("a", "c", "b")) == 1


def _calibration(candidate_id: str):
    return tuple(
        EphemeralCalibrationObservationV1(
            candidate_id=candidate_id,
            split="development" if index < 5 else "validation",
            raw_confidence=0.05 + index * 0.1,
            correct=index % 2 == 0,
        )
        for index in range(10)
    )


def test_calibration_is_candidate_local_complete_and_threshold_free() -> None:
    evaluation = evaluate_generated_calibration(_calibration("OCR-L0"))

    assert evaluation.candidate_id == "OCR-L0"
    assert evaluation.sample_count == 10
    assert evaluation.correct_count == 5
    assert len(evaluation.bins) == 5
    assert sum(item.sample_count for item in evaluation.bins) == 10
    assert evaluation.quality_threshold_approved is False
    assert evaluation.promotion_authorized is False
    assert 0 <= evaluation.expected_calibration_error <= 1
    assert 0 <= evaluation.brier_score <= 1

    mixed = (*_calibration("OCR-L0")[:1], *_calibration("OCR-L1")[:1])
    with pytest.raises(ValueError, match="candidate-local"):
        evaluate_generated_calibration(mixed)
    with pytest.raises(ValueError, match="requires generated observations"):
        evaluate_generated_calibration(())

    sparse = tuple(
        EphemeralCalibrationObservationV1(
            candidate_id="OCR-L0",
            split="development",
            raw_confidence=0.1,
            correct=True,
        )
        for _ in range(2)
    )
    sparse_result = evaluate_generated_calibration(sparse)
    assert sum(item.sample_count == 0 for item in sparse_result.bins) == 4

    non_finite = EphemeralCalibrationObservationV1.model_construct(
        candidate_id="OCR-L0",
        split="development",
        raw_confidence=float("nan"),
        correct=False,
        synthetic_only=True,
        retained=False,
    )
    with pytest.raises(ValueError, match="finite"):
        evaluate_generated_calibration((non_finite,))


def test_ephemeral_normalization_cannot_enter_canonical_evidence() -> None:
    result = normalize_ephemeral_hypothesis(
        _latin("SYN-A1B2-C3D4"),
        segmenter=ClosedTestSegmenter(),
    )

    with pytest.raises(AnprBoundaryViolation) as direct:
        canonical_anpr_evidence_json(result)
    assert direct.value.code == "plate_text_persistence_prohibited"

    for field in (
        "nfc_value",
        "normalized_display_candidate",
        "graphemes",
        "raw_hypothesis_digest",
    ):
        with pytest.raises(AnprBoundaryViolation) as nested:
            canonical_anpr_evidence_json({"aggregate": {field: "must-not-echo"}})
        assert nested.value.code == "plate_text_persistence_prohibited"
        assert "must-not-echo" not in str(nested.value)


def test_contract_rejects_cross_script_candidate_and_non_abstention() -> None:
    result = normalize_ephemeral_hypothesis(
        _latin("SYN-A1B2-C3D4"),
        segmenter=ClosedTestSegmenter(),
    )
    document = result.model_dump(mode="json")
    document["script_lane"] = "devanagari"
    with pytest.raises(ValidationError):
        EphemeralPlateNormalizationV1.model_validate(document)

    document = result.model_dump(mode="json")
    document["abstain"] = False
    with pytest.raises(ValidationError):
        EphemeralPlateNormalizationV1.model_validate(document)


class FakeRegex:
    __version__ = ANPR_PINNED_REGEX_VERSION
    VERSION1 = object()

    @staticmethod
    def findall(_pattern: str, value: str, _flags: object) -> list[str]:
        return list(value)


def _pin_test_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(normalization_module.sys, "version_info", (3, 12, 13))
    monkeypatch.setattr(
        normalization_module.unicodedata,
        "unidata_version",
        ANPR_PINNED_UNICODE_VERSION,
    )


def test_exact_regex_adapter_version_import_and_segmentation_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _pin_test_runtime(monkeypatch)
    monkeypatch.setattr(
        normalization_module.importlib,
        "import_module",
        lambda _name: FakeRegex(),
    )
    adapter = ExactRegexGraphemeSegmenter()
    assert adapter.segment("ABC") == ("A", "B", "C")

    class ExplodingRegex(FakeRegex):
        @staticmethod
        def findall(_pattern: str, _value: str, _flags: object) -> list[str]:
            raise RuntimeError("bounded")

    monkeypatch.setattr(
        normalization_module.importlib,
        "import_module",
        lambda _name: ExplodingRegex(),
    )
    with pytest.raises(NormalizationViolation) as invalid:
        ExactRegexGraphemeSegmenter().segment("ABC")
    assert invalid.value.code == "invalid_unicode"

    class EmptyRegex(FakeRegex):
        @staticmethod
        def findall(_pattern: str, _value: str, _flags: object) -> list[str]:
            return []

    monkeypatch.setattr(
        normalization_module.importlib,
        "import_module",
        lambda _name: EmptyRegex(),
    )
    with pytest.raises(NormalizationViolation) as empty:
        ExactRegexGraphemeSegmenter().segment("ABC")
    assert empty.value.code == "invalid_unicode"


def test_exact_regex_adapter_rejects_unicode_package_and_import_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(normalization_module.sys, "version_info", (3, 12, 13))
    monkeypatch.setattr(normalization_module.unicodedata, "unidata_version", "0.0.0")
    with pytest.raises(NormalizationViolation) as unicode_drift:
        ExactRegexGraphemeSegmenter()
    assert unicode_drift.value.code == "grapheme_runtime_version_mismatch"

    _pin_test_runtime(monkeypatch)

    def unavailable(_name: str):
        raise ImportError("missing")

    monkeypatch.setattr(normalization_module.importlib, "import_module", unavailable)
    with pytest.raises(NormalizationViolation) as missing:
        ExactRegexGraphemeSegmenter()
    assert missing.value.code == "grapheme_runtime_unavailable"

    class WrongRegex(FakeRegex):
        __version__ = "0.0.0"

    monkeypatch.setattr(
        normalization_module.importlib,
        "import_module",
        lambda _name: WrongRegex(),
    )
    with pytest.raises(NormalizationViolation) as package_drift:
        ExactRegexGraphemeSegmenter()
    assert package_drift.value.code == "grapheme_runtime_version_mismatch"


def test_defensive_unreachable_contract_paths_still_fail_closed() -> None:
    with pytest.raises(NormalizationViolation) as empty:
        segment_generated_reference("", "latin", segmenter=ClosedTestSegmenter())
    assert empty.value.code == "invalid_hypothesis"

    with pytest.raises(NormalizationViolation) as surrogate:
        segment_generated_reference("\ud800", "latin", segmenter=ClosedTestSegmenter())
    assert surrogate.value.code == "invalid_unicode"

    with pytest.raises(NormalizationViolation) as wrong_type:
        normalize_ephemeral_hypothesis(object(), segmenter=ClosedTestSegmenter())  # type: ignore[arg-type]
    assert wrong_type.value.code == "invalid_hypothesis"

    valid = _latin("SYN-A1B2-C3D4")
    invalid_lineage = EphemeralLatinOcrHypothesisV1.model_construct(
        **{**valid.model_dump(), "source_id": "untrusted"}
    )
    with pytest.raises(NormalizationViolation) as lineage:
        normalize_ephemeral_hypothesis(
            invalid_lineage,
            segmenter=ClosedTestSegmenter(),
        )
    assert lineage.value.code == "invalid_hypothesis"

    expanded = EphemeralAuxiliaryOcrHypothesisV1.model_construct(
        **{**_devanagari("\u0958").model_dump(), "raw_text": "\u0958" * 17}
    )
    with pytest.raises(NormalizationViolation) as expanded_output:
        normalize_ephemeral_hypothesis(expanded, segmenter=ClosedTestSegmenter())
    assert expanded_output.value.code == "output_too_long"

    too_many_clusters = EphemeralLatinOcrHypothesisV1.model_construct(
        **{**valid.model_dump(), "raw_text": "A" * 17}
    )
    with pytest.raises(NormalizationViolation) as clusters:
        normalize_ephemeral_hypothesis(
            too_many_clusters,
            segmenter=ClosedTestSegmenter(),
        )
    assert clusters.value.code == "grapheme_limit_exceeded"
