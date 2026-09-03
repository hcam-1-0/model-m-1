#!/usr/bin/env python3
"""Generate and verify bounded P3.5 W7 normalization evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from hcam.analytics.anpr import (  # noqa: E402
    ANPR_PINNED_PYTHON_VERSION,
    ANPR_PINNED_REGEX_VERSION,
    ANPR_PINNED_UNICODE_VERSION,
    ExactRegexGraphemeSegmenter,
    GraphemeSegmenter,
    NormalizationGeneratedEvaluationV1,
    NormalizationGeneratedSliceV1,
    SyntheticAnprExecutionPolicyV1,
    derive_ephemeral_auxiliary_sample,
    derive_generated_request,
    evaluate_generated_calibration,
    generate_ephemeral_token,
    measure_generated_normalization,
    normalize_ephemeral_hypothesis,
    segment_generated_reference,
    synthetic_corpus_plan_fixture,
)
from hcam.analytics.anpr.contracts import (  # noqa: E402
    OCR_L0_ARTIFACT_SHA256,
    OCR_L1_ARTIFACT_SHA256,
    EphemeralAuxiliaryOcrHypothesisV1,
    EphemeralCalibrationObservationV1,
    EphemeralLatinOcrHypothesisV1,
    NormalizationCandidate,
)
from hcam.analytics.anpr.guardrails import canonical_anpr_evidence_json  # noqa: E402


RUNTIME_ROOT = Path(r"E:\h-cam-research-cache\phase-3\p3-5-runtime")
EVIDENCE_PATH = (
    ROOT / "contracts" / "phase-3" / "p3-5-normalization-evaluation.json"
)
MAX_EVIDENCE_BYTES = 128 * 1024
MAX_EVIDENCE_NODES = 8_192
_W7_WORK_PACKAGE = "P35-W7_normalization_confidence_abstention_and_bounded_consensus"
_LATIN_ARTIFACTS = {
    "OCR-L0": (
        "OCR-L0-PPOCRV6-SMALL-INFER-PROPOSED",
        OCR_L0_ARTIFACT_SHA256,
    ),
    "OCR-L1": (
        "OCR-L1-PPOCRV6-MEDIUM-INFER-PROPOSED",
        OCR_L1_ARTIFACT_SHA256,
    ),
}


class NormalizationToolError(RuntimeError):
    pass


def _identifier(prefix: str, domain: str, index: int) -> str:
    digest = hashlib.sha256(f"{domain}\0{index}".encode("ascii")).hexdigest()
    return f"{prefix}_{digest[:32]}"


def _load_authorization() -> dict[str, object]:
    path = ROOT / "contracts" / "phase-3" / "p3-5-start-authorization.json"
    try:
        authorization = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise NormalizationToolError("W7 authorization cannot be read") from exc
    runtime = authorization.get("allowed_runtime")
    if not isinstance(runtime, dict) or (
        authorization.get("decision_id") != "D-P3.5-START"
        or authorization.get("effective") is not True
        or _W7_WORK_PACKAGE not in authorization.get("allowed_work_packages", [])
        or authorization.get("allowed_network_actions") != []
        or runtime.get("network_access") is not False
        or runtime.get("external_runtime_root") != str(RUNTIME_ROOT)
        or runtime.get("python_version") != ANPR_PINNED_PYTHON_VERSION
        or f"regex=={ANPR_PINNED_REGEX_VERSION}"
        not in runtime.get("direct_packages", [])
        or runtime.get("repository_dependency_or_lockfile_change") is not False
        or runtime.get("tesseract_runtime_authorized") is not False
    ):
        raise NormalizationToolError("W7 authorization boundary changed")
    return authorization


def _verify_exact_runtime() -> None:
    expected_prefix = (RUNTIME_ROOT / "venv").resolve()
    if Path(sys.prefix).resolve() != expected_prefix:
        raise NormalizationToolError("W7 must run from the exact external runtime")
    if ".".join(str(value) for value in sys.version_info[:3]) != ANPR_PINNED_PYTHON_VERSION:
        raise NormalizationToolError("W7 Python version changed")
    if unicodedata.unidata_version != ANPR_PINNED_UNICODE_VERSION:
        raise NormalizationToolError("W7 Unicode data version changed")


def _blocked_network_attempt() -> int:
    original = socket.create_connection

    def denied(*_args: object, **_kwargs: object) -> socket.socket:
        raise PermissionError("network denied by P3.5 W7")

    socket.create_connection = denied
    try:
        try:
            socket.create_connection(("127.0.0.1", 9), timeout=0.01)
        except PermissionError:
            return 1
        raise NormalizationToolError("W7 network denial did not fail closed")
    finally:
        socket.create_connection = original


def _policy() -> SyntheticAnprExecutionPolicyV1:
    return SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")


def _latin_hypotheses() -> tuple[tuple[str, EphemeralLatinOcrHypothesisV1], ...]:
    plan = synthetic_corpus_plan_fixture()
    policy = _policy()
    values: list[tuple[str, EphemeralLatinOcrHypothesisV1]] = []
    for index in range(12):
        split = "development" if index < plan.counts.development else "validation"
        split_index = index if split == "development" else index - plan.counts.development
        request = derive_generated_request(plan, split, split_index)
        token = generate_ephemeral_token(request, policy=policy)
        candidate: NormalizationCandidate = "OCR-L0" if index % 2 == 0 else "OCR-L1"
        raw_text = token.token
        if index % 3 == 0:
            raw_text = raw_text.lower()
        if index % 4 == 0:
            raw_text = raw_text.replace("-", "", 1)
        artifact_id, artifact_sha256 = _LATIN_ARTIFACTS[candidate]
        hypothesis = EphemeralLatinOcrHypothesisV1(
            result_id=_identifier("anprocr", "hcam.p35w7.latin-result", index),
            region_id=_identifier("anprregion", "hcam.p35w7.latin-region", index),
            sample_id=_identifier("anprsample", "hcam.p35w7.latin-sample", index),
            candidate_id=candidate,
            artifact_id=artifact_id,
            artifact_sha256=artifact_sha256,
            raw_text=raw_text,
            raw_confidence=round(0.08 + index * 0.075, 6),
            latency_ms=0.0,
        )
        values.append((token.token, hypothesis))
    return tuple(values)


def _devanagari_hypotheses() -> tuple[
    tuple[str, EphemeralAuxiliaryOcrHypothesisV1], ...
]:
    policy = _policy()
    values: list[tuple[str, EphemeralAuxiliaryOcrHypothesisV1]] = []
    for index in range(12):
        sample = derive_ephemeral_auxiliary_sample(
            "devanagari",
            index,
            policy=policy,
        )
        raw_text = sample.text[:-1] if index % 5 == 0 else sample.text
        hypothesis = EphemeralAuxiliaryOcrHypothesisV1(
            result_id=_identifier("anprauxocr", "hcam.p35w7.deva-result", index),
            region_id=_identifier("anprauxregion", "hcam.p35w7.deva-region", index),
            sample_id=sample.sample_id,
            raw_text=raw_text,
            raw_confidence=round(0.11 + index * 0.07, 6),
            latency_ms=0.0,
        )
        values.append((sample.text, hypothesis))
    return tuple(values)


def _normalization_slice(
    script: str,
    fixtures: tuple[
        tuple[str, EphemeralLatinOcrHypothesisV1 | EphemeralAuxiliaryOcrHypothesisV1],
        ...,
    ],
    *,
    segmenter: GraphemeSegmenter,
) -> NormalizationGeneratedSliceV1:
    normalized = [
        (reference, normalize_ephemeral_hypothesis(hypothesis, segmenter=segmenter))
        for reference, hypothesis in fixtures
    ]
    metrics = [
        measure_generated_normalization(reference, value, segmenter=segmenter)
        for reference, value in normalized
    ]
    return NormalizationGeneratedSliceV1(
        script_lane=script,
        fixture_kind="deterministic_hypothesis_contract_fixture",
        sample_count=len(fixtures),
        hypothesis_count=len(fixtures),
        normalized_count=len(normalized),
        abstained_count=sum(value.abstain for _, value in normalized),
        synthetic_format_count=sum(
            value.format_family == "synthetic_non_issuable" for _, value in normalized
        ),
        unrecognized_format_count=sum(
            value.format_family == "unrecognized" for _, value in normalized
        ),
        nfc_transform_count=sum(value.nfc_transform_performed for _, value in normalized),
        case_transform_count=sum(value.case_transform_performed for _, value in normalized),
        reference_scalar_count=sum(value.reference_scalar_count for value in metrics),
        reference_grapheme_count=sum(value.reference_grapheme_count for value in metrics),
        observed_scalar_count=sum(value.observed_scalar_count for value in metrics),
        observed_grapheme_count=sum(value.observed_grapheme_count for value in metrics),
        code_point_edit_distance=sum(value.code_point_edit_distance for value in metrics),
        grapheme_edit_distance=sum(value.grapheme_edit_distance for value in metrics),
    )


def _gujarati_reference_slice(
    *, segmenter: GraphemeSegmenter
) -> NormalizationGeneratedSliceV1:
    policy = _policy()
    samples = tuple(
        derive_ephemeral_auxiliary_sample("gujarati", index, policy=policy)
        for index in range(12)
    )
    graphemes = tuple(
        segment_generated_reference(sample.text, "gujarati", segmenter=segmenter)
        for sample in samples
    )
    return NormalizationGeneratedSliceV1(
        script_lane="gujarati",
        fixture_kind="generated_render_reference_only",
        sample_count=len(samples),
        hypothesis_count=0,
        normalized_count=0,
        abstained_count=0,
        synthetic_format_count=0,
        unrecognized_format_count=0,
        nfc_transform_count=0,
        case_transform_count=0,
        reference_scalar_count=sum(len(sample.text) for sample in samples),
        reference_grapheme_count=sum(len(value) for value in graphemes),
        observed_scalar_count=0,
        observed_grapheme_count=0,
        code_point_edit_distance=0,
        grapheme_edit_distance=0,
    )


def _calibration(candidate_id: NormalizationCandidate):
    observations = tuple(
        EphemeralCalibrationObservationV1(
            candidate_id=candidate_id,
            split="development" if index < 5 else "validation",
            raw_confidence=round(0.05 + index * 0.1, 6),
            correct=(index + {"OCR-L0": 0, "OCR-L1": 1, "OCR-D0": 2}[candidate_id])
            % 3
            != 0,
        )
        for index in range(10)
    )
    return evaluate_generated_calibration(observations)


def _core_payload(segmenter: GraphemeSegmenter) -> dict[str, object]:
    latin = _normalization_slice(
        "latin",
        _latin_hypotheses(),
        segmenter=segmenter,
    )
    devanagari = _normalization_slice(
        "devanagari",
        _devanagari_hypotheses(),
        segmenter=segmenter,
    )
    gujarati = _gujarati_reference_slice(segmenter=segmenter)
    calibrations = tuple(
        _calibration(candidate_id) for candidate_id in ("OCR-L0", "OCR-L1", "OCR-D0")
    )
    return {
        "slices": (latin, devanagari, gujarati),
        "calibration_evaluations": calibrations,
    }


def build_evaluation(
    *,
    segmenter: GraphemeSegmenter | None = None,
    verify_runtime: bool = True,
) -> NormalizationGeneratedEvaluationV1:
    _load_authorization()
    if verify_runtime:
        _verify_exact_runtime()
    active_segmenter = segmenter or ExactRegexGraphemeSegmenter()
    observations = tuple(_core_payload(active_segmenter) for _ in range(20))
    canonical = tuple(
        json.dumps(
            {
                key: [item.model_dump(mode="json") for item in value]
                for key, value in observation.items()
            },
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        for observation in observations
    )
    first = observations[0]
    return NormalizationGeneratedEvaluationV1(
        slices=first["slices"],
        calibration_evaluations=first["calibration_evaluations"],
        replay_output_deterministic=len(set(canonical)) == 1,
        network_attempt_count=_blocked_network_attempt(),
    )


def render_evaluation(evaluation: NormalizationGeneratedEvaluationV1) -> str:
    return canonical_anpr_evidence_json(
        evaluation,
        maximum_bytes=MAX_EVIDENCE_BYTES,
        maximum_nodes=MAX_EVIDENCE_NODES,
    )


def check_evidence() -> int:
    try:
        actual = EVIDENCE_PATH.read_text(encoding="utf-8")
        parsed = NormalizationGeneratedEvaluationV1.model_validate_json(actual)
        canonical = render_evaluation(parsed)
    except (OSError, ValueError) as exc:
        print(f"[fail] P3.5 W7 evidence: {exc}")
        return 1
    prohibited = (
        '"raw_text"',
        '"nfc_value"',
        '"normalized_display_candidate"',
        '"graphemes"',
        '"raw_hypothesis_digest"',
        '"sample_id"',
        '"region_id"',
        '"result_id"',
        "SYN-",
        "anprsample_",
        "anprregion_",
        "anprauxsample_",
        "B:\\",
    )
    if actual != canonical or any(value in actual for value in prohibited):
        print("[fail] P3.5 W7 evidence contains ephemeral text or identifiers")
        return 1
    print(f"[pass] {EVIDENCE_PATH.relative_to(ROOT)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--write-evidence", action="store_true")
    evaluate.add_argument("--acknowledge-generated-only-evidence", action="store_true")
    subparsers.add_parser("check-evidence")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "check-evidence":
            return check_evidence()
        if args.write_evidence and not args.acknowledge_generated_only_evidence:
            print("Refusing to write W7 evidence without generated-only acknowledgment")
            return 2
        evaluation = build_evaluation()
        rendered = render_evaluation(evaluation)
        if args.write_evidence:
            EVIDENCE_PATH.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"[write] {EVIDENCE_PATH.relative_to(ROOT)}")
        else:
            print(rendered, end="")
        return 0
    except (NormalizationToolError, OSError, ValueError) as exc:
        print(f"P3.5 W7 failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
