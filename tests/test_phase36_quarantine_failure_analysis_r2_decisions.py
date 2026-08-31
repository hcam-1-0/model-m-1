from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
STEM = "p3-6-quarantine-failure-analysis-r2"
SOURCES_PATH = CONTRACTS / f"{STEM}-research-sources.json"
DECISIONS_PATH = CONTRACTS / f"{STEM}-decision-packet.json"
PROPOSAL_PATH = CONTRACTS / f"{STEM}-proposal.json"
DOCUMENT_PATH = DOCS / f"{STEM}-proposal.md"
PACKAGE_PATH = CONTRACTS / f"{STEM}-decision-package.json"
ACCEPTANCE_PATH = CONTRACTS / f"{STEM}-owner-decisions.json"
PACKAGE_DIGEST = "19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B"
ACCEPTANCE_DIGEST = (
    "802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3"
)
U3G_PACKAGE_DIGEST = (
    "C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B"
)
U3G_AUTHORIZATION_DIGEST = (
    "12DBCEA9BB4C7AECDED5A42CCE2962CFBB689488F1B713990687DE876AC01070"
)
U3G_RESULT_DIGEST = (
    "417AB2F17C42FD6313CC2798AC055EEF75AB16F0431BE6486619C762FA253226"
)
U3G_EVIDENCE_DIGEST = (
    "B1D454E1F1390C0FB7D594D80197BA87DA75B5D4216CBF9177F8883E46268B4D"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_package_binds_exact_core_files() -> None:
    package = _read(PACKAGE_PATH)
    expected_paths = {
        f"contracts/phase-3/{STEM}-research-sources.json": SOURCES_PATH,
        f"contracts/phase-3/{STEM}-decision-packet.json": DECISIONS_PATH,
        f"contracts/phase-3/{STEM}-proposal.json": PROPOSAL_PATH,
        f"docs/phase-3/{STEM}-proposal.md": DOCUMENT_PATH,
    }
    package_hashes = {
        item["path"]: item["sha256"] for item in package["core_files"]
    }

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["core_file_count"] == 4
    assert package_hashes == {
        path: _sha256(file_path) for path, file_path in expected_paths.items()
    }
    assert package["recommended_selection"] == "A/A/A/A/A/A"


def test_all_six_decisions_are_unselected_A_through_D_choices() -> None:
    packet = _read(DECISIONS_PATH)
    decisions = packet["decisions"]

    assert [item["decision_id"] for item in decisions] == [
        f"D-P3.6-U3H-{index:03d}" for index in range(1, 7)
    ]
    for decision in decisions:
        assert decision["recommended_option"] == "A"
        assert decision["selected_option"] is None
        assert [option["option"] for option in decision["options"]] == [
            "A",
            "B",
            "C",
            "D",
        ]


def test_recommended_effect_is_bounded_and_non_executable() -> None:
    effect = _read(DECISIONS_PATH)[
        "effect_if_recommended_AAAAAA_is_later_accepted"
    ]

    assert effect["current_process_allow_mask_policy"] == (
        "exact_Modify_plus_automatic_Synchronize_only"
    )
    assert effect["DACL_verification_policy"] == (
        "independent_normalized_three_tuple_and_unauthorized_principal_checks"
    )
    assert effect["Defender_status_transport_policy"] == (
        "native_local_Windows_PowerShell_5_1_scalar_projection"
    )
    assert effect["attempt_decomposition_policy"] == (
        "storage_first_then_separate_Defender_attempt"
    )
    for field, value in effect.items():
        if field.startswith("immediate_"):
            assert value is False


def test_owner_acceptance_binds_exact_package_and_all_six_A_selections() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert _sha256(ACCEPTANCE_PATH) == ACCEPTANCE_DIGEST
    assert acceptance["package_digest_sha256"] == PACKAGE_DIGEST
    assert acceptance["accepted_by"] == "mayank-admin"
    assert acceptance["owner_statement_received"] == "\n".join(
        f"D-P3.6-U3H-{index:03d}: A" for index in range(1, 7)
    )
    assert [item["decision_id"] for item in acceptance["selections"]] == [
        f"D-P3.6-U3H-{index:03d}" for index in range(1, 7)
    ]
    assert all(
        item["selected_option"] == "A" for item in acceptance["selections"]
    )


def test_acceptance_authorizes_proposal_preparation_only() -> None:
    acceptance = _read(ACCEPTANCE_PATH)
    effect = acceptance["accepted_effect"]

    assert effect["transaction_runner_proposal_preparation_authorized"] is True
    assert effect["storage_only_action_and_authorization_proposal_preparation_authorized"] is True
    assert effect["future_Defender_only_proposal_policy_selected"] is True
    assert effect["Defender_only_proposal_preparation_authorized_now"] is False
    assert effect["next_executable_action"] == "none"
    for field in [
        "another_attempt_authorized",
        "F_or_ACL_action_authorized",
        "Defender_query_hash_or_trust_action_authorized",
        "scanner_query_install_or_execution_authorized",
        "transaction_runner_implementation_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "runtime_or_model_execution_authorized",
        "profile_resolution_or_activation_authorized",
        "implementation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert acceptance[field] is False


def test_research_uses_primary_sources_and_performs_zero_machine_actions() -> None:
    sources = _read(SOURCES_PATH)

    assert sources["status"] == "primary_source_research_complete_planning_only"
    assert len(sources["primary_sources"]) == 7
    assert {item["publisher"] for item in sources["primary_sources"]} == {
        "Microsoft Learn",
        "Microsoft Reference Source",
    }
    assert all(count == 0 for count in sources["research_actions"].values())
    assert all(
        authority is False for authority in sources["current_authority"].values()
    )


def test_consumed_U3G_facts_and_inference_limits_are_preserved() -> None:
    sources = _read(SOURCES_PATH)
    attempt = sources["consumed_attempt"]
    observed = sources["confirmed_observations"]
    analyses = {
        item["analysis_id"]: item for item in sources["causal_analysis"]
    }

    assert attempt["package_digest_sha256"] == U3G_PACKAGE_DIGEST
    assert attempt["authorization_sha256"] == U3G_AUTHORIZATION_DIGEST
    assert attempt["result_sha256"] == U3G_RESULT_DIGEST
    assert attempt["evidence_sha256"] == U3G_EVIDENCE_DIGEST
    assert attempt["attempt_consumed"] is True
    assert attempt["retry_authorized"] is False
    assert observed["explicit_rule_count_exactly_three"] is True
    assert observed["current_process_Modify_rule_pass"] is False
    assert observed["Defender_product_version"] is None
    assert observed["Defender_candidate_evaluated"] is False
    assert analyses["CA-U3H-ACL-001"]["confidence"] == (
        "high_inference_not_machine_proven"
    )
    assert "cannot be reconstructed" in analyses["CA-U3H-ACL-001"]["limitation"]
    assert analyses["CA-U3H-DEFENDER-001"]["confidence"] == (
        "confirmed_data_gap_with_transport_hypothesis"
    )


def test_proposal_and_package_grant_no_current_authority() -> None:
    proposal = _read(PROPOSAL_PATH)
    package = _read(PACKAGE_PATH)

    assert proposal["status"] == "owner_decisions_pending_non_effective"
    assert proposal["current_effect"]["owner_selections_pending"] is True
    assert package["status"] == "sealed_non_effective_owner_selections_pending"
    assert package[
        "owner_selection_may_be_inferred_from_continue_prior_U3G_authority_or_any_other_decision"
    ] is False
    assert package["current_effect"]["owner_selections_pending"] is True
    for field, value in package["current_effect"].items():
        if field != "owner_selections_pending":
            assert value is False


def test_canonical_ledgers_record_accepted_U3H_without_reopening_U3G() -> None:
    ledgers = [
        _read(CONTRACTS / "p3-6-entry-gates.json"),
        _read(CONTRACTS / "p3-6-capability-profile-policy.json"),
        _read(CONTRACTS / "p3-6-unblock-plan.json"),
    ]

    for ledger in ledgers:
        U3G = ledger["quarantine_remediation_r1_authorization_package"]
        U3H = ledger["quarantine_failure_analysis_r2_decision_package"]
        digest = U3H.get("digest_sha256", U3H.get("package_digest_sha256"))
        assert U3G["attempt_consumed"] is True
        assert U3G["retry_authorized"] is False
        assert digest == PACKAGE_DIGEST
        assert U3H["recommended_selection"] == "A/A/A/A/A/A"
        assert U3H["selected_options"] == "A/A/A/A/A/A"
        assert U3H["owner_selections_pending"] is False
        assert U3H["acceptance_sha256"] == ACCEPTANCE_DIGEST
        assert U3H["transaction_runner_proposal_preparation_authorized"] is True
        assert U3H["storage_only_proposal_preparation_authorized"] is True
        assert U3H["Defender_only_proposal_preparation_authorized_now"] is False
        assert U3H["another_attempt_authorized"] is False
        assert U3H["transaction_runner_implementation_authorized"] is False
        assert U3H["profile_activation_authorized"] is False


def test_next_action_is_non_effective_runtime_binding_review() -> None:
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    action = unblock["next_portable_planning_action"]

    assert action["action"] == (
        "owner_review_of_exact_U3L_machine_handler_implementation_"
        "authorization_package"
    )
    assert action["decision_ids"] == [
        "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-AUTH"
    ]
    assert action["final_U3K_package_digest_sha256"] == (
        "4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E"
    )
    assert action["owner_implementation_acceptance_pending"] is False
    assert action["owner_runtime_binding_authorization_pending"] is False
    assert action["owner_runtime_binding_evidence_acceptance_pending"] is False
    assert action["machine_handler_proposal_package_digest_sha256"] == (
        "EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311"
    )
    assert action["owner_machine_handler_implementation_authorization_pending"]
    assert action["machine_handler_proposal_preparation_authority"] is False
    assert action["machine_handler_implementation_authority"] is False
    assert action["runtime_binding_observation_authority"] is False
    assert action["Defender_only_proposal_preparation_authority_now"] is False
    assert action["retry_authorized"] is False
    assert action["another_attempt_authority"] is False
    assert action["transaction_runner_implementation_authority"] is False
    assert action["transaction_runner_execution_authority"] is False


def test_gates_and_human_records_remain_synchronized() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    states = {item["gate_id"]: item["state"] for item in gates["gates"]}
    documents = [
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
    ]

    assert states["P36-G1"] == "blocked"
    assert states["P36-G2"] == "blocked"
    assert states["P36-G4"] == "blocked"
    assert states["P36-G5"] == "blocked"
    for path in documents:
        text = path.read_text(encoding="utf-8")
        assert PACKAGE_DIGEST in text
        assert "U3H" in text
    assert "DR-0065" in (DOCS / "decision-register.md").read_text(
        encoding="utf-8"
    )
    assert "DR-0066" in (DOCS / "decision-register.md").read_text(
        encoding="utf-8"
    )
    assert ACCEPTANCE_DIGEST in (DOCS / "decision-register.md").read_text(
        encoding="utf-8"
    )
    assert f"{STEM}-decision-package.json" in (CONTRACTS / "README.md").read_text(
        encoding="utf-8"
    )
