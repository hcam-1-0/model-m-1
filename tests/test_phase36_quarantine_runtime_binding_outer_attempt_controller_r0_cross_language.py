import json
from pathlib import Path

from tools.phase36_quarantine_runtime_binding_outer_attempt_controller_r0_reference import (
    canonical_sha256,
    contract_projection,
    projections_equal,
)


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = ROOT / (
    "tools/phase36_quarantine_runtime_binding_outer_attempt_controller_r0.ps1"
)
VECTORS = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-binding-outer-attempt-controller-r0-vectors.json"
)
BEGIN = "# HCAM_OUTER_CONTRACT_PROJECTION_JSON_BEGIN"
END = "# HCAM_OUTER_CONTRACT_PROJECTION_JSON_END"


def _powershell_projection() -> dict[str, object]:
    source = POWERSHELL.read_text(encoding="utf-8")
    block = source.split(BEGIN, 1)[1].split(END, 1)[0]
    return json.loads(block.split("<#", 1)[1].rsplit("#>", 1)[0].strip())


def test_powershell_and_python_contract_projections_are_canonically_equal() -> None:
    powershell = _powershell_projection()
    python = contract_projection()

    assert projections_equal(powershell, python)
    assert canonical_sha256(powershell) == canonical_sha256(python)


def test_generated_cross_language_group_is_source_independent_and_deterministic() -> None:
    manifest = json.loads(VECTORS.read_text(encoding="utf-8"))
    vectors = [
        item
        for item in manifest["vectors"]
        if item["group"] == "PowerShell_Python_canonical_projection_equivalence"
    ]

    assert len(vectors) == 32
    assert len({item["expected_result_sha256"] for item in vectors}) == 1
    assert all(item["expected_result"]["succeeded"] is True for item in vectors)


def test_contract_projection_excludes_runtime_values_and_sensitive_material() -> None:
    projection = json.dumps(contract_projection(), sort_keys=True).casefold()

    for token in (
        "c:\\",
        "hostname",
        "username",
        "password",
        "private",
        "government",
        "stdout_value",
        "stderr_value",
    ):
        assert token not in projection

