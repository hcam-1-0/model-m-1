from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
CONTRACT_ROOT = ROOT / "contracts/phase-5/p5-7"
ALLOCATION = {
    "cross_portal_journeys_and_replay": 512,
    "contract_API_event_and_concurrency": 320,
    "accessibility": 256,
    "localization_time_and_Unicode": 192,
    "browser_layout_and_resource_profiles": 256,
    "performance_scale_and_bundles": 192,
    "resilience": 192,
    "security_privacy_and_supply_chain": 128,
}
REQUIRED_RECORDS = {
    "quality-contracts.v1.json",
    "journey-manifest.json",
    "generated-contract-cases.json",
    "generated-workloads.json",
    "browser-viewport-profile-matrix.json",
    "accessibility-evidence-manifest.json",
    "localization-time-manifest.json",
    "performance-budget-manifest.json",
    "resilience-fault-manifest.json",
    "security-privacy-manifest.json",
    "source-manifest.json",
}
FORBIDDEN_KEYS = {
    "password",
    "secret",
    "token",
    "credential",
    "biometric",
    "owner_name",
    "registration_number",
    "watchlist_identity",
    "raw_payload",
    "camera_locator",
    "media_url",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def recursive_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key).lower() for key in value} | set().union(
            *(recursive_keys(item) for item in value.values()), set()
        )
    if isinstance(value, list):
        return set().union(*(recursive_keys(item) for item in value), set())
    return set()


def test_phase57_record_set_case_count_and_distribution_are_exact() -> None:
    assert REQUIRED_RECORDS <= {path.name for path in CONTRACT_ROOT.glob("*.json")}
    generated = read_json(CONTRACT_ROOT / "generated-contract-cases.json")
    assert generated["generated_only"] is True
    assert generated["exact_case_count"] == 2048
    assert len(generated["cases"]) == 2048
    assert len({case["ref"] for case in generated["cases"]}) == 2048
    assert generated["allocation"] == ALLOCATION
    assert {
        category: sum(case["category"] == category for case in generated["cases"])
        for category in ALLOCATION
    } == ALLOCATION


def test_phase57_portfolio_dimensions_and_claim_boundaries_are_exact() -> None:
    contracts = read_json(CONTRACT_ROOT / "quality-contracts.v1.json")
    journeys = read_json(CONTRACT_ROOT / "journey-manifest.json")
    matrix = read_json(CONTRACT_ROOT / "browser-viewport-profile-matrix.json")
    assert len(contracts["surfaces"]) == 9
    assert len(contracts["states"]) == 20
    assert len(journeys["journeys"]) == 14
    assert len(matrix["viewports"]) == 7
    assert len(matrix["resource_profiles"]) == 6
    assert matrix["primary"] == {
        "engine": "chromium",
        "channel": "msedge",
        "automatic_download": False,
    }
    assert matrix["missing_optional_policy"] == "blocked_or_unsupported_never_pass"
    assert contracts["production_claim_authorized"] is False


def test_phase57_replay_and_workloads_are_deterministic() -> None:
    cases_path = CONTRACT_ROOT / "generated-contract-cases.json"
    workloads = read_json(CONTRACT_ROOT / "generated-workloads.json")
    assert workloads["corpus_sha256"] == sha256(cases_path)
    assert len(workloads["replays"]) == 2
    assert {replay["sha256"] for replay in workloads["replays"]} == {
        workloads["corpus_sha256"]
    }
    assert [workload["id"] for workload in workloads["workloads"]] == ["C1", "C10", "C50"]
    assert sum(workload["case_count"] for workload in workloads["workloads"]) == 2048


def test_phase57_generated_records_have_no_prohibited_keys() -> None:
    generated = read_json(CONTRACT_ROOT / "generated-contract-cases.json")
    assert not (recursive_keys(generated) & FORBIDDEN_KEYS)
    assert all(case["generated_only"] is True for case in generated["cases"])
    assert all(case["authority"] in {"read_only", "mandatory_review", "non_effective"} for case in generated["cases"])


def test_phase57_dependency_baseline_is_byte_exact_and_not_refreshed() -> None:
    baseline = read_json(FRONTEND / "evidence/p5-7-dependency-baseline.json")
    assert baseline["status"] == "preserved_not_refreshed"
    assert baseline["resolution_download_install_update_or_lockfile_change"] is False
    assert baseline["vulnerability_refresh"] is False
    assert sha256(FRONTEND / "pnpm-lock.yaml") == baseline["lockfile"]["sha256"]
    assert sha256(FRONTEND / "sbom.cdx.json") == baseline["sbom"]["sha256"]
    assert sha256(FRONTEND / "dependency-evidence.json") == baseline["dependency_evidence"]["sha256"]


def test_phase57_source_manifest_binds_only_generated_quality_sources() -> None:
    manifest = read_json(CONTRACT_ROOT / "source-manifest.json")
    assert manifest["generated_only"] is True
    assert manifest["source_file_count"] == 5
    for entry in manifest["sources"]:
        path = ROOT / entry["path"]
        assert path.is_file()
        assert path.stat().st_size == entry["bytes"]
        assert sha256(path) == entry["sha256"]


def test_phase57_start_allowlists_are_complete_and_product_source_remains_closed() -> None:
    package = read_json(ROOT / "contracts/phase-5/p5-7-start-authorization-package.json")
    for relative in package["exact_additive_implementation_paths"]:
        assert (ROOT / relative).is_file(), relative
    assert package["existing_file_change_constraints"][-1].startswith(
        "application_and_existing_shared_package_source_remediation_is_not_authorized"
    )
    assert package["progress_boundary"]["P5_7_technical_cap_points_before_owner_acceptance"] == 11
    assert package["progress_boundary"]["P5_7_owner_acceptance_points"] == 1


def test_phase57_final_acceptance_remains_separate() -> None:
    acceptance = ROOT / "contracts/phase-5/p5-7-acceptance.json"
    if acceptance.exists():
        assert read_json(acceptance)["effective"] is True
    else:
        assert not acceptance.exists()
