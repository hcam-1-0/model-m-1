from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tools/phase36_consolidated_runtime_closeout_u4d_reference.py"
HARNESS = (
    ROOT / "tools/phase36_consolidated_runtime_closeout_u4d_generated_validation.ps1"
)
CONTRACT = (
    ROOT
    / "contracts/phase-3/p3-6-consolidated-runtime-closeout-u4d-process-output-contract.json"
)
BEGIN = "# HCAM_U4D_CONTRACT_PROJECTION_JSON_BEGIN"
END = "# HCAM_U4D_CONTRACT_PROJECTION_JSON_END"


def _load_reference() -> ModuleType:
    spec = importlib.util.spec_from_file_location("u4d_reference_projection", REFERENCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _PowerShell_projection() -> dict[str, object]:
    source = HARNESS.read_text(encoding="utf-8")
    assert source.count(BEGIN) == source.count(END) == 1
    payload = source.split(BEGIN, 1)[1].split(END, 1)[0]
    payload = payload.replace("<#", "", 1).replace("#>", "", 1).strip()
    return json.loads(payload)


def test_PowerShell_and_Python_canonical_projections_match() -> None:
    module = _load_reference()
    assert _PowerShell_projection() == module.canonical_projection()


def test_projection_matches_contract_limits_operation_and_child_reasons() -> None:
    projection = _PowerShell_projection()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert projection["contract_version"] == contract["contract_version"]
    assert projection["operation"] == contract["operation"]
    assert (
        projection["required_case_count"]
        == contract["limits"]["required_generated_case_count"]
    )
    assert (
        projection["maximum_stdout_bytes"] == contract["limits"]["maximum_stdout_bytes"]
    )
    assert (
        projection["maximum_stderr_bytes"] == contract["limits"]["maximum_stderr_bytes"]
    )
    assert (
        projection["terminal_line_count"]
        == contract["limits"]["terminal_stdout_line_count"]
    )
    assert projection["child_reason_codes"] == contract["child_envelope_reason_codes"]
