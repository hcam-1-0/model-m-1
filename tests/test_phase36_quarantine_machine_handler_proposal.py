import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

RESEARCH_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-research-sources.json"
)
IMPLEMENTATION_CONTRACT_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-implementation-contract.json"
)
TEST_PLAN_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-generated-test-plan.json"
)
PROPOSAL_PATH = (
    CONTRACTS
    / "p3-6-quarantine-machine-handlers-r0-implementation-authorization-proposal.json"
)
PACKAGE_PATH = (
    CONTRACTS
    / "p3-6-quarantine-machine-handlers-r0-implementation-authorization-package.json"
)
REVIEW_PATH = (
    DOCS
    / "p3-6-quarantine-machine-handlers-r0-implementation-authorization-proposal.md"
)
RUNNER_PATH = ROOT / "tools" / "phase36_quarantine_transaction_runner.ps1"
IMPLEMENTATION_PACKAGE_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-implementation-package.json"
)

PACKAGE_DIGEST = (
    "EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311"
)
RESEARCH_DIGEST = (
    "13D63D2A85811466F476549A11D9A5D431F2543A4ED1CDB391DAE20BF0F5ABFA"
)
IMPLEMENTATION_CONTRACT_DIGEST = (
    "7ED610CAE26B6C92D8B2C2105754D7E8BD377B7C3790354ABAE554CBB104397F"
)
TEST_PLAN_DIGEST = (
    "5D69AFDC9612251F80309BF74983D0949B3060DBA84229F19ADCF841378DD2C2"
)
PROPOSAL_DIGEST = (
    "1D30854E15187DB5F97B48541F2A72AD4EF5FAA441A121E584089425D98F1114"
)
REVIEW_DIGEST = (
    "77A5B83FC7062214B9B834466D5961C84CC308347DB6725188696F3B0269B2E8"
)
RUNNER_DIGEST = (
    "C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15"
)
DECISION_ID = "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-AUTH"

ACTION_IDS = [
    "U3K-A01-UTC-CLOCK-START",
    "U3K-A02-PACKAGE-RUNNER-AUTHORITY-VERIFY",
    "U3K-A03-AUTHORIZATION-RECORD",
    "U3K-A04-F-DRIVE-INFO",
    "U3K-A05-CANONICAL-PATH-AND-ABSENCE",
    "U3K-A06-PROTECTED-DACL-CONSTRUCT",
    "U3K-A07-SECURITY-AT-CREATE-ROOT",
    "U3K-A08-NORMALIZED-DACL-VERIFY",
    "U3K-A09-ATOMIC-CAPABILITY-PROBE",
    "U3K-A10-NORMALIZE-HASH-WRITE",
]


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_package_and_all_twelve_core_files_are_exact() -> None:
    package = _read(PACKAGE_PATH)

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["status"] == "sealed_non_effective_owner_authorization_pending"
    assert package["owner_decision_id"] == DECISION_ID
    assert package["core_file_count"] == 12
    assert len(package["core_files"]) == 12

    for item in package["core_files"]:
        if item["path"] == "tools/phase36_quarantine_transaction_runner.ps1":
            assert item["sha256"] == RUNNER_DIGEST
            assert _sha256(RUNNER_PATH) != RUNNER_DIGEST
        else:
            assert _sha256(ROOT / item["path"]) == item["sha256"]

    assert _sha256(RESEARCH_PATH) == RESEARCH_DIGEST
    assert _sha256(IMPLEMENTATION_CONTRACT_PATH) == IMPLEMENTATION_CONTRACT_DIGEST
    assert _sha256(TEST_PLAN_PATH) == TEST_PLAN_DIGEST
    assert _sha256(PROPOSAL_PATH) == PROPOSAL_DIGEST
    assert _sha256(REVIEW_PATH) == REVIEW_DIGEST
    assert {
        item["path"]: item["sha256"] for item in package["core_files"]
    }["tools/phase36_quarantine_transaction_runner.ps1"] == RUNNER_DIGEST


def test_primary_sources_record_exclusive_creation_correction() -> None:
    research = _read(RESEARCH_PATH)
    sources = {item["source_id"]: item for item in research["sources"]}

    assert research["status"] == "primary_sources_reviewed_planning_only"
    assert len(sources) == 12
    assert all(
        item["url"].startswith("https://learn.microsoft.com/")
        for item in sources.values()
    )
    assert "MS-CREATEDIRECTORYW" in sources
    assert "MS-ACL-CREATE-DIRECTORY" in sources
    assert "MS-MOVEFILEEXW" in sources
    assert (
        "the_managed_CreateDirectory_extension_cannot_prove_attempt_ownership_"
        "when_the_target_appears_between_precheck_and_create"
        in research["research_conclusions"]
    )
    assert research["current_authority"]["machine_handler_implementation_authorized"] is False
    assert research["current_authority"]["PowerShell_or_runner_execution_authorized"] is False
    assert research["current_authority"]["F_or_ACL_action_authorized"] is False


def test_implementation_contract_is_static_isolated_and_non_effective() -> None:
    contract = _read(IMPLEMENTATION_CONTRACT_PATH)
    actions = contract["action_implementation_contracts"]

    assert contract["future_implementation_authorization_decision"] == DECISION_ID
    assert [item["action_id"] for item in actions] == ACTION_IDS
    assert contract["proposed_source_architecture"]["pure_handler_state_machine"][
        "direct_machine_APIs_allowed"
    ] is False
    assert contract["proposed_source_architecture"]["windows_storage_adapter"][
        "network_registry_process_service_and_scanner_APIs_allowed"
    ] is False
    assert actions[6]["required_API"] == (
        "CreateDirectoryW_with_nonnull_SECURITY_ATTRIBUTES"
    )
    assert actions[6]["existing_root_or_race_effect"] == (
        "fail_closed_without_modification_or_cleanup"
    )
    assert actions[8]["probe_policy"]["bytes"] == 4096
    assert actions[8]["probe_policy"]["retention_after_success"] == 0
    assert contract["transaction_invariants"]["automatic_retry"] is False
    assert contract["transaction_invariants"]["network_access"] is False

    current = contract["current_effect"]
    assert current["owner_implementation_authorization_pending"] is True
    assert current["machine_handler_implementation_authorized"] is False
    assert current["source_or_test_file_change_authorized"] is False
    assert current["PowerShell_or_runner_execution_authorized"] is False
    assert current["windows_adapter_import_or_execution_authorized"] is False
    assert current["storage_or_machine_access_authorized"] is False
    assert current["remote_git_authorized"] is False


def test_generated_plan_has_exactly_sixty_four_unique_machine_free_vectors() -> None:
    plan = _read(TEST_PLAN_PATH)
    action_groups = plan["action_vector_groups"]

    assert [group["action_id"] for group in action_groups] == ACTION_IDS
    action_count = sum(group["vector_count"] for group in action_groups)
    cross_count = plan["cross_cutting_vectors"]["vector_count"]
    assert action_count == 56
    assert cross_count == 8
    assert action_count + cross_count == plan["fixture_policy"]["total_vectors"] == 64

    vector_ids = [
        vector_id
        for group in action_groups
        for vector_id in group["required_cases"]
    ] + plan["cross_cutting_vectors"]["required_cases"]
    assert len(vector_ids) == 64
    assert len(set(vector_ids)) == 64
    assert all(
        len(group["required_cases"]) == group["vector_count"]
        for group in action_groups
    )
    assert (
        len(plan["cross_cutting_vectors"]["required_cases"])
        == plan["cross_cutting_vectors"]["vector_count"]
    )

    boundary = plan["harness_boundary"]
    assert boundary["PowerShell_execution"] is False
    assert boundary["runner_or_module_import"] is False
    assert boundary["windows_adapter_import_or_execution"] is False
    assert boundary["machine_or_filesystem_mutation"] is False
    assert boundary["network_access"] is False


def test_proposal_requests_only_future_bounded_implementation() -> None:
    proposal = _read(PROPOSAL_PATH)
    effect = proposal["requested_owner_effect_if_exact_package_digest_is_accepted"]
    gate = proposal["current_gate_effect"]

    assert proposal["decision_id"] == DECISION_ID
    assert effect["authorize_exact_source_implementation_only"] is True
    assert effect["authorize_exact_generated_Python_reference_tests_only"] is True
    assert effect["authorize_exclusive_CreateDirectoryW_security_at_create_correction"] is True
    assert effect["PowerShell_parser_runner_or_module_execution_authorized"] is False
    assert effect["windows_adapter_import_or_execution_authorized"] is False
    assert effect["machine_storage_runtime_or_ACL_observation_authorized"] is False
    assert effect["F_or_other_volume_access_authorized"] is False
    assert effect["remote_git_authorized"] is False
    assert "<MACHINE_HANDLER_PROPOSAL_PACKAGE_DIGEST_SHA256>" in proposal[
        "owner_statement_template"
    ]
    assert proposal["owner_statement_template"].startswith(f"{DECISION_ID}:")

    assert gate["owner_machine_handler_implementation_authorization_pending"] is True
    assert gate["machine_handler_implementation_authorized"] is False
    assert gate["source_or_test_change_authorized"] is False
    assert gate["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False
    assert gate["storage_attempt_authorized"] is False
    assert gate["F_or_ACL_action_authorized"] is False


def test_authorized_runner_supersedes_placeholder_without_machine_apis() -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8")

    assert _sha256(RUNNER_PATH) != RUNNER_DIGEST
    assert "[ValidateSet('Contract', 'Storage')]" in source
    assert "P36_MACHINE_HANDLER_NOT_IMPLEMENTED" not in source
    assert "switch -CaseSensitive ($ActionId)" in source
    assert "CreateDirectoryW" not in source
    assert "System.IO.DriveInfo" not in source
    assert "FileSystemAclExtensions.CreateDirectory" not in source


def test_canonical_ledgers_record_consumed_authorization_and_acceptance_gate() -> None:
    for ledger_name in [
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ]:
        ledger = _read(CONTRACTS / ledger_name)
        state = ledger[
            "quarantine_machine_handlers_r0_implementation_authorization_package"
        ]
        assert state["package_digest_sha256"] == PACKAGE_DIGEST
        assert state["owner_decision_id"] == DECISION_ID
        assert state["owner_authorization_pending"] is False
        assert state["machine_handler_implementation_authorized"] is True
        assert state["machine_action_handlers_implemented"] is True
        assert state["implementation_package_digest_sha256"] == _sha256(
            IMPLEMENTATION_PACKAGE_PATH
        )
        assert state["owner_implementation_acceptance_pending"] is False
        assert state["machine_handler_implementation_accepted"] is True
        assert state["PowerShell_or_runner_execution_authorized"] is False
        assert state["storage_attempt_authorized"] is False
        assert state["F_or_ACL_action_authorized"] is False

    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    action = unblock["next_portable_planning_action"]
    assert action["action"] == (
        "prepare_separate_non_effective_generated_PowerShell_validation_and_"
        "fresh_runtime_binding_planning_package"
    )
    assert action["decision_ids"] == [
        "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE"
    ]
    assert action["machine_handler_proposal_package_digest_sha256"] == PACKAGE_DIGEST
    assert action["machine_handler_implementation_package_digest_sha256"] == (
        _sha256(IMPLEMENTATION_PACKAGE_PATH)
    )
    assert action["owner_machine_handler_implementation_authorization_pending"] is False
    assert action["owner_implementation_acceptance_pending"] is False
    assert action["machine_action_handlers_implemented"] is True
    assert action["machine_handler_proposal_preparation_authority"] is False
    assert action["machine_handler_implementation_authority"] is False
    assert action["source_or_test_change_authority"] is False
    assert action["PowerShell_or_runner_execution_authority"] is False
    assert action["runtime_binding_proposal_preparation_authority"] is True
    assert unblock["runtime_execution_authorized"] is False

    for path in [
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
    ]:
        text = path.read_text(encoding="utf-8")
        assert PACKAGE_DIGEST in text
        assert _sha256(IMPLEMENTATION_PACKAGE_PATH) in text
        assert DECISION_ID in text or path.name in {"README.md", "p3-6-capability-profiles.md"}

    review = REVIEW_PATH.read_text(encoding="utf-8")
    assert DECISION_ID in review
    assert "CreateDirectoryW" in review
    assert "64 deterministic generated vectors" in review
    assert "does not authorize implementation" in review
