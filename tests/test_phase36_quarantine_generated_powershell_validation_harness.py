from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
HARNESS_PATH = ROOT / "tools" / "phase36_quarantine_generated_validation.ps1"
VECTORS_PATH = (
    CONTRACTS / "p3-6-quarantine-generated-powershell-validation-r0-vectors.json"
)
PLAN_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-generated-test-plan.json"
)
AUTH_PACKAGE_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r0-implementation-"
    "authorization-package.json"
)
EVIDENCE_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r0-implementation-evidence.json"
)
IMPLEMENTATION_PACKAGE_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r0-implementation-package.json"
)
REVIEW_PATH = (
    DOCS
    / "p3-6-quarantine-generated-validation-harness-r0-implementation-"
    "evidence-review.md"
)
RUNNER_PATH = ROOT / "tools" / "phase36_quarantine_transaction_runner.ps1"
HANDLER_PATH = ROOT / "tools" / "phase36_quarantine_machine_handlers.psm1"
ADAPTER_PATH = ROOT / "tools" / "phase36_quarantine_windows_storage_adapter.psm1"

AUTH_PACKAGE_DIGEST = (
    "F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1"
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
OWNER_STATEMENT_SHA256 = (
    "47E98DA596090BD1768B5296F763F2765F6171BFA0F87A8E8191D23853C6006A"
)
OWNER_STATEMENT = (
    "D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-AUTH: I, mayank-admin, "
    "authorize source-only implementation of the generated PowerShell validation "
    "harness against package digest "
    "F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1. "
    "Implementation is limited to the exact paths, read-only inputs, generated-only "
    "fixtures, static Python checks, evidence, package, ledger, documentation, and "
    "compatibility-test changes allowlisted by that package. The accepted runner, "
    "pure-handler, and Windows-adapter sources must remain byte-exact. PowerShell "
    "must not be parsed, imported, or executed; the runner and modules must not run; "
    "no runtime or hardware may be observed; and no machine, storage, F:, ACL, "
    "probe, cleanup, Defender/scanner, network, download, artifact, model, inference, "
    "camera/media/data, container/Kubernetes, deployment, or remote Git action may "
    "occur. The result must be sealed for separate acceptance before any validation "
    "or fresh runtime-binding authorization package can be prepared."
)

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


def _merge(base: dict[str, object], mutation: dict[str, object]) -> dict[str, object]:
    return {**base, **mutation}


def _contract_outcome(fixture: dict[str, object]) -> str:
    authority = (
        "package_digest_match",
        "core_hashes_match",
        "owner_statement_match",
        "authorization_window_valid",
        "attempt_unused",
        "runner_binding_match",
        "runtime_binding_match",
    )
    if not all(fixture[name] is True for name in authority):
        return "deny_before_machine_access"
    if fixture["action_ids"] != ACTION_IDS:
        return "default_deny_before_machine_access"
    if fixture["path_policy"] == "prohibited":
        return "deny_without_access"
    if (
        fixture["path_policy"] != "exact"
        or fixture["candidate_volume"] != "F:"
        or fixture["candidate_root"] != "F:\\HCAM-Quarantine"
        or fixture["probe_bytes"] != 4096
        or fixture["per_action_timeout_seconds"] != 30
        or fixture["total_timeout_seconds"] != 120
    ):
        return "deny_before_machine_access"
    if len(fixture["output_paths"]) != 3:
        return "default_deny_and_no_additional_write"
    if fixture["forbidden_output_present"] is True:
        return "output_schema_reject_and_fail_closed"
    if fixture["candidate_absent"] is False:
        return "fail_without_ACL_or_content_modification"
    if fixture["acl_case"] != "none":
        rights = sorted(set(fixture["current_process_rights"]))
        rights_pass = rights == ["Modify", "Synchronize"]
        if fixture["unauthorized_principal"] is True:
            return "rule_count_and_unauthorized_principal_checks_fail"
        if (
            fixture["inherited_rule"] is True
            or fixture["deny_rule"] is True
            or fixture["inheritance_pass"] is False
            or fixture["propagation_pass"] is False
            or fixture["access_type_pass"] is False
        ):
            return "overall_DACL_check_fail"
        if not rights_pass and fixture["acl_case"] == "tuple_independence":
            return "rights_fail_and_unauthorized_principal_absence_remains_true"
        if not rights_pass:
            return "current_process_rights_check_fail"
        return "current_process_rights_check_pass"
    if fixture["probe_case"] == "success":
        return "two_hash_checks_pass_and_no_probe_content_retained"
    if fixture["probe_case"] == "failure":
        return "storage_blocked_no_retry_cleanup_scope_does_not_expand"
    return "contract_valid_no_machine_execution"


def _all_true(value: dict[str, object], names: tuple[str, ...]) -> bool:
    return all(value.get(name) is True for name in names)


def _handler_reason(action_id: str, value: dict[str, object]) -> str:
    if action_id == ACTION_IDS[0]:
        if value.get("ok") is not True:
            return "clock_unavailable"
        if value.get("read_count") != 1 or "monotonic_seconds" not in value:
            return "clock_read_count_invalid"
    elif action_id == ACTION_IDS[1]:
        required = (
            "ok",
            "owner_statement_exact_match",
            "authorization_window_current",
            "attempt_unused",
            "execution_package_hashes_match",
            "source_hashes_match",
            "runtime_binding_matches",
            "target_action_limits_outputs_match",
        )
        if not _all_true(value, required):
            if value.get("attempt_unused") is False:
                return "attempt_already_consumed"
            if value.get("authorization_window_current") is False:
                return "authorization_window_invalid"
            if value.get("source_hashes_match") is False or value.get(
                "runtime_binding_matches"
            ) is False:
                return "source_or_runtime_binding_invalid"
            return "authority_binding_invalid"
    elif action_id == ACTION_IDS[2]:
        required = (
            "ok",
            "schema_valid",
            "size_valid",
            "destination_absent",
            "partial_absent",
            "flushed_to_disk",
            "nonreplacement_rename",
        )
        if not _all_true(value, required):
            if value.get("destination_absent") is False or value.get(
                "partial_absent"
            ) is False:
                return "authorization_record_exists"
            if value.get("schema_valid") is False or value.get("size_valid") is False:
                return "authorization_record_invalid"
            return "authorization_record_write_failed"
    elif action_id == ACTION_IDS[3]:
        if value.get("properties_available") is not True:
            return "drive_property_unavailable"
        if value.get("drive_ready") is not True:
            return "drive_not_ready"
        if value.get("drive_type") != "Fixed":
            return "drive_type_not_allowed"
        if value.get("filesystem") not in {"NTFS", "ReFS"}:
            return "filesystem_not_allowed"
        if int(value.get("available_free_bytes", 0)) < 5 * 1024**3 or float(
            value.get("available_free_percent", 0.0)
        ) < 15.0:
            return "capacity_below_minimum"
    elif action_id == ACTION_IDS[4]:
        if value.get("attributes_available") is not True:
            return "candidate_attribute_unavailable"
        if value.get("exact_canonical_path") is not True:
            return "candidate_path_invalid"
        if value.get("parent_reparse") is True or value.get("candidate_reparse") is True:
            return "candidate_or_parent_reparse"
        if value.get("candidate_absent") is not True:
            return "candidate_exists"
    elif action_id == ACTION_IDS[5]:
        if value.get("identity_available") is not True:
            return "identity_unavailable"
        if value.get("identity_collision") is True:
            return "identity_collision"
        required = (
            "ok",
            "descriptor_bounded",
            "inheritance_protected",
            "exact_three_allow_tuples",
            "identity_not_persisted",
            "account_translation_absent",
        )
        if not _all_true(value, required):
            return "security_descriptor_invalid"
    elif action_id == ACTION_IDS[6]:
        if value.get("error_already_exists") is True:
            return "root_preexisting_or_raced"
        if (
            value.get("required_API_used") is not True
            or value.get("security_attributes_nonnull") is not True
            or value.get("fallback_used") is True
        ):
            return "root_creation_mechanism_invalid"
        if value.get("native_success") is not True:
            return "root_create_failed"
    elif action_id == ACTION_IDS[7]:
        if not all(item is True for item in value.values()):
            return "DACL_policy_failed"
    elif action_id == ACTION_IDS[8]:
        if value.get("probe_paths_absent") is not True:
            return "probe_path_preexisting"
        if value.get("cleanup_complete") is not True:
            return "probe_cleanup_failed"
        required = (
            "ok",
            "exact_byte_count",
            "write_through",
            "flush_to_disk",
            "first_hash_match",
            "rename_write_through_only",
            "second_hash_match",
            "cleanup_complete",
            "zero_retention",
        )
        if not _all_true(value, required):
            return "probe_write_failed"
    elif action_id == ACTION_IDS[9]:
        if value.get("size_valid") is False:
            return "output_too_large"
        if value.get("schema_valid") is False or value.get("canonical_JSON") is False:
            return "output_schema_invalid"
        required = (
            "ok",
            "schema_valid",
            "size_valid",
            "canonical_JSON",
            "hashes_computed",
            "flushed_to_disk",
            "nonreplacement_rename",
        )
        if not _all_true(value, required):
            return "output_write_failed"
    else:
        return "unknown_action"
    return "ok"


def test_exact_authorization_is_recorded_without_expanding_scope() -> None:
    evidence = _read(EVIDENCE_PATH)

    assert _sha256(AUTH_PACKAGE_PATH) == AUTH_PACKAGE_DIGEST
    assert evidence["authorization"]["owner_statement"] == OWNER_STATEMENT
    assert len(OWNER_STATEMENT.encode()) == 1010
    assert hashlib.sha256(OWNER_STATEMENT.encode()).hexdigest().upper() == (
        OWNER_STATEMENT_SHA256
    )
    assert evidence["authorization"]["owner_statement_sha256"] == (
        OWNER_STATEMENT_SHA256
    )
    assert evidence["authorization"]["package_digest_sha256"] == (
        AUTH_PACKAGE_DIGEST
    )
    actions = evidence["actions_performed"]
    assert actions["source_only_implementation"] is True
    for field in (
        "PowerShell_parsed_imported_or_executed",
        "runner_or_module_executed",
        "runtime_or_hardware_observed",
        "machine_storage_F_ACL_probe_cleanup_or_scanner_action",
        "network_download_artifact_model_media_or_data_action",
        "container_Kubernetes_deployment_or_remote_git_action",
    ):
        assert actions[field] is False


def test_accepted_sources_remain_byte_exact() -> None:
    assert _sha256(RUNNER_PATH) == RUNNER_DIGEST
    assert _sha256(HANDLER_PATH) == HANDLER_DIGEST
    assert _sha256(ADAPTER_PATH) == ADAPTER_DIGEST


def test_vector_manifest_is_generated_bounded_and_exactly_twenty_plus_sixty_four() -> None:
    manifest = _read(VECTORS_PATH)
    plan = _read(PLAN_PATH)
    contract = manifest["contract_vectors"]
    handlers = manifest["handler_vectors"]
    action = [item for item in handlers if item["kind"] == "action"]
    cross = [item for item in handlers if item["kind"] == "cross_cutting"]

    assert manifest["counts"] == {
        "contract": 20,
        "handler_action": 56,
        "handler_cross_cutting": 8,
        "handler": 64,
        "total": 84,
    }
    assert len(contract) == 20
    assert len(action) == 56
    assert len(cross) == 8
    ids = [item["vector_id"] for item in contract + handlers]
    assert len(ids) == len(set(ids)) == 84
    planned = [
        case_id
        for group in plan["action_vector_groups"]
        for case_id in group["required_cases"]
    ] + plan["cross_cutting_vectors"]["required_cases"]
    assert {item["vector_id"] for item in handlers} == set(planned)
    policy = manifest["fixture_policy"]
    assert policy["generated_only"] is True
    assert policy["machine_facts_present"] is False
    assert policy[
        "private_personal_Government_camera_media_model_or_artifact_data_present"
    ] is False
    assert policy["network_input_present"] is False
    assert policy["raw_fixture_retention"] is False
    assert len(VECTORS_PATH.read_bytes()) <= 262144


@pytest.mark.parametrize(
    "vector",
    _read(VECTORS_PATH)["contract_vectors"],
    ids=lambda item: item["vector_id"],
)
def test_twenty_contract_fixtures_match_sealed_outcomes(
    vector: dict[str, object],
) -> None:
    manifest = _read(VECTORS_PATH)
    fixture = _merge(manifest["contract_base_fixture"], vector["mutation"])

    assert _contract_outcome(fixture) == vector["expected"]["outcome"]
    assert "secret" not in json.dumps(fixture).lower()


@pytest.mark.parametrize(
    "vector",
    [
        item
        for item in _read(VECTORS_PATH)["handler_vectors"]
        if item["kind"] == "action"
    ],
    ids=lambda item: item["vector_id"],
)
def test_fifty_six_handler_action_fixtures_match_accepted_source_semantics(
    vector: dict[str, object],
) -> None:
    manifest = _read(VECTORS_PATH)
    base = manifest["handler_base_transcripts"][vector["action_id"]]
    fixture = _merge(base, vector["mutation"])
    reason = _handler_reason(vector["action_id"], fixture)

    assert reason == vector["expected"]["reason_code"]
    assert (reason == "ok") is (vector["expected"]["outcome"] == "passed")
    assert len(json.dumps(fixture).encode()) <= 16384


def test_eight_cross_cutting_vectors_are_closed_and_generated() -> None:
    manifest = _read(VECTORS_PATH)
    cross = [
        item for item in manifest["handler_vectors"] if item["kind"] == "cross_cutting"
    ]
    expected_scenarios = {
        "invalid_envelope_action_plan",
        "out_of_order_transition",
        "transaction_timeout",
        "bounded_cleanup_flags",
        "sanitized_projection",
        "forbidden_surfaces_absent",
        "adapter_not_imported",
        "terminal_authority_false",
    }

    assert {item["scenario"] for item in cross} == expected_scenarios
    assert all(
        item["expected"]["outcome"]
        in {"blocked", "manual_review_required", "invariant_enforced"}
        for item in cross
    )


def test_harness_has_exact_modes_bindings_and_read_only_layers() -> None:
    source = HARNESS_PATH.read_text(encoding="utf-8")

    assert "[ValidateSet('Parse', 'Contract', 'Handler', 'Aggregate')]" in source
    assert "Set-StrictMode -Version Latest" in source
    assert "$ErrorActionPreference = 'Stop'" in source
    assert "$PSModuleAutoLoadingPreference = 'None'" in source
    assert "P36-QUARANTINE-GENERATED-VALIDATION-HARNESS-R2-1.2.0" in source
    assert "[System.Management.Automation.Language.Parser]::ParseFile" in source
    assert "windows_adapter_parser_only" in source
    assert source.count("Import-Module") == 2
    assert "-Name $script:UtilityManifestPath" in source
    assert "-Cmdlet $script:RequiredUtilityCommands" in source
    assert "-Name $script:HandlerModulePath" in source
    assert "-Scope Local" in source
    assert "-Function $script:RequiredHandlerExports" in source
    assert "-NoClobber" in source
    assert "Import-Module -Name $script:WindowsAdapterParserPath" not in source
    assert RUNNER_DIGEST in source
    assert HANDLER_DIGEST in source
    assert ADAPTER_DIGEST in source
    for action_id in ACTION_IDS:
        assert source.count(f"'{action_id}'") >= 1


def test_harness_uses_bounded_read_only_dotnet_sha256_streaming() -> None:
    source = HARNESS_PATH.read_text(encoding="utf-8")
    start = source.index("function Get-P36FileSha256")
    end = source.index("function Assert-P36ExactBindings")
    hashing = source[start:end]

    assert "Get-FileHash" not in source
    assert "$script:MaximumHashBufferBytes = 65536" in source
    assert "[System.IO.FileStream]::new(" in hashing
    assert "[System.IO.FileMode]::Open" in hashing
    assert "[System.IO.FileAccess]::Read" in hashing
    assert "[System.IO.FileShare]::Read" in hashing
    assert "$script:MaximumHashBufferBytes" in hashing
    assert "[System.IO.FileOptions]::SequentialScan" in hashing
    assert "[System.Security.Cryptography.SHA256]::Create()" in hashing
    assert "$algorithm.ComputeHash($stream)" in hashing
    assert "[System.Convert]::ToHexString($digest)" in hashing
    assert "finally" in hashing
    assert "$algorithm.Dispose()" in hashing
    assert "$stream.Dispose()" in hashing
    assert "$env:PSModulePath" not in source
    assert source.count("Import-Module") == 2


def test_harness_emits_only_allowlisted_layer_failure_codes() -> None:
    source = HARNESS_PATH.read_text(encoding="utf-8")
    trap_start = source.index("trap {")
    trap_end = source.index("function Get-P36FileSha256")
    trap = source[trap_start:trap_end]
    layers = (
        "binding",
        "manifest",
        "parser",
        "contract",
        "handler",
        "result_serialization",
    )

    assert "$script:AllowedFailureLayers = @(" in source
    assert "$script:FailureLayer = 'binding'" in source
    for layer in layers:
        assert f"'{layer}'" in source
        assert f"$script:FailureLayer = '{layer}'" in source
    assert "$script:AllowedFailureLayers -ccontains $script:FailureLayer" in trap
    assert 'reason_code = "$($safeFailureLayer)_failed"' in trap
    assert "$_" not in trap
    assert "Exception" not in trap
    assert "InvocationInfo" not in trap
    assert "raw_process_output_retained = $false" in trap
    assert "raw_exception_retained = $false" in trap


def test_runner_child_invocation_is_contract_only_and_bounded() -> None:
    source = HARNESS_PATH.read_text(encoding="utf-8")
    start = source.index("function Invoke-P36BoundedContractChild")
    end = source.index("function Invoke-P36ContractLayer")
    child = source[start:end]

    assert ".FileName = $script:RuntimePath" in child
    assert ".UseShellExecute = $false" in child
    assert ".RedirectStandardOutput = $true" in child
    assert ".RedirectStandardError = $true" in child
    assert ".CreateNoWindow = $true" in child
    for argument in ("'-NoLogo'", "'-NoProfile'", "'-NonInteractive'"):
        assert argument in child
    assert "ArgumentList.Add('Contract')" in child
    assert "ContractVectorJson" in child
    assert "Storage" not in child
    assert "WaitForExit($script:ContractTimeoutMilliseconds)" in child
    assert "Kill($true)" in child
    assert "$script:MaximumStdoutBytes" in child
    assert "$script:MaximumStderrBytes" in child


def test_harness_has_no_forbidden_dynamic_machine_or_network_surface() -> None:
    source = HARNESS_PATH.read_text(encoding="utf-8")
    manifest = _read(VECTORS_PATH)
    forbidden = set(manifest["handler_forbidden_source_tokens"]) | {
        "Invoke-Command",
        "ForEach-Object -Parallel",
        "Start-Job",
        "ThreadJob",
        "Runspace",
        "New-Item",
        "Remove-Item",
        "Move-Item",
        "Copy-Item",
        "Set-Content",
        "Add-Content",
        "Out-File",
        "Registry::",
        "Get-CimInstance",
        "Get-WmiObject",
        "Get-Service",
        "Set-Service",
        "MpCmdRun",
        "Get-MpComputerStatus",
        "WebClient",
        "$env:",
    }

    for token in forbidden:
        assert token not in source
    assert "StorageRequestJson" not in source
    assert "runner_storage_invocation_count = 0" in source
    assert "windows_adapter_import_or_execution_count = 0" in source
    assert "machine_action_count = 0" in source
    assert "network_action_count = 0" in source
    assert "raw_fixture_retained = $false" in source
    assert "raw_process_output_retained = $false" in source
    assert "raw_exception_retained = $false" in source


def test_implementation_package_binds_exact_source_vector_test_evidence_and_review() -> None:
    package = _read(IMPLEMENTATION_PACKAGE_PATH)

    assert package["status"] == (
        "sealed_source_only_generated_static_validated_owner_acceptance_pending"
    )
    assert package["future_acceptance_decision_id"] == (
        "D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE"
    )
    assert package["core_file_count"] == len(package["core_files"])
    superseded_by_R1 = {
        "tools/phase36_quarantine_generated_validation.ps1",
        "tests/test_phase36_quarantine_generated_powershell_validation_harness.py",
    }
    for item in package["core_files"]:
        if item["path"] not in superseded_by_R1:
            assert _sha256(ROOT / item["path"]) == item["sha256"]
    historical = {item["path"]: item["sha256"] for item in package["core_files"]}
    assert historical["tools/phase36_quarantine_generated_validation.ps1"] == (
        "48FC33E1928BA186C11005DBDEC055E5558D58677D51EB864D3740BCFBA208C1"
    )
    assert REVIEW_PATH.exists()
    effect = package["current_gate_effect"]
    assert effect["owner_implementation_acceptance_pending"] is True
    assert effect["PowerShell_parser_import_or_execution_authorized"] is False
    assert effect["D_P3_6_U3N_GENERATED_VALIDATION_RUNTIME_BINDING_R1_AUTH_requestable"] is False
    assert effect["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False
