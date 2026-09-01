from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
TOOLS = ROOT / "tools"

AUTHORIZATION = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-remediation-"
    "implementation-authorization.json"
)
AUTHORIZATION_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-remediation-"
    "implementation-authorization-package.json"
)
REMEDIATION_CONTRACT = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-remediation-contract.json"
)
EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-implementation-evidence.json"
)
IMPLEMENTATION_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-implementation-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-generated-validation-harness-r1-implementation-"
    "evidence-review.md"
)
HARNESS = TOOLS / "phase36_quarantine_generated_validation.ps1"

DECISION = "D-P3.6-U3O-VALIDATION-HARNESS-R1-REMEDIATION-IMPLEMENTATION-AUTH"
ACCEPTANCE_DECISION = (
    "D-P3.6-U3O-VALIDATION-HARNESS-R1-REMEDIATION-IMPLEMENTATION-ACCEPTANCE"
)
AUTHORIZATION_PACKAGE_DIGEST = (
    "17B2142E7F3502724C6653371556DA17F7231D6C56AB0421EC39725556EAA338"
)
AUTHORIZATION_DIGEST = (
    "8C422C504F5620DFBBF0FC37924B2046E80F0EF7F8C739038F604188543E3014"
)
OWNER_STATEMENT_DIGEST = (
    "619A9D574A45C479190773E003BBFDBF1749FD907319B32FDCF262FD6CD7E6D4"
)
IMMUTABLE_HASHES = {
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


def test_exact_U3O_authorization_is_recorded_and_scope_bounded() -> None:
    authorization = _read(AUTHORIZATION)

    assert _sha256(AUTHORIZATION) == AUTHORIZATION_DIGEST
    assert authorization["decision_id"] == DECISION
    assert authorization["authorized_by"] == "mayank-admin"
    assert authorization["owner_statement_utf8_bytes"] == 1307
    statement = authorization["owner_statement_received"].encode()
    assert len(statement) == 1307
    assert hashlib.sha256(statement).hexdigest().upper() == OWNER_STATEMENT_DIGEST
    assert authorization["owner_statement_sha256"] == OWNER_STATEMENT_DIGEST
    assert authorization["authorization_package_sha256"] == (
        AUTHORIZATION_PACKAGE_DIGEST
    )
    assert _sha256(AUTHORIZATION_PACKAGE) == AUTHORIZATION_PACKAGE_DIGEST
    effect = authorization["authorization_effect"]
    assert effect["source_only_remediation_implementation_authorized"] is True
    assert effect["generated_static_Python_tests_authorized"] is True
    for name in (
        "PowerShell_parse_import_or_execution_authorized",
        "runtime_or_hardware_observation_authorized",
        "retry_or_U3P_package_preparation_authorized",
        "machine_storage_F_B_ACL_probe_cleanup_or_scanner_action_authorized",
        "network_download_artifact_model_inference_camera_media_or_data_action_authorized",
        "container_Kubernetes_profile_activation_deployment_or_remote_git_authorized",
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable",
    ):
        assert effect[name] is False


def test_harness_R1_uses_bounded_read_only_dotnet_hashing() -> None:
    source = HARNESS.read_text(encoding="utf-8")
    start = source.index("function Get-P36FileSha256")
    end = source.index("function Assert-P36ExactBindings")
    hashing = source[start:end]

    assert "P36-QUARANTINE-GENERATED-VALIDATION-HARNESS-R1-1.1.0" in source
    assert "$PSModuleAutoLoadingPreference = 'None'" in source
    assert "Get-FileHash" not in source
    assert "$script:MaximumHashBufferBytes = 65536" in source
    for token in (
        "[System.IO.FileStream]::new(",
        "[System.IO.FileMode]::Open",
        "[System.IO.FileAccess]::Read",
        "[System.IO.FileShare]::Read",
        "[System.IO.FileOptions]::SequentialScan",
        "[System.Security.Cryptography.SHA256]::Create()",
        "$algorithm.ComputeHash($stream)",
        "[System.Convert]::ToHexString($digest)",
        "$algorithm.Dispose()",
        "$stream.Dispose()",
    ):
        assert token in hashing
    assert "finally" in hashing
    assert "Microsoft.PowerShell.Utility" not in source
    assert source.count("Import-Module") == 1


def test_harness_R1_failure_diagnostics_are_allowlisted_and_sanitized() -> None:
    source = HARNESS.read_text(encoding="utf-8")
    trap = source[source.index("trap {") : source.index("function Get-P36FileSha256")]
    layers = [
        "binding",
        "manifest",
        "parser",
        "contract",
        "handler",
        "result_serialization",
    ]

    for layer in layers:
        assert f"'{layer}'" in source
        assert f"$script:FailureLayer = '{layer}'" in source
    assert "$script:AllowedFailureLayers -ccontains $script:FailureLayer" in trap
    assert 'reason_code = "$($safeFailureLayer)_failed"' in trap
    for forbidden in ("$_", "Exception", "InvocationInfo", "StackTrace"):
        assert forbidden not in trap
    assert "raw_fixture_retained = $false" in trap
    assert "raw_process_output_retained = $false" in trap
    assert "raw_exception_retained = $false" in trap


def test_accepted_vectors_runner_handler_and_adapter_remain_byte_exact() -> None:
    for path, expected in IMMUTABLE_HASHES.items():
        assert _sha256(ROOT / path) == expected


def test_nonobservational_evidence_binds_source_tests_and_limitations() -> None:
    evidence = _read(EVIDENCE)

    assert evidence["decision_id"] == DECISION
    assert evidence["status"] == (
        "sealed_source_only_generated_static_evidence_owner_acceptance_pending"
    )
    assert evidence["authorization_record_sha256"] == AUTHORIZATION_DIGEST
    assert evidence["source_result"]["harness_R1_sha256"] == _sha256(HARNESS)
    assert evidence["source_result"]["Get_FileHash_present"] is False
    assert evidence["source_result"]["allowed_failure_layer_count"] == 6
    assert evidence["validation"]["generated_reference_vector_count"] == 84
    assert evidence["validation"]["focused_preseal_tests_passed"] == 105
    assert evidence["validation"]["full_phase36_preseal_tests_passed"] == 397
    actions = evidence["actions_performed"]
    assert actions["source_only_remediation_implementation"] is True
    for name, value in actions.items():
        if name != "source_only_remediation_implementation":
            assert value is False
    assert evidence["gate_effect"]["owner_implementation_acceptance_pending"] is True
    assert evidence["gate_effect"]["U3P_package_preparation_authorized"] is False
    assert evidence["gate_effect"]["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False


def test_implementation_package_binds_exact_current_core() -> None:
    package = _read(IMPLEMENTATION_PACKAGE)

    assert package["authorization_decision_id"] == DECISION
    assert package["future_acceptance_decision_id"] == ACCEPTANCE_DECISION
    assert package["core_file_count"] == len(package["core_files"])
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["current_gate_effect"]["owner_implementation_acceptance_pending"]
    assert package["current_gate_effect"]["U3P_package_preparation_authorized"] is False
    assert package["current_gate_effect"][
        "PowerShell_parse_import_or_execution_authorized"
    ] is False
    assert package["current_gate_effect"][
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable"
    ] is False
    assert REVIEW.exists()


def test_ledgers_and_human_records_bind_current_package_and_pending_acceptance() -> None:
    package_digest = _sha256(IMPLEMENTATION_PACKAGE)
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read(CONTRACTS / name)
        state = ledger[
            "quarantine_generated_validation_harness_r1_remediation_"
            "implementation_authorization_package"
        ]
        assert state["implementation_package_sha256"] == package_digest
        assert state["owner_U3O_authorization_pending"] is False
        assert state["implementation_authority_consumed"] is True
        assert state["source_only_implementation_complete"] is True
        assert state["owner_implementation_acceptance_pending"] is True
        assert state["PowerShell_parser_import_or_execution_authorized"] is False
        assert state["runtime_retry_authorized"] is False
        assert state["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

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
        assert ACCEPTANCE_DECISION in text
        assert package_digest in text


def test_line_endings_and_separate_acceptance_gate_are_explicit() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (AUTHORIZATION, EVIDENCE, IMPLEMENTATION_PACKAGE, REVIEW, Path(__file__)):
        assert f"{path.name} text eol=lf" in attributes
    assert not (
        CONTRACTS
        / "p3-6-quarantine-generated-validation-harness-r1-implementation-"
        "acceptance.json"
    ).exists()
