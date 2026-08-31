from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
ACCEPTANCE_PATH = (
    CONTRACTS / "p3-6-portable-compatibility-validation-owner-decisions.json"
)
PACKAGE_PATH = CONTRACTS / "p3-6-portable-compatibility-validation-package.json"
DECISIONS_PATH = (
    CONTRACTS / "p3-6-portable-compatibility-validation-decision-packet.json"
)
PACKAGE_DIGEST = "9727D15FDAA49A0DEE06327A41E772762F3D7A2560A5F4BDEFAA6EC3FDEFCD3A"
U3F_PACKAGE_DIGEST = (
    "9EBE27812F6E1D8D52728248B33B54A852FECCD59E0BB8B0F919925461DF4F78"
)
ACCEPTANCE_DIGEST = (
    "FECF3EF71F5A7550871C91BF3A58BFA9D279A88C312A4E96019EC2457821CA77"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_acceptance_binds_exact_sealed_package_and_owner_statement() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert _sha256(ACCEPTANCE_PATH) == ACCEPTANCE_DIGEST
    assert acceptance["package_digest_sha256"] == PACKAGE_DIGEST
    assert acceptance["accepted_by"] == "mayank-admin"
    assert acceptance["status"] == "accepted_planning_policy_only_non_effective"
    assert acceptance["owner_statement_received"] == (
        "D-P3.6-U3C-001: A\n"
        "D-P3.6-U3C-002: A\n"
        "D-P3.6-U3C-003: A\n"
        "D-P3.6-U3C-004: A"
    )


def test_all_four_recommended_options_are_selected_separately_from_packet() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    packet = _read(DECISIONS_PATH)

    assert [item["decision_id"] for item in acceptance["selections"]] == [
        "D-P3.6-U3C-001",
        "D-P3.6-U3C-002",
        "D-P3.6-U3C-003",
        "D-P3.6-U3C-004",
    ]
    assert [item["selected_option"] for item in acceptance["selections"]] == [
        "A",
        "A",
        "A",
        "A",
    ]
    assert all(item["recommended_option"] == "A" for item in packet["decisions"])
    assert all(item["selected_option"] is None for item in packet["decisions"])


def test_AAAA_policies_preserve_exact_runtime_workload_gate_and_lifecycle() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    policies = {
        item["decision_id"]: item["accepted_policy"]
        for item in acceptance["selections"]
    }

    assert policies == {
        "D-P3.6-U3C-001": "deterministic_low_contention_CPU_reference",
        "D-P3.6-U3C-002": (
            "bounded_three_seed_CONTRACT_plus_C1_INFER_matrix"
        ),
        "D-P3.6-U3C-003": (
            "hard_safety_then_non_promotional_calibration_then_sealed_"
            "held_out_validation"
        ),
        "D-P3.6-U3C-004": (
            "five_revision_immutable_compatibility_lifecycle"
        ),
    }


def test_acceptance_changes_no_profile_or_execution_gate() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    effect = acceptance["accepted_effect"]

    assert effect["planning_policy_selected"] is True
    assert effect["compatibility_manifest_exists"] is False
    assert effect["generated_validation_evidence_exists"] is False
    assert effect["numeric_promotional_thresholds_exist"] is False
    assert effect["portable_profile_resolver_eligible"] is False
    assert effect["portable_profile_activation_authorized"] is False
    assert effect["P36_G2"] == "blocked"
    assert effect["next_executable_action"] == "none"


def test_acceptance_grants_no_acquisition_execution_or_implementation() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert all(
        acceptance[field] is False
        for field in [
            "inventory_collection_authorized",
            "artifact_or_dependency_acquisition_authorized",
            "runtime_or_model_execution_authorized",
            "hardware_testing_authorized",
            "profile_resolution_or_activation_authorized",
            "container_or_kubernetes_action_authorized",
            "camera_media_or_data_access_authorized",
            "implementation_authorized",
            "deployment_authorized",
            "remote_git_authorized",
        ]
    )


def test_canonical_ledgers_record_acceptance_without_opening_G2() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    gate_states = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert gate_states["P36-G2"] == "blocked"
    for ledger in [gates, policy, unblock]:
        state = ledger["portable_compatibility_validation_package"]
        assert state["selected_options"] == "A/A/A/A"
        assert state["owner_selections_pending"] is False
        assert state["acceptance_record"].endswith(
            "p3-6-portable-compatibility-validation-owner-decisions.json"
        )
        assert state["acceptance_sha256"] == ACCEPTANCE_DIGEST
        assert state["profile_activation_authorized"] is False
    assert unblock["next_portable_planning_action"][
        "implementation_or_runtime_authority"
    ] is False
    assert unblock["next_portable_planning_action"][
        "artifact_or_dependency_acquisition_authority"
    ] is False
    assert unblock["runtime_execution_authorized"] is False


def test_consumed_U3E_path_advances_to_U3F_owner_choices() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    action = unblock["next_portable_planning_action"]

    assert acceptance["accepted_effect"]["next_planning_output"] == (
        "non_executable_R1_artifact_supply_chain_and_generated_calibration_"
        "authorization_prerequisites"
    )
    assert action["action"] == (
        "owner_select_D_P3_6_U3F_001_through_006_against_exact_sealed_"
        "decision_package"
    )
    assert action["package_digest_sha256"] == U3F_PACKAGE_DIGEST
    assert action["candidate_root"] == "F:\\HCAM-Quarantine"
    assert action["owner_selections_pending"] is True
    assert action["another_attempt_authority"] is False
    assert action["status"] == "sealed_non_effective_owner_selections_pending"


def test_human_records_and_indexes_are_synchronized() -> None:
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    acceptances = (DOCS / "p3-6-planning-acceptances.md").read_text(
        encoding="utf-8"
    )
    profile = (DOCS / "p3-6-capability-profiles.md").read_text(encoding="utf-8")
    contracts_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    assert "DR-0059: Portable compatibility" in decision_register
    assert ACCEPTANCE_DIGEST in decision_register
    assert "accepted the four U3C choices as `A/A/A/A`" in backlog
    assert "U3C `A/A/A/A` planning policies are owner accepted" in phase_index
    assert "Portable Compatibility And Generated C1 Policies" in acceptances
    assert "U3C `A/A/A/A` planning policies are owner accepted" in profile
    assert "p3-6-portable-compatibility-validation-owner-decisions.json" in (
        contracts_index
    )
