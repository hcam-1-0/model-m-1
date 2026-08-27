from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass
from typing import Literal, Protocol, cast

from hcam.analytics.anpr.contracts import (
    ANPR_GENERATED_SOURCE_ID,
    ANPR_PINNED_PYTHON_VERSION,
    ANPR_PINNED_REGEX_VERSION,
    ANPR_PINNED_UNICODE_VERSION,
    ANPR_TOKEN_PATTERN,
    CandidateCalibrationEvaluationV1,
    CalibrationBinV1,
    EphemeralAuxiliaryOcrHypothesisV1,
    EphemeralCalibrationObservationV1,
    EphemeralLatinOcrHypothesisV1,
    EphemeralPlateNormalizationV1,
    NormalizationCandidate,
    NormalizationScript,
)


NormalizationViolationCode = Literal[
    "grapheme_limit_exceeded",
    "grapheme_runtime_unavailable",
    "grapheme_runtime_version_mismatch",
    "invalid_hypothesis",
    "invalid_unicode",
    "output_too_long",
    "prohibited_character",
    "script_mismatch",
    "unexpected_whitespace",
    "unsupported_script",
]
GeneratedReferenceScript = Literal["latin", "devanagari", "gujarati"]

_TOKEN_PATTERN = re.compile(ANPR_TOKEN_PATTERN, flags=re.ASCII)
_PROHIBITED_BIDI = frozenset({"LRE", "LRO", "RLE", "RLO", "PDF", "LRI", "RLI", "FSI", "PDI"})


class NormalizationViolation(ValueError):
    """Fail-closed W7 error whose message cannot expose recognized text."""

    def __init__(self, code: NormalizationViolationCode) -> None:
        super().__init__(f"P3.5 normalization failed: {code}")
        self.code = code


class GraphemeSegmenter(Protocol):
    regex_version: str
    unicode_version: str

    def segment(self, value: str) -> tuple[str, ...]: ...


class ExactRegexGraphemeSegmenter:
    """Lazy adapter for the exact reviewed external W7 runtime."""

    regex_version = ANPR_PINNED_REGEX_VERSION
    unicode_version = ANPR_PINNED_UNICODE_VERSION

    def __init__(self) -> None:
        if ".".join(str(value) for value in sys.version_info[:3]) != ANPR_PINNED_PYTHON_VERSION:
            raise NormalizationViolation("grapheme_runtime_version_mismatch")
        if unicodedata.unidata_version != ANPR_PINNED_UNICODE_VERSION:
            raise NormalizationViolation("grapheme_runtime_version_mismatch")
        try:
            module = importlib.import_module("regex")
        except ImportError as exc:
            raise NormalizationViolation("grapheme_runtime_unavailable") from exc
        if getattr(module, "__version__", None) != ANPR_PINNED_REGEX_VERSION:
            raise NormalizationViolation("grapheme_runtime_version_mismatch")
        self._module = module

    def segment(self, value: str) -> tuple[str, ...]:
        try:
            clusters = tuple(
                cast(
                    list[str],
                    self._module.findall(r"\X", value, self._module.VERSION1),
                )
            )
        except Exception as exc:
            raise NormalizationViolation("invalid_unicode") from exc
        if not clusters or "".join(clusters) != value:
            raise NormalizationViolation("invalid_unicode")
        return clusters


@dataclass(frozen=True, slots=True)
class GeneratedTextMetricsV1:
    reference_scalar_count: int
    reference_grapheme_count: int
    observed_scalar_count: int
    observed_grapheme_count: int
    code_point_edit_distance: int
    grapheme_edit_distance: int


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _hypothesis_digest(
    hypothesis: EphemeralLatinOcrHypothesisV1 | EphemeralAuxiliaryOcrHypothesisV1,
) -> str:
    digest = hashlib.sha256(
        b"hcam.anpr.p35w7.raw-hypothesis.v1\0"
        + _canonical_bytes(
            {
                "candidate_id": hypothesis.candidate_id,
                "raw_confidence": hypothesis.raw_confidence,
                "raw_text": hypothesis.raw_text,
                "result_id": hypothesis.result_id,
            }
        )
    ).hexdigest()
    return f"sha256:{digest}"


def _validate_segmenter(segmenter: GraphemeSegmenter) -> None:
    if (
        segmenter.regex_version != ANPR_PINNED_REGEX_VERSION
        or segmenter.unicode_version != ANPR_PINNED_UNICODE_VERSION
    ):
        raise NormalizationViolation("grapheme_runtime_version_mismatch")


def _character_allowed(character: str, script: GeneratedReferenceScript) -> bool:
    if script == "latin":
        return character == "-" or character.isascii() and character.isalnum()
    codepoint = ord(character)
    expected_range = (0x0900, 0x097F) if script == "devanagari" else (0x0A80, 0x0AFF)
    return expected_range[0] <= codepoint <= expected_range[1] and unicodedata.category(
        character
    )[0] in {"L", "M", "N"}


def _validate_text(value: str, script: GeneratedReferenceScript) -> None:
    if not isinstance(value, str) or not value:
        raise NormalizationViolation("invalid_hypothesis")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise NormalizationViolation("invalid_unicode") from exc
    if len(value) > 32:
        raise NormalizationViolation("output_too_long")
    if any(character.isspace() for character in value):
        raise NormalizationViolation("unexpected_whitespace")
    for character in value:
        category = unicodedata.category(character)
        if (
            category in {"Cc", "Cf", "Cn", "Cs"}
            or unicodedata.bidirectional(character) in _PROHIBITED_BIDI
        ):
            raise NormalizationViolation("prohibited_character")
        if not _character_allowed(character, script):
            raise NormalizationViolation("unsupported_script")


def segment_generated_reference(
    value: str,
    script: GeneratedReferenceScript,
    *,
    segmenter: GraphemeSegmenter,
) -> tuple[str, ...]:
    """Segment a code-defined generated reference; no external input path calls this."""

    _validate_segmenter(segmenter)
    _validate_text(value, script)
    nfc_value = unicodedata.normalize("NFC", value)
    clusters = segmenter.segment(nfc_value)
    if len(clusters) > 16:
        raise NormalizationViolation("grapheme_limit_exceeded")
    return clusters


def _script_for_hypothesis(
    hypothesis: EphemeralLatinOcrHypothesisV1 | EphemeralAuxiliaryOcrHypothesisV1,
) -> tuple[NormalizationCandidate, NormalizationScript]:
    if isinstance(hypothesis, EphemeralLatinOcrHypothesisV1):
        return hypothesis.candidate_id, "latin"
    if isinstance(hypothesis, EphemeralAuxiliaryOcrHypothesisV1):
        return "OCR-D0", "devanagari"
    raise NormalizationViolation("invalid_hypothesis")


def normalize_ephemeral_hypothesis(
    hypothesis: EphemeralLatinOcrHypothesisV1 | EphemeralAuxiliaryOcrHypothesisV1,
    *,
    segmenter: GraphemeSegmenter,
) -> EphemeralPlateNormalizationV1:
    """Derive an ephemeral candidate without mutating, correcting, or accepting it."""

    candidate_id, script = _script_for_hypothesis(hypothesis)
    if hypothesis.source_id != ANPR_GENERATED_SOURCE_ID or hypothesis.synthetic_only is not True:
        raise NormalizationViolation("invalid_hypothesis")
    _validate_segmenter(segmenter)
    raw_text = hypothesis.raw_text
    _validate_text(raw_text, script)
    nfc_value = unicodedata.normalize("NFC", raw_text)
    if len(nfc_value) > 32:
        raise NormalizationViolation("output_too_long")
    graphemes = segmenter.segment(nfc_value)
    if len(graphemes) > 16:
        raise NormalizationViolation("grapheme_limit_exceeded")

    display_candidate = nfc_value.upper() if script == "latin" else nfc_value
    payload = display_candidate.removeprefix("SYN-").replace("-", "")
    synthetic_format = (
        script == "latin"
        and _TOKEN_PATTERN.fullmatch(display_candidate) is not None
        and any(character.isalpha() for character in payload)
        and any(character.isdigit() for character in payload)
    )
    if script == "devanagari":
        format_family = "unrecognized"
        reason = "auxiliary_observation_only"
    elif synthetic_format:
        format_family = "synthetic_non_issuable"
        reason = "quality_threshold_unapproved"
    else:
        format_family = "unrecognized"
        reason = "synthetic_grammar_rejected"
    grammar_outcome = (
        "synthetic_grammar_valid" if synthetic_format else "synthetic_grammar_rejected"
    )
    raw_confidence = float(hypothesis.raw_confidence)
    return EphemeralPlateNormalizationV1(
        candidate_id=candidate_id,
        script_lane=script,
        raw_hypothesis_digest=_hypothesis_digest(hypothesis),
        nfc_value=nfc_value,
        graphemes=graphemes,
        normalized_display_candidate=display_candidate,
        raw_scalar_count=len(raw_text),
        nfc_scalar_count=len(nfc_value),
        grapheme_count=len(graphemes),
        format_family=format_family,
        validation_outcomes=(
            "utf8_valid",
            "unicode_scalar_valid",
            "nfc_derived",
            "graphemes_segmented",
            "allowlist_valid",
            grammar_outcome,
        ),
        nfc_transform_performed=raw_text != nfc_value,
        case_transform_performed=nfc_value != display_candidate,
        raw_confidence=raw_confidence,
        calibrated_confidence=raw_confidence,
        abstention_reason=reason,
    )


def sequence_edit_distance(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_value in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_value in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_value != right_value),
                )
            )
        previous = current
    return previous[-1]


def measure_generated_normalization(
    reference: str,
    observed: EphemeralPlateNormalizationV1,
    *,
    segmenter: GraphemeSegmenter,
) -> GeneratedTextMetricsV1:
    reference_graphemes = segment_generated_reference(
        reference,
        observed.script_lane,
        segmenter=segmenter,
    )
    nfc_reference = unicodedata.normalize("NFC", reference)
    return GeneratedTextMetricsV1(
        reference_scalar_count=len(nfc_reference),
        reference_grapheme_count=len(reference_graphemes),
        observed_scalar_count=len(observed.nfc_value),
        observed_grapheme_count=len(observed.graphemes),
        code_point_edit_distance=sequence_edit_distance(
            tuple(nfc_reference), tuple(observed.nfc_value)
        ),
        grapheme_edit_distance=sequence_edit_distance(
            reference_graphemes, observed.graphemes
        ),
    )


def evaluate_generated_calibration(
    observations: tuple[EphemeralCalibrationObservationV1, ...],
) -> CandidateCalibrationEvaluationV1:
    if not observations:
        raise ValueError("calibration requires generated observations")
    candidate_ids = {item.candidate_id for item in observations}
    if len(candidate_ids) != 1:
        raise ValueError("calibration observations must be candidate-local")
    bins: list[list[EphemeralCalibrationObservationV1]] = [
        [] for _ in range(5)
    ]
    for observation in observations:
        if not math.isfinite(observation.raw_confidence):
            raise ValueError("calibration confidence must be finite")
        bins[min(int(observation.raw_confidence * 5), 4)].append(observation)

    bin_contracts: list[CalibrationBinV1] = []
    weighted_gap = 0.0
    for index, values in enumerate(bins):
        if values:
            mean_confidence = sum(item.raw_confidence for item in values) / len(values)
            correct_count = sum(item.correct for item in values)
            accuracy = correct_count / len(values)
            gap = abs(mean_confidence - accuracy)
            weighted_gap += len(values) * gap
            statistics = {
                "mean_confidence": round(mean_confidence, 6),
                "accuracy": round(accuracy, 6),
                "absolute_calibration_gap": round(gap, 6),
            }
        else:
            correct_count = 0
            statistics = {
                "mean_confidence": None,
                "accuracy": None,
                "absolute_calibration_gap": None,
            }
        bin_contracts.append(
            CalibrationBinV1(
                bin_index=index,
                lower_bound=index / 5,
                upper_bound=(index + 1) / 5,
                sample_count=len(values),
                correct_count=correct_count,
                **statistics,
            )
        )
    brier_score = sum(
        (item.raw_confidence - float(item.correct)) ** 2 for item in observations
    ) / len(observations)
    return CandidateCalibrationEvaluationV1(
        candidate_id=next(iter(candidate_ids)),
        sample_count=len(observations),
        correct_count=sum(item.correct for item in observations),
        bins=tuple(bin_contracts),
        expected_calibration_error=round(weighted_gap / len(observations), 6),
        brier_score=round(brier_score, 6),
    )
