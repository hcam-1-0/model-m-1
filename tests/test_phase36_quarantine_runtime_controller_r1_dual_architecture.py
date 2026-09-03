from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
SELECTIONS = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-dual-architecture-owner-selections.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-dual-architecture-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-dual-architecture-planning-package.json"
)
REVIEW = DOCS / "p3-6-quarantine-runtime-controller-r1-dual-architecture-proposal.md"
R0_PACKAGE_DIGEST = (
    "30DE3B7E261568FC1DB6499C9975B600298BD8E3531858D2BC688E1BF5527592"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_owner_selections_are_recorded_without_inferring_r0_acceptance() -> None:
    record = _read(SELECTIONS)
    normalized = {
        item["decision_id"]: item["normalized_selection"]
        for item in record["selections"]
    }
    assert normalized == {
        "D-P3.6-U3S-001": "A+B",
        "D-P3.6-U3S-002": "A",
        "D-P3.6-U3S-003": "A",
        "D-P3.6-U3S-004": "A",
    }
    assert (
        record["original_planning_package"]["sha256"] == R0_PACKAGE_DIGEST
    )
    assert (
        record["original_planning_package"]["exact_acceptance_template_satisfied"]
        is False
    )
    assert record["current_effect"]["controller_or_test_implementation_authorized"] is False


def test_dual_controllers_have_non_overlapping_default_authority() -> None:
    proposal = _read(PROPOSAL)
    assert proposal["PowerShell_controller"]["default_machine_action_authority"] is True
    assert proposal["Python_controller"]["default_machine_API_access"] is False
    assert proposal["Python_controller"]["default_subprocess_execution"] is False
    policy = proposal["authority_and_failover_policy"]
    assert policy["default_executor"] == "PowerShell_controller"
    assert policy["Python_controller_is_runtime_fallback"] is False
    assert policy["simultaneous_machine_execution"] is False
    assert policy["automatic_failover"] is False
    assert policy["automatic_retry"] is False


def test_shared_contract_and_cross_language_divergence_fail_closed() -> None:
    proposal = _read(PROPOSAL)
    shared = proposal["shared_contract_layer"]
    assert shared["implementation_specific_schema_extensions_allowed"] is False
    assert shared["unknown_field_policy"] == "reject"
    assert shared["unknown_reason_code_policy"] == "fail_closed_as_result_contract_invalid"
    assert (
        proposal["authority_and_failover_policy"][
            "PowerShell_Python_policy_disagreement"
        ]
        == "terminal_fail_closed"
    )
    generated = proposal["generated_validation_policy"]
    assert generated["cross_language_projection_equivalence_required"] is True
    assert generated["machine_API_or_runtime_execution_in_source_acceptance_suite"] is False


def test_three_gate_reentry_keeps_runtime_and_u3k_closed() -> None:
    proposal = _read(PROPOSAL)
    gates = proposal["three_gate_reentry_sequence"]
    assert [gate["gate"] for gate in gates] == [
        "U3S_SOURCE_IMPLEMENTATION",
        "U3T_PREFLIGHT_ONLY_RUNTIME_DIAGNOSTIC",
        "LATER_FULL_GENERATED_VALIDATION",
    ]
    assert gates[0]["runtime_or_machine_observation"] is False
    assert gates[1]["Python_machine_execution"] is False
    assert gates[2]["U3K_authority"] is False
    effect = proposal["effect_if_R1_package_accepted"]
    assert effect["implementation_authorized"] is False
    assert effect["retry_or_generated_validation_authorized"] is False
    assert effect["U3K_authorized"] is False


def test_r1_package_is_additive_bound_and_non_effective() -> None:
    package = _read(PACKAGE)
    assert package["core_file_count"] == 4
    assert package["supersession_policy"]["R0_package_modified"] is False
    assert package["supersession_policy"]["R0_exact_acceptance_recorded"] is False
    assert package["recorded_selections"] == {
        "D-P3.6-U3S-001": "A+B",
        "D-P3.6-U3S-002": "A",
        "D-P3.6-U3S-003": "A",
        "D-P3.6-U3S-004": "A",
    }
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    gate = package["current_gate_effect"]
    assert gate["revised_R1_acceptance_pending"] is True
    assert gate["attempts_authorized"] == 0
    assert gate["source_or_test_implementation_authorized"] is False
    assert gate["PowerShell_or_Python_execution_authorized"] is False
    assert gate["Python_machine_access_or_fallback_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["U3K_authorized"] is False


def test_r1_records_and_review_use_lf() -> None:
    for path in (SELECTIONS, PROPOSAL, PACKAGE, REVIEW, Path(__file__)):
        assert b"\r\n" not in path.read_bytes()
