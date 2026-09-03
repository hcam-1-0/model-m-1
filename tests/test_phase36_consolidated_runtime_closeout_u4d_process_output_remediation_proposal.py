from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

U4C_PACKAGE = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4c-remediation-planning-package.json"
)
U4C_ACCEPTANCE = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4c-remediation-planning-acceptance.json"
)
SOURCE_CONTRACT = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4d-process-output-remediation-source-implementation-contract.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4d-process-output-remediation-source-implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-consolidated-runtime-closeout-u4d-process-output-remediation-source-implementation-authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-consolidated-runtime-closeout-u4d-process-output-remediation-authorization-proposal.md"
)
HISTORICAL_TEST = (
    ROOT / "tests/test_phase36_consolidated_runtime_closeout_authorization_proposal.py"
)

U4C_PACKAGE_DIGEST = "26182B3EFB369C56741DFCEC51DCE412DB3EC4EF5170C0741847F1ADAE4481C0"
U4C_ACCEPTANCE_DIGEST = (
    "722B4180D7FD81CAC3CB829C1F9A901705DC7EF87E86E1527F5E18D00926330C"
)
U4D_PACKAGE_DIGEST = "2DAD142AE31D5A3738ABADD0098512B61C0BC2C3A5C7C915BF99DE8D40FB7F74"
HISTORICAL_TEST_DIGEST = (
    "E8001AFD5B558EEBA51A0714C02DCD2C9F22B65F93A74AF4D3323130983B82EF"
)


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


def test_exact_U4C_owner_acceptance_is_recorded_without_wider_authority() -> None:
    assert _sha256(U4C_PACKAGE) == U4C_PACKAGE_DIGEST
    assert _sha256(U4C_ACCEPTANCE) == U4C_ACCEPTANCE_DIGEST
    acceptance = _read(U4C_ACCEPTANCE)

    assert acceptance["accepted_by"] == "mayank-admin"
    assert acceptance["canonical_owner_statement_utf8_bytes"] == 1031
    assert acceptance["canonical_owner_statement_sha256"] == (
        "9367A8E580FBB3FC136518D6611D1AA7DBC37D14DD61A131FD4144E620CB051D"
    )
    assert acceptance["selected_decisions"] == {
        "D-P3.6-U4C-001": "A",
        "D-P3.6-U4C-002": "A",
        "D-P3.6-U4C-003": "A",
        "D-P3.6-U4C-004": "A",
        "D-P3.6-U4C-005": "A",
    }
    authority = acceptance["authority_granted"]
    assert (
        authority[
            "prepare_separate_non_effective_U4D_source_implementation_authorization_proposal"
        ]
        is True
    )
    assert (
        authority[
            "harness_controller_contract_vector_test_model_or_product_implementation"
        ]
        is False
    )
    assert authority["PowerShell_parse_import_dot_source_or_execution"] is False
    assert authority["another_attempt_or_U3K"] is False
    assert authority["Phase_3_closeout_commit_push_or_remote_Git"] is False


def test_U4D_source_contract_binds_exact_surfaces_and_protocol() -> None:
    contract = _read(SOURCE_CONTRACT)

    assert len(contract["immutable_accepted_inputs"]) == 16
    assert len(contract["exact_future_additive_paths"]) == 17
    assert len(set(contract["exact_future_additive_paths"])) == 17
    assert len(contract["bounded_existing_synchronization_paths"]) == 13
    assert contract["exact_compatibility_transition"] == {
        "path": "tests/test_phase36_consolidated_runtime_closeout_authorization_proposal.py",
        "pre_edit_sha256": HISTORICAL_TEST_DIGEST,
        "allowed_change": "replace_only_the_obsolete_all_seven_future_outputs_absent_assertion_with_assertions_that_all_seven_paths_remain_exact_and_unique_authorization_result_and_evidence_exist_and_acceptance_plus_three_U3K_outputs_remain_absent",
        "all_other_historical_package_digest_scope_security_and_closed_gate_assertions_preserved": True,
    }
    child = contract["required_child_surface"]
    assert child["result_emission_API"] == "System.Console.Out.WriteLine"
    assert child["terminal_line_count"] == 1
    assert child["maximum_stdout_bytes"] == 4096
    assert child["maximum_stderr_bytes"] == 0
    assert child["CLIXML_or_PowerShell_object_serialization_allowed"] is False
    assert (
        contract["required_generated_static_evidence"]["minimum_generated_vector_count"]
        == 320
    )
    assert contract["later_separate_gate"]["maximum_attempts"] == 1


def test_U4D_future_implementation_paths_are_absent_and_history_is_unchanged() -> None:
    contract = _read(SOURCE_CONTRACT)
    paths = contract["exact_future_additive_paths"]
    transition = contract["exact_compatibility_transition"]

    assert len(paths) == len(set(paths)) == 17
    assert all((ROOT / path).is_file() for path in paths)
    assert transition["pre_edit_sha256"] == HISTORICAL_TEST_DIGEST
    # The R5 transition preserves the consumed R4 output records while the
    # package keeps the earlier post-U4D digest as immutable history.
    assert _sha256(HISTORICAL_TEST) == (
        "C610D44A1ADF3536C0E3126877A8C45CEF002F5013697E757005F4E212435010"
    )
    for item in contract["immutable_accepted_inputs"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_U4D_proposal_and_package_are_non_effective_and_exactly_sealed() -> None:
    assert _sha256(PACKAGE) == U4D_PACKAGE_DIGEST
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)

    assert package["core_file_count"] == len(package["core_files"]) == 12
    assert len({item["path"] for item in package["core_files"]}) == 12
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["exact_future_additive_path_count"] == 17
    assert package["exact_compatibility_transition_path_count"] == 1
    assert package["required_generated_vector_minimum"] == 320
    assert package["future_runtime_gate"]["maximum_attempts"] == 1
    assert package["future_runtime_gate"]["not_authorized_by_this_package"] is True

    effect = proposal["current_effect"]
    assert effect["owner_U4D_source_implementation_authorization_pending"] is True
    assert (
        effect["D_P3_6_U4D_PROCESS_OUTPUT_REMEDIATION_IMPLEMENTATION_AUTH_requestable"]
        is True
    )
    assert (
        effect[
            "source_harness_contract_vector_test_or_evidence_implementation_authorized"
        ]
        is False
    )
    assert effect["historical_compatibility_test_edit_authorized"] is False
    assert effect["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert effect["another_attempt_or_U3K_authorized"] is False
    assert effect["Phase_3_closeout_commit_push_or_remote_Git_authorized"] is False


def test_canonical_ledgers_expose_accepted_U4C_and_pending_U4D() -> None:
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        U4C = state[
            "p3_6_consolidated_runtime_closeout_u4c_remediation_planning_package"
        ]
        # The sealed U4C planning snapshot stays historical; acceptance is
        # recorded in a separate append-only ledger entry below.
        assert U4C["owner_decisions_pending"] is True
        assert U4C["requestable"] is True

        accepted = state[
            "p3_6_consolidated_runtime_closeout_u4c_remediation_planning_acceptance"
        ]
        assert accepted["selected_options"] == "A/A/A/A/A"
        assert accepted["acceptance_record_sha256"] == U4C_ACCEPTANCE_DIGEST

    entry = _read(CONTRACTS / "p3-6-entry-gates.json")[
        "p3_6_consolidated_runtime_closeout_u4d_process_output_remediation_source_implementation_authorization_package"
    ]
    profile = _read(CONTRACTS / "p3-6-capability-profile-policy.json")[
        "p3_6_consolidated_runtime_closeout_u4d_process_output_remediation_source_implementation_authorization_package"
    ]
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_U4D_process_output_remediation_source_implementation_authorization_action"
    ]
    for item in (entry, profile, unblock):
        assert (
            item[
                "package_digest_sha256"
                if "package_digest_sha256" in item
                else "authorization_package_sha256"
            ]
            == U4D_PACKAGE_DIGEST
        )
        assert item["owner_source_implementation_authorization_pending"] is False
        assert item["canonical_owner_statement_sha256"] == (
            "0238D5D659F9D35068C9949DAB57DD8D72A88F624847A7593263CE767E3C51B5"
        )
        assert item["compatibility_self_binding_amendment_sha256"] == (
            "2D3BA9EC453CFCF8BFEF18B72A8FAB67E49AC1C2E929BA106BAA6E80C419CA0F"
        )
        assert item["proposal_test_compatibility_amendment_sha256"] == (
            "24A39807CC463909BF342C36B931FD220FF3003F64774C90D32374C13758088E"
        )

    assert entry["source_or_test_implementation_authorized"] is True
    assert entry[
        "D_P3_6_U4D_PROCESS_OUTPUT_REMEDIATION_IMPLEMENTATION_AUTH_requestable"
    ] is False
    assert entry["PowerShell_runtime_machine_storage_U3K_or_closeout_authorized"] is False
    assert entry["commit_push_or_remote_Git_authorized"] is False
    assert profile["source_or_test_implementation_authorized"] is True
    assert profile["requestable"] is False
    assert profile["profile_selection_activation_runtime_or_deployment_authorized"] is False
    assert profile["commit_push_or_remote_Git_authorized"] is False
    assert unblock[
        "source_harness_contract_vector_test_or_evidence_implementation_authorized"
    ] is True
    assert unblock["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert unblock["runtime_or_machine_observation_authorized"] is False
    assert unblock["retry_or_U3K_authorized"] is False
    assert unblock["Phase_3_closeout_commit_push_or_remote_Git_authorized"] is False


def test_U4D_planning_records_are_LF_registered_and_human_state_is_current() -> None:
    paths = [
        U4C_ACCEPTANCE,
        SOURCE_CONTRACT,
        PROPOSAL,
        PACKAGE,
        REVIEW,
        Path(__file__),
    ]
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        assert attributes.count(f"{relative} text eol=lf") == 1
        assert path.read_bytes().endswith(b"\n")
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
        REVIEW,
    ):
        text = path.read_text(encoding="utf-8")
        assert "D-P3.6-U4D" in text
        assert U4D_PACKAGE_DIGEST in text or path == REVIEW
