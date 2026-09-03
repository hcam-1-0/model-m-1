from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

U3U_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3u-remediation-planning-package.json"
)
U3U_ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3u-remediation-planning-acceptance.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-source-implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-source-implementation-authorization-package.json"
)
IMPLEMENTATION_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-implementation-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-implementation-authorization-proposal.md"
)

U3U_PACKAGE_DIGEST = "C58B9291E06396374DE92308F2CC52CDB51824BFFDFD1958E4D655C75A894CCD"
U3U_ACCEPTANCE_DIGEST = (
    "64C1CDAC72E15988A86434AD85981C59A94AC885DE8D1927A025D13DA2165A03"
)
U3V_PACKAGE_DIGEST = "745C50AEB4DB61147C541F897F5E78987F64D9C3B137559F7CA811C0A6A5FD33"
U3U_DECISION = "D-P3.6-U3U-FAILURE-ANALYSIS-DECISIONS"
U3V_DECISION = "D-P3.6-U3V-H1-R1-DIAGNOSTIC-IMPLEMENTATION-AUTH"


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


def test_exact_U3U_acceptance_is_bound_and_grants_proposal_preparation_only() -> None:
    acceptance = _read(U3U_ACCEPTANCE)
    assert _sha256(U3U_PACKAGE) == U3U_PACKAGE_DIGEST
    assert _sha256(U3U_ACCEPTANCE) == U3U_ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == U3U_DECISION
    assert acceptance["accepted_package_sha256"] == U3U_PACKAGE_DIGEST
    statement = acceptance["canonical_owner_statement"]
    assert len(statement.encode("utf-8")) == 853
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        "936964507E19F905390CD5A0AABE1547E3AF88E5EF6A19F9F22F429870A2D1DF"
    )
    assert acceptance["selected_decisions"] == {
        "D-P3.6-U3U-001": "A",
        "D-P3.6-U3U-002": "A",
        "D-P3.6-U3U-003": "A",
        "D-P3.6-U3U-004": "A",
    }
    authority = acceptance["authority_granted"]
    assert (
        authority[
            "prepare_separate_source_only_H1_R1_implementation_authorization_proposal"
        ]
        is True
    )
    assert authority["harness_controller_test_model_or_product_implementation"] is False
    assert authority["PowerShell_parse_import_dot_source_or_execution"] is False
    assert authority["another_attempt_or_U3K"] is False


def test_U3V_package_is_digest_bound_and_all_core_files_match() -> None:
    package = _read(PACKAGE)
    assert _sha256(PACKAGE) == U3V_PACKAGE_DIGEST
    assert package["decision_id"] == U3V_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 12
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_U3V_scope_has_eight_present_paths_and_one_bounded_transition() -> None:
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)
    paths = proposal["exact_future_implementation_paths"]
    assert paths == package["exact_future_implementation_paths"]
    assert len(paths) == len(set(paths)) == 8
    assert all((ROOT / path).is_file() for path in paths)
    transition = proposal["exact_compatibility_transition_path"]
    assert transition["path"] == (
        "tests/test_phase36_quarantine_runtime_controller_u3u_remediation_planning.py"
    )
    assert (
        transition[
            "historical_digest_attempt_failure_analysis_decision_and_zero_authority_assertions_must_remain"
        ]
        is True
    )


def test_U3V_taxonomy_evidence_and_machine_disabled_boundaries_are_exact() -> None:
    proposal = _read(PROPOSAL)
    contract = proposal["required_diagnostic_contract"]
    assert contract["allowlisted_terminal_reason_codes"] == [
        "source_binding_failed",
        "controller_top_level_shape_invalid",
        "controller_contract_identity_invalid",
        "controller_terminal_state_invalid",
        "controller_reason_family_invalid",
        "controller_stage_projection_invalid",
        "controller_action_counts_invalid",
        "controller_retention_projection_invalid",
        "controller_gate_effect_invalid",
        "controller_projection_valid",
        "diagnostic_internal_contract_invalid",
    ]
    assert (
        contract[
            "candidate_values_type_names_keys_raw_projection_exception_stdout_stderr_or_environment_retained"
        ]
        is False
    )
    requirements = proposal["required_source_and_evidence_invariants"]
    assert requirements["minimum_generated_vectors"] == 128
    assert requirements["minimum_Python_reference_branch_coverage_percent"] == 95
    validation = proposal["permitted_generated_validation_if_exactly_authorized"]
    assert validation["PowerShell_parser_import_dot_source_or_execution"] is False
    assert (
        validation[
            "filesystem_runtime_registry_environment_network_native_API_or_subprocess_access_by_reference_classifier"
        ]
        is False
    )


def test_U3V_package_grants_zero_current_implementation_or_runtime_authority() -> None:
    package = _read(PACKAGE)
    gate = package["current_gate_effect"]
    assert gate["owner_U3V_source_implementation_authorization_pending"] is True
    assert gate["D_P3_6_U3V_H1_R1_DIAGNOSTIC_IMPLEMENTATION_AUTH_requestable"] is True
    assert (
        gate[
            "source_contract_harness_reference_vector_test_or_evidence_implementation_authorized"
        ]
        is False
    )
    assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert gate["Python_machine_access_or_fallback_authorized"] is False
    assert gate["runtime_manifest_hardware_or_machine_observation_authorized"] is False
    assert gate["another_attempt_or_U3K_authorized"] is False
    assert gate["deployment_or_remote_Git_authorized"] is False


def test_canonical_ledgers_record_U3V_source_complete_and_runtime_closed() -> None:
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        accepted = state[
            "quarantine_runtime_controller_u3u_remediation_planning_package"
        ]
        assert accepted["owner_decisions_pending"] is False
        assert accepted["acceptance_record_sha256"] == U3U_ACCEPTANCE_DIGEST
        assert accepted["selected_options"] == "A/A/A/A"
        pending = state[
            "quarantine_runtime_controller_u3v_h1_r1_diagnostic_source_implementation_authorization_package"
        ]
        assert pending["package_digest_sha256"] == U3V_PACKAGE_DIGEST
        assert pending["owner_U3V_source_implementation_authorization_pending"] is False
        assert (
            pending["D_P3_6_U3V_H1_R1_DIAGNOSTIC_IMPLEMENTATION_AUTH_requestable"]
            is False
        )
        assert pending["source_or_test_implementation_authorized"] is True
        assert pending["source_implementation_complete"] is True
        assert pending["generated_vector_count"] == 128
        assert pending["Python_reference_branch_coverage_percent"] >= 95
        assert pending["implementation_package_sha256"] == _sha256(
            IMPLEMENTATION_PACKAGE
        )
        assert pending["owner_U3V_source_implementation_acceptance_pending"] is True
        assert pending["compatibility_test_allowlist_amendment_decision_id"] == (
            "D-P3.6-U3V-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT"
        )
        assert pending["compatibility_test_allowlist_amendment_statement_utf8_bytes"] == 1703
        assert pending["compatibility_test_allowlist_amendment_statement_sha256"] == (
            "9BE9C3F3D2BB9ABE11A84CCCE2E4DDF79B3370AF017AD9E0B56E29C2426B541E"
        )
        assert pending["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
        assert pending["runtime_or_machine_observation_authorized"] is False
        assert pending["runtime_diagnostic_package_preparation_authorized"] is False
        assert pending["another_attempt_or_U3K_authorized"] is False
        assert pending["deployment_or_remote_git_authorized"] is False


def test_new_records_are_LF_registered_and_human_state_is_synchronized() -> None:
    paths = [U3U_ACCEPTANCE, PROPOSAL, PACKAGE, REVIEW, Path(__file__)]
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in paths:
        relative = path.as_posix().removeprefix(ROOT.as_posix() + "/")
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()

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
    ):
        text = path.read_text(encoding="utf-8")
        assert U3U_DECISION in text
        assert U3V_DECISION in text
        assert U3V_PACKAGE_DIGEST in text
