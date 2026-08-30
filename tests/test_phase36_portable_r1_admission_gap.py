from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
GAP_PATH = CONTRACTS / "p3-6-portable-r1-admission-gap.json"
DECISIONS_PATH = CONTRACTS / "p3-6-portable-r1-decision-packet.json"
PACKAGE_PATH = CONTRACTS / "p3-6-portable-r1-admission-package.json"
DOCUMENT_PATH = DOCS / "p3-6-portable-r1-admission-gap.md"
PACKAGE_DIGEST = "471146FAD62F926648C71ED3FE5359F74DC47E8870562E3EAE92AAD1ED5A269F"
R1_DIGEST = "FB061C906D1CE5F7FE3B32B70F6CA5134C486F474E2618B23884466C2E58C76F"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_package_binds_exact_core_files_without_self_hash() -> None:
    package = _read(PACKAGE_PATH)
    expected = {
        "contracts/phase-3/p3-6-portable-r1-admission-gap.json": GAP_PATH,
        "contracts/phase-3/p3-6-portable-r1-decision-packet.json": DECISIONS_PATH,
        "docs/phase-3/p3-6-portable-r1-admission-gap.md": DOCUMENT_PATH,
    }
    recorded = {item["path"]: item["sha256"] for item in package["core_files"]}

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["core_file_count"] == 3
    assert recorded == {path: _sha256(file_path) for path, file_path in expected.items()}
    assert "package_digest" not in package


def test_gap_binds_exact_R1_portable_R0_and_phase_minus_1_revisions() -> None:
    gap = _read(GAP_PATH)
    inputs = gap["inputs"]

    assert inputs["inventory_R1"]["sha256"] == R1_DIGEST
    assert inputs["inventory_R1"]["schema_validation_status"] == (
        "passed_exact_shared_v1alpha1"
    )
    assert inputs["accepted_portable_R0_package"]["sha256"] == (
        "56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B"
    )
    assert inputs["phase_minus_1_contracts"]["revision"] == (
        "d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8"
    )
    assert inputs["phase_minus_1_deployment"]["revision"] == (
        "71095fe89d2b711e4982ddc0130fcaedda8703e7"
    )
    assert len(inputs["phase_minus_1_contracts"]["schemas"]) == 5


def test_R1_satisfies_inventory_shape_without_becoming_capacity_evidence() -> None:
    gap = _read(GAP_PATH)
    satisfied = set(gap["R1_satisfied_facts"])

    assert "shared_node_capability_inventory_shape" in satisfied
    assert "bounded_observation_and_validity_timestamps" in satisfied
    assert "model_runtime_compatibility" not in satisfied
    assert "allocatable_capacity" not in satisfied
    assert gap["inputs"]["inventory_R1"]["use_after_expiry"].startswith(
        "immutable_historical_evidence_only"
    )


def test_resolver_matrix_has_exactly_seven_inputs_and_only_inventory_exists() -> None:
    matrix = _read(GAP_PATH)["resolver_input_matrix"]
    states = {item["kind"]: item["state"] for item in matrix}

    assert set(states) == {
        "capability_inventory",
        "authorization_context",
        "policy_snapshot",
        "compatibility_snapshot",
        "workload_requirements",
        "pipeline_graph",
        "capacity_snapshot",
    }
    assert states["capability_inventory"].startswith("available_only")
    assert states["authorization_context"].startswith("missing")
    assert states["compatibility_snapshot"] == "missing"
    assert states["capacity_snapshot"].startswith("missing")


def test_gap_ledger_is_complete_sequential_and_fail_closed() -> None:
    gap = _read(GAP_PATH)
    gaps = gap["gaps"]

    assert gap["gap_count"] == len(gaps) == 22
    assert [item["gap_id"] for item in gaps] == [
        f"P36-R1-GAP-{index:02d}" for index in range(1, 23)
    ]
    assert gap["gate_effect"] == {
        "P36_G2": "blocked",
        "portable_profile_resolver_eligible": False,
        "portable_profile_activation_authorized": False,
        "inventory_collection_authorized": False,
        "runtime_execution_authorized": False,
        "implementation_authorized": False,
    }


def test_owner_packet_has_four_independent_unselected_A_to_D_choices() -> None:
    packet = _read(DECISIONS_PATH)

    assert packet["status"] == "owner_selections_pending_non_executable"
    assert packet["recommended_selection"] == "A/A/A/A"
    assert [item["decision_id"] for item in packet["decisions"]] == [
        "D-P3.6-U3B-001",
        "D-P3.6-U3B-002",
        "D-P3.6-U3B-003",
        "D-P3.6-U3B-004",
    ]
    for decision in packet["decisions"]:
        assert decision["recommended_option"] == "A"
        assert decision["selected_option"] is None
        assert [option["option"] for option in decision["options"]] == [
            "A",
            "B",
            "C",
            "D",
        ]


def test_recommended_AAAA_is_policy_only_and_grants_no_authority() -> None:
    packet = _read(DECISIONS_PATH)
    effect = packet["effect_if_recommended_AAAA_is_later_accepted"]

    assert effect["immediate_profile_eligibility"] is False
    assert effect["immediate_collection_authority"] is False
    assert effect["immediate_runtime_or_implementation_authority"] is False
    assert packet["owner_acceptance_may_be_inferred_from_continue_or_other_decision"] is False
    assert all(
        packet[field] is False
        for field in [
            "inventory_collection_authorized",
            "artifact_or_dependency_acquisition_authorized",
            "profile_resolution_or_activation_authorized",
            "runtime_or_model_execution_authorized",
            "hardware_testing_authorized",
            "container_or_kubernetes_action_authorized",
            "camera_media_or_data_access_authorized",
            "implementation_authorized",
            "deployment_authorized",
            "remote_git_authorized",
        ]
    )


def test_canonical_ledgers_link_package_and_keep_G2_blocked() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    gate_states = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert gate_states["P36-G2"] == "blocked"
    assert gates["portable_r1_admission_gap_package"]["digest_sha256"] == (
        PACKAGE_DIGEST
    )
    assert policy["portable_r1_admission_gap_package"][
        "package_digest_sha256"
    ] == PACKAGE_DIGEST
    assert policy["portable_r1_admission_gap_package"]["owner_selections_pending"]
    assert not policy["portable_r1_admission_gap_package"]["resolver_eligible"]
    assert unblock["portable_r1_admission_gap_package"][
        "package_digest_sha256"
    ] == PACKAGE_DIGEST
    assert unblock["next_inventory_planning_action"]["recommended_selection"] == (
        "A/A/A/A"
    )
    assert not unblock["next_inventory_planning_action"][
        "implementation_or_collection_authority"
    ]


def test_package_and_decision_indexes_are_synchronized() -> None:
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    phase_plan = (DOCS / "p3-6-plan.md").read_text(encoding="utf-8")
    unblock_doc = (DOCS / "p3-6-unblock-plan.md").read_text(encoding="utf-8")
    contracts_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    assert "DR-0057: P3.6 Portable CPU R1 Admission Gap R0" in decision_register
    assert PACKAGE_DIGEST in decision_register
    assert PACKAGE_DIGEST in backlog
    assert "p3-6-portable-r1-admission-gap.md" in phase_index
    assert PACKAGE_DIGEST in phase_plan
    assert "No selection may be inferred from `continue`" in unblock_doc
    assert "p3-6-portable-r1-admission-package.json" in contracts_index


def test_sealed_package_itself_grants_no_executable_authority() -> None:
    package = _read(PACKAGE_PATH)

    assert package["status"] == "sealed_non_effective_owner_selections_pending"
    assert package["owner_acceptance_may_be_inferred_from_continue_or_other_decision"] is False
    assert package["current_gate_effect"]["P36_G2"] == "blocked"
    assert all(
        package[field] is False
        for field in [
            "inventory_collection_authorized",
            "artifact_or_dependency_acquisition_authorized",
            "profile_resolution_or_activation_authorized",
            "runtime_or_model_execution_authorized",
            "hardware_testing_authorized",
            "container_or_kubernetes_action_authorized",
            "camera_media_or_data_access_authorized",
            "implementation_authorized",
            "deployment_authorized",
            "remote_git_authorized",
        ]
    )
