from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
STEM = "p3-6-portable-r1-supply-chain-prerequisite"
ACCEPTANCE_PATH = CONTRACTS / f"{STEM}-owner-decisions.json"
PACKAGE_PATH = CONTRACTS / f"{STEM}-package.json"
DECISIONS_PATH = CONTRACTS / f"{STEM}-decision-packet.json"
PACKAGE_DIGEST = "496F4A9C7D6325868283589EAA108F4A26C9CAE3F7BE49102685706CCC2AA16B"
ACCEPTANCE_DIGEST = (
    "F68BDE02AF96E3992A8C64F1F01A85CAC960F529946EA12FA4899D9EBFC197A9"
)
U3E_PACKAGE_DIGEST = (
    "9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_acceptance_binds_exact_package_and_owner_statement() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert _sha256(ACCEPTANCE_PATH) == ACCEPTANCE_DIGEST
    assert acceptance["package_digest_sha256"] == PACKAGE_DIGEST
    assert acceptance["accepted_by"] == "mayank-admin"
    assert acceptance["status"] == "accepted_planning_policy_only_non_effective"
    assert acceptance["owner_statement_received"] == (
        "D-P3.6-U3D-001: A\n"
        "D-P3.6-U3D-002: A\n"
        "D-P3.6-U3D-003: A\n"
        "D-P3.6-U3D-004: A\n"
        "D-P3.6-U3D-005: A"
    )


def test_all_five_A_options_are_selected_without_mutating_packet() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    packet = _read(DECISIONS_PATH)

    assert [item["decision_id"] for item in acceptance["selections"]] == [
        "D-P3.6-U3D-001",
        "D-P3.6-U3D-002",
        "D-P3.6-U3D-003",
        "D-P3.6-U3D-004",
        "D-P3.6-U3D-005",
    ]
    assert all(
        item["selected_option"] == "A" for item in acceptance["selections"]
    )
    assert all(item["recommended_option"] == "A" for item in packet["decisions"])
    assert all(item["selected_option"] is None for item in packet["decisions"])


def test_AAAAA_policies_preserve_fail_closed_supply_chain_boundaries() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    policies = {
        item["decision_id"]: item["accepted_policy"]
        for item in acceptance["selections"]
    }

    assert policies == {
        "D-P3.6-U3D-001": (
            "owner_supplied_local_fixed_root_with_separate_bounded_attestation"
        ),
        "D-P3.6-U3D-002": (
            "Defender_plus_ModelScan_plus_framework_free_passive_inspector"
        ),
        "D-P3.6-U3D-003": (
            "all_layers_clean_supported_complete_and_fail_closed"
        ),
        "D-P3.6-U3D-004": (
            "sequential_partial_hash_scan_ML_BOM_atomic_seal"
        ),
        "D-P3.6-U3D-005": (
            "immutable_passive_R1_then_separately_authorized_generated_only_R2"
        ),
    }


def test_acceptance_changes_no_storage_scanner_profile_or_execution_gate() -> None:
    effect = _read(ACCEPTANCE_PATH)["accepted_effect"]

    assert effect["planning_policy_selected"] is True
    assert effect["exact_storage_root_bound"] is False
    assert effect["storage_attestation_exists"] is False
    assert effect["scanner_chain_bound_or_installed"] is False
    assert effect["artifact_acquisition_authorized"] is False
    assert effect["R1_supply_chain_evidence_exists"] is False
    assert effect["R2_runtime_or_calibration_authorized"] is False
    assert effect["portable_profile_resolver_eligible"] is False
    assert effect["portable_profile_activation_authorized"] is False
    assert [effect[gate] for gate in ["P36_G1", "P36_G2", "P36_G4", "P36_G5"]] == [
        "blocked",
        "blocked",
        "blocked",
        "blocked",
    ]
    assert effect["next_executable_action"] == "none"


def test_acceptance_grants_no_query_write_install_acquisition_or_execution() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    for field in [
        "storage_or_hardware_query_authorized",
        "storage_write_probe_or_cleanup_authorized",
        "scanner_query_install_or_execution_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "runtime_or_model_execution_authorized",
        "hardware_testing_authorized",
        "profile_resolution_or_activation_authorized",
        "container_or_kubernetes_action_authorized",
        "camera_media_or_data_access_authorized",
        "implementation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert acceptance[field] is False


def test_canonical_ledgers_record_acceptance_without_opening_gates() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    gate_states = {item["gate_id"]: item["state"] for item in gates["gates"]}
    gate_summaries = {
        item["gate_id"]: item["summary"] for item in gates["gates"]
    }

    assert gate_states["P36-G2"] == "blocked"
    assert gate_states["P36-G4"] == "blocked"
    assert "U3D A/A/A/A/A policies are owner accepted" in gate_summaries["P36-G2"]
    assert "U3D A/A/A/A/A supply-chain policies" in gate_summaries["P36-G4"]
    assert "owner review" not in gate_summaries["P36-G4"]
    for ledger in [gates, policy, unblock]:
        state = ledger["portable_r1_supply_chain_prerequisite_package"]
        assert state["selected_options"] == "A/A/A/A/A"
        assert state["owner_selections_pending"] is False
        assert state["acceptance_record"].endswith(f"{STEM}-owner-decisions.json")
        assert state["acceptance_sha256"] == ACCEPTANCE_DIGEST
        assert state["exact_quarantine_root_bound"] is False
        assert state["exact_scanner_chain_bound"] is False
        assert state["artifact_or_dependency_acquisition_authorized"] is False
        assert state["profile_activation_authorized"] is False


def test_next_action_is_exact_U3E_owner_review() -> None:
    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_portable_planning_action"
    ]

    assert action["action"] == (
        "owner_review_D_P3_6_U3E_BINDING_R0_AUTH_against_exact_sealed_package"
    )
    assert action["package_digest_sha256"] == U3E_PACKAGE_DIGEST
    assert action["candidate_root"] == "F:\\HCAM-Quarantine"
    assert action["owner_authorization_pending"] is True
    assert action["implementation_or_runtime_authority"] is False
    assert action["artifact_or_dependency_acquisition_authority"] is False
    assert action["profile_activation_authority"] is False


def test_human_records_and_indexes_are_synchronized() -> None:
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    acceptances = (DOCS / "p3-6-planning-acceptances.md").read_text(
        encoding="utf-8"
    )
    contracts_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    for text in [decision_register, acceptances, contracts_index]:
        assert ACCEPTANCE_DIGEST in text
    assert "policies accepted" in decision_register
    assert "accepted the five U3D choices as `A/A/A/A/A`" in backlog
    assert "owner accepted as `A/A/A/A/A` planning policy" in phase_index
    assert f"{STEM}-owner-decisions.json" in contracts_index
