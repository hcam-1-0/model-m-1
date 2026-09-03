from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTER_R3 = ROOT / "tools/phase36_consolidated_runtime_closeout_r3_generated_validation.ps1"
HANDLER_R3 = ROOT / "tools/phase36_quarantine_generated_validation_r3.ps1"
EVIDENCE = ROOT / (
    "contracts/phase-3/"
    "p3-6-consolidated-runtime-closeout-r3-generated-validation-evidence.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_historical_runtime_inputs_remain_byte_exact() -> None:
    expected = {
        "tools/phase36_consolidated_runtime_closeout_u4d_generated_validation.ps1": (
            "5267365930985C0CFBC0E3A96F5D4B58DDD9072EBF222AA607D24773F0AFA72B"
        ),
        "tools/phase36_quarantine_generated_validation.ps1": (
            "830D88F8915B084DEF1089927FF785C9C0E7BDB6F0755B5315EE85E9DA8A8B8A"
        ),
        "tools/phase36_quarantine_runtime_binding_outer_attempt_controller_r0.ps1": (
            "0E539126536CEF9F490EE164C5ECEC2FED36649C163FAAA8F32193B2DB744B99"
        ),
        "contracts/phase-3/"
        "p3-6-quarantine-runtime-binding-outer-attempt-controller-r0-vectors.json": (
            "EE25BD99942F0CB68E157439ADEA230D3E549FBAC1743AC783775DDA58AA7B13"
        ),
        "contracts/phase-3/"
        "p3-6-quarantine-generated-powershell-validation-r0-vectors.json": (
            "5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C"
        ),
    }
    assert {_path: _sha256(ROOT / _path) for _path in expected} == expected


def test_outer_r3_has_typed_normalization_and_default_deny_validation() -> None:
    source = OUTER_R3.read_text(encoding="utf-8")
    assert "ConvertTo-HcamU4dGeneratedContractValue" in source
    assert "Test-HcamU4dGeneratedControllerRequest" in source
    assert "Test-HcamU4dContainsProhibitedField" in source
    assert "New-HcamOuterDefaultDenyResult -AttemptsConsumed $Attempts" in source
    assert "-Cmdlet @('ConvertFrom-Json', 'ConvertTo-Json')" in source
    assert "Invoke-HcamOuterAttemptControllerR0" in source
    assert "raw_retained_bytes\":0" in source


def test_handler_r3_is_self_bound_and_keeps_machine_paths_closed() -> None:
    source = HANDLER_R3.read_text(encoding="utf-8")
    assert "P36-QUARANTINE-GENERATED-VALIDATION-HARNESS-R3-1.3.0" in source
    assert "'phase36_quarantine_generated_validation_r3.ps1'" in source
    assert "$script:RequiredCoreCommands" in source
    assert "'Microsoft.PowerShell.Core'" in source
    assert "@(Compare-Object" in source
    assert "runner_storage_invocation_count = 0" in source
    assert "windows_adapter_import_or_execution_count = 0" in source
    assert "storage_attempt_authorized = $false" in source
    assert "-Mode Storage" not in source
    assert "-StorageRequestJson" not in source


def test_evidence_binds_exact_successors_and_all_500_cases() -> None:
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    outer = evidence["outer_policy_validation"]
    handler = evidence["runner_handler_validation"]

    assert outer["successor_harness_sha256"] == _sha256(OUTER_R3)
    assert handler["successor_harness_sha256"] == _sha256(HANDLER_R3)
    assert outer["required_cases"] == outer["accepted_cases"] == 416
    assert handler["runner_contract_cases"] == 20
    assert handler["pure_handler_cases"] == 64
    assert handler["accepted_cases"] == 84
    assert outer["accepted_cases"] + handler["accepted_cases"] == 500
    assert all(value is False for value in evidence["closed_gates"].values())
