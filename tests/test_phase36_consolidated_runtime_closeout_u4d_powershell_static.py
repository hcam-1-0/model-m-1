from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = (
    ROOT / "tools/phase36_consolidated_runtime_closeout_u4d_generated_validation.ps1"
)


def test_harness_is_inert_default_off_and_suppresses_nondata_streams() -> None:
    source = HARNESS.read_text(encoding="utf-8")

    assert "$Script:HcamU4dMachineAuthorityEnabled = $false" in source
    assert "$Script:HcamU4dAutomaticRetryEnabled = $false" in source
    assert "$Script:HcamU4dRawRetentionEnabled = $false" in source
    for preference in (
        "$ProgressPreference = 'SilentlyContinue'",
        "$WarningPreference = 'SilentlyContinue'",
        "$VerbosePreference = 'SilentlyContinue'",
        "$DebugPreference = 'SilentlyContinue'",
        "$InformationPreference = 'SilentlyContinue'",
        "$PSModuleAutoLoadingPreference = 'None'",
    ):
        assert preference in source


def test_harness_has_one_console_result_surface_and_no_raw_diagnostics() -> None:
    source = HARNESS.read_text(encoding="utf-8")

    assert source.count("[System.Console]::Out.WriteLine($Json)") == 1
    assert source.count("[System.Environment]::Exit(0)") == 1
    assert 'raw_retained_bytes":0' in source
    for token in (
        "Write-Output",
        "Write-Error",
        "Write-Warning",
        "Write-Verbose",
        "Write-Debug",
        "Write-Information",
        "$_.Exception",
        "$Error[",
        "Get-FileHash",
        "Resolve-Path",
        "Get-ChildItem",
        "Invoke-Expression",
        "Start-Process",
        "Invoke-WebRequest",
        "Invoke-RestMethod",
    ):
        assert token not in source


def test_harness_binds_only_accepted_controller_and_vector_manifest() -> None:
    source = HARNESS.read_text(encoding="utf-8")

    assert "Get-HcamU4dBoundedSha256" in source
    assert source.count("$ControllerHash") >= 2
    assert source.count("$VectorHash") >= 2
    assert "$null = . ([System.IO.FileInfo]::new($ControllerPath).FullName)" in source
    assert "Invoke-HcamOuterAttemptControllerR0 -Request $Vector.request" in source
    assert "$Script:HcamU4dRequiredCaseCount = 416" in source
    assert "$Manifest.vectors.Count -ne $Script:HcamU4dRequiredCaseCount" in source


def test_harness_does_not_expose_machine_storage_network_or_Git_operations() -> None:
    source = HARNESS.read_text(encoding="utf-8").lower()

    for token in (
        "createfilew",
        "createdirectoryw",
        "setnamedsecurityinfo",
        "get-acl",
        "set-acl",
        "f:\\",
        "b:\\",
        "mpcmdrun",
        "modelscan",
        "kubectl",
        "docker",
        "git push",
        "git commit",
        "http://",
        "https://",
    ):
        assert token not in source
