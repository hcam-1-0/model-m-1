from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
ACCEPTANCE_PATH = CONTRACTS / "p3-6-portable-r1-owner-decisions.json"
PACKAGE_PATH = CONTRACTS / "p3-6-portable-r1-admission-package.json"
DECISIONS_PATH = CONTRACTS / "p3-6-portable-r1-decision-packet.json"
PACKAGE_DIGEST = "471146FAD62F926648C71ED3FE5359F74DC47E8870562E3EAE92AAD1ED5A269F"
ACCEPTANCE_DIGEST = "7695027BB68878ED7CE41B6BD940EB777CD280279294E5C35B99614C3C57F5FA"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_acceptance_binds_exact_sealed_package_and_owner_statement() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert _sha256(ACCEPTANCE_PATH) == ACCEPTANCE_DIGEST
    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert acceptance["package_digest_sha256"] == PACKAGE_DIGEST
    assert acceptance["accepted_by"] == "mayank-admin"
    assert acceptance["status"] == "accepted_planning_policy_only_non_effective"
    assert acceptance["owner_statement_received"] == (
        "D-P3.6-U3B-001: A\n"
        "D-P3.6-U3B-002: A\n"
        "D-P3.6-U3B-003: A\n"
        "D-P3.6-U3B-004: A"
    )


def test_all_four_recommended_options_are_explicitly_selected() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    packet = _read(DECISIONS_PATH)

    assert [item["decision_id"] for item in acceptance["selections"]] == [
        "D-P3.6-U3B-001",
        "D-P3.6-U3B-002",
        "D-P3.6-U3B-003",
        "D-P3.6-U3B-004",
    ]
    assert [item["selected_option"] for item in acceptance["selections"]] == [
        "A",
        "A",
        "A",
        "A",
    ]
    assert all(item["recommended_option"] == "A" for item in packet["decisions"])


def test_R1_was_fresh_at_acceptance_but_is_not_profile_admission() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    inventory_state = acceptance["inventory_R1_state_at_acceptance"]
    accepted_at = _timestamp(acceptance["accepted_at"])
    valid_until = _timestamp(inventory_state["valid_until"])

    assert accepted_at < valid_until
    assert inventory_state["freshness_at_acceptance"] == (
        "fresh_within_accepted_24_hour_window"
    )
    assert inventory_state["admission_use"].startswith("inventory_input_only")
    assert inventory_state["refresh_now_authorized"] is False
    assert acceptance["accepted_effect"]["portable_profile_resolver_eligible"] is False
    assert acceptance["accepted_effect"]["P36_G2"] == "blocked"


def test_AAAA_policy_is_fail_closed_complete_and_generated_only() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    policies = {
        item["decision_id"]: item["accepted_policy"]
        for item in acceptance["selections"]
    }

    assert policies == {
        "D-P3.6-U3B-001": "just_in_time_digest_bound_refresh",
        "D-P3.6-U3B-002": "strict_seven_input_fail_closed_admission",
        "D-P3.6-U3B-003": "complete_immutable_compatibility_bundle",
        "D-P3.6-U3B-004": (
            "deterministic_generated_only_CONTRACT_and_C1_INFER_matrix"
        ),
    }
    assert acceptance["accepted_effect"]["remaining_evidence_gap_count"] == 22
    assert acceptance["accepted_effect"]["next_executable_action"] == "none"


def test_acceptance_grants_no_collection_execution_or_implementation() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert all(
        acceptance[field] is False
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
    assert set(acceptance["continuing_non_authorization"]) >= {
        "inventory_recollection_or_reusable_collector",
        "runtime_model_inference_or_benchmark_execution",
        "profile_resolution_admission_activation_or_placement",
        "deployment",
        "remote_git",
    }


def test_canonical_ledgers_record_acceptance_without_opening_G2() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    gate_states = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert gate_states["P36-G2"] == "blocked"
    for ledger in [gates, policy, unblock]:
        state = ledger["portable_r1_admission_gap_package"]
        assert state["selected_options"] == "A/A/A/A"
        assert state["owner_selections_pending"] is False
        assert state["acceptance_record"].endswith(
            "p3-6-portable-r1-owner-decisions.json"
        )
        assert state["profile_activation_authorized"] is False
    assert unblock["next_portable_planning_action"][
        "implementation_or_runtime_authority"
    ] is False
    assert unblock["runtime_execution_authorized"] is False


def test_human_records_and_indexes_are_synchronized() -> None:
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    profile_doc = (DOCS / "p3-6-capability-profiles.md").read_text(
        encoding="utf-8"
    )
    contracts_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    assert "DR-0058: P3.6 Portable R1 Admission Policies Accepted" in (
        decision_register
    )
    assert PACKAGE_DIGEST in decision_register
    assert "accepted the recommended `A/A/A/A` planning policies" in backlog
    assert "owner accepted as `A/A/A/A` planning policy only" in " ".join(
        phase_index.split()
    )
    assert "U3B `A/A/A/A` admission" in profile_doc
    assert "p3-6-portable-r1-owner-decisions.json" in contracts_index
