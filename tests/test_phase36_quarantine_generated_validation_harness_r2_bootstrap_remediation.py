from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
HARNESS = ROOT / "tools" / "phase36_quarantine_generated_validation.ps1"
VECTORS = (
    CONTRACTS / "p3-6-quarantine-generated-powershell-validation-r0-vectors.json"
)
RUNNER = ROOT / "tools" / "phase36_quarantine_transaction_runner.ps1"
HANDLER = ROOT / "tools" / "phase36_quarantine_machine_handlers.psm1"
ADAPTER = ROOT / "tools" / "phase36_quarantine_windows_storage_adapter.psm1"
GATES = CONTRACTS / "p3-6-entry-gates.json"
EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-implementation-evidence.json"
)
IMPLEMENTATION_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-implementation-package.json"
)
REVIEW = (
    ROOT
    / "docs/phase-3/p3-6-quarantine-generated-validation-harness-r2-"
    "implementation-evidence-review.md"
)

PACKAGE_DIGEST = (
    "5EC2889439E81B9F955FE7C3864A0931466458EAFA77C5797E44B24DC9AB0B47"
)
AUTHORIZATION_STATEMENT_SHA256 = (
    "F3EFCD79F0F0207CB67E57D439357A25C22C015DCFCB4B04C4C041D32D40404D"
)
VECTOR_DIGEST = (
    "5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C"
)
RUNNER_DIGEST = (
    "22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A"
)
HANDLER_DIGEST = (
    "41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721"
)
ADAPTER_DIGEST = (
    "232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9"
)
UTILITY_COMMANDS = (
    "Compare-Object",
    "ConvertFrom-Json",
    "ConvertTo-Json",
    "ForEach-Object",
    "Measure-Object",
    "Sort-Object",
    "Where-Object",
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _source() -> str:
    return HARNESS.read_text(encoding="utf-8")


def _bootstrap(source: str) -> str:
    return source[
        source.index("$script:BootstrapFailureJson =") : source.index(
            "$script:ContractId ="
        )
    ]


def test_exact_digest_bound_authorization_precedes_source_implementation() -> None:
    state = _read(GATES)[
        "quarantine_generated_validation_harness_r2_bootstrap_remediation_"
        "implementation_authorization_package"
    ]
    statement = state["owner_authorization_statement"]

    assert state["package_digest_sha256"] == PACKAGE_DIGEST
    assert state["owner_U3Q_authorization_pending"] is False
    assert state[
        "D_P3_6_U3Q_VALIDATION_HARNESS_R2_BOOTSTRAP_REMEDIATION_"
        "IMPLEMENTATION_AUTH_requestable"
    ] is False
    assert state["implementation_authorized"] is False
    assert state["implementation_authority_consumed"] is True
    assert state["source_only_implementation_complete"] is True
    assert state["owner_implementation_acceptance_pending"] is True
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        AUTHORIZATION_STATEMENT_SHA256
    )
    assert state["owner_authorization_statement_sha256"] == (
        AUTHORIZATION_STATEMENT_SHA256
    )
    for field in (
        "PowerShell_parser_import_or_execution_authorized",
        "runtime_or_hardware_observation_authorized",
        "retry_or_U3R_package_preparation_authorized",
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable",
        "profile_activation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ):
        assert state[field] is False


def test_bootstrap_uses_only_the_exact_pshome_utility_manifest() -> None:
    source = _source()
    bootstrap = _bootstrap(source)

    expected_parts = (
        "[System.IO.Path]::Combine($PSHOME, 'Modules')",
        "'Microsoft.PowerShell.Utility'",
        "'Microsoft.PowerShell.Utility.psd1'",
        "[System.IO.Path]::GetFullPath($expectedUtilityManifestPath)",
        "[System.StringComparison]::OrdinalIgnoreCase",
        "$utilityManifestInfo.Length -gt 131072",
        "[System.IO.FileAttributes]::Directory",
        "[System.IO.FileAttributes]::ReparsePoint",
    )
    for part in expected_parts:
        assert part in bootstrap
    assert "$env:PSModulePath" not in source
    assert "PSModulePath" not in bootstrap
    assert "Import-Module -Name Microsoft.PowerShell.Utility" not in source
    assert "Import-Module -Name 'Microsoft.PowerShell.Utility'" not in source


def test_utility_import_is_exact_allowlisted_local_and_no_clobber() -> None:
    source = _source()
    bootstrap = _bootstrap(source)
    import_lines = [
        line.strip() for line in bootstrap.splitlines() if "Import-Module" in line
    ]

    assert len(import_lines) == 1
    utility_import = import_lines[0]
    for token in (
        "-Name $script:UtilityManifestPath",
        "-Scope Local",
        "-NoClobber",
        "-Cmdlet $script:RequiredUtilityCommands",
        "-Function @()",
        "-Alias @()",
        "-Variable @()",
        "-ErrorAction Stop",
    ):
        assert token in utility_import
    assert "-Force" not in utility_import
    for command in UTILITY_COMMANDS:
        assert bootstrap.count(f"'{command}'") == 1
    assert source.count("Import-Module") == 2


def test_all_fourteen_existing_utility_references_are_allowlisted() -> None:
    source = _source()
    existing_layers = source[source.index("$script:ContractId =") :]
    counts = {
        command: len(
            re.findall(
                rf"(?<![A-Za-z0-9_-]){re.escape(command)}(?![A-Za-z0-9_-])",
                existing_layers,
            )
        )
        for command in UTILITY_COMMANDS
    }

    assert set(counts) == set(UTILITY_COMMANDS)
    assert all(count > 0 for count in counts.values())
    assert sum(counts.values()) == 14


def test_provenance_is_verified_before_autoload_is_disabled() -> None:
    source = _source()
    bootstrap = _bootstrap(source)
    import_at = bootstrap.index("Import-Module -Name $script:UtilityManifestPath")
    provenance_at = bootstrap.index("$command.Source -cne $script:UtilityModuleName")
    autoload_at = bootstrap.index("$PSModuleAutoLoadingPreference = 'None'")

    assert import_at < provenance_at < autoload_at
    assert "$command.ModuleName -cne $script:UtilityModuleName" in bootstrap
    assert "-not $seenUtilityCommands.Add($command.Name)" in bootstrap
    assert "P36_UTILITY_COMMAND_PROVENANCE_INVALID" in bootstrap
    assert "P36_UTILITY_COMMAND_SET_INVALID" in bootstrap
    assert source.count("$PSModuleAutoLoadingPreference = 'None'") == 1


def test_bootstrap_failure_writer_is_fixed_bounded_and_module_independent() -> None:
    source = _source()
    bootstrap = _bootstrap(source)
    literal_match = re.search(
        r"\$script:BootstrapFailureJson = '([^'\r\n]+)'", bootstrap
    )
    assert literal_match is not None
    literal = literal_match.group(1)
    result = json.loads(literal)
    writer_start = bootstrap.index("function Write-P36BootstrapFailure")
    writer_end = bootstrap.index("\n}\n\ntry {", writer_start) + 2
    writer = bootstrap[writer_start:writer_end]

    assert len(literal.encode("ascii")) <= 2048
    assert result["contract_id"] == (
        "P36-QUARANTINE-GENERATED-VALIDATION-HARNESS-R2-1.2.0"
    )
    assert result["mode"] == "bootstrap"
    assert result["reason_code"] == "binding_failed"
    assert result["terminal"] is True
    assert result["succeeded"] is False
    assert "[System.Console]::Out.WriteLine($script:BootstrapFailureJson)" in writer
    assert "exit 1" in writer
    assert "$_" not in writer
    for command in UTILITY_COMMANDS:
        assert command not in writer


def test_existing_behavior_and_immutable_sources_remain_bound() -> None:
    source = _source()

    assert "[ValidateSet('Parse', 'Contract', 'Handler', 'Aggregate')]" in source
    assert "P36-QUARANTINE-GENERATED-VALIDATION-HARNESS-R2-1.2.0" in source
    assert "ArgumentList.Add('Contract')" in source
    assert "StorageRequestJson" not in source
    assert _sha256(VECTORS) == VECTOR_DIGEST
    assert _sha256(RUNNER) == RUNNER_DIGEST
    assert _sha256(HANDLER) == HANDLER_DIGEST
    assert _sha256(ADAPTER) == ADAPTER_DIGEST


def test_nonobservational_evidence_binds_source_tests_and_prohibitions() -> None:
    evidence = _read(EVIDENCE)

    assert evidence["authorization"]["package_sha256"] == PACKAGE_DIGEST
    assert evidence["authorization"]["checkpoint_commit"] == "7a11175"
    assert evidence["authorization"]["owner_statement_sha256"] == (
        AUTHORIZATION_STATEMENT_SHA256
    )
    assert evidence["authorization"]["compatibility_amendment_commit"] == (
        "d1b4354"
    )
    assert evidence["source_result"]["harness_R2_sha256"] == _sha256(HARNESS)
    assert evidence["source_result"]["utility_cmdlet_allowlist"] == list(
        UTILITY_COMMANDS
    )
    assert evidence["immutable_inputs"]["all_byte_exact"] is True
    validation = evidence["validation"]
    assert validation["generated_reference_vector_count"] == 84
    assert validation["full_phase36_static_checks_passed"] == 427
    assert validation["failed_static_checks"] == 0
    actions = evidence["actions_performed"]
    assert actions["source_only_R2_bootstrap_remediation"] is True
    for name, value in actions.items():
        if name != "source_only_R2_bootstrap_remediation":
            assert value is False


def test_implementation_package_binds_exact_R2_result_and_acceptance_gate() -> None:
    package = _read(IMPLEMENTATION_PACKAGE)

    assert package["authorization_decision_id"] == (
        "D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-"
        "IMPLEMENTATION-AUTH"
    )
    assert package["future_acceptance_decision_id"] == (
        "D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-"
        "IMPLEMENTATION-ACCEPTANCE"
    )
    assert package["core_file_count"] == len(package["core_files"])
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    result = package["implementation_result"]
    assert result["remediated_R2_harness_sha256"] == _sha256(HARNESS)
    assert result["exact_Utility_cmdlet_allowlist_count"] == 7
    gate = package["current_gate_effect"]
    assert gate["source_only_implementation_complete"] is True
    assert gate["owner_implementation_acceptance_pending"] is True
    assert gate["U3R_package_preparation_authorized"] is False
    assert gate["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False
    assert REVIEW.exists()
