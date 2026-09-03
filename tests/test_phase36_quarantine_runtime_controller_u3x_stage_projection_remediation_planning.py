from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

AUTHORIZATION = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-authorization.json"
)
RESULT = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-result.json"
)
EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-evidence.json"
)
ANALYSIS = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-failure-analysis-r0.json"
)
DECISIONS = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3x-stage-projection-remediation-decision-packet.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3x-stage-projection-remediation-planning-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3x-stage-projection-remediation-decision-packet.md"
)

PACKAGE_DIGEST = "80CA25BC1F1EE77E5A9ED8ADEF76C695D5169544CB75B6A57A03692463FFA460"
ATTEMPT_DIGESTS = {
    AUTHORIZATION: "6471C2CBB298D2090B789037FDCBFB20B843A565D470E0D8C2D0609DE71A0E7D",
    RESULT: "1B2DA0107938D21AF003DE40CC9B1405D81A5B9C00843B2D7FBB1867F17926EE",
    EVIDENCE: "84DC68C3800983AFA65EBB19C99A36D02C3D97CD28F6D937C43CF5292AF12A45",
}
IMMUTABLE_RUNTIME_INPUTS = {
    ROOT / "tools" / "phase36_quarantine_runtime_controller.ps1": (
        "78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB"
    ),
    ROOT / "tools" / "phase36_quarantine_runtime_controller_u3v_h1_r1_diagnostic.ps1": (
        "CD868E3F06CA12AC424B2C4C221F6425FCD0DA289C527DED462121333513B1C9"
    ),
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-contract.json": (
        "F0E41634760E3697F74EA2DEA44E7B2004392557E3167504BD69F2D78A4DC3CB"
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


def test_U3W_attempt_records_are_exact_consumed_and_failed_closed() -> None:
    for path, digest in ATTEMPT_DIGESTS.items():
        assert _sha256(path) == digest

    authorization = _read(AUTHORIZATION)
    result = _read(RESULT)
    evidence = _read(EVIDENCE)
    assert authorization["effective_for_attempt"] is False
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert result["attempt_consumed"] is True
    assert result["reason_code"] == "controller_stage_projection_invalid"
    assert result["runtime_binding"]["trust_verified"] is True
    assert result["accepted_source_binding"]["postflight_hashes_matched"] is True
    assert result["process_boundary"]["exact_diagnostic_invocation_count"] == 1
    assert result["process_boundary"]["automatic_retry_count"] == 0
    assert result["process_boundary"]["raw_stdout_or_stderr_retained"] is False
    assert evidence["gate_effect"]["authorization_reusable"] is False
    assert evidence["gate_effect"]["U3K_package_preparation_authorized"] is False


def test_analysis_separates_confirmed_stage_failure_from_null_hypothesis() -> None:
    analysis = _read(ANALYSIS)
    facts = analysis["confirmed_facts"]
    boundaries = analysis["interpretation_boundaries"]
    hypotheses = {item["hypothesis_id"]: item for item in analysis["hypotheses"]}

    assert facts["sanitized_reason_code"] == "controller_stage_projection_invalid"
    assert facts["controller_reason_family"] == "policy_valid"
    assert facts["accepted_source_hashes_matched_before_and_after_process"] == "5_of_5"
    assert boundaries["reason_code_proves_the_failure_is_within_stage_projection_validation"] is True
    assert boundaries["exact_controller_stage_projection_values_observed"] is False
    assert boundaries["PowerShell_null_to_empty_string_coercion_confirmed_by_retained_runtime_evidence"] is False
    assert hypotheses["H1-FAILED-ACTION-NULL-COERCED-TO-EMPTY-STRING"]["confidence"] == (
        "high_inference_not_runtime_confirmed"
    )
    assert analysis["recommended_remediation_direction"][
        "diagnostic_contract_weakened_to_accept_empty_string"
    ] is False
    assert analysis["gate_effect"]["retry_authorized"] is False


def test_U3X_decision_packet_has_four_complete_A_to_D_choices() -> None:
    packet = _read(DECISIONS)
    assert [decision["decision_id"] for decision in packet["decisions"]] == [
        "D-P3.6-U3X-001",
        "D-P3.6-U3X-002",
        "D-P3.6-U3X-003",
        "D-P3.6-U3X-004",
    ]
    for decision in packet["decisions"]:
        assert decision["recommended_option"] == "A"
        assert set(decision["options"]) == {"A", "B", "C", "D"}
    effect = packet["effect_of_owner_selection"]
    assert effect["prepare_separate_source_only_controller_R1_implementation_authorization_proposal"] is True
    assert effect["implementation_authorized"] is False
    assert effect["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert effect["retry_authorized"] is False
    assert effect["U3K_authorized"] is False


def test_U3X_package_binds_six_files_and_grants_zero_authority() -> None:
    package = _read(PACKAGE)
    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["core_file_count"] == len(package["core_files"]) == 6
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["recommended_selection"] == "A/A/A/A"
    assert all(item["selected_option"] is None for item in package["owner_decisions"])
    gate = package["current_gate_effect"]
    assert gate["owner_decisions_pending"] is True
    assert gate["D_P3_6_U3X_FAILURE_ANALYSIS_DECISIONS_requestable"] is True
    assert gate["attempts_authorized"] == 0
    assert gate["controller_harness_contract_vector_or_test_modification_authorized"] is False
    assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["U3K_authorized"] is False


def test_canonical_ledgers_record_consumed_U3W_and_pending_U3X() -> None:
    consumed_key = (
        "quarantine_runtime_controller_u3w_h1_r1_diagnostic_runtime_binding_r1_consumed_attempt"
    )
    package_key = (
        "quarantine_runtime_controller_u3x_stage_projection_remediation_planning_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        consumed = state[consumed_key]
        assert consumed["attempts_consumed"] == 1
        assert consumed["terminal_reason_code"] == "controller_stage_projection_invalid"
        assert consumed["authorization_reusable"] is False
        assert consumed["U3K_or_remote_git_authorized"] is False

        pending = state[package_key]
        assert pending["owner_decision_id"] == "D-P3.6-U3X-FAILURE-ANALYSIS-DECISIONS"
        assert pending["package_digest_sha256"] == PACKAGE_DIGEST
        assert pending["owner_decisions_pending"] is True
        assert pending["recommended_selection"] == "A/A/A/A"
        assert pending["attempts_authorized"] == 0
        assert pending["retry_or_U3K_authorized"] is False


def test_historical_runtime_sources_remain_byte_exact_and_LF_registered() -> None:
    for path, digest in IMMUTABLE_RUNTIME_INPUTS.items():
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


def test_human_records_expose_current_U3X_decision_and_digest() -> None:
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
        assert "controller_stage_projection_invalid" in text
        assert "D-P3.6-U3X" in text
        assert PACKAGE_DIGEST in text or path == REVIEW
