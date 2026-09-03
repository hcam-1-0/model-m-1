import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = ROOT / (
    "tools/phase36_quarantine_runtime_binding_outer_attempt_controller_r0.ps1"
)
PYTHON = ROOT / (
    "tools/phase36_quarantine_runtime_binding_outer_attempt_controller_r0_reference.py"
)
BEGIN = "# HCAM_OUTER_CONTRACT_PROJECTION_JSON_BEGIN"
END = "# HCAM_OUTER_CONTRACT_PROJECTION_JSON_END"


def _source() -> str:
    return POWERSHELL.read_text(encoding="utf-8")


def _projection() -> dict[str, object]:
    block = _source().split(BEGIN, 1)[1].split(END, 1)[0]
    return json.loads(block.split("<#", 1)[1].rsplit("#>", 1)[0].strip())


def _function_block(name: str, next_name: str | None = None) -> str:
    source = _source().split(f"function {name} {{", 1)[1]
    if next_name is not None:
        source = source.split(f"function {next_name} {{", 1)[0]
    return source


def test_source_is_definition_only_default_off_and_contains_no_machine_adapter() -> None:
    source = _source()
    folded = source.casefold()

    assert "$Script:HcamOuterMachineAuthorityEnabled = $false" in source
    assert "$Script:HcamOuterAutomaticRetryEnabled = $false" in source
    assert "$Script:HcamOuterPythonMachineFallbackEnabled = $false" in source
    assert source.count("function Invoke-HcamOuterAttemptControllerR0 {") == 1
    assert source.rstrip().endswith("}")
    forbidden = (
        "add-type",
        "dllimport",
        "get-childitem",
        "get-ciminstance",
        "get-content",
        "get-item",
        "get-wmiobject",
        "import-module",
        "invoke-expression",
        "invoke-restmethod",
        "invoke-webrequest",
        "microsoft.win32",
        "new-item",
        "remove-item",
        "set-content",
        "start-process",
        "system.io.",
        "system.net",
    )
    assert all(token not in folded for token in forbidden)


def test_fixed_parent_reduction_is_exact_ordered_and_literal_true() -> None:
    block = _function_block(
        "Test-HcamOuterFixedParentSet", "New-HcamOuterPredicateFlags"
    )

    assert "$Records.Count -ne 3" in block
    assert "$Index = 0; $Index -lt 3; $Index += 1" in block
    assert "-ExpectedIndex $Index" in block
    assert "$Records[$Index].valid -ne $true" in block
    assert "Where-Object" not in block
    assert ".Count -eq 0" not in block


def test_controller_is_static_allowlist_dispatch_without_dynamic_evaluation() -> None:
    source = _source()
    invoke = _function_block("Invoke-HcamOuterAttemptControllerR0")

    assert "generated_contract_validation_v1" in source
    assert "terminal_default_deny_internal_failure" in source
    assert "$Script:HcamOuterSupportedOperations" in invoke
    assert "$Script:HcamOuterStages" in source
    assert "Invoke-Expression" not in source
    assert "ScriptBlock" not in source
    assert "& $" not in source


def test_embedded_projection_is_strict_json_and_has_required_contract_shape() -> None:
    projection = _projection()

    assert projection["contract_version"] == "1.0.0"
    assert projection["supported_operations"] == [
        "generated_contract_validation_v1"
    ]
    assert len(projection["stages"]) == 11
    assert projection["parent_indexes"] == [0, 1, 2]
    assert projection["process_limits"] == {
        "max_processes": 1,
        "max_result_bytes": 32768,
        "max_stderr_bytes": 0,
        "max_stdout_bytes": 16384,
        "timeout_ms": 120000,
    }


def test_python_reference_is_syntax_valid_without_machine_imports() -> None:
    tree = ast.parse(PYTHON.read_text(encoding="utf-8"))
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

    assert "open" not in names
    assert "exec" not in names
    assert "eval" not in names
    assert "__import__" not in names


def test_sources_are_lf_terminated() -> None:
    for path in (POWERSHELL, PYTHON):
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload

