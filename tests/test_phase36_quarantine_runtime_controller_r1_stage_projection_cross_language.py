import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools.phase36_quarantine_runtime_controller_r1_reference import (
    ACTION_FAILURE_REASONS,
    ACTION_ORDER,
    contract_projection,
    evaluate_request,
    projections_equal,
)


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = ROOT / "tools/phase36_quarantine_runtime_controller_r1.ps1"
CONTRACT = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-controller-r1-stage-projection-contract.json"
)
VECTORS = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-controller-r1-stage-projection-vectors.json"
)
MANIFEST = json.loads(VECTORS.read_text(encoding="utf-8"))
CROSS_VECTORS = [
    vector
    for vector in MANIFEST["vectors"]
    if vector["group"] == "cross_language_canonical_projection"
]
FAILURE_VECTORS = [
    vector
    for vector in MANIFEST["vectors"]
    if vector["group"]
    in {"all_eighteen_failure_actions", "all_eighteen_failure_reasons"}
]
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


def _static_powershell_projection() -> dict[str, object]:
    source = POWERSHELL.read_text(encoding="utf-8")
    block = source.split("# HCAM_CONTRACT_PROJECTION_JSON_BEGIN", 1)[1].split(
        "# HCAM_CONTRACT_PROJECTION_JSON_END", 1
    )[0]
    return json.loads(block.split("<#", 1)[1].rsplit("#>", 1)[0].strip())


def _apply(root: object, mutation: dict[str, object]) -> None:
    operation = mutation["op"]
    if operation == "none":
        return
    node = root
    for part in mutation["path"][:-1]:
        node = node[part]
    key = mutation["path"][-1]
    if operation == "set":
        node[key] = copy.deepcopy(mutation["value"])
    elif operation == "add":
        node[key] = copy.deepcopy(mutation["value"])
    elif operation == "delete":
        del node[key]
    elif operation == "swap":
        left, right = mutation["indices"]
        node[key][left], node[key][right] = node[key][right], node[key][left]
    else:
        raise AssertionError(operation)


def test_static_powershell_and_python_contract_projections_match_exactly() -> None:
    powershell = _static_powershell_projection()
    python = contract_projection()

    assert powershell == python
    assert projections_equal(powershell)


@pytest.mark.parametrize("vector", CROSS_VECTORS, ids=lambda vector: vector["id"])
def test_all_cross_language_projection_vectors(vector: dict[str, object]) -> None:
    candidate = contract_projection()
    _apply(candidate, vector["mutation"])
    assert projections_equal(candidate) is vector["expected_equal"]


@pytest.mark.parametrize("vector", FAILURE_VECTORS, ids=lambda vector: vector["id"])
def test_all_action_reason_vectors_preserve_exact_semantics(
    vector: dict[str, object],
) -> None:
    request = copy.deepcopy(MANIFEST["base_request"])
    mutation = vector["mutation"]
    if mutation["op"] == "multi":
        for child in mutation["mutations"]:
            _apply(request, child)
    else:
        _apply(request, mutation)
    result = evaluate_request(request)

    assert result == vector["expected_projection"]
    failed_action = result["stage_projection"]["failed_action"]
    assert failed_action in ACTION_ORDER
    assert result["reason_code"] == ACTION_FAILURE_REASONS[failed_action]


def test_contract_and_sources_share_the_same_eighteen_action_mapping() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    projection = _static_powershell_projection()

    assert contract["action_order"] == projection["action_order"] == list(ACTION_ORDER)
    assert contract["action_failure_reasons"] == projection[
        "action_failure_reasons"
    ] == ACTION_FAILURE_REASONS


def test_all_four_accepted_historical_inputs_remain_byte_exact() -> None:
    for relative, expected in IMMUTABLE_INPUTS.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()
        assert actual == expected


def test_cross_language_group_count_is_exact() -> None:
    assert len(CROSS_VECTORS) == 32
    assert len(FAILURE_VECTORS) == 64
