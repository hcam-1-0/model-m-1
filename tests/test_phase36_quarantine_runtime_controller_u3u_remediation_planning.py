from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

AUTHORIZATION = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-authorization.json"
)
RESULT = (
    CONTRACTS / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-result.json"
)
EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-evidence.json"
)
ANALYSIS = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-failure-analysis-r0.json"
)
DECISIONS = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3u-remediation-decision-packet.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3u-remediation-planning-package.json"
)
REVIEW = DOCS / "p3-6-quarantine-runtime-controller-u3u-remediation-decision-packet.md"

PACKAGE_DIGEST = "C58B9291E06396374DE92308F2CC52CDB51824BFFDFD1958E4D655C75A894CCD"
ATTEMPT_DIGESTS = {
    AUTHORIZATION: "34AEBB1FC200E1BBC635130A0E41433DC1B4718A1354541F29CC378A4736481D",
    RESULT: "B7DAEF8067FACA055A664FC1FD62FA8C3F2CF8C0C27E27679B7DA7AD8E174CFD",
    EVIDENCE: "2706F18CA283428A17FDEB0AEB02CC350FE88336D8FBF9AC00CD040F3F0A51E1",
}
IMMUTABLE_RUNTIME_INPUTS = {
    ROOT / "tools" / "phase36_quarantine_runtime_controller_u3t_preflight.ps1": (
        "69CBF4637A22BB7859ED07D19804C8576D76FB1270FF58D0D182EED2592FCE7B"
    ),
    ROOT / "tools" / "phase36_quarantine_runtime_controller.ps1": (
        "78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB"
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


def test_attempt_records_are_exact_consumed_and_fail_closed() -> None:
    for path, digest in ATTEMPT_DIGESTS.items():
        assert _sha256(path) == digest

    authorization = _read(AUTHORIZATION)
    result = _read(RESULT)
    evidence = _read(EVIDENCE)
    assert authorization["effective_for_attempt"] is False
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert result["attempt_consumed"] is True
    assert result["reason_code"] == "result_contract_invalid"
    assert result["runtime_binding"]["trust_verified"] is True
    assert result["accepted_source_binding"]["postflight_hashes_matched"] is True
    assert result["process_boundary"]["exact_H1_preflight_invocation_count"] == 1
    assert result["process_boundary"]["automatic_retry_count"] == 0
    assert evidence["gate_effect"]["authorization_reusable"] is False
    assert evidence["gate_effect"]["U3K_package_preparation_authorized"] is False


def test_analysis_separates_confirmed_facts_from_unobserved_root_cause() -> None:
    analysis = _read(ANALYSIS)
    facts = analysis["confirmed_facts"]
    boundaries = analysis["interpretation_boundaries"]
    assert (
        facts["runtime_path_parent_metadata_hash_and_cache_only_trust_passed"] is True
    )
    assert facts["accepted_source_hashes_matched_before_and_after_process"] == "5_of_5"
    assert facts["sanitized_reason_code"] == "result_contract_invalid"
    assert boundaries["underlying_controller_reason_code_observed"] is False
    assert boundaries["exact_failed_H1_predicate_observed"] is False
    assert boundaries["blind_retry_safe"] is False
    assert len(analysis["confirmed_design_gaps"]) == 2
    assert len(analysis["hypotheses"]) == 4
    assert analysis["gate_effect"]["retry_authorized"] is False


def test_decision_packet_has_four_complete_A_to_D_choices() -> None:
    packet = _read(DECISIONS)
    assert [decision["decision_id"] for decision in packet["decisions"]] == [
        "D-P3.6-U3U-001",
        "D-P3.6-U3U-002",
        "D-P3.6-U3U-003",
        "D-P3.6-U3U-004",
    ]
    for decision in packet["decisions"]:
        assert decision["recommended_option"] == "A"
        assert set(decision["options"]) == {"A", "B", "C", "D"}
    effect = packet["effect_of_owner_selection"]
    assert (
        effect[
            "prepare_separate_source_only_H1_R1_implementation_authorization_proposal"
        ]
        is True
    )
    assert effect["implementation_authorized"] is False
    assert effect["runtime_or_machine_observation_authorized"] is False
    assert effect["retry_authorized"] is False
    assert effect["U3K_authorized"] is False


def test_planning_package_binds_core_files_and_grants_zero_authority() -> None:
    package = _read(PACKAGE)
    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["core_file_count"] == len(package["core_files"]) == 6
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["recommended_selection"] == "A/A/A/A"
    assert all(item["selected_option"] is None for item in package["owner_decisions"])
    gate = package["current_gate_effect"]
    assert gate["owner_decisions_pending"] is True
    assert gate["attempts_authorized"] == 0
    assert gate["H1_R1_harness_or_test_modification_authorized"] is False
    assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["U3K_authorized"] is False


def test_canonical_ledgers_record_U3U_acceptance_and_closed_runtime_gates() -> None:
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        attempt = state[
            "quarantine_runtime_controller_u3t_runtime_binding_r1_authorization_package"
        ]
        assert attempt["owner_U3T_R1_authorization_pending"] is False
        assert attempt["attempts_consumed"] == 1
        assert attempt["terminal_reason_code"] == "result_contract_invalid"
        package = state[
            "quarantine_runtime_controller_u3u_remediation_planning_package"
        ]
        assert package["package_digest_sha256"] == PACKAGE_DIGEST
        assert package["owner_decisions_pending"] is False
        assert package["acceptance_record_sha256"] == (
            "64C1CDAC72E15988A86434AD85981C59A94AC885DE8D1927A025D13DA2165A03"
        )
        assert package["selected_options"] == "A/A/A/A"
        assert package["attempts_authorized"] == 0
        assert package["retry_or_U3K_authorized"] is False
        transition = state[
            "quarantine_runtime_controller_u3v_h1_r1_diagnostic_source_implementation_authorization_package"
        ]
        assert transition["package_digest_sha256"] == (
            "745C50AEB4DB61147C541F897F5E78987F64D9C3B137559F7CA811C0A6A5FD33"
        )
        assert transition["owner_U3V_source_implementation_authorization_pending"] is False
        assert transition["source_implementation_complete"] is True
        assert transition["generated_vector_count"] == 128
        assert transition["Python_reference_branch_coverage_percent"] >= 95
        assert transition["owner_U3V_source_implementation_acceptance_pending"] is True
        assert transition["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
        assert transition["runtime_diagnostic_package_preparation_authorized"] is False
        assert transition["another_attempt_or_U3K_authorized"] is False


def test_historical_sources_are_immutable_and_new_records_are_registered_LF() -> None:
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
        relative = path.as_posix().removeprefix(ROOT.as_posix() + "/")
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()


def test_human_records_expose_current_owner_decision_and_digest() -> None:
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
        assert "D-P3.6-U3U" in text
        assert PACKAGE_DIGEST in text or path == REVIEW
