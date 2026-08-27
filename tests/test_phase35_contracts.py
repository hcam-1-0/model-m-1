from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from hcam.analytics.anpr.contracts import generated_request_fixture
from hcam.analytics.anpr.guardrails import canonical_anpr_evidence_json
from tools import phase35_contracts
from tools import phase35_latin_ocr
from tools import phase35_normalization


def test_p3_5_w1_contract_snapshots_are_current() -> None:
    assert phase35_contracts.check_contracts() == 0


def test_p3_5_w1_contract_writer_requires_review_acknowledgment() -> None:
    with redirect_stdout(io.StringIO()):
        assert phase35_contracts.write_contracts(acknowledged=False) == 2


def test_generated_request_fixture_is_canonical_and_contains_no_plate_text() -> None:
    expected = canonical_anpr_evidence_json(generated_request_fixture())
    actual = phase35_contracts.FIXTURE_PATH.read_text(encoding="utf-8")
    document = json.loads(actual)

    assert actual == expected
    assert "token" not in document
    assert "text" not in document
    assert "path" not in document
    assert "url" not in document


def test_sealed_split_fixture_is_canonical_and_contains_no_token_text() -> None:
    actual = phase35_contracts.SPLIT_MANIFEST_PATH.read_text(encoding="utf-8")
    expected = phase35_contracts.render_contracts()[
        phase35_contracts.SPLIT_MANIFEST_PATH
    ]
    document = json.loads(actual)

    assert actual == expected
    assert document["content"]["sealed"] is True
    assert document["content"]["final_test_frozen"] is True
    assert document["content"]["final_test_tuning_allowed"] is False
    assert document["content"]["token_text_persisted"] is False
    assert document["content"]["token_commitment_persisted"] is False
    assert '"token"' not in actual
    assert "SYN-" not in actual


def test_ground_truth_crop_fixture_is_canonical_and_pixel_free() -> None:
    actual = phase35_contracts.GROUND_TRUTH_CROP_PATH.read_text(encoding="utf-8")
    expected = phase35_contracts.render_contracts()[
        phase35_contracts.GROUND_TRUTH_CROP_PATH
    ]
    document = json.loads(actual)

    assert actual == expected
    assert document["source_id"] == "DATA-PLATE-GEN-R0"
    assert document["external_input_count"] == 0
    assert document["model_execution_performed"] is False
    assert document["weights_loaded"] is False
    assert document["frame_pixels_persisted"] is False
    assert document["crop_pixels_persisted"] is False
    assert document["plate_text_persisted"] is False
    assert document["localization"]["hypothesis_count"] == 1
    assert document["localization"]["candidate_id"] is None
    assert document["crop"]["pixels_ephemeral"] is True
    assert document["crop"]["pixels_persisted"] is False
    assert '"bgr_bytes"' not in actual
    assert '"token"' not in actual
    assert "SYN-" not in actual


def test_generated_latin_ocr_evidence_is_canonical_and_zero_retention() -> None:
    assert phase35_latin_ocr.check_evidence() == 0

    actual = phase35_latin_ocr.EVIDENCE_PATH.read_text(encoding="utf-8")
    document = json.loads(actual)

    assert document["external_input_count"] == 0
    assert document["model_download_count"] == 0
    assert document["raw_output_persisted"] is False
    assert document["sample_or_region_identifiers_persisted"] is False
    assert {item["candidate_id"] for item in document["candidate_evaluations"]} == {
        "OCR-L0",
        "OCR-L1",
    }
    assert all(
        item["final_test_used"] is False
        and item["replay_output_deterministic"] is True
        and item["network_access_performed"] is False
        for item in document["candidate_evaluations"]
    )
    assert "SYN-" not in actual
    assert '"raw_text"' not in actual
    assert "anprsample_" not in actual
    assert "anprregion_" not in actual


def test_generated_normalization_evidence_is_canonical_and_zero_retention() -> None:
    assert phase35_normalization.check_evidence() == 0

    actual = phase35_normalization.EVIDENCE_PATH.read_text(encoding="utf-8")
    document = json.loads(actual)

    assert document["external_text_input_count"] == 0
    assert document["model_execution_count"] == 0
    assert document["normalized_output_persisted"] is False
    assert document["grapheme_values_persisted"] is False
    assert document["quality_threshold_decided"] is False
    assert document["operational_acceptance_count"] == 0
    assert document["consensus_execution_count"] == 0
    assert '"raw_text"' not in actual
    assert '"nfc_value"' not in actual
    assert '"graphemes"' not in actual
    assert "SYN-" not in actual
