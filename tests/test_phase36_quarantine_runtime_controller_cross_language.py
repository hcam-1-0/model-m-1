import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools.phase36_quarantine_runtime_controller_reference import (
    contract_projection,
    evaluate_request,
    projections_equal,
)


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL_PATH = ROOT / "tools/phase36_quarantine_runtime_controller.ps1"
VECTORS_PATH = (
    ROOT / "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-vectors.json"
)
MANIFEST = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
CROSS_VECTORS = [
    vector for vector in MANIFEST["vectors"] if vector["group"] == "cross_language_projection"
]
IMMUTABLE_HASHES = {
    "tools/phase36_quarantine_generated_validation.ps1": (
        "830D88F8915B084DEF1089927FF785C9C0E7BDB6F0755B5315EE85E9DA8A8B8A"
    ),
    "contracts/phase-3/p3-6-quarantine-generated-powershell-validation-r0-vectors.json": (
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


def _static_powershell_projection() -> dict[str, object]:
    source = POWERSHELL_PATH.read_text(encoding="utf-8")
    block = source.split("# HCAM_CONTRACT_PROJECTION_JSON_BEGIN", 1)[1].split(
        "# HCAM_CONTRACT_PROJECTION_JSON_END", 1
    )[0]
    return json.loads(block.split("<#", 1)[1].rsplit("#>", 1)[0].strip())


def _apply(root: object, mutation: dict[str, object]) -> None:
    if mutation["op"] == "none":
        return
    if mutation["op"] == "multi":
        for child in mutation["mutations"]:
            _apply(root, child)
        return
    node = root
    for part in mutation["path"][:-1]:
        node = node[part]
    key = mutation["path"][-1]
    if mutation["op"] in {"set", "add"}:
        node[key] = copy.deepcopy(mutation["value"])
    elif mutation["op"] == "delete":
        del node[key]
    elif mutation["op"] == "swap":
        left, right = mutation["indices"]
        node[key][left], node[key][right] = node[key][right], node[key][left]
    else:
        raise AssertionError(mutation["op"])


def test_powershell_and_python_contract_projections_are_exactly_equal() -> None:
    powershell = _static_powershell_projection()
    python = contract_projection()

    assert powershell == python
    assert projections_equal(powershell)


def test_projection_difference_always_fails_closed() -> None:
    missing = contract_projection()
    del missing["action_order"]
    extra = contract_projection()
    extra["implementation_extension"] = True
    reordered = contract_projection()
    reordered["action_order"] = list(reversed(reordered["action_order"]))

    assert projections_equal(None) is False
    assert projections_equal([]) is False
    assert projections_equal(missing) is False
    assert projections_equal(extra) is False
    assert projections_equal(reordered) is False


@pytest.mark.parametrize("vector", CROSS_VECTORS, ids=lambda vector: vector["id"])
def test_cross_language_vectors_match_the_canonical_expected_projection(
    vector: dict[str, object],
) -> None:
    request = copy.deepcopy(MANIFEST["base_request"])
    _apply(request, vector["mutation"])

    assert evaluate_request(request) == vector["expected_projection"]
    assert vector["expected_projection"]["gate_effect"]["machine_action_authorized"] is False


def test_all_five_accepted_inputs_remain_byte_exact() -> None:
    for relative, expected in IMMUTABLE_HASHES.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()
        assert actual == expected


def test_cross_language_vector_count_is_exact() -> None:
    assert len(CROSS_VECTORS) == 32
