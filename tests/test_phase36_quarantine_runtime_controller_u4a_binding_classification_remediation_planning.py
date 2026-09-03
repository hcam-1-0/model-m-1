from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

AUTHORIZATION = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-authorization.json"
)
RESULT = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-result.json"
)
EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-evidence.json"
)
ANALYSIS = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-failure-analysis-r0.json"
)
DECISIONS = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u4a-binding-classification-remediation-decision-packet.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u4a-binding-classification-remediation-planning-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u4a-binding-classification-remediation-decision-packet.md"
)

PACKAGE_DIGEST = "0918CD9775DA870C530233BD8728325164159A53777A42FAA8DB5B4A7C8DA5D9"
ATTEMPT_DIGESTS = {
    AUTHORIZATION: "FC1AE35876012CEFDCB52AE5A274FC5787FAE1AE722A9709AC76782C78C530D1",
    RESULT: "C9743F0FC8906E46701E07A01A1C651F4B4B2C0517FAB722A97C1396F40F7303",
    EVIDENCE: "34BDA40E4450F35AF4A86E3C7566B9AFCA01413D70FE9CA9EB70B35A1B921BFF",
}
IMMUTABLE_U3Z_INPUTS = {
    ROOT / "tools" / "phase36_quarantine_runtime_controller_r1_generated_validation.ps1": (
        "D9EE5CC7599AACCE3363CE5C29EE479D777F94CF886AE779390B7027C40FA382"
    ),
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-vectors.json": (
        "7BCDFCA583644BD4ED5F4B747C3969B4C9FF4029B48734F8BD4D90BA5D600A21"
    ),
    ROOT / "tools" / "phase36_quarantine_runtime_controller_r1.ps1": (
        "787655BAC55DDF563E9D1DC43EC37F010C271AB381E541B0734028E3F2B90B31"
    ),
    CONTRACTS / "p3-6-quarantine-runtime-controller-r1-stage-projection-contract.json": (
        "637C5400122874149D9835CC6BC521E5EEC9160222F4A7AC5CA1F6CD99E1BCC4"
    ),
    CONTRACTS / "p3-6-quarantine-runtime-controller-r1-stage-projection-vectors.json": (
        "D8EDF5C0255B40FB6C28BB014C09DC503D2B53665E69C5AA5AB65C744AEA81E4"
    ),
    ROOT / "tools" / "phase36_quarantine_runtime_controller_r1_reference.py": (
        "B5C7328CD666E0A8988F9B616C5B2A914D690A40BF2EA289C1F1C755E42B86F0"
    ),
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


def test_U3Z_R1_attempt_records_are_exact_consumed_and_failed_closed() -> None:
    for path, digest in ATTEMPT_DIGESTS.items():
        assert _sha256(path) == digest

    authorization = _read(AUTHORIZATION)
    result = _read(RESULT)
    evidence = _read(EVIDENCE)
    assert authorization["effective_for_attempt"] is False
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert result["gate_effect"]["attempt_consumed"] is True
    assert result["sanitized_outcome"]["reason_code"] == "binding_failed"
    assert result["runtime_binding"]["fixed_parents_validated_before_and_after_process"] is False
    assert result["process"]["exact_runtime_invocation_count"] == 0
    assert result["process"]["controller_dot_source_count"] == 0
    assert result["sanitized_outcome"]["cases_executed"] == 0
    assert result["attempt"]["automatic_retry_count"] == 0
    assert evidence["gate_effect"]["authorization_reusable"] is False
    assert evidence["gate_effect"]["U3K_package_preparation_authorized"] is False
    assert all(value == 0 for value in evidence["prohibited_action_evidence"].values())


def test_analysis_localizes_failure_without_claiming_a_parent_or_U3Z_defect() -> None:
    analysis = _read(ANALYSIS)
    facts = analysis["confirmed_facts"]
    boundaries = analysis["interpretation_boundaries"]
    hypotheses = {item["hypothesis_id"]: item for item in analysis["hypotheses"]}

    assert facts["sanitized_reason_code"] == "binding_failed"
    assert facts["fixed_parents_validated_before_process"] is False
    assert facts["runtime_hash_collected"] is False
    assert facts["source_binding_started"] is False
    assert facts["PowerShell_runtime_invocation_count"] == 0
    assert facts["generated_contract_cases_executed"] == 0
    assert boundaries["which_fixed_parent_predicate_failed_is_known"] is False
    assert boundaries["actual_parent_absence_reparse_or_canonical_mismatch_is_confirmed"] is False
    assert boundaries["runtime_binary_invalidity_is_confirmed"] is False
    assert boundaries["accepted_U3Z_harness_or_controller_defect_is_indicated_by_this_attempt"] is False
    assert hypotheses["H1-FIXED-PARENT-SET-AGGREGATION-FAILED"]["confidence"] == (
        "high_inference_not_confirmed_by_retained_runtime_evidence"
    )
    assert hypotheses["H4-U3Z-GENERATED-CONTRACT-VALIDATION-FAILED"]["confidence"] == (
        "rejected_by_execution_boundary"
    )
    assert analysis["gate_effect"]["retry_authorized"] is False


def test_U4A_decision_packet_has_four_complete_A_to_D_choices() -> None:
    packet = _read(DECISIONS)
    assert [decision["decision_id"] for decision in packet["decisions"]] == [
        "D-P3.6-U4A-001",
        "D-P3.6-U4A-002",
        "D-P3.6-U4A-003",
        "D-P3.6-U4A-004",
    ]
    for decision in packet["decisions"]:
        assert decision["recommended_option"] == "A"
        assert set(decision["options"]) == {"A", "B", "C", "D"}
    effect = packet["effect_of_owner_selection"]
    assert effect[
        "prepare_separate_source_only_outer_attempt_controller_remediation_implementation_authorization_proposal"
    ] is True
    assert effect["implementation_authorized"] is False
    assert effect["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert effect["retry_authorized"] is False
    assert effect["U3K_authorized"] is False


def test_U4A_package_binds_six_files_and_grants_zero_authority() -> None:
    package = _read(PACKAGE)
    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["core_file_count"] == len(package["core_files"]) == 6
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["recommended_selection"] == "A/A/A/A"
    assert all(item["selected_option"] is None for item in package["owner_decisions"])
    gate = package["current_gate_effect"]
    assert gate["owner_decisions_pending"] is True
    assert gate["D_P3_6_U4A_U3Z_R1_FAILURE_ANALYSIS_DECISIONS_requestable"] is True
    assert gate["attempts_authorized"] == 0
    assert gate["outer_controller_contract_vector_or_test_modification_authorized"] is False
    assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["U3K_authorized"] is False


def test_canonical_ledgers_record_consumed_U3Z_R1_and_pending_U4A() -> None:
    consumed_key = (
        "quarantine_runtime_controller_u3z_generated_contract_validation_runtime_binding_r1_consumed_attempt"
    )
    package_key = (
        "quarantine_runtime_controller_u4a_binding_classification_remediation_planning_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        consumed = state[consumed_key]
        assert consumed["attempts_consumed"] == 1
        assert consumed["terminal_reason_code"] == "binding_failed"
        assert consumed["PowerShell_runtime_invocation_count"] == 0
        assert consumed["generated_contract_cases_executed"] == 0
        assert consumed["authorization_reusable"] is False
        assert consumed["retry_U3K_or_remote_Git_authorized"] is False

        pending = state[package_key]
        assert pending["owner_decision_id"] == (
            "D-P3.6-U4A-U3Z-R1-FAILURE-ANALYSIS-DECISIONS"
        )
        assert pending["package_digest_sha256"] == PACKAGE_DIGEST
        assert pending["owner_decisions_pending"] is True
        assert pending["recommended_selection"] == "A/A/A/A"
        assert pending["attempts_authorized"] == 0
        assert pending["implementation_retry_U3K_or_remote_Git_authorized"] is False


def test_accepted_U3Z_sources_remain_byte_exact_and_new_records_are_LF_registered() -> None:
    for path, digest in IMMUTABLE_U3Z_INPUTS.items():
        assert _sha256(path) == digest

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
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()


def test_human_records_expose_current_U4A_decision_and_digest() -> None:
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
        assert "binding_failed" in text
        assert "D-P3.6-U4A" in text
        assert PACKAGE_DIGEST in text or path == REVIEW
