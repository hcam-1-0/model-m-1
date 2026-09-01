from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
RUNNER_STEM = "p3-6-quarantine-transaction-runner-r0"
RUNNER_SOURCE_PATH = CONTRACTS / f"{RUNNER_STEM}-source-proposal.txt"
RUNNER_CONTRACT_PATH = CONTRACTS / f"{RUNNER_STEM}-source-contract.json"
RUNNER_TESTS_PATH = CONTRACTS / f"{RUNNER_STEM}-contract-tests.json"
RUNNER_PROPOSAL_PATH = (
    CONTRACTS / f"{RUNNER_STEM}-implementation-authorization-proposal.json"
)
RUNNER_DOCUMENT_PATH = (
    DOCS / f"{RUNNER_STEM}-implementation-authorization-proposal.md"
)
RUNNER_PACKAGE_PATH = (
    CONTRACTS / f"{RUNNER_STEM}-implementation-authorization-package.json"
)
STORAGE_STEM = "p3-6-quarantine-storage-r2"
STORAGE_ACTION_PATH = CONTRACTS / f"{STORAGE_STEM}-action-spec.json"
STORAGE_PROPOSAL_PATH = CONTRACTS / f"{STORAGE_STEM}-authorization-proposal.json"
STORAGE_DOCUMENT_PATH = DOCS / f"{STORAGE_STEM}-authorization-proposal.md"
STORAGE_PACKAGE_PATH = (
    CONTRACTS / f"{STORAGE_STEM}-authorization-proposal-package.json"
)
U3H_ACCEPTANCE_PATH = (
    CONTRACTS / "p3-6-quarantine-failure-analysis-r2-owner-decisions.json"
)
U3H_ACCEPTANCE_DIGEST = (
    "802497CFBBF2279D91170DCD777A828A1E38BBC20A7E01EE2C1A41490E35EBE3"
)
RUNNER_SOURCE_DIGEST = (
    "DCCEF81B1D8634E851FBF19AF6260FF71120A2FDB2DFE50468801A4527714C83"
)
RUNNER_CONTRACT_DIGEST = (
    "473048EF79BC359913AF85515509AD6F1AA8BA32DFD3E5D6E37B4BB170CB45F8"
)
RUNNER_TESTS_DIGEST = (
    "3E834BC64BA1F20A0DD6338F865EDC62A0A02B1987AD71E8D8A8488ABC23AB38"
)
RUNNER_PROPOSAL_DIGEST = (
    "38EA229DEBB89A0CA46A9C1733A980F189CE20509FB13DCBBA7D198D6BB92FDA"
)
RUNNER_DOCUMENT_DIGEST = (
    "4A4AA81C5D1CF7561009EBF3D0F84E6110BFADC825DA523D0FD0D02F9E7212BF"
)
RUNNER_PACKAGE_DIGEST = (
    "712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3"
)
STORAGE_ACTION_DIGEST = (
    "1825C65DFEEEF02EA12AF3D506385657870DCB631D2CDB157DB0F9C919C2DE2A"
)
STORAGE_PROPOSAL_DIGEST = (
    "BA974EA4F613C8CF5C9AAE63FBBD57EB930B736704BEF90154B7BF4C24294425"
)
STORAGE_DOCUMENT_DIGEST = (
    "2205AEAC8B3BFDC6A18AE8615726B585F8C48791463FCF5BD0FFFFFDC32EC285"
)
STORAGE_PACKAGE_DIGEST = (
    "8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398"
)
RUNNER_AUTH_DIGEST = (
    "CD81871C6B6F560CDC01E9D6AA919B71F9E108DEB3AEA3C04B17BAF28C60D525"
)
STORAGE_ACCEPTANCE_DIGEST = (
    "6F68EB164DC662086F7444D49638FFAB95F7FF1586469BB5E5E2DC876185AAA5"
)
RUNNER_IMPLEMENTATION_PACKAGE_DIGEST = (
    "71F85A03157FB48EB7BC8950BD618BF7C00718F8602F75C29F5E069E0EB7DE67"
)
RUNNER_IMPLEMENTATION_ACCEPTANCE_DIGEST = (
    "70F2EE1133648F16CA6298C25FB6C46F56AA7C88FBA97553BDD0A2F55D90C63A"
)
RUNTIME_BINDING_PACKAGE_DIGEST = (
    "37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_runner_package_binds_exact_six_core_files() -> None:
    package = _read(RUNNER_PACKAGE_PATH)
    expected = {
        "contracts/phase-3/"
        "p3-6-quarantine-failure-analysis-r2-owner-decisions.json": (
            U3H_ACCEPTANCE_DIGEST
        ),
        f"contracts/phase-3/{RUNNER_STEM}-source-proposal.txt": (
            RUNNER_SOURCE_DIGEST
        ),
        f"contracts/phase-3/{RUNNER_STEM}-source-contract.json": (
            RUNNER_CONTRACT_DIGEST
        ),
        f"contracts/phase-3/{RUNNER_STEM}-contract-tests.json": (
            RUNNER_TESTS_DIGEST
        ),
        f"contracts/phase-3/{RUNNER_STEM}-implementation-"
        "authorization-proposal.json": RUNNER_PROPOSAL_DIGEST,
        f"docs/phase-3/{RUNNER_STEM}-implementation-"
        "authorization-proposal.md": RUNNER_DOCUMENT_DIGEST,
    }
    hashes = {item["path"]: item["sha256"] for item in package["core_files"]}

    assert _sha256(RUNNER_PACKAGE_PATH) == RUNNER_PACKAGE_DIGEST
    assert package["core_file_count"] == 6
    assert hashes == expected
    for path, digest in expected.items():
        assert _sha256(ROOT / path) == digest


def test_runner_source_is_deliberately_non_executable() -> None:
    source = RUNNER_SOURCE_PATH.read_text(encoding="utf-8")
    contract = _read(RUNNER_CONTRACT_PATH)

    assert "NON-EXECUTABLE PLANNING ARTIFACT" in source
    assert "NO HANDLER IMPLEMENTATION" in source
    assert "Every other identifier is DENY" in source
    assert contract["proposal_classification"]["executable_source"] is False
    assert contract["proposal_classification"][
        "handler_implementation_present"
    ] is False
    assert contract["proposal_classification"]["machine_access_capable"] is False
    assert contract["future_runtime_binding_requirements"][
        "runtime_query_hash_or_trust_authorized_now"
    ] is False


def test_runner_dispatch_is_exact_static_and_default_deny() -> None:
    dispatch = _read(RUNNER_CONTRACT_PATH)["default_deny_dispatch"]
    expected = [
        "UTC-CLOCK-START",
        "PACKAGE-RUNNER-AUTHORITY-VERIFY",
        "AUTHORIZATION-RECORD",
        "F-DRIVE-INFO",
        "CANONICAL-PATH-AND-ABSENCE",
        "PROTECTED-DACL-CONSTRUCT",
        "SECURITY-AT-CREATE-ROOT",
        "NORMALIZED-DACL-VERIFY",
        "ATOMIC-CAPABILITY-PROBE",
        "NORMALIZE-HASH-WRITE",
    ]

    assert dispatch["allowlisted_action_ids"] == [
        f"U3K-A{index:02d}-{suffix}"
        for index, suffix in enumerate(expected, start=1)
    ]
    assert dispatch["unknown_action"] == "deny_before_machine_access"
    assert dispatch["dynamic_eval_allowed"] is False
    assert dispatch["dynamic_scriptblock_allowed"] is False
    assert dispatch["command_string_construction_allowed"] is False
    assert dispatch["shell_fallback_allowed"] is False


def test_generated_contract_vectors_cover_required_fail_closed_classes() -> None:
    suite = _read(RUNNER_TESTS_PATH)
    vectors = suite["required_vectors"]
    categories = {item["category"] for item in vectors}

    assert len(vectors) == 20
    assert len({item["vector_id"] for item in vectors}) == 20
    assert categories == {
        "authority",
        "supply_chain",
        "dispatch",
        "scope",
        "storage_precondition",
        "ACL",
        "probe",
        "decomposition",
        "sanitization",
    }
    assert suite["fixture_policy"]["generated_only"] is True
    assert suite["fixture_policy"]["network"] is False
    assert suite["fixture_policy"]["filesystem_access"] is False
    assert suite["current_effect"]["tests_executed"] is False


def test_runner_proposal_requests_implementation_only_and_is_non_effective() -> None:
    proposal = _read(RUNNER_PROPOSAL_PATH)
    package = _read(RUNNER_PACKAGE_PATH)

    assert proposal["decision_id"] == (
        "D-P3.6-U3I-RUNNER-R0-IMPLEMENTATION-AUTH"
    )
    assert proposal["requested_owner_effect"][
        "authorize_runner_implementation_only"
    ] is True
    assert proposal["requested_owner_effect"]["permit_storage_attempt"] is False
    assert proposal["current_effect"]["effective"] is False
    assert package["status"] == (
        "sealed_non_effective_owner_implementation_authorization_pending"
    )
    for field in [
        "runner_implementation_authorized",
        "runner_or_contract_test_execution_authorized",
        "storage_or_hardware_query_authorized",
        "storage_directory_creation_ACL_write_probe_or_cleanup_authorized",
        "Defender_query_hash_or_WinVerifyTrust_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "runtime_or_model_execution_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert package[field] is False


def test_storage_package_binds_exact_five_core_files() -> None:
    package = _read(STORAGE_PACKAGE_PATH)
    expected = {
        "contracts/phase-3/"
        "p3-6-quarantine-failure-analysis-r2-owner-decisions.json": (
            U3H_ACCEPTANCE_DIGEST
        ),
        f"contracts/phase-3/{RUNNER_STEM}-implementation-"
        "authorization-package.json": RUNNER_PACKAGE_DIGEST,
        f"contracts/phase-3/{STORAGE_STEM}-action-spec.json": (
            STORAGE_ACTION_DIGEST
        ),
        f"contracts/phase-3/{STORAGE_STEM}-authorization-proposal.json": (
            STORAGE_PROPOSAL_DIGEST
        ),
        f"docs/phase-3/{STORAGE_STEM}-authorization-proposal.md": (
            STORAGE_DOCUMENT_DIGEST
        ),
    }
    hashes = {item["path"]: item["sha256"] for item in package["core_files"]}

    assert _sha256(STORAGE_PACKAGE_PATH) == STORAGE_PACKAGE_DIGEST
    assert package["core_file_count"] == 5
    assert hashes == expected
    for path, digest in expected.items():
        assert _sha256(ROOT / path) == digest


def test_storage_R2_is_exact_storage_only_sequence() -> None:
    spec = _read(STORAGE_ACTION_PATH)
    actions = spec["action_allowlist"]
    action_text = json.dumps(actions)

    assert spec["target"]["candidate_root"] == "F:\\HCAM-Quarantine"
    assert spec["target"]["owner_prohibited_volume"] == "B:"
    assert spec["target"]["required_initial_candidate_state"] == "absent"
    assert spec["transaction_bounds"]["maximum_authorized_attempts"] == 1
    assert spec["transaction_bounds"]["maximum_probe_bytes"] == 4096
    assert spec["transaction_bounds"]["network_access"] is False
    assert spec["transaction_bounds"]["automatic_retry"] is False
    assert [item["action_id"] for item in actions] == _read(
        RUNNER_CONTRACT_PATH
    )["default_deny_dispatch"]["allowlisted_action_ids"]
    assert "DEFENDER" not in action_text.upper()
    assert "MPCMD" not in action_text.upper()
    assert "WINVERIFYTRUST" not in action_text.upper()


def test_storage_R2_corrects_DACL_semantics_without_weakening_principals() -> None:
    policy = _read(STORAGE_ACTION_PATH)["platform_identity_and_DACL_policy"]
    rules = policy["required_explicit_allow_tuples"]
    normalization = policy["normalization_policy"]

    assert [(item["principal"], item["requested_rights"]) for item in rules] == [
        ("ephemeral_current_process_SID", "Modify"),
        ("S-1-5-18", "FullControl"),
        ("S-1-5-32-544", "FullControl"),
    ]
    assert rules[0]["expected_returned_semantic_rights"] == (
        "Modify,Synchronize"
    )
    assert rules[0]["forbidden_rights"] == [
        "ChangePermissions",
        "TakeOwnership",
        "FullControl",
        "generic_all",
        "unknown_bits",
    ]
    assert normalization["subset_only_check_allowed"] is False
    assert normalization["unknown_rights_bits_allowed"] is False
    assert normalization[
        "unauthorized_principal_absence_independent_from_rights_match"
    ] is True
    assert policy["explicit_rule_count_required"] == 3
    assert policy["inherited_rules_allowed"] is False
    assert policy["deny_rules_allowed"] is False
    assert policy["additional_explicit_rules_allowed"] is False


def test_storage_proposal_is_planning_only_and_final_U3K_is_blocked() -> None:
    proposal = _read(STORAGE_PROPOSAL_PATH)
    package = _read(STORAGE_PACKAGE_PATH)

    assert proposal["planning_acceptance_decision_id"] == (
        "D-P3.6-U3J-STORAGE-R2-PROPOSAL-ACCEPTANCE"
    )
    assert proposal["future_execution_authorization_decision_id"] == (
        "D-P3.6-U3K-STORAGE-R2-AUTH"
    )
    assert len(proposal[
        "prerequisites_before_final_U3K_execution_package_may_be_prepared"
    ]) == 8
    assert proposal["current_effect"]["effective"] is False
    assert package["current_gate_effect"][
        "final_U3K_execution_package_exists"
    ] is False
    for field in [
        "runner_implementation_authorized",
        "runner_or_contract_test_execution_authorized",
        "storage_or_hardware_query_authorized",
        "storage_directory_creation_ACL_write_probe_or_cleanup_authorized",
        "Defender_query_hash_or_WinVerifyTrust_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "runtime_or_model_execution_authorized",
        "implementation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert package[field] is False


def test_accepted_decisions_and_implementation_package_are_exact() -> None:
    runner_auth = CONTRACTS / f"{RUNNER_STEM}-implementation-authorization.json"
    storage_acceptance = CONTRACTS / f"{STORAGE_STEM}-proposal-acceptance.json"
    implementation_package = _read(
        CONTRACTS / f"{RUNNER_STEM}-implementation-package.json"
    )

    assert _sha256(runner_auth) == RUNNER_AUTH_DIGEST
    assert _sha256(storage_acceptance) == STORAGE_ACCEPTANCE_DIGEST
    assert _sha256(
        CONTRACTS / f"{RUNNER_STEM}-implementation-package.json"
    ) == RUNNER_IMPLEMENTATION_PACKAGE_DIGEST
    assert implementation_package["validation_summary"][
        "generated_contract_vectors_passed"
    ] == 20
    assert implementation_package["validation_summary"][
        "PowerShell_source_executed"
    ] is False
    assert implementation_package["implementation_scope"][
        "machine_action_handlers_implemented"
    ] is False
    assert implementation_package["current_gate_effect"][
        "owner_implementation_acceptance_pending"
    ] is True
    assert implementation_package["runner_execution_authorized"] is False


def test_ledgers_and_human_records_point_to_current_runtime_binding_gate() -> None:
    ledgers = [
        _read(CONTRACTS / "p3-6-entry-gates.json"),
        _read(CONTRACTS / "p3-6-capability-profile-policy.json"),
        _read(CONTRACTS / "p3-6-unblock-plan.json"),
    ]
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

    for ledger in ledgers:
        runner = ledger[
            "quarantine_transaction_runner_r0_implementation_authorization_package"
        ]
        storage = ledger["quarantine_storage_r2_authorization_proposal_package"]
        assert runner["package_digest_sha256"] == RUNNER_PACKAGE_DIGEST
        assert runner["owner_implementation_authorization_pending"] is False
        assert runner["authorization_sha256"] == RUNNER_AUTH_DIGEST
        assert runner["runner_implementation_authorized"] is True
        assert storage["package_digest_sha256"] == STORAGE_PACKAGE_DIGEST
        assert storage["owner_planning_acceptance_pending"] is False
        assert storage["acceptance_sha256"] == STORAGE_ACCEPTANCE_DIGEST
        assert storage["storage_design_accepted"] is True
        assert storage["another_attempt_authorized"] is False
        assert storage["F_or_ACL_action_authorized"] is False
        implementation = ledger[
            "quarantine_transaction_runner_r0_implementation_package"
        ]
        assert implementation["package_digest_sha256"] == (
            RUNNER_IMPLEMENTATION_PACKAGE_DIGEST
        )
        assert implementation["owner_implementation_acceptance_pending"] is False
        assert implementation["acceptance_sha256"] == (
            RUNNER_IMPLEMENTATION_ACCEPTANCE_DIGEST
        )
        assert implementation["runner_execution_authorized"] is False
        runtime_binding = ledger[
            "quarantine_transaction_runner_r0_runtime_binding_authorization_package"
        ]
        assert runtime_binding["package_digest_sha256"] == (
            RUNTIME_BINDING_PACKAGE_DIGEST
        )
        assert runtime_binding["owner_authorization_pending"] is False
        assert runtime_binding["runtime_binding_observation_completed"] is True
        assert runtime_binding["owner_evidence_acceptance_pending"] is False
        assert runtime_binding["final_U3K_package_preparation_authorized"] is True
        assert runtime_binding["runtime_binding_observation_authorized"] is False
        assert runtime_binding["runner_execution_authorized"] is False

    action = ledgers[2]["next_portable_planning_action"]
    assert action["decision_ids"] == [
        "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE"
    ]
    assert action["final_U3K_package_digest_sha256"] == (
        "4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E"
    )
    assert action["owner_implementation_acceptance_pending"] is False
    assert action["runtime_binding_proposal_preparation_authority"] is True
    assert action["owner_runtime_binding_authorization_pending"] is False
    assert action["owner_runtime_binding_evidence_acceptance_pending"] is False
    assert action["machine_handler_proposal_package_digest_sha256"] == (
        "EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311"
    )
    assert action[
        "owner_machine_handler_implementation_authorization_pending"
    ] is False
    assert action["machine_handler_proposal_preparation_authority"] is False
    assert action["machine_handler_implementation_authority"] is False
    assert action["runtime_binding_observation_authority"] is False
    assert action["transaction_runner_implementation_authority"] is False
    assert action["transaction_runner_execution_authority"] is False
    assert action["another_attempt_authority"] is False

    for path in documents:
        text = path.read_text(encoding="utf-8")
        assert RUNNER_PACKAGE_DIGEST in text
        assert STORAGE_PACKAGE_DIGEST in text
        assert RUNNER_IMPLEMENTATION_PACKAGE_DIGEST in text
        assert RUNTIME_BINDING_PACKAGE_DIGEST in text
    register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    assert "DR-0067" in register
    assert "DR-0068" in register
    assert "DR-0069" in register
    assert "DR-0070" in register
    assert "DR-0071" in register
    assert "DR-0072" in register
    assert "DR-0073" in register
    assert "DR-0074" in register
