from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts/phase-5/p5-6"
FRONTEND = ROOT / "frontend"
EXPECTED_GROUPS = {
    "organization_identity_membership_role_capability_and_session": 176,
    "policy_changes_approval_SoD_ETag_and_idempotency": 192,
    "camera_stream_provider_secret_ref_feature_config_profile_and_retention": 176,
    "security_posture_denials_audit_refs_compliance_exceptions_and_attestations": 160,
    "supply_chain_service_health_queues_workers_circuits_and_degradation": 160,
    "SLO_budgets_storage_recovery_maintenance_capacity_and_topology": 128,
    "cross_department_hostile_input_redaction_overclaim_and_signal_separation": 80,
    "accessibility_handoff_state_and_cross_profile_equivalence": 48,
}
REQUIRED_RECORDS = {
    "admin-contracts.v1.json",
    "security-contracts.v1.json",
    "operations-contracts.v1.json",
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
        nested = set().union(*(recursive_keys(item) for item in value.values()), set())
        return {str(key).lower() for key in value} | nested
    if isinstance(value, list):
        return set().union(*(recursive_keys(item) for item in value), set())
    return set()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_phase56_record_set_and_case_distribution_are_exact() -> None:
    names = {path.name for path in CONTRACT_ROOT.glob("*.json")}
    assert REQUIRED_RECORDS <= names
    generated = read_json(CONTRACT_ROOT / "generated-contract-cases.json")
    assert generated["marker"] == "HCAM_GENERATED_ONLY_P5_6"
    assert generated["seed"] == "HCAM-P5.6-R0-2026-09-10"
    assert generated["exact_case_count"] == 1120
    assert len(generated["cases"]) == 1120
    assert len({case["ref"] for case in generated["cases"]}) == 1120
    assert {item["group"]: item["count"] for item in generated["groups"]} == EXPECTED_GROUPS


def test_phase56_generated_records_are_non_effective_and_field_minimized() -> None:
    cases = read_json(CONTRACT_ROOT / "generated-contract-cases.json")
    prohibited = read_json(CONTRACT_ROOT / "prohibited-field-manifest.json")
    assert prohibited["findings"] == 0
    assert prohibited["secret_values_retained"] == 0
    assert prohibited["raw_logs_retained"] == 0
    assert prohibited["media_or_model_bytes_retained"] == 0
    forbidden = {str(key).lower() for key in prohibited["forbidden_keys"]}
    assert not (recursive_keys(cases) & forbidden)
    assert all(case["generated"] is True for case in cases["cases"])
    assert all(case["effective"] is False for case in cases["cases"])


def test_phase56_workloads_and_replays_are_deterministic() -> None:
    workloads = read_json(CONTRACT_ROOT / "generated-workloads.json")
    assert [item["profile"] for item in workloads["workloads"]] == ["C1", "C10", "C50"]
    assert [item["departments"] for item in workloads["workloads"]] == [2, 10, 50]
    assert len({item["sha256"] for item in workloads["replays"]}) == 1
    assert all(item["hardware_claim"] is False for item in workloads["workloads"])
    assert all(item["production_claim"] is False for item in workloads["workloads"])


def test_phase56_contract_boundaries_are_explicit() -> None:
    admin = read_json(CONTRACT_ROOT / "admin-contracts.v1.json")
    security = read_json(CONTRACT_ROOT / "security-contracts.v1.json")
    operations = read_json(CONTRACT_ROOT / "operations-contracts.v1.json")
    assert admin["authorization"]["default_deny"] is True
    assert admin["authorization"]["postgresql_rls_equivalence"] is True
    assert admin["boundaries"]["effective_mutation"] is False
    assert admin["boundaries"]["break_glass"] is False
    assert security["signal_lanes"] == [
        "operational",
        "security",
        "audit",
        "evidence",
        "administrative",
    ]
    assert security["boundaries"]["secret_resolution"] is False
    assert security["boundaries"]["scanner_execution"] is False
    assert operations["boundaries"]["live_telemetry"] is False
    assert operations["boundaries"]["backup_restore_or_recovery_execution"] is False
    assert operations["profile_authority_invariant"] is True


def test_phase56_dependency_baseline_is_byte_stable() -> None:
    baseline = read_json(FRONTEND / "evidence/p5-6-dependency-baseline.json")
    assert baseline["result"] == "pass"
    assert baseline["package_manager_executed"] is False
    assert baseline["dependency_resolution"] is False
    assert sha256(FRONTEND / "pnpm-lock.yaml") == baseline["lockfile_sha256"]
    assert sha256(FRONTEND / "sbom.cdx.json") == baseline["sbom_sha256"]


def test_phase56_portal_source_preserves_truth_and_action_boundaries() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (
            FRONTEND / "apps/admin-center/src",
            FRONTEND / "apps/security-center/src",
            FRONTEND / "apps/operations-center/src",
        )
        for path in sorted(root.rglob("*.tsx"))
    )
    assert "no effective mutation" in source.lower()
    assert "no secret value" in source.lower()
    assert "not live telemetry" in source.lower()
    assert "Kill-switch control is unavailable" in source


def test_phase56_start_allowlist_and_exit_acceptance_remain_separate() -> None:
    start = read_json(ROOT / "contracts/phase-5/p5-6-start-authorization-package.json")
    for relative in start["exact_additive_implementation_paths"]:
        assert (ROOT / relative).is_file(), relative
    acceptance = ROOT / "contracts/phase-5/p5-6-acceptance.json"
    if acceptance.exists():
        assert read_json(acceptance)["effective"] is True
    else:
        assert not acceptance.exists()
