from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hcam.analytics.activation import (
    P3_3_CONFIGURATION_VERSION,
    P3_3_PIPELINE_VERSION,
    P3_3_POLICY_VERSION,
    P3_3_TRACKER_VERSION,
)
from hcam.analytics.models import (
    AnalyticsTrackerEpoch,
    AnalyticsTrack,
    AnalyticsTrackLifecycle,
    AnalyticsTrackingRun,
)
from hcam.analytics.tracking import TrackerConfiguration
from hcam.analytics.tracking.generated_sequences import GENERATOR_VERSION
from hcam.settings import Settings
from tools import phase33_implementation_readiness as readiness
from tools.phase33_tracking_evidence import _validate_report


ROOT = Path(__file__).parents[1]


def _document(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _canonical_digest(relative: str) -> str:
    document = _document(relative)
    payload = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _normalized_file_digest(relative: str) -> str:
    payload = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def test_p3_3_versions_are_bound_to_reviewed_artifacts() -> None:
    tracker = _document("contracts/phase-3/p3-3-tracker-source.json")
    evaluator = _document("contracts/phase-3/p3-3-evaluator-source.json")

    assert tracker["commit"] == "d1bf0191adff59bc8fcfeaa0b33d3d1642552a99"
    assert evaluator["commit"] == "12c8791b303e0a0b50f753af204249e622d0281a"
    assert tracker["upstream_dependencies_accepted"] is False
    assert evaluator["runtime_dependency"] is False
    assert P3_3_TRACKER_VERSION == tracker["canonical_selected_source_digest"]
    assert P3_3_POLICY_VERSION == _normalized_file_digest(
        "contracts/phase-3/p3-3-tracker-policy.json"
    )
    assert P3_3_PIPELINE_VERSION == _canonical_digest(
        "contracts/phase-3/p3-3-runtime-profile.json"
    )
    assert GENERATOR_VERSION == _canonical_digest(
        "contracts/phase-3/p3-3-generated-suite.json"
    )
    assert P3_3_CONFIGURATION_VERSION == TrackerConfiguration().digest


def test_p3_3_evaluation_report_passes_without_real_data_claims() -> None:
    report = _document("contracts/phase-3/p3-3/evaluation-report.json")

    assert _validate_report(report) == []
    assert report["trackeval_parity"]["maximum_hota_absolute_error"] == 0
    assert report["trackeval_parity"]["maximum_idf1_absolute_error"] == 0
    assert report["bytetrack_component_parity"]["passed"] is True
    assert report["bytetrack_component_parity"]["full_historical_runtime_executed"] is False
    assert report["gates"]["per_class_hota_minimum_observed"] == 1
    assert report["gates"]["per_class_idf1_minimum_observed"] == 1
    assert report["gates"]["short_occlusion_recovery_rate"] == 1
    assert any("real-CCTV accuracy" in item for item in report["limitations"])


def test_p3_3_storage_has_no_media_identity_or_cross_camera_columns() -> None:
    prohibited = {
        "biometric",
        "blob",
        "bytes",
        "clip",
        "embedding",
        "face",
        "global",
        "identity",
        "image",
        "locator",
        "media",
        "owner",
        "path",
        "plate",
        "reid",
        "url",
        "video",
        "watchlist",
    }
    for model in (
        AnalyticsTrackingRun,
        AnalyticsTrackerEpoch,
        AnalyticsTrack,
        AnalyticsTrackLifecycle,
    ):
        columns = {column.name.lower() for column in model.__table__.columns}
        assert not any(
            token in column for column in columns for token in prohibited
        )
        assert not {"frame_bytes", "frame_data", "raw_frame"} & columns


def test_generated_tracking_runtime_is_default_off_and_production_forbidden() -> None:
    assert Settings(environment="test").analytics_generated_tracking_enabled is False
    with pytest.raises(ValueError, match="tracking runtime is forbidden"):
        Settings(
            environment="production",
            database_url="postgresql+psycopg://hcam@db/hcam",
            analytics_generated_tracking_enabled=True,
        )


def test_p3_3_static_package_is_ready_for_owner_acceptance() -> None:
    report = readiness.build_report(require_clean_source=False)

    assert report.status == "ready_for_owner_acceptance"
    assert report.failures == 0
    assert report.manual_gates == 1
    assert len(report.package_digest) == 64
    assert report.package_digest == report.package_digest.upper()
    assert {check.name for check in report.checks} == {
        "required_files",
        "work_authorization",
        "artifact_bindings",
        "generated_evaluation",
        "sbom",
        "structural_boundaries",
        "validation_evidence",
        "owner_acceptance",
    }


def test_p3_3_package_digest_is_deterministic_and_path_relative() -> None:
    first_digest, first_manifest = readiness.package_digest()
    second_digest, second_manifest = readiness.package_digest()

    assert first_digest == second_digest
    assert first_manifest == second_manifest
    assert len(first_manifest) == len(readiness.PACKAGE_FILES)
    assert all(":\\" not in item for item in first_manifest)
    assert all(" sha256=" in item and " bytes=" in item for item in first_manifest)
