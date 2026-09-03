import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL_PATH = ROOT / "tools/phase36_quarantine_runtime_controller.ps1"
PYTHON_PATH = ROOT / "tools/phase36_quarantine_runtime_controller_reference.py"
BEGIN = "# HCAM_CONTRACT_PROJECTION_JSON_BEGIN"
END = "# HCAM_CONTRACT_PROJECTION_JSON_END"


def _powershell_projection() -> dict[str, object]:
    source = POWERSHELL_PATH.read_text(encoding="utf-8")
    block = source.split(BEGIN, 1)[1].split(END, 1)[0]
    payload = block.split("<#", 1)[1].rsplit("#>", 1)[0].strip()
    return json.loads(payload)


def test_powershell_source_is_definition_only_and_default_denied() -> None:
    source = POWERSHELL_PATH.read_text(encoding="utf-8")

    assert "$Script:HcamMachineAuthorityEnabled = $false" in source
    assert "$Script:HcamAutomaticRetryEnabled = $false" in source
    assert "$Script:HcamPythonMachineFallbackEnabled = $false" in source
    assert source.count("function Invoke-HcamRuntimeController {") == 1
    assert "PowerShell_only" not in source
    assert "Preflight' -or" in source
    assert "owner_source_implementation_acceptance_required" in source


def test_powershell_source_has_no_dynamic_network_or_direct_machine_surface() -> None:
    source = POWERSHELL_PATH.read_text(encoding="utf-8").casefold()
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
    for token in forbidden:
        assert token not in source


def test_powershell_static_projection_is_bounded_and_complete() -> None:
    projection = _powershell_projection()

    assert projection["contract_version"] == "1.0.0"
    assert len(projection["action_order"]) == 18
    assert len(projection["failure_reason_codes"]) == 18
    assert set(projection["action_order"]) == set(projection["action_failure_reasons"])
    assert set(projection["failure_reason_codes"]) == set(
        projection["action_failure_reasons"].values()
    )
    assert projection["modes"] == ["Policy", "Preflight"]


def test_python_reference_imports_are_machine_disabled_and_standard_library_only() -> None:
    tree = ast.parse(PYTHON_PATH.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])

    assert imported == {"hashlib", "json", "typing"}
    assert imported.isdisjoint({
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
    })


def test_controller_sources_are_lf_only() -> None:
    for path in (POWERSHELL_PATH, PYTHON_PATH):
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload
