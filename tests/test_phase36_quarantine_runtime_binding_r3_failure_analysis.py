from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r0-remediation-planning-package.json"
)

ATTEMPT_DIGESTS = {
    "p3-6-quarantine-generated-validation-runtime-binding-r3-authorization.json": (
        "D7A51E7F4F806F959F437E678C31FC93769FD34B3305EE04DD08290E98D15C2B"
    ),
    "p3-6-quarantine-generated-validation-runtime-binding-r3-result.json": (
        "497AF7FFA6EEC1B08611FCEB184AC7597A2666B26DF7A6705F3B1BDF9E460C71"
    ),
    "p3-6-quarantine-generated-validation-runtime-binding-r3-evidence.json": (
        "59E8DE24BD6099BCE2BB197E57300B49606FAFE66A4B0CCCBF6348A7BBEB3059"
    ),
}


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_consumed_attempt_records_remain_exact_and_fail_closed() -> None:
    for name, digest in ATTEMPT_DIGESTS.items():
        assert _sha256(CONTRACTS / name) == digest

    authorization = _read(
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r3-authorization.json"
    )
    result = _read(
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r3-result.json"
    )
    evidence = _read(
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r3-evidence.json"
    )
    assert authorization["effective_for_additional_attempt"] is False
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert result["reason_code"] == "runtime_binding_failed"
    assert result["process_boundary"]["aggregate_invocation_count"] == 0
    assert evidence["gate_effect"]["authorization_reusable"] is False
    assert evidence["gate_effect"]["U3K_package_preparation_authorized"] is False


def test_failure_analysis_distinguishes_facts_hypotheses_and_authority() -> None:
    analysis = _read(
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r3-failure-analysis-r0.json"
    )
    assert analysis["root_cause_assessment"]["root_cause_confirmed"] is False
    assert len(analysis["hypotheses"]) == 4
    assert analysis["non_attempt_transport_event"]["attempt_consumed"] is False
    assert analysis["gate_effect"]["source_or_test_implementation_authorized"] is False
    assert analysis["gate_effect"]["runtime_or_machine_observation_authorized"] is False
    assert analysis["gate_effect"]["retry_authorized"] is False


def test_decision_packet_contains_four_complete_a_to_d_choices() -> None:
    packet = _read(
        CONTRACTS
        / "p3-6-quarantine-runtime-controller-r0-remediation-decision-packet.json"
    )
    decisions = packet["decisions"]
    assert [decision["decision_id"] for decision in decisions] == [
        "D-P3.6-U3S-001",
        "D-P3.6-U3S-002",
        "D-P3.6-U3S-003",
        "D-P3.6-U3S-004",
    ]
    for decision in decisions:
        assert decision["recommended_option"] == "A"
        assert set(decision["options"]) == {"A", "B", "C", "D"}
    effect = packet["effect_of_owner_selection"]
    assert effect["prepare_separate_source_only_controller_implementation_authorization_proposal"] is True
    assert effect["implementation_authorized"] is False
    assert effect["runtime_or_machine_observation_authorized"] is False
    assert effect["retry_authorized"] is False


def test_planning_package_binds_all_core_files_and_grants_zero_authority() -> None:
    package = _read(PACKAGE)
    assert package["core_file_count"] == 6
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["recommended_selection"] == "A/A/A/A"
    assert all(item["selected_option"] is None for item in package["owner_decisions"])
    gate = package["current_gate_effect"]
    assert gate["owner_decisions_pending"] is True
    assert gate["attempts_authorized"] == 0
    assert gate["controller_source_or_test_modification_authorized"] is False
    assert gate["PowerShell_parse_import_or_execution_authorized"] is False
    assert gate["runtime_manifest_hardware_or_machine_observation_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["U3K_authorized"] is False


def test_human_review_document_and_new_records_use_lf() -> None:
    paths = [
        DOCS / "p3-6-quarantine-runtime-controller-r0-remediation-decision-packet.md",
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r3-authorization.json",
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r3-result.json",
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r3-evidence.json",
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r3-failure-analysis-r0.json",
        CONTRACTS
        / "p3-6-quarantine-runtime-controller-r0-remediation-decision-packet.json",
        PACKAGE,
        Path(__file__),
    ]
    for path in paths:
        assert b"\r\n" not in path.read_bytes()
