from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter
from dataclasses import dataclass
from numbers import Real
from typing import Literal, Protocol

from hcam.analytics.anpr.contracts import (
    ANPR_GENERATED_SOURCE_ID,
    ANPR_GENERATOR_VERSION,
    ANPR_LATIN_RENDERER_VERSION,
    MAX_ANPR_CROP_HEIGHT,
    MAX_ANPR_CROP_WIDTH,
    MAX_ANPR_LOCAL_SAMPLES,
    OCR_L0_ARTIFACT_SHA256,
    OCR_L1_ARTIFACT_SHA256,
    AnprSplit,
    EphemeralLatinOcrHypothesisV1,
    EphemeralSyntheticTokenV1,
    GeneratedTokenRequestV1,
    LatinOcrCandidate,
    LatinOcrCandidateEvaluationV1,
    LatinOcrDistributionV1,
    LatinOcrFailureCode,
    LatinOcrFailureCountsV1,
    LatinOcrGeneratedSliceV1,
    SyntheticAnprExecutionPolicyV1,
    SyntheticCorpusPlanV1,
)
from hcam.analytics.anpr.generator import (
    derive_generated_request,
    derive_split_manifest_entry,
    generate_ephemeral_token,
)


AnprOcrCode = Literal[
    "engine_error",
    "invalid_confidence",
    "invalid_output",
    "malformed_result",
    "no_result",
    "output_too_long",
    "unexpected_whitespace",
    "unsupported_script",
]

_BYTES_PER_PIXEL = 3
_CANDIDATES = {
    "OCR-L0": {
        "artifact_id": "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
        "artifact_sha256": OCR_L0_ARTIFACT_SHA256,
        "model_name": "PP-OCRv6_small_rec",
    },
    "OCR-L1": {
        "artifact_id": "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED",
        "artifact_sha256": OCR_L1_ARTIFACT_SHA256,
        "model_name": "PP-OCRv6_medium_rec",
    },
}

# A repository-owned bitmap alphabet keeps W5 generated inputs independent of
# system fonts and external text. Each string is a 5x7 row-major glyph.
_GLYPHS = {
    "-": "00000000000000011111000000000000000",
    "0": "01110100011001110101110011000101110",
    "1": "00100011000010000100001000010001110",
    "2": "01110100010000100110010001000011111",
    "3": "11110000010000101110000010000111110",
    "4": "00010001100101010010111110001000010",
    "5": "11111100001111000001000011000101110",
    "6": "00110010001000011110100011000101110",
    "7": "11111000010001000100010000100001000",
    "8": "01110100011000101110100011000101110",
    "9": "01110100011000101111000010001001100",
    "A": "01110100011000111111100011000110001",
    "B": "11110100011000111110100011000111110",
    "C": "01111100001000010000100001000001111",
    "D": "11110100011000110001100011000111110",
    "E": "11111100001000011110100001000011111",
    "F": "11111100001000011110100001000010000",
    "G": "01111100001000010111100011000101111",
    "H": "10001100011000111111100011000110001",
    "I": "01110001000010000100001000010001110",
    "J": "00111000100001000010100101001001100",
    "K": "10001100101010011000101001001010001",
    "L": "10000100001000010000100001000011111",
    "M": "10001110111010110101100011000110001",
    "N": "10001110011010110011100011000110001",
    "O": "01110100011000110001100011000101110",
    "P": "11110100011000111110100001000010000",
    "Q": "01110100011000110001101011001001101",
    "R": "11110100011000111110101001001010001",
    "S": "01111100001000001110000010000111110",
    "T": "11111001000010000100001000010000100",
    "U": "10001100011000110001100011000101110",
    "V": "10001100011000110001100010101000100",
    "W": "10001100011000110101101011010101010",
    "X": "10001100010101000100010101000110001",
    "Y": "10001100010101000100001000010000100",
    "Z": "11111000010001000100010001000011111",
}


class AnprOcrViolation(ValueError):
    """Bounded OCR failure that never includes generated or recognized text."""

    def __init__(self, code: AnprOcrCode) -> None:
        super().__init__(f"P3.5 Latin OCR failed: {code}")
        self.code = code


@dataclass(frozen=True, slots=True)
class RawLatinOcrEngineResultV1:
    raw_text: object
    raw_confidence: object
    alternatives: tuple[tuple[object, object], ...] = ()


@dataclass(frozen=True, slots=True)
class GeneratedLatinOcrCropV1:
    """Generated text and pixels are intentionally confined to process memory."""

    width: int
    height: int
    bgr_bytes: bytes
    sample_id: str
    region_id: str
    request: GeneratedTokenRequestV1
    ephemeral_token: EphemeralSyntheticTokenV1
    layout: Literal["single_line", "two_line"]
    source_id: str = ANPR_GENERATED_SOURCE_ID
    generator_version: str = ANPR_GENERATOR_VERSION
    renderer_version: str = ANPR_LATIN_RENDERER_VERSION

    def __post_init__(self) -> None:
        if not (
            1 <= self.width <= MAX_ANPR_CROP_WIDTH
            and 1 <= self.height <= MAX_ANPR_CROP_HEIGHT
        ):
            raise AnprOcrViolation("invalid_output")
        if len(self.bgr_bytes) != self.width * self.height * _BYTES_PER_PIXEL:
            raise AnprOcrViolation("invalid_output")
        if (
            self.source_id != ANPR_GENERATED_SOURCE_ID
            or self.generator_version != ANPR_GENERATOR_VERSION
            or self.renderer_version != ANPR_LATIN_RENDERER_VERSION
            or self.request.source_id != self.source_id
            or self.request.generator_version != self.generator_version
            or self.request.request_id != self.ephemeral_token.request_id
            or self.request.layout != self.layout
            or self.ephemeral_token.layout != self.layout
            or self.ephemeral_token.script != "latin"
            or self.ephemeral_token.synthetic_only is not True
        ):
            raise AnprOcrViolation("invalid_output")


class LatinOcrEngine(Protocol):
    candidate_id: LatinOcrCandidate
    extracted_inventory_sha256: str

    def recognize(
        self, crop: GeneratedLatinOcrCropV1
    ) -> RawLatinOcrEngineResultV1: ...


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


def _fill_rectangle(
    pixels: bytearray,
    *,
    width: int,
    x: int,
    y: int,
    rectangle_width: int,
    rectangle_height: int,
    color: bytes,
) -> None:
    row = color * rectangle_width
    stride = width * _BYTES_PER_PIXEL
    for row_index in range(y, y + rectangle_height):
        start = row_index * stride + x * _BYTES_PER_PIXEL
        pixels[start : start + len(row)] = row


def _draw_line(
    pixels: bytearray,
    *,
    canvas_width: int,
    canvas_height: int,
    value: str,
    y: int,
    scale: int,
) -> None:
    glyph_width = 5 * scale
    gap = scale
    line_width = len(value) * glyph_width + (len(value) - 1) * gap
    x = (canvas_width - line_width) // 2
    if x < 4 or y < 4 or y + 7 * scale > canvas_height - 4:
        raise AnprOcrViolation("invalid_output")
    for character in value:
        glyph = _GLYPHS.get(character)
        if glyph is None:
            raise AnprOcrViolation("unsupported_script")
        for bit_index, bit in enumerate(glyph):
            if bit == "1":
                _fill_rectangle(
                    pixels,
                    width=canvas_width,
                    x=x + (bit_index % 5) * scale,
                    y=y + (bit_index // 5) * scale,
                    rectangle_width=scale,
                    rectangle_height=scale,
                    color=b"\x14\x14\x14",
                )
        x += glyph_width + gap


def render_generated_latin_crop(
    plan: SyntheticCorpusPlanV1,
    split: AnprSplit,
    sample_index: int,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> GeneratedLatinOcrCropV1:
    request = derive_generated_request(plan, split, sample_index)
    entry = derive_split_manifest_entry(plan, split, sample_index)
    token = generate_ephemeral_token(request, policy=policy)
    if request.layout == "single_line":
        width, height, scale = 416, 64, 5
        lines = ((token.token, 14),)
    else:
        width, height, scale = 320, 104, 5
        lines = ((token.token[:4], 10), (token.token[4:], 56))

    pixels = bytearray(b"\xf8\xf6\xf2" * (width * height))
    _fill_rectangle(
        pixels,
        width=width,
        x=0,
        y=0,
        rectangle_width=width,
        rectangle_height=3,
        color=b"\x24\x24\x24",
    )
    _fill_rectangle(
        pixels,
        width=width,
        x=0,
        y=height - 3,
        rectangle_width=width,
        rectangle_height=3,
        color=b"\x24\x24\x24",
    )
    _fill_rectangle(
        pixels,
        width=width,
        x=0,
        y=0,
        rectangle_width=3,
        rectangle_height=height,
        color=b"\x24\x24\x24",
    )
    _fill_rectangle(
        pixels,
        width=width,
        x=width - 3,
        y=0,
        rectangle_width=3,
        rectangle_height=height,
        color=b"\x24\x24\x24",
    )
    for value, y in lines:
        _draw_line(
            pixels,
            canvas_width=width,
            canvas_height=height,
            value=value,
            y=y,
            scale=scale,
        )

    region_material = {
        "renderer_version": ANPR_LATIN_RENDERER_VERSION,
        "sample_id": entry.sample_id,
    }
    return GeneratedLatinOcrCropV1(
        width=width,
        height=height,
        bgr_bytes=bytes(pixels),
        sample_id=entry.sample_id,
        region_id=_identifier(
            "anprregion",
            "hcam.anpr.p35w5.generated-latin-region.v1",
            region_material,
        ),
        request=request,
        ephemeral_token=token,
        layout=request.layout,
    )


def _validate_raw_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise AnprOcrViolation("invalid_output")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise AnprOcrViolation("invalid_output") from exc
    if len(value) > 32 or len(value) > 16:
        raise AnprOcrViolation("output_too_long")
    if any(character.isspace() for character in value):
        raise AnprOcrViolation("unexpected_whitespace")
    if not all(
        character == "-"
        or "0" <= character <= "9"
        or "A" <= character <= "Z"
        or "a" <= character <= "z"
        for character in value
    ):
        raise AnprOcrViolation("unsupported_script")
    return value


def _validate_confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise AnprOcrViolation("invalid_confidence")
    confidence = float(value)
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise AnprOcrViolation("invalid_confidence")
    return confidence


def build_ephemeral_latin_hypothesis(
    crop: GeneratedLatinOcrCropV1,
    *,
    candidate_id: LatinOcrCandidate,
    engine_result: RawLatinOcrEngineResultV1,
    latency_ms: float,
) -> EphemeralLatinOcrHypothesisV1:
    candidate = _CANDIDATES[candidate_id]
    if engine_result.raw_text is None and engine_result.raw_confidence is None:
        raise AnprOcrViolation("no_result")
    raw_text = _validate_raw_text(engine_result.raw_text)
    raw_confidence = _validate_confidence(engine_result.raw_confidence)
    if not isinstance(engine_result.alternatives, tuple) or len(
        engine_result.alternatives
    ) > 5:
        raise AnprOcrViolation("malformed_result")
    if any(
        not isinstance(item, tuple) or len(item) != 2
        for item in engine_result.alternatives
    ):
        raise AnprOcrViolation("malformed_result")
    alternatives = tuple(
        {
            "rank": rank,
            "raw_text": _validate_raw_text(item[0]),
            "raw_confidence": _validate_confidence(item[1]),
        }
        for rank, item in enumerate(engine_result.alternatives, start=1)
    )
    if not isinstance(latency_ms, Real) or not math.isfinite(float(latency_ms)):
        raise AnprOcrViolation("malformed_result")
    if float(latency_ms) < 0 or float(latency_ms) > 600_000:
        raise AnprOcrViolation("malformed_result")
    return EphemeralLatinOcrHypothesisV1(
        result_id=_identifier(
            "anprocr",
            "hcam.anpr.p35w5.ocr-result.v1",
            {"candidate_id": candidate_id, "sample_id": crop.sample_id},
        ),
        region_id=crop.region_id,
        sample_id=crop.sample_id,
        candidate_id=candidate_id,
        artifact_id=candidate["artifact_id"],
        artifact_sha256=candidate["artifact_sha256"],
        raw_text=raw_text,
        raw_confidence=raw_confidence,
        alternatives=alternatives,
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
                    previous[right_index - 1]
                    + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def _distribution(values: list[float]) -> LatinOcrDistributionV1:
    if not values:
        raise ValueError("distribution requires at least one value")
    ordered = sorted(float(value) for value in values)

    def percentile(fraction: float) -> float:
        index = max(0, math.ceil(fraction * len(ordered)) - 1)
        return ordered[index]

    return LatinOcrDistributionV1(
        minimum=round(ordered[0], 6),
        p50=round(percentile(0.50), 6),
        p95=round(percentile(0.95), 6),
        maximum=round(ordered[-1], 6),
        mean=round(sum(ordered) / len(ordered), 6),
    )


def _failure_counts(counter: Counter[str]) -> LatinOcrFailureCountsV1:
    return LatinOcrFailureCountsV1(
        **{name: counter[name] for name in LatinOcrFailureCode.__args__}
    )


def _sample_sequence(
    plan: SyntheticCorpusPlanV1, sample_count: int
) -> tuple[tuple[AnprSplit, int], ...]:
    if not 1 <= sample_count <= MAX_ANPR_LOCAL_SAMPLES:
        raise ValueError("Latin OCR sample count is outside the local limit")
    available = (
        (("development", index) for index in range(plan.counts.development)),
        (("validation", index) for index in range(plan.counts.validation)),
    )
    samples = tuple(item for sequence in available for item in sequence)
    if sample_count > len(samples):
        raise ValueError("Latin OCR evidence cannot open final-test samples")
    return samples[:sample_count]


def evaluate_generated_latin_candidate(
    plan: SyntheticCorpusPlanV1,
    engine: LatinOcrEngine,
    *,
    policy: SyntheticAnprExecutionPolicyV1,
    sample_count: int,
    replay_runs: int = 20,
    network_attempt_count: int = 0,
) -> LatinOcrCandidateEvaluationV1:
    if replay_runs != 20:
        raise ValueError("P3.5 W5 deterministic replay requires exactly 20 runs")
    samples = _sample_sequence(plan, sample_count)
    failure_counter: Counter[str] = Counter()
    slice_failures = {layout: Counter() for layout in ("single_line", "two_line")}
    slice_totals = {
        layout: {"sample": 0, "success": 0, "exact": 0, "reference": 0, "edit": 0}
        for layout in ("single_line", "two_line")
    }
    confidences: list[float] = []
    latencies: list[float] = []
    exact_matches = 0
    total_edit_distance = 0
    reference_scalar_count = 0
    succeeded = 0

    for split, sample_index in samples:
        crop = render_generated_latin_crop(
            plan,
            split,
            sample_index,
            policy=policy,
        )
        expected = crop.ephemeral_token.token
        aggregate = slice_totals[crop.layout]
        aggregate["sample"] += 1
        aggregate["reference"] += len(expected)
        reference_scalar_count += len(expected)
        started = time.perf_counter_ns()
        try:
            raw_result = engine.recognize(crop)
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            hypothesis = build_ephemeral_latin_hypothesis(
                crop,
                candidate_id=engine.candidate_id,
                engine_result=raw_result,
                latency_ms=elapsed_ms,
            )
        except AnprOcrViolation as exc:
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            failure_counter[exc.code] += 1
            slice_failures[crop.layout][exc.code] += 1
            total_edit_distance += len(expected)
            aggregate["edit"] += len(expected)
        except Exception:
            elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
            failure_counter["engine_error"] += 1
            slice_failures[crop.layout]["engine_error"] += 1
            total_edit_distance += len(expected)
            aggregate["edit"] += len(expected)
        else:
            succeeded += 1
            aggregate["success"] += 1
            edit_distance = _edit_distance(expected, hypothesis.raw_text)
            total_edit_distance += edit_distance
            aggregate["edit"] += edit_distance
            if expected == hypothesis.raw_text:
                exact_matches += 1
                aggregate["exact"] += 1
            confidences.append(hypothesis.raw_confidence)
        latencies.append(elapsed_ms)

    replay_crop = render_generated_latin_crop(
        plan,
        "development",
        0,
        policy=policy,
    )
    replay_observations: list[tuple[str, str | float]] = []
    for _ in range(replay_runs):
        started = time.perf_counter_ns()
        try:
            replay_raw = engine.recognize(replay_crop)
            replay_hypothesis = build_ephemeral_latin_hypothesis(
                replay_crop,
                candidate_id=engine.candidate_id,
                engine_result=replay_raw,
                latency_ms=(time.perf_counter_ns() - started) / 1_000_000,
            )
        except AnprOcrViolation as exc:
            replay_observations.append(("failure", exc.code))
        except Exception:
            replay_observations.append(("failure", "engine_error"))
        else:
            replay_observations.append(
                (
                    replay_hypothesis.raw_text,
                    round(replay_hypothesis.raw_confidence, 8),
                )
            )

    slices = tuple(
        LatinOcrGeneratedSliceV1(
            layout=layout,
            sample_count=values["sample"],
            succeeded=values["success"],
            failed=values["sample"] - values["success"],
            exact_matches=values["exact"],
            reference_scalar_count=values["reference"],
            raw_edit_distance=values["edit"],
            failure_counts=_failure_counts(slice_failures[layout]),
        )
        for layout, values in slice_totals.items()
    )
    candidate = _CANDIDATES[engine.candidate_id]
    return LatinOcrCandidateEvaluationV1(
        candidate_id=engine.candidate_id,
        artifact_id=candidate["artifact_id"],
        artifact_sha256=candidate["artifact_sha256"],
        extracted_inventory_sha256=engine.extracted_inventory_sha256,
        model_name=candidate["model_name"],
        sample_count=sample_count,
        succeeded=succeeded,
        failed=sample_count - succeeded,
        exact_matches=exact_matches,
        reference_scalar_count=reference_scalar_count,
        raw_edit_distance=total_edit_distance,
        failure_counts=_failure_counts(failure_counter),
        slices=slices,
        confidence_distribution=_distribution(confidences) if confidences else None,
        latency_ms_distribution=_distribution(latencies),
        replay_output_deterministic=len(set(replay_observations)) == 1,
        network_attempt_count=network_attempt_count,
    )
