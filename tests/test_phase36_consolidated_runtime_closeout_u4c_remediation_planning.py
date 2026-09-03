from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

AUTHORIZATION = CONTRACTS / "p3-6-consolidated-runtime-closeout-authorization.json"
RESULT = CONTRACTS / "p3-6-consolidated-runtime-closeout-result.json"
EVIDENCE = CONTRACTS / "p3-6-consolidated-runtime-closeout-evidence.json"
ANALYSIS = CONTRACTS / "p3-6-consolidated-runtime-closeout-r1-failure-analysis.json"
DECISIONS = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4c-remediation-decision-packet.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4c-remediation-planning-package.json"
)
REVIEW = (
    DOCS / "p3-6-consolidated-runtime-closeout-u4c-remediation-decision-packet.md"
)

PACKAGE_DIGEST = "26182B3EFB369C56741DFCEC51DCE412DB3EC4EF5170C0741847F1ADAE4481C0"
ATTEMPT_DIGESTS = {
    AUTHORIZATION: "53EC06DD2968A5BC733D701A421B15FE8934A7BF9946654133D7DFEBDCE67542",
    RESULT: "4AB72B831F96E996F5F90199443AE9D747A7F55804112E7291313048506E6B41",
    EVIDENCE: "DCFF4345885F5E40B6B8E7427CF4BB0528493EF2401B275D2039F9998AFFF479",
}


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read(path: Path) -> dict[str, object]:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_attempt_records_are_exact_consumed_and_failed_closed() -> None:
    for path, digest in ATTEMPT_DIGESTS.items():
        assert _sha256(path) == digest

    authorization = _read(AUTHORIZATION)
    result = _read(RESULT)
    evidence = _read(EVIDENCE)

    assert authorization["effective_for_attempt"] is False
    assert authorization["authorization_scope"]["runtime_attempts_consumed"] == 1
    assert authorization["authorization_scope"]["U3K_storage_attempts_consumed"] == 0
    assert authorization["consumed_attempt"]["additional_attempt_authorized"] is False
    assert result["attempt"]["sanitized_reason_code"] == (
        "process_output_bounds_failed"
    )
    assert result["runtime_binding"]["passed"] is True
    assert result["source_binding"]["passed"] is True
    assert result["generated_validation"]["outer_controller_result_accepted"] is False
    assert result["execution_and_access"][
        "outer_controller_dot_source_requested_count"
    ] == 1
    assert result["execution_and_access"][
        "outer_controller_dot_source_accepted_count"
    ] == 0
    assert result["U3K_storage"]["machine_or_storage_action_started"] is False
    assert result["U3K_storage"]["F_drive_access_count"] == 0
    assert evidence["terminal_gate"]["Phase_3_complete"] is False
    assert evidence["terminal_gate"][
        "new_digest_bound_authorization_required_for_any_further_attempt"
    ] is True


def test_analysis_separates_confirmed_output_failure_from_unknown_stream() -> None:
    analysis = _read(ANALYSIS)
    facts = analysis["confirmed_facts"]
    boundaries = analysis["interpretation_boundaries"]
    hypotheses = {item["hypothesis_id"]: item for item in analysis["hypotheses"]}

    assert facts["earliest_failed_action"] == (
        "CA-RC-A05-OUTER-CONTROLLER-GENERATED-VALIDATION"
    )
    assert facts["sanitized_reason_code"] == "process_output_bounds_failed"
    assert facts["one_or_more_output_predicates_failed"] is True
    assert facts["handler_process_started"] is False
    assert facts["U3K_preflight_or_storage_started"] is False
    assert boundaries["stdout_exceeded_16384_is_confirmed"] is False
    assert boundaries["stderr_nonzero_is_confirmed"] is False
    assert boundaries["child_exit_code_is_known"] is False
    assert boundaries["outer_controller_dot_source_completed_is_confirmed"] is False
    assert boundaries["generated_case_mismatch_is_confirmed"] is False
    assert hypotheses["H4-PARENT-CLASSIFICATION-GAP"]["confirmed"] is True
    assert hypotheses["H5-OUTER-CONTROLLER-DETERMINISTIC-DEFECT"][
        "confirmed"
    ] is False
    transition = analysis["known_static_compatibility_transition"]
    assert transition["current_full_Phase_3_6_tests_passed"] == 2011
    assert transition["current_full_Phase_3_6_tests_failed"] == 1
    assert transition["failure_is_the_exact_obsolete_assertion_only"] is True
    assert transition["compatibility_test_modification_authorized"] is False
    assert transition["future_U4D_exact_allowlist_required"] is True
    assert analysis["gate_effect"]["another_attempt_authorized"] is False
    assert analysis["gate_effect"]["U3K_authorized"] is False


def test_U4C_packet_has_five_complete_A_to_D_decisions() -> None:
    packet = _read(DECISIONS)
    assert [decision["decision_id"] for decision in packet["decisions"]] == [
        "D-P3.6-U4C-001",
        "D-P3.6-U4C-002",
        "D-P3.6-U4C-003",
        "D-P3.6-U4C-004",
        "D-P3.6-U4C-005",
    ]
    for decision in packet["decisions"]:
        assert decision["recommended_option"] == "A"
        assert set(decision["options"]) == {"A", "B", "C", "D"}
    assert packet["recommended_selection"] == {
        "D-P3.6-U4C-001": "A",
        "D-P3.6-U4C-002": "A",
        "D-P3.6-U4C-003": "A",
        "D-P3.6-U4C-004": "A",
        "D-P3.6-U4C-005": "A",
    }
    effect = packet["effect_of_owner_selection"]
    assert effect[
        "prepare_separate_source_only_U4D_remediation_implementation_authorization_proposal"
    ] is True
    assert effect["source_or_test_implementation_authorized"] is False
    assert effect["another_attempt_authorized"] is False
    assert effect["U3K_authorized"] is False


def test_U4C_package_binds_six_files_and_grants_zero_authority() -> None:
    package = _read(PACKAGE)
    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["core_file_count"] == len(package["core_files"]) == 6
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["recommended_selection"] == "A/A/A/A/A"
    assert all(item["selected_option"] is None for item in package["owner_decisions"])
    gate = package["current_gate_effect"]
    assert gate["owner_decisions_pending"] is True
    assert gate[
        "D_P3_6_U4C_CLOSEOUT_R1_FAILURE_ANALYSIS_DECISIONS_requestable"
    ] is True
    assert gate["attempts_authorized"] == 0
    assert gate["source_harness_contract_vector_or_test_implementation_authorized"] is False
    assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["U3K_authorized"] is False
    assert gate["Phase_3_closeout_or_commit_authorized"] is False


def test_canonical_ledgers_record_consumed_closeout_and_pending_U4C() -> None:
    consumed_key = "p3_6_consolidated_runtime_closeout_r1_consumed_attempt"
    package_key = (
        "p3_6_consolidated_runtime_closeout_u4c_remediation_planning_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        consumed = state[consumed_key]
        assert consumed["attempts_consumed"] == 1
        assert consumed["authorization_reusable"] is False
        assert consumed["terminal_reason_code"] == "process_output_bounds_failed"
        assert consumed["runtime_binding_passed"] is True
        assert consumed["source_binding_passed"] is True
        assert consumed["accepted_generated_case_count"] == 0
        assert consumed["U3K_storage_attempt_count"] == 0
        assert consumed["Phase_3_complete"] is False

        pending = state[package_key]
        assert pending["owner_decision_id"] == (
            "D-P3.6-U4C-CLOSEOUT-R1-FAILURE-ANALYSIS-DECISIONS"
        )
        assert pending["package_digest_sha256"] == PACKAGE_DIGEST
        assert pending["recommended_selection"] == "A/A/A/A/A"
        assert pending["owner_decisions_pending"] is True
        assert pending["attempts_authorized"] == 0


def test_new_records_are_LF_registered_and_success_outputs_remain_absent() -> None:
    paths = [
        AUTHORIZATION,
        RESULT,
        EVIDENCE,
        ANALYSIS,
        DECISIONS,
        PACKAGE,
        REVIEW,
        Path(__file__),
    ]
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        assert attributes.count(f"{relative} text eol=lf") == 1
        assert b"\r\n" not in path.read_bytes()

    assert (
        CONTRACTS / "p3-6-consolidated-runtime-closeout-acceptance.json"
    ).is_file()
    for path in (
        CONTRACTS / "p3-6-quarantine-storage-r2-authorization.json",
        CONTRACTS / "p3-6-quarantine-storage-r2-result.json",
        CONTRACTS / "p3-6-quarantine-storage-r2-evidence.json",
    ):
        assert path.is_file()


def test_human_records_expose_current_U4C_gate_and_package_digest() -> None:
    for path in (
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
        REVIEW,
    ):
        text = path.read_text(encoding="utf-8")
        assert "process_output_bounds_failed" in text
        assert "D-P3.6-U4C" in text
        assert PACKAGE_DIGEST in text or path == REVIEW
