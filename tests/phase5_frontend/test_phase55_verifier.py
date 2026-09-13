from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts/phase-5/p5-5"
FRONTEND = ROOT / "frontend"
EXPECTED_GROUPS = {
    "chronology": 128,
    "reconstruction_comparison": 128,
    "correction_retraction": 128,
    "evidence_state_matrix": 160,
    "provenance_custody": 128,
    "authorization_concurrency": 96,
    "accessibility_localization": 96,
    "handoff_teardown": 96,
}
REQUIRED_RECORDS = {
    "investigation-contracts.v1.json",
    "evidence-contracts.v1.json",
    "generated-contract-cases.json",
    "generated-workloads.json",
    "prohibited-field-manifest.json",
    "source-manifest.json",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def recursive_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key).lower() for key in value} | set().union(
            *(recursive_keys(item) for item in value.values()), set()
        )
    if isinstance(value, list):
        return set().union(*(recursive_keys(item) for item in value), set())
    return set()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_phase55_record_set_and_case_distribution_are_exact() -> None:
    names = {path.name for path in CONTRACT_ROOT.glob("*.json")}
    assert REQUIRED_RECORDS <= names
    generated = read_json(CONTRACT_ROOT / "generated-contract-cases.json")
    assert generated["marker"] == "HCAM_GENERATED_ONLY_P5_5"
    assert generated["exact_case_count"] == 960
    assert len(generated["cases"]) == 960
    assert len({case["case_ref"] for case in generated["cases"]}) == 960
    assert {item["group"]: item["count"] for item in generated["groups"]} == EXPECTED_GROUPS


def test_phase55_generated_records_are_non_operational_and_field_minimized() -> None:
    cases = read_json(CONTRACT_ROOT / "generated-contract-cases.json")
    prohibited = read_json(CONTRACT_ROOT / "prohibited-field-manifest.json")
    assert prohibited["findings"] == 0
    assert prohibited["source_and_media_retention_bytes"] == 0
    assert not (recursive_keys(cases) & set(prohibited["forbidden_keys"]))
    assert all(case["generated"] is True for case in cases["cases"])
    assert all(case["operational_authority"] is False for case in cases["cases"])


def test_phase55_workloads_and_replays_are_deterministic() -> None:
    workloads = read_json(CONTRACT_ROOT / "generated-workloads.json")
    assert [item["profile"] for item in workloads["workloads"]] == ["C1", "C10", "C50"]
    assert [item["investigations"] for item in workloads["workloads"]] == [1, 10, 50]
    assert len({item["sha256"] for item in workloads["replays"]}) == 1
    assert all(item["retained_source_bytes"] == 0 for item in workloads["workloads"])
    assert all(item["capacity_claim"] is False for item in workloads["workloads"])


def test_phase55_source_and_evidence_boundaries_are_explicit() -> None:
    investigation = read_json(CONTRACT_ROOT / "investigation-contracts.v1.json")
    evidence = read_json(CONTRACT_ROOT / "evidence-contracts.v1.json")
    assert investigation["chronology_authority"] == "record_sequence"
    assert investigation["boundaries"]["append_only_history"] is True
    assert investigation["boundaries"]["operational_actions"] is False
    assert len(evidence["orthogonal_state_axes"]) == 7
    assert evidence["boundaries"]["integrity_is_not_truth"] is True
    assert evidence["boundaries"]["source_resolution"] is False
    assert evidence["boundaries"]["media_rendering"] is False


def test_phase55_dependency_baseline_is_byte_stable() -> None:
    baseline = read_json(FRONTEND / "evidence/p5-5-dependency-baseline.json")
    assert baseline["result"] == "pass"
    assert baseline["further_package_manager_execution"] is False
    assert sha256(FRONTEND / "pnpm-lock.yaml") == baseline["lockfile_sha256"]
    assert sha256(FRONTEND / "sbom.cdx.json") == baseline["sbom_sha256"]


def test_phase55_ui_source_has_required_truth_and_operation_boundaries() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (
            FRONTEND / "apps/investigation-center/src",
            FRONTEND / "apps/evidence-center/src",
        )
        for path in sorted(root.rglob("*.tsx"))
    )
    assert "Record sequence is authoritative" in source
    assert "Integrity is not truth" in source
    assert "Source operations unavailable" in source
    assert "No source bytes" in source


def test_phase55_exit_acceptance_is_separate() -> None:
    acceptance = ROOT / "contracts/phase-5/p5-5-acceptance.json"
    if acceptance.exists():
        assert read_json(acceptance)["effective"] is True
    else:
        assert not acceptance.exists()
