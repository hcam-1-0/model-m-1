from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

RESEARCH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-remediation-"
    "research-sources.json"
)
ANALYSIS = (
    CONTRACTS / "p3-6-quarantine-generated-validation-failure-analysis-r0.json"
)
CONTRACT = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-remediation-contract.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-remediation-"
    "implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-remediation-"
    "implementation-authorization-package.json"
)
R1_IMPLEMENTATION_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-implementation-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-generated-validation-harness-r1-remediation-"
    "authorization-proposal.md"
)
HARNESS = ROOT / "tools" / "phase36_quarantine_generated_validation.ps1"

DECISION = "D-P3.6-U3O-VALIDATION-HARNESS-R1-REMEDIATION-IMPLEMENTATION-AUTH"
PACKAGE_DIGEST = (
    "17B2142E7F3502724C6653371556DA17F7231D6C56AB0421EC39725556EAA338"
)
EXPECTED_HASHES = {
    RESEARCH: "96D975DE3AD9524FE6EBBB1900D8B3C521DD3D700DB04F5FFA2A46C36B312E9D",
    ANALYSIS: "41AC6993A6C633FABA0BF2FCEAFF8F892111DDBBF74073847D7AEFF9631A76D3",
    CONTRACT: "1ED27515EEA158BF72E5D2C33C3A1BE62E7541FB0C801A767520F28E0F064F65",
    PROPOSAL: "EC6D56F47F2598812EE8C0D5DAA453DA5C97A509F81F3F186CCC11F576273BFC",
    REVIEW: "80AD04F3ABD4ED01211F2BE9559093BE046843A4310866244DB729E3A2E6D7F8",
}
IMMUTABLE_SOURCE_HASHES = {
    "contracts/phase-3/"
    "p3-6-quarantine-generated-powershell-validation-r0-vectors.json": (
        "5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C"
    ),
    "tools/phase36_quarantine_transaction_runner.ps1": (
        "22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A"
    ),
    "tools/phase36_quarantine_machine_handlers.psm1": (
        "41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721"
    ),
    "tools/phase36_quarantine_windows_storage_adapter.psm1": (
        "232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9"
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


def test_failed_U3N_attempt_is_exact_consumed_basis() -> None:
    analysis = _read(ANALYSIS)
    facts = analysis["confirmed_attempt_facts"]

    assert facts["attempts_authorized"] == facts["attempts_consumed"] == 1
    assert facts["retry_authorized"] is False
    assert facts["outer_exact_runtime_invocation_count"] == 1
    assert facts["accepted_Aggregate_result_received"] is False
    assert facts["sanitized_failure_reason"] == "generated_validation_process_failed"
    assert facts["prohibited_action_count"] == 0
    assert facts["U3K_requestable"] is False
    gate = analysis["current_gate_effect"]
    assert gate["remediation_implementation_authorized"] is False
    assert gate["retry_authorized"] is False
    assert gate["U3K_package_preparation_authorized"] is False


def test_research_records_high_confidence_but_not_runtime_confirmation() -> None:
    research = _read(RESEARCH)
    observations = research["repository_observations"]
    conclusion = research["research_conclusion"]

    assert observations["module_autoload_preference_is_None_before_binding_check"]
    assert observations["binding_helper_invokes_Get_FileHash"]
    assert observations["explicit_Microsoft_PowerShell_Utility_import_present"] is False
    assert conclusion["classification"] == (
        "high_confidence_source_runtime_dependency_conflict_not_runtime_confirmed"
    )
    assert conclusion["preferred_remediation"] == (
        "remove_the_module_dependency_and_hash_with_bounded_dotnet_streaming"
    )
    assert {item["url"] for item in research["sources"]} == {
        "https://learn.microsoft.com/en-us/powershell/module/"
        "microsoft.powershell.core/about/about_preference_variables?view=powershell-7.5",
        "https://learn.microsoft.com/en-us/powershell/module/"
        "microsoft.powershell.utility/get-filehash?view=powershell-7.5",
        "https://learn.microsoft.com/en-us/dotnet/api/"
        "system.security.cryptography.sha256.hashdata?view=net-9.0",
    }


def test_remediation_contract_is_minimal_bounded_and_default_deny() -> None:
    contract = _read(CONTRACT)
    remediation = contract["exact_source_remediation"]
    diagnostics = contract["sanitized_diagnostic_remediation"]

    assert remediation["modifiable_source"] == (
        "tools/phase36_quarantine_generated_validation.ps1"
    )
    assert remediation["replace_dependency"] == "Get-FileHash"
    assert remediation["preserve_PSModuleAutoLoadingPreference_None"] is True
    assert remediation["preserve_single_handler_Import_Module_surface"] is True
    assert remediation["new_utility_module_import_allowed"] is False
    assert diagnostics["allowed_failure_layers"] == [
        "binding",
        "manifest",
        "parser",
        "contract",
        "handler",
        "result_serialization",
    ]
    assert diagnostics["raw_exception_message_type_stack_or_invocation_info_allowed"] is False
    assert diagnostics["raw_stdout_or_stderr_allowed"] is False
    assert contract["unchanged_behavior"]["total_generated_vector_count"] == 84
    assert contract["unchanged_behavior"]["windows_adapter_import_or_execution_count"] == 0
    assert not any(contract["implementation_non_authorization"].values())


def test_package_binds_every_core_file_and_remains_non_effective() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["future_authorization_decision_id"] == DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 17
    for item in package["core_files"]:
        if item["path"] != "tools/phase36_quarantine_generated_validation.ps1":
            assert _sha256(ROOT / item["path"]) == item["sha256"]
    gate = package["current_gate_effect"]
    assert gate["U3N_authorization_consumed"] is True
    assert gate["U3N_retry_authorized"] is False
    assert gate["owner_U3O_authorization_pending"] is True
    assert gate[
        "D_P3_6_U3O_VALIDATION_HARNESS_R1_REMEDIATION_IMPLEMENTATION_AUTH_requestable"
    ] is True
    assert gate["harness_source_or_test_modification_authorized"] is False
    assert gate["PowerShell_parse_import_or_execution_authorized"] is False
    assert gate["U3P_runtime_retry_package_preparation_authorized"] is False
    assert gate["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False


def test_proposal_requires_exact_owner_authorization() -> None:
    proposal = _read(PROPOSAL)

    assert proposal["decision_id"] == DECISION
    assert proposal["current_effect"]["owner_U3O_authorization_pending"] is True
    assert proposal["current_effect"]["source_or_test_modification_authorized"] is False
    statement = proposal["owner_statement_template"]
    assert statement.startswith(f"{DECISION}:")
    assert "<U3O_REMEDIATION_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in statement
    assert "PowerShell must not be parsed, imported, or executed" in statement


def test_immutable_sources_remain_byte_exact_and_harness_is_remediated() -> None:
    for path, expected in EXPECTED_HASHES.items():
        assert _sha256(path) == expected
    for path, expected in IMMUTABLE_SOURCE_HASHES.items():
        assert _sha256(ROOT / path) == expected

    source = HARNESS.read_text(encoding="utf-8")
    assert "$PSModuleAutoLoadingPreference = 'None'" in source
    assert "Get-FileHash" not in source
    assert "[System.IO.FileStream]::new(" in source
    assert "[System.Security.Cryptography.SHA256]::Create()" in source
    assert "P36-QUARANTINE-GENERATED-VALIDATION-HARNESS-R2-1.2.0" in source
    assert source.count("Import-Module") == 2


def test_canonical_ledgers_and_human_records_point_to_U3O_acceptance() -> None:
    implementation_digest = _sha256(R1_IMPLEMENTATION_PACKAGE)
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read(CONTRACTS / name)
        entry = ledger[
            "quarantine_generated_validation_harness_r1_remediation_"
            "implementation_authorization_package"
        ]
        assert entry["package_digest_sha256"] == PACKAGE_DIGEST
        assert entry["owner_decision_id"] == DECISION
        assert entry["owner_U3O_authorization_pending"] is False
        assert entry["implementation_authority_consumed"] is True
        assert entry["source_only_implementation_complete"] is True
        assert entry["implementation_package_sha256"] == implementation_digest
        assert entry["owner_implementation_acceptance_pending"] is False
        assert entry["source_and_generated_static_evidence_accepted"] is True
        assert entry["U3P_package_preparation_authorized"] is True
        assert entry["source_or_test_modification_authorized"] is False
        assert entry["runtime_retry_authorized"] is False
        assert entry["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

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
        assert DECISION in text
        assert PACKAGE_DIGEST in text
        assert "0EAA18F17307799430955E06EF50779BF4696300DF368680CBE5CB5913E93C42" in text


def test_line_ending_registry_includes_all_new_U3O_surfaces() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    names = [
        path.name
        for path in (RESEARCH, ANALYSIS, CONTRACT, PROPOSAL, PACKAGE, REVIEW)
    ] + [Path(__file__).name]
    for name in names:
        assert f"{name} text eol=lf" in attributes
