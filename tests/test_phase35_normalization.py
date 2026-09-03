from __future__ import annotations

import json
import unicodedata

import pytest

from hcam.analytics.anpr import (
    ANPR_PINNED_REGEX_VERSION,
    ANPR_PINNED_UNICODE_VERSION,
)
from tools import phase35_normalization


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


def test_w7_authorization_is_exact_external_and_zero_network() -> None:
    authorization = phase35_normalization._load_authorization()
    runtime = authorization["allowed_runtime"]

    assert phase35_normalization._W7_WORK_PACKAGE in authorization[
        "allowed_work_packages"
    ]
    assert authorization["allowed_network_actions"] == []
    assert runtime["external_runtime_root"] == str(phase35_normalization.RUNTIME_ROOT)
    assert runtime["network_access"] is False
    assert runtime["repository_dependency_or_lockfile_change"] is False
    assert runtime["tesseract_runtime_authorized"] is False


def test_generated_w7_evaluation_is_aggregate_only_and_deterministic() -> None:
    evaluation = phase35_normalization.build_evaluation(
        segmenter=ClosedTestSegmenter(),
        verify_runtime=False,
    )
    rendered = phase35_normalization.render_evaluation(evaluation)
    document = json.loads(rendered)

    assert document["replay_runs"] == 20
    assert document["replay_output_deterministic"] is True
    assert document["network_attempt_count"] == 1
    assert document["network_access_performed"] is False
    assert document["model_execution_count"] == 0
    assert document["quality_threshold_decided"] is False
    assert document["operational_acceptance_count"] == 0
    assert document["consensus_execution_count"] == 0
    assert {item["script_lane"] for item in document["slices"]} == {
        "latin",
        "devanagari",
        "gujarati",
    }
    assert {item["candidate_id"] for item in document["calibration_evaluations"]} == {
        "OCR-L0",
        "OCR-L1",
        "OCR-D0",
    }
    for prohibited in (
        '"raw_text"',
        '"nfc_value"',
        '"normalized_display_candidate"',
        '"graphemes"',
        "SYN-",
        "anprsample_",
        "anprauxsample_",
    ):
        assert prohibited not in rendered


def test_repository_runtime_cannot_impersonate_exact_w7_runtime() -> None:
    with pytest.raises(
        phase35_normalization.NormalizationToolError,
        match="exact external runtime",
    ):
        phase35_normalization.build_evaluation(
            segmenter=ClosedTestSegmenter(),
            verify_runtime=True,
        )


def test_tracked_w7_evidence_is_canonical_and_zero_retention() -> None:
    assert phase35_normalization.check_evidence() == 0


def test_tool_paths_never_use_prohibited_b_drive() -> None:
    source = phase35_normalization.ROOT.joinpath(
        "tools", "phase35_normalization.py"
    ).read_text(encoding="utf-8")

    assert source.count('"B:\\\\",') == 1
    assert "Path(r\"B:" not in source
    assert str(phase35_normalization.RUNTIME_ROOT).startswith("E:\\")
    assert str(phase35_normalization.EVIDENCE_PATH).startswith(
        str(phase35_normalization.ROOT)
    )
