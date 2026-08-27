from __future__ import annotations

import hashlib
import json
import math
import time
import unicodedata
from collections import Counter
from dataclasses import dataclass
from numbers import Real
from typing import Protocol

from hcam.analytics.anpr.contracts import (
    ANPR_AUXILIARY_GENERATOR_VERSION,
    ANPR_AUXILIARY_RENDERER_VERSION,
    ANPR_GENERATED_SOURCE_ID,
    FONT_D0_ARTIFACT_SHA256,
    FONT_G0_ARTIFACT_SHA256,
    MAX_ANPR_CROP_HEIGHT,
    MAX_ANPR_CROP_WIDTH,
    MAX_ANPR_LOCAL_SAMPLES,
    AuxiliaryDegradation,
    AuxiliaryFailureCountsV1,
    AuxiliaryFontCandidate,
    AuxiliaryFontRenderingEvaluationV1,
    AuxiliaryFontRenderingSliceV1,
    AuxiliaryGeneratedSliceV1,
    AuxiliaryScript,
    DevanagariOcrCandidateEvaluationV1,
    EphemeralAuxiliaryOcrHypothesisV1,
    LatinOcrDistributionV1,
    SyntheticAnprExecutionPolicyV1,
)


AuxiliaryFailureCode = (
    "engine_error",
    "invalid_confidence",
    "invalid_output",
    "malformed_result",
    "no_result",
    "output_too_long",
    "unexpected_whitespace",
    "unsupported_script",
)

_BYTES_PER_PIXEL = 3
_DEGRADATIONS: tuple[AuxiliaryDegradation, ...] = (
    "clean",
    "low_contrast",
    "downscaled",
)

# This closed repository-owned vocabulary intentionally contains only standalone
# letters and digits. The exact runtime lacks HarfBuzz/RAQM, so combining marks,
# conjuncts, arbitrary text, and complex shaping stay fail-closed.
_VOCABULARY: dict[AuxiliaryScript, tuple[str, ...]] = {
    "devanagari": (
        "\u0905\u0915\u092e\u0967",
        "\u0906\u0916\u092f\u0968",
        "\u0907\u0917\u0930\u0969",
        "\u0908\u0918\u0932\u096a",
        "\u0909\u091a\u0935\u096b",
        "\u090a\u091b\u0936\u096c",
        "\u090f\u091c\u0938\u096d",
        "\u0910\u091f\u0939\u096e",
        "\u0913\u0924\u0928\u096f",
        "\u0914\u0926\u092a\u0966",
        "\u090b\u092c\u092d\u0967",
        "\u0915\u0921\u092e\u0968",
    ),
    "gujarati": (
        "\u0a85\u0a95\u0aae\u0ae7",
        "\u0a86\u0a96\u0aaf\u0ae8",
        "\u0a87\u0a97\u0ab0\u0ae9",
        "\u0a88\u0a98\u0ab2\u0aea",
        "\u0a89\u0a9a\u0ab5\u0aeb",
        "\u0a8a\u0a9b\u0ab6\u0aec",
        "\u0a8f\u0a9c\u0ab8\u0aed",
        "\u0a90\u0a9f\u0ab9\u0aee",
        "\u0a93\u0aa4\u0aa8\u0aef",
        "\u0a94\u0aa6\u0aaa\u0ae6",
        "\u0a8b\u0aac\u0aad\u0ae7",
        "\u0a95\u0aa1\u0aae\u0ae8",
    ),
}
_ALLOWED_CHARACTERS = {
    script: frozenset("".join(values)) for script, values in _VOCABULARY.items()
}
_FONT_PROFILES = {
    "FONT-D0": (
        "FONT-D0-NOTO-SANS-DEVANAGARI-VARIABLE-PROPOSED",
        FONT_D0_ARTIFACT_SHA256,
        "devanagari",
        "Noto Sans Devanagari",
    ),
    "FONT-G0": (
        "FONT-G0-NOTO-SANS-GUJARATI-VARIABLE-PROPOSED",
        FONT_G0_ARTIFACT_SHA256,
        "gujarati",
        "Noto Sans Gujarati",
    ),
}


class AuxiliaryAnprViolation(ValueError):
    """Bounded W6 failure that cannot expose generated or recognized text."""

    def __init__(self, code: str) -> None:
        if code not in AuxiliaryFailureCode:
            code = "malformed_result"
        super().__init__(f"P3.5 auxiliary lane failed: {code}")
        self.code = code


@dataclass(frozen=True, slots=True)
class EphemeralAuxiliarySampleV1:
    sample_id: str
    script: AuxiliaryScript
    degradation: AuxiliaryDegradation
    text: str
    source_id: str = ANPR_GENERATED_SOURCE_ID
    generator_version: str = ANPR_AUXILIARY_GENERATOR_VERSION
    synthetic_only: bool = True

    def __post_init__(self) -> None:
        vocabulary = _VOCABULARY.get(self.script)
        if (
            vocabulary is None
            or self.source_id != ANPR_GENERATED_SOURCE_ID
            or self.generator_version != ANPR_AUXILIARY_GENERATOR_VERSION
            or self.synthetic_only is not True
            or self.text not in vocabulary
            or not self.sample_id.startswith("anprauxsample_")
        ):
            raise AuxiliaryAnprViolation("invalid_output")


@dataclass(frozen=True, slots=True)
class RawRenderedAuxiliaryPixelsV1:
    width: int
    height: int
    bgr_bytes: bytes


@dataclass(frozen=True, slots=True)
class GeneratedAuxiliaryCropV1:
    width: int
    height: int
    bgr_bytes: bytes
    sample: EphemeralAuxiliarySampleV1
    region_id: str
    font_candidate_id: AuxiliaryFontCandidate
    font_artifact_sha256: str
    font_family: str
    renderer_version: str = ANPR_AUXILIARY_RENDERER_VERSION

    def __post_init__(self) -> None:
        expected = _FONT_PROFILES.get(self.font_candidate_id)
        if expected is None or not (
            1 <= self.width <= MAX_ANPR_CROP_WIDTH
            and 1 <= self.height <= MAX_ANPR_CROP_HEIGHT
            and len(self.bgr_bytes) == self.width * self.height * _BYTES_PER_PIXEL
            and self.renderer_version == ANPR_AUXILIARY_RENDERER_VERSION
            and self.font_artifact_sha256 == expected[1]
            and self.sample.script == expected[2]
            and self.font_family == expected[3]
            and self.region_id.startswith("anprauxregion_")
        ):
            raise AuxiliaryAnprViolation("invalid_output")


@dataclass(frozen=True, slots=True)
class RawAuxiliaryOcrEngineResultV1:
    raw_text: object
    raw_confidence: object


class AuxiliaryFontRenderer(Protocol):
    candidate_id: AuxiliaryFontCandidate
    artifact_sha256: str
    font_family: str
    shaping_backend: str

    def render(
        self, sample: EphemeralAuxiliarySampleV1
    ) -> RawRenderedAuxiliaryPixelsV1: ...


class DevanagariOcrEngine(Protocol):
    candidate_id: str
    extracted_inventory_sha256: str

    def recognize(
        self, crop: GeneratedAuxiliaryCropV1
    ) -> RawAuxiliaryOcrEngineResultV1: ...


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _identifier(prefix: str, domain: str, value: object) -> str:
    digest = hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical_bytes(value))
    return f"{prefix}_{digest.hexdigest()[:32]}"


def _validate_policy(policy: SyntheticAnprExecutionPolicyV1) -> None:
    if (
        policy.enabled is not True
        or policy.environment == "production"
        or policy.execution_scope != "generated_only"
        or policy.input_mode != "deterministic_seed_only"
        or policy.network_access != "denied"
        or policy.artifact_download != "denied"
        or policy.plate_text_persistence != "denied"
        or policy.arbitrary_input != "denied"
    ):
        raise AuxiliaryAnprViolation("invalid_output")


def derive_ephemeral_auxiliary_sample(
    script: AuxiliaryScript,
    sample_index: int,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> EphemeralAuxiliarySampleV1:
    _validate_policy(policy)
    vocabulary = _VOCABULARY.get(script)
    if vocabulary is None:
        raise ValueError("unsupported auxiliary script")
    if not 0 <= sample_index < min(len(vocabulary), MAX_ANPR_LOCAL_SAMPLES):
        raise ValueError("auxiliary sample index is outside the closed vocabulary")
    material = {
        "generator_version": ANPR_AUXILIARY_GENERATOR_VERSION,
        "sample_index": sample_index,
        "script": script,
    }
    return EphemeralAuxiliarySampleV1(
        sample_id=_identifier(
            "anprauxsample",
            "hcam.anpr.p35w6.auxiliary-sample.v1",
            material,
        ),
        script=script,
        degradation=_DEGRADATIONS[sample_index % len(_DEGRADATIONS)],
        text=vocabulary[sample_index],
    )


def render_generated_auxiliary_crop(
    renderer: AuxiliaryFontRenderer,
    script: AuxiliaryScript,
    sample_index: int,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> GeneratedAuxiliaryCropV1:
    if script not in _VOCABULARY:
        raise AuxiliaryAnprViolation("unsupported_script")
    sample = derive_ephemeral_auxiliary_sample(
        script,
        sample_index,
        policy=policy,
    )
    expected_candidate: AuxiliaryFontCandidate = (
        "FONT-D0" if script == "devanagari" else "FONT-G0"
    )
    expected = _FONT_PROFILES[expected_candidate]
    if (
        renderer.candidate_id != expected_candidate
        or renderer.artifact_sha256 != expected[1]
        or renderer.font_family != expected[3]
        or renderer.shaping_backend != "basic_freetype_no_raqm"
    ):
        raise AuxiliaryAnprViolation("invalid_output")
    try:
        rendered = renderer.render(sample)
    except AuxiliaryAnprViolation:
        raise
    except Exception as exc:
        raise AuxiliaryAnprViolation("engine_error") from exc
    if not isinstance(rendered, RawRenderedAuxiliaryPixelsV1):
        raise AuxiliaryAnprViolation("malformed_result")
    return GeneratedAuxiliaryCropV1(
        width=rendered.width,
        height=rendered.height,
        bgr_bytes=rendered.bgr_bytes,
        sample=sample,
        region_id=_identifier(
            "anprauxregion",
            "hcam.anpr.p35w6.auxiliary-region.v1",
            {
                "font_candidate_id": renderer.candidate_id,
                "sample_id": sample.sample_id,
            },
        ),
        font_candidate_id=renderer.candidate_id,
        font_artifact_sha256=renderer.artifact_sha256,
        font_family=renderer.font_family,
    )


def _validate_devanagari_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise AuxiliaryAnprViolation("invalid_output")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise AuxiliaryAnprViolation("invalid_output") from exc
    if len(value) > 16:
        raise AuxiliaryAnprViolation("output_too_long")
    if any(character.isspace() for character in value):
        raise AuxiliaryAnprViolation("unexpected_whitespace")
    if any(
        character not in _ALLOWED_CHARACTERS["devanagari"]
        or unicodedata.combining(character)
        or unicodedata.category(character).startswith("C")
        for character in value
    ):
        raise AuxiliaryAnprViolation("unsupported_script")
    return value


def _validate_confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise AuxiliaryAnprViolation("invalid_confidence")
    confidence = float(value)
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise AuxiliaryAnprViolation("invalid_confidence")
    return confidence


def build_ephemeral_devanagari_hypothesis(
    crop: GeneratedAuxiliaryCropV1,
    *,
    engine_result: RawAuxiliaryOcrEngineResultV1,
    latency_ms: float,
) -> EphemeralAuxiliaryOcrHypothesisV1:
    if crop.sample.script != "devanagari" or crop.font_candidate_id != "FONT-D0":
        raise AuxiliaryAnprViolation("unsupported_script")
    if engine_result.raw_text is None and engine_result.raw_confidence is None:
        raise AuxiliaryAnprViolation("no_result")
    raw_text = _validate_devanagari_text(engine_result.raw_text)
    raw_confidence = _validate_confidence(engine_result.raw_confidence)
    if (
        not isinstance(latency_ms, Real)
        or not math.isfinite(float(latency_ms))
        or not 0 <= float(latency_ms) <= 600_000
    ):
        raise AuxiliaryAnprViolation("malformed_result")
    return EphemeralAuxiliaryOcrHypothesisV1(
        result_id=_identifier(
            "anprauxocr",
            "hcam.anpr.p35w6.devanagari-ocr-result.v1",
            {"candidate_id": "OCR-D0", "sample_id": crop.sample.sample_id},
        ),
        region_id=crop.region_id,
        sample_id=crop.sample.sample_id,
        raw_text=raw_text,
        raw_confidence=raw_confidence,
        latency_ms=float(latency_ms),
    )


def _edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def _distribution(values: list[float]) -> LatinOcrDistributionV1:
    if not values:
        raise ValueError("distribution requires at least one value")
    ordered = sorted(float(value) for value in values)

    def percentile(fraction: float) -> float:
        return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]

    return LatinOcrDistributionV1(
        minimum=round(ordered[0], 6),
        p50=round(percentile(0.50), 6),
        p95=round(percentile(0.95), 6),
        maximum=round(ordered[-1], 6),
        mean=round(sum(ordered) / len(ordered), 6),
    )


def _failure_counts(counter: Counter[str]) -> AuxiliaryFailureCountsV1:
    return AuxiliaryFailureCountsV1(
        **{name: counter[name] for name in AuxiliaryFailureCode}
    )


def evaluate_generated_auxiliary_font(
    renderer: AuxiliaryFontRenderer,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
    sample_count: int,
    replay_runs: int = 20,
    ocr_execution_performed: bool,
) -> AuxiliaryFontRenderingEvaluationV1:
    if renderer.candidate_id not in _FONT_PROFILES:
        raise ValueError("only exact W6 fonts are authorized")
    if replay_runs != 20:
        raise ValueError("P3.5 W6 font replay requires exactly 20 runs")
    if not 1 <= sample_count <= len(_VOCABULARY[_FONT_PROFILES[renderer.candidate_id][2]]):
        raise ValueError("font-rendering sample count is outside the closed vocabulary")
    expected = _FONT_PROFILES[renderer.candidate_id]
    script: AuxiliaryScript = expected[2]
    totals = {
        degradation: {"sample": 0, "success": 0}
        for degradation in _DEGRADATIONS
    }
    succeeded = 0
    for sample_index in range(sample_count):
        sample = derive_ephemeral_auxiliary_sample(script, sample_index, policy=policy)
        totals[sample.degradation]["sample"] += 1
        try:
            render_generated_auxiliary_crop(
                renderer,
                script,
                sample_index,
                policy=policy,
            )
        except AuxiliaryAnprViolation:
            continue
        succeeded += 1
        totals[sample.degradation]["success"] += 1

    replay = [
        render_generated_auxiliary_crop(renderer, script, 0, policy=policy)
        for _ in range(replay_runs)
    ]
    first = replay[0]
    replay_deterministic = all(
        item.width == first.width
        and item.height == first.height
        and item.bgr_bytes == first.bgr_bytes
        for item in replay[1:]
    )
    return AuxiliaryFontRenderingEvaluationV1(
        candidate_id=renderer.candidate_id,
        artifact_id=expected[0],
        artifact_sha256=expected[1],
        script_lane=script,
        font_family=expected[3],
        sample_count=sample_count,
        generated_grapheme_count=sample_count * 4,
        succeeded=succeeded,
        failed=sample_count - succeeded,
        slices=tuple(
            AuxiliaryFontRenderingSliceV1(
                degradation=degradation,
                sample_count=values["sample"],
                succeeded=values["success"],
                failed=values["sample"] - values["success"],
            )
            for degradation, values in totals.items()
        ),
        replay_pixels_deterministic=replay_deterministic,
        ocr_execution_performed=ocr_execution_performed,
    )


def evaluate_generated_devanagari_candidate(
    renderer: AuxiliaryFontRenderer,
    engine: DevanagariOcrEngine,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
    sample_count: int,
    replay_runs: int = 20,
    network_attempt_count: int = 0,
) -> DevanagariOcrCandidateEvaluationV1:
    if engine.candidate_id != "OCR-D0":
        raise ValueError("only exact OCR-D0 is authorized for W6")
    if replay_runs != 20:
        raise ValueError("P3.5 W6 OCR replay requires exactly 20 runs")
    if not 1 <= sample_count <= len(_VOCABULARY["devanagari"]):
        raise ValueError("Devanagari sample count is outside the closed vocabulary")
    failures: Counter[str] = Counter()
    slice_failures = {degradation: Counter() for degradation in _DEGRADATIONS}
    totals = {
        degradation: {
            "sample": 0,
            "success": 0,
            "exact": 0,
            "reference": 0,
            "grapheme": 0,
            "edit": 0,
        }
        for degradation in _DEGRADATIONS
    }
    confidences: list[float] = []
    latencies: list[float] = []
    succeeded = 0
    exact_matches = 0
    reference_scalar_count = 0
    raw_edit_distance = 0

    for sample_index in range(sample_count):
        sample = derive_ephemeral_auxiliary_sample(
            "devanagari", sample_index, policy=policy
        )
        aggregate = totals[sample.degradation]
        aggregate["sample"] += 1
        aggregate["reference"] += len(sample.text)
        aggregate["grapheme"] += len(sample.text)
        reference_scalar_count += len(sample.text)
        started = time.perf_counter_ns()
        try:
            crop = render_generated_auxiliary_crop(
                renderer,
                "devanagari",
                sample_index,
                policy=policy,
            )
            raw_result = engine.recognize(crop)
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            hypothesis = build_ephemeral_devanagari_hypothesis(
                crop,
                engine_result=raw_result,
                latency_ms=elapsed_ms,
            )
        except AuxiliaryAnprViolation as exc:
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            failures[exc.code] += 1
            slice_failures[sample.degradation][exc.code] += 1
            raw_edit_distance += len(sample.text)
            aggregate["edit"] += len(sample.text)
        except Exception:
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            failures["engine_error"] += 1
            slice_failures[sample.degradation]["engine_error"] += 1
            raw_edit_distance += len(sample.text)
            aggregate["edit"] += len(sample.text)
        else:
            succeeded += 1
            aggregate["success"] += 1
            distance = _edit_distance(sample.text, hypothesis.raw_text)
            raw_edit_distance += distance
            aggregate["edit"] += distance
            if sample.text == hypothesis.raw_text:
                exact_matches += 1
                aggregate["exact"] += 1
            confidences.append(hypothesis.raw_confidence)
        latencies.append(elapsed_ms)

    replay_crop = render_generated_auxiliary_crop(
        renderer,
        "devanagari",
        0,
        policy=policy,
    )
    replay_observations: list[tuple[str, str | float]] = []
    for _ in range(replay_runs):
        started = time.perf_counter_ns()
        try:
            raw_result = engine.recognize(replay_crop)
            hypothesis = build_ephemeral_devanagari_hypothesis(
                replay_crop,
                engine_result=raw_result,
                latency_ms=(time.perf_counter_ns() - started) / 1_000_000,
            )
        except AuxiliaryAnprViolation as exc:
            replay_observations.append(("failure", exc.code))
        except Exception:
            replay_observations.append(("failure", "engine_error"))
        else:
            replay_observations.append(
                (hypothesis.raw_text, round(hypothesis.raw_confidence, 8))
            )

    return DevanagariOcrCandidateEvaluationV1(
        extracted_inventory_sha256=engine.extracted_inventory_sha256,
        sample_count=sample_count,
        succeeded=succeeded,
        failed=sample_count - succeeded,
        exact_matches=exact_matches,
        reference_scalar_count=reference_scalar_count,
        reference_grapheme_count=reference_scalar_count,
        raw_edit_distance=raw_edit_distance,
        failure_counts=_failure_counts(failures),
        slices=tuple(
            AuxiliaryGeneratedSliceV1(
                degradation=degradation,
                sample_count=values["sample"],
                succeeded=values["success"],
                failed=values["sample"] - values["success"],
                exact_matches=values["exact"],
                reference_scalar_count=values["reference"],
                reference_grapheme_count=values["grapheme"],
                raw_edit_distance=values["edit"],
                failure_counts=_failure_counts(slice_failures[degradation]),
            )
            for degradation, values in totals.items()
        ),
        confidence_distribution=_distribution(confidences) if confidences else None,
        latency_ms_distribution=_distribution(latencies),
        replay_output_deterministic=len(set(replay_observations)) == 1,
        network_attempt_count=network_attempt_count,
    )


def auxiliary_vocabulary_size(script: AuxiliaryScript) -> int:
    return len(_VOCABULARY[script])
