from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

AUTHORIZATION = (
    CONTRACTS / "p3-6-consolidated-runtime-closeout-r2-authorization.json"
)
RESULT = CONTRACTS / "p3-6-consolidated-runtime-closeout-r2-result.json"
EVIDENCE = CONTRACTS / "p3-6-consolidated-runtime-closeout-r2-evidence.json"
SOURCES = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-r2-failure-analysis-research-sources.json"
)
ANALYSIS = CONTRACTS / "p3-6-consolidated-runtime-closeout-r2-failure-analysis.json"
DECISIONS = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4e-remediation-decision-packet.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4e-remediation-planning-package.json"
)
REVIEW = (
    DOCS / "p3-6-consolidated-runtime-closeout-u4e-remediation-decision-packet.md"
)

PACKAGE_DIGEST = "C0BF901B7D66BE11A250F9369C5CE564A59A726E88877E4A77CD36F310997B7D"
ATTEMPT_DIGESTS = {
    AUTHORIZATION: "A8F8B8D9DD6DE42948D8B5B9BD2E869A2490D6758578B0D493C6E4C592798B12",
    RESULT: "B49F02F504CF4D02B1D8BA59808154BE180A7EF5B251859F356D18A896E386BC",
    EVIDENCE: "7D76C61B6D2DB5544B3C79BB19B145F27AF371014C174CA8ED8AECDB3AC5D2C6",
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


def test_R2_records_are_exact_consumed_and_failed_before_execution() -> None:
    for path, digest in ATTEMPT_DIGESTS.items():
        assert _sha256(path) == digest

    authorization = _read(AUTHORIZATION)
    result = _read(RESULT)
    evidence = _read(EVIDENCE)

    assert authorization["status"] == "authorized_single_attempt_recorded_before_observation"
    assert result["status"] == "terminal_failed_closed_authorization_consumed_no_retry"
    assert result["terminal_outcome"]["sanitized_reason_code"] == (
        "utility_closure_declared_target_missing"
    )
    assert result["terminal_outcome"]["authorization_reusable"] is False
    assert result["terminal_outcome"]["earliest_failed_action"] == (
        "R2-A04-UTILITY-MANIFEST-AND-CLOSURE-BINDING"
    )
    assert result["execution_counts"]["total_generated_cases_accepted"] == 0
    assert result["execution_counts"]["U3K_storage_attempt_count"] == 0
    assert result["execution_counts"]["F_drive_access_count"] == 0
    assert evidence["terminal_gate_effect"]["Phase_3_complete"] is False
    assert evidence["terminal_gate_effect"]["authorization_reusable"] is False


def test_official_sources_support_hypothesis_without_claiming_local_cause() -> None:
    sources = _read(SOURCES)
    assert sources["status"] == "official_public_documentation_planning_only"
    assert len(sources["sources"]) == 2
    assert {item["publisher"] for item in sources["sources"]} == {"Microsoft"}
    assert all(
        item["url"].startswith("https://learn.microsoft.com/")
        for item in sources["sources"]
    )
    limits = sources["interpretation_limits"]
    assert limits["official_documentation_confirms_the_missing_R2_target_identity"] is False
    assert limits["official_documentation_confirms_the_installed_module_is_incomplete"] is False
    assert limits["planning_may_treat_manifest_directory_resolution_as_the_leading_hypothesis"] is True
    assert not any(sources["actions_performed"].values())


def test_analysis_preserves_confirmed_facts_and_unknown_target_boundary() -> None:
    analysis = _read(ANALYSIS)
    facts = analysis["confirmed_facts"]
    limits = analysis["interpretation_boundaries"]
    hypotheses = {item["hypothesis_id"]: item for item in analysis["hypotheses"]}

    assert facts["sanitized_reason_code"] == "utility_closure_declared_target_missing"
    assert facts["manifest_parser_error_count"] == 0
    assert facts["missing_declared_target_count_observed_before_stop"] == 1
    assert facts["target_PowerShell_generated_validation_process_count"] == 0
    assert facts["generated_case_execution_count"] == 0
    assert facts["U3K_preflight_or_storage_started"] is False
    assert limits["missing_declared_target_field_name_is_known"] is False
    assert limits["missing_declared_target_path_or_extension_is_known"] is False
    assert limits["resolver_used_PSHome_instead_of_manifest_directory_is_confirmed"] is False
    assert hypotheses["H1-MANIFEST-BASE-RESOLUTION-MISMATCH"]["confirmed"] is False
    assert hypotheses["H4-CLOSURE-REQUIREDNESS-DESIGN-GAP"]["confirmed"] is True
    assert analysis["gate_effect"]["another_attempt_authorized"] is False
    assert analysis["gate_effect"]["U3K_authorized"] is False


def test_U4E_packet_has_five_complete_A_to_D_decisions() -> None:
    packet = _read(DECISIONS)
    expected = [f"D-P3.6-U4E-{index:03d}" for index in range(1, 6)]
    assert [decision["decision_id"] for decision in packet["decisions"]] == expected
    for decision in packet["decisions"]:
        assert decision["recommended_option"] == "A"
        assert set(decision["options"]) == {"A", "B", "C", "D"}
    assert packet["recommended_selection"] == {
        decision_id: "A" for decision_id in expected
    }
    effect = packet["effect_of_owner_selection"]
    assert effect[
        "prepare_separate_source_only_U4F_manifest_closure_remediation_implementation_authorization_proposal"
    ] is True
    assert effect["source_contract_controller_harness_vector_or_test_implementation_authorized"] is False
    assert effect["another_attempt_authorized"] is False
    assert effect["U3K_authorized"] is False


def test_U4E_package_binds_seven_files_and_grants_zero_authority() -> None:
    package = _read(PACKAGE)
    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["core_file_count"] == len(package["core_files"]) == 7
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["recommended_selection"] == "A/A/A/A/A"
    assert all(item["selected_option"] is None for item in package["owner_decisions"])
    gate = package["current_gate_effect"]
    assert gate["owner_decisions_pending"] is True
    assert gate[
        "D_P3_6_U4E_CLOSEOUT_R2_FAILURE_ANALYSIS_DECISIONS_requestable"
    ] is True
    assert gate["attempts_authorized"] == 0
    assert gate["source_contract_controller_harness_vector_or_test_implementation_authorized"] is False
    assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert gate["runtime_manifest_hardware_machine_storage_or_network_observation_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["U3K_authorized"] is False
    assert gate["Phase_3_closeout_or_commit_authorized"] is False


def test_canonical_ledgers_record_consumed_R2_and_pending_U4E() -> None:
    R2_key = "p3_6_consolidated_runtime_closeout_r2_authorization_package"
    U4E_key = "p3_6_consolidated_runtime_closeout_u4e_remediation_planning_package"
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
    ):
        state = _read(CONTRACTS / name)
        consumed = state[R2_key]
        assert consumed["attempts_consumed"] == 1
        assert consumed["terminal_reason_code"] == (
            "utility_closure_declared_target_missing"
        )
        assert consumed["generated_case_execution_count"] == 0
        assert consumed["U3K_storage_attempt_count"] == 0
        assert consumed["owner_runtime_closeout_R2_authorization_pending"] is False

        pending = state[U4E_key]
        assert pending["package_digest_sha256"] == PACKAGE_DIGEST
        assert pending["recommended_selection"] == "A/A/A/A/A"
        assert pending["owner_decisions_pending"] is True
        assert pending["attempts_authorized"] == 0

    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    consumed = unblock["next_consolidated_runtime_closeout_R2_authorization_action"]
    assert consumed["attempts_consumed"] == 1
    assert consumed["status"] == "consumed_terminal_failed_closed_no_retry"
    pending = unblock["next_U4E_closeout_R2_failure_analysis_decision_action"]
    assert pending["planning_package_sha256"] == PACKAGE_DIGEST
    assert pending["owner_decisions_pending"] is True
    assert pending["attempts_authorized"] == 0


def test_records_are_LF_registered_and_future_authority_is_absent() -> None:
    paths = [SOURCES, ANALYSIS, DECISIONS, PACKAGE, REVIEW, Path(__file__)]
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        assert attributes.count(f"{relative} text eol=lf") == 1
        assert b"\r\n" not in path.read_bytes()

    for path in (
        CONTRACTS
        / "p3-6-consolidated-runtime-closeout-u4e-remediation-planning-acceptance.json",
        CONTRACTS
        / "p3-6-consolidated-runtime-closeout-u4f-source-implementation-authorization-package.json",
        CONTRACTS / "p3-6-consolidated-runtime-closeout-r3-authorization.json",
        CONTRACTS / "p3-6-consolidated-runtime-closeout-r2-acceptance.json",
    ):
        assert path.exists() is False
    assert (
        CONTRACTS / "p3-6-quarantine-storage-r2-authorization.json"
    ).is_file()


def test_human_records_expose_current_U4E_gate_and_digest() -> None:
    paths = (
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
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "utility_closure_declared_target_missing" in text
        assert "U4E" in text
        assert PACKAGE_DIGEST in text or path == REVIEW
