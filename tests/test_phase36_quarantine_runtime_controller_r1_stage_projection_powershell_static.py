import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = ROOT / "tools/phase36_quarantine_runtime_controller_r1.ps1"
PYTHON = ROOT / "tools/phase36_quarantine_runtime_controller_r1_reference.py"
BEGIN = "# HCAM_CONTRACT_PROJECTION_JSON_BEGIN"
END = "# HCAM_CONTRACT_PROJECTION_JSON_END"
IMMUTABLE_INPUTS = {
    "tools/phase36_quarantine_runtime_controller.ps1": (
        "78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB"
    ),
    "tools/phase36_quarantine_runtime_controller_u3v_h1_r1_diagnostic.ps1": (
        "CD868E3F06CA12AC424B2C4C221F6425FCD0DA289C527DED462121333513B1C9"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-contract.json": (
        "F0E41634760E3697F74EA2DEA44E7B2004392557E3167504BD69F2D78A4DC3CB"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-evidence.json": (
        "84DC68C3800983AFA65EBB19C99A36D02C3D97CD28F6D937C43CF5292AF12A45"
    ),
}


def _source() -> str:
    return POWERSHELL.read_text(encoding="utf-8")


def _static_projection() -> dict[str, object]:
    block = _source().split(BEGIN, 1)[1].split(END, 1)[0]
    return json.loads(block.split("<#", 1)[1].rsplit("#>", 1)[0].strip())


def _function_block(name: str, next_name: str) -> str:
    source = _source()
    return source.split(f"function {name} {{", 1)[1].split(
        f"function {next_name} {{", 1
    )[0]


def test_policy_success_constructs_literal_nulls_without_string_boundary() -> None:
    source = _source()
    success = _function_block(
        "New-HcamPolicyValidProjection", "New-HcamActionFailureProjection"
    )

    assert "[AllowNull()]" not in source
    assert "[string]$FailedAction" not in source
    assert "failed_action = $null" in success
    assert "failed_stage = $null" in success
    assert "-ReasonCode 'policy_valid'" in success
    assert "-Succeeded $true" in success
    assert "[string]" not in success


def test_failure_constructor_uses_nonempty_mapped_action_and_reason() -> None:
    failure = _function_block(
        "New-HcamActionFailureProjection", "Test-HcamActionPlan"
    )

    assert "[Parameter(Mandatory = $true)]" in failure
    assert "[string]$Action" in failure
    assert "$Script:HcamActionFailureReasons.Contains($Action)" in failure
    assert "failed_action = $Action" in failure
    assert "failed_stage = $ReasonCode" in failure
    assert "-Succeeded $false" in failure


def test_source_is_definition_only_default_denied_and_machine_free() -> None:
    source = _source()
    folded = source.casefold()

    assert "$Script:HcamMachineAuthorityEnabled = $false" in source
    assert "$Script:HcamAutomaticRetryEnabled = $false" in source
    assert "$Script:HcamPythonMachineFallbackEnabled = $false" in source
    assert source.count("function Invoke-HcamRuntimeControllerR1 {") == 1
    assert source.rstrip().endswith("}")
    forbidden = (
        "invoke-expression",
        "start-process",
        "invoke-webrequest",
        "invoke-restmethod",
        "system.net",
        "dllimport",
        "add-type",
        "import-module",
        "get-childitem",
        "get-item",
        "get-content",
        "set-content",
        "new-item",
        "remove-item",
        "move-item",
        "copy-item",
        "get-wmiobject",
        "get-ciminstance",
        "microsoft.win32",
        "system.io.",
    )
    assert all(token not in folded for token in forbidden)


def test_embedded_projection_is_complete_static_JSON_only() -> None:
    projection = _static_projection()

    assert projection["contract_version"] == "1.0.0"
    assert len(projection["action_order"]) == 18
    assert len(projection["failure_reason_codes"]) == 18
    assert projection["stage_projection_fields"] == [
        "completed_actions",
        "failed_action",
        "failed_stage",
    ]
    assert set(projection["action_order"]) == set(
        projection["action_failure_reasons"]
    )


def test_python_reference_imports_are_standard_library_and_machine_disabled() -> None:
    tree = ast.parse(PYTHON.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])

    assert imported == {"hashlib", "json", "typing"}
    assert imported.isdisjoint(
        {
            "ctypes",
            "cffi",
            "os",
            "pathlib",
            "platform",
            "socket",
            "subprocess",
            "urllib",
            "importlib",
            "requests",
        }
    )


def test_historical_inputs_are_immutable_and_new_sources_are_LF_only() -> None:
    for relative, expected in IMMUTABLE_INPUTS.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()
        assert actual == expected
    for path in (POWERSHELL, PYTHON):
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload
