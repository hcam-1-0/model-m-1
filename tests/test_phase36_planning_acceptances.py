from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_portable_acceptance_binds_exact_package_without_activation() -> None:
    record = _read(CONTRACTS / "p3-6-portable-cpu-profile-acceptance.json")
    package = CONTRACTS / "p3-6-portable-cpu-profile-package.json"

    assert record["decision_id"] == "D-P3.6-PORTABLE-PROPOSAL-R0-ACCEPTANCE"
    assert record["package_digest_sha256"] == _sha256(package)
    assert record["status"] == "accepted_planning_package_only"
    assert record["inventory_recollection_authorized"] is False
    assert record["profile_activation_authorized"] is False
    assert record["runtime_execution_authorized"] is False
    assert record["implementation_authorized"] is False


def test_inventory_policy_acceptance_binds_exact_a_a_a_a_selection() -> None:
    record = _read(CONTRACTS / "p3-6-inventory-admission-owner-decisions.json")
    package = CONTRACTS / "p3-6-inventory-admission-package.json"

    assert record["package_digest_sha256"] == _sha256(package)
    assert [item["decision_id"] for item in record["decisions"]] == [
        "D-P3.6-U3A-001",
        "D-P3.6-U3A-002",
        "D-P3.6-U3A-003",
        "D-P3.6-U3A-004",
    ]
    assert [item["selected_option"] for item in record["decisions"]] == [
        "A",
        "A",
        "A",
        "A",
    ]
    assert record["accepted_policy"]["freshness_window_seconds"] == 86400
    assert record["current_R0_effect"]["preserved"] is True
    assert record["current_R0_effect"]["admission_eligible"] is False
    assert record["inventory_recollection_authorized"] is False


def test_model_metadata_acceptance_binds_package_without_acquisition() -> None:
    record = _read(CONTRACTS / "p3-6-model-artifact-research-acceptance.json")
    package = CONTRACTS / "p3-6-model-artifact-research-package.json"

    assert record["decision_id"] == "D-P3.6-MODEL-PROPOSAL-R0-ACCEPTANCE"
    assert record["package_digest_sha256"] == _sha256(package)
    assert record["accepted_metadata_candidates"] == ["DET-E1", "DET-B1", "DET-A1"]
    assert record["artifact_acquisition_authorized"] is False
    assert record["runtime_execution_authorized"] is False
    assert record["implementation_authorized"] is False


def test_acceptance_records_use_exact_owner_and_source_head() -> None:
    paths = [
        CONTRACTS / "p3-6-portable-cpu-profile-acceptance.json",
        CONTRACTS / "p3-6-inventory-admission-owner-decisions.json",
        CONTRACTS / "p3-6-model-artifact-research-acceptance.json",
    ]
    for path in paths:
        record = _read(path)
        assert record["accepted_by"] == "mayank-admin"
        assert record["accepted_on"] == "2026-08-30"
        assert record["accepted_repository_head"] == (
            "af97ebff2add80de599a9386c3fedda07834f3df"
        )
        assert record["remote_git_authorized"] is False


def test_acceptance_summary_preserves_blocked_gate_state() -> None:
    summary = (DOCS / "p3-6-planning-acceptances.md").read_text(encoding="utf-8")

    assert "`P36-G1` | Blocked" in summary
    assert "`P36-G2` | Blocked" in summary
    assert "`P36-G4` | Blocked" in summary
    assert "`P36-G5` | Blocked" in summary
    assert "D-P3.6-INVENTORY-R1-AUTH" in summary
    assert "D-P3.6-MODEL-RESEARCH-R1-AUTH" in summary


def test_canonical_gate_policy_and_unblock_records_apply_acceptances() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")

    states = {gate["gate_id"]: gate["state"] for gate in gates["gates"]}
    assert states["P36-G1"] == "blocked"
    assert states["P36-G2"] == "blocked"
    assert states["P36-G4"] == "blocked"
    assert states["P36-G5"] == "blocked"

    assert gates["portable_cpu_profile_proposal"]["status"].startswith("accepted")
    assert gates["model_artifact_research_package"]["status"].startswith("accepted")
    assert gates["inventory_admission_gap_package"]["status"].startswith(
        "owner_policy_selections_accepted"
    )
    assert policy["inventory_admission_gap"]["owner_policy_selections_pending"] is False
    assert policy["inventory_admission_gap"]["owner_policy_selection"] == "A/A/A/A"
    assert unblock["next_inventory_planning_action"]["implementation_or_collection_authority"] is False


def test_acceptance_records_are_indexed_without_mutating_sealed_packages() -> None:
    phase_readme = (DOCS / "README.md").read_text(encoding="utf-8")
    contracts_readme = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    assert "p3-6-planning-acceptances.md" in phase_readme
    assert "p3-6-portable-cpu-profile-acceptance.json" in contracts_readme
    assert "p3-6-inventory-admission-owner-decisions.json" in contracts_readme
    assert "p3-6-model-artifact-research-acceptance.json" in contracts_readme
