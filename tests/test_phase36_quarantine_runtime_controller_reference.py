import copy
import json
from pathlib import Path

import pytest

from tools.phase36_quarantine_runtime_controller_reference import (
    ACTION_ORDER,
    canonical_json,
    canonical_sha256,
    evaluate_request,
    validate_request,
    validate_result,
)


ROOT = Path(__file__).resolve().parents[1]
VECTORS_PATH = (
    ROOT / "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-vectors.json"
)
MANIFEST = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
VECTORS = MANIFEST["vectors"]


def _apply_mutation(root: object, mutation: dict[str, object]) -> None:
    operation = mutation["op"]
    if operation == "none":
        return
    if operation == "multi":
        for child in mutation["mutations"]:
            _apply_mutation(root, child)
        return

    node = root
    for part in mutation["path"][:-1]:
        node = node[part]
    key = mutation["path"][-1]
    if operation in {"set", "add"}:
        node[key] = copy.deepcopy(mutation["value"])
    elif operation == "delete":
        del node[key]
    elif operation == "append":
        node[key].append(copy.deepcopy(mutation["value"]))
    elif operation == "swap":
        left, right = mutation["indices"]
        node[key][left], node[key][right] = node[key][right], node[key][left]
    else:
        raise AssertionError(operation)


def _request_for(vector: dict[str, object]) -> dict[str, object]:
    request = copy.deepcopy(MANIFEST["base_request"])
    _apply_mutation(request, vector["mutation"])
    return request


@pytest.mark.parametrize("vector", VECTORS, ids=lambda vector: vector["id"])
def test_all_192_generated_vectors(vector: dict[str, object]) -> None:
    result = evaluate_request(_request_for(vector))

    assert result == vector["expected_projection"]
    assert validate_result(result)
    assert result["terminal"] is True
    assert result["action_counts"]["retries"] == 0
    assert result["gate_effect"]["python_machine_fallback"] is False


def test_canonical_serialization_and_hash_are_stable() -> None:
    left = {"z": [3, 2, 1], "a": {"b": True}}
    right = {"a": {"b": True}, "z": [3, 2, 1]}

    assert canonical_json(left) == canonical_json(right) == '{"a":{"b":true},"z":[3,2,1]}'
    assert canonical_sha256(left) == canonical_sha256(right)
    assert len(canonical_sha256(left)) == 64
    with pytest.raises(ValueError):
        canonical_json({"value": float("nan")})


def test_request_validation_rejects_non_mapping_and_nested_prohibited_material() -> None:
    request = copy.deepcopy(MANIFEST["base_request"])
    request["input_bindings"]["stage_outcomes"] = {"safe": [
        {"nested": {"PASSWORD": "generated-only"}}
    ]}

    assert validate_request(None) is False
    assert validate_request([]) is False
    assert validate_request(request) is False


def test_observed_stderr_cleanup_and_retention_bounds_fail_closed() -> None:
    cases = (
        ("stderr_bytes", 4097, "process_output_bounds_failed"),
        ("cleanup_count", 5, "result_contract_invalid"),
        ("retained_raw_bytes", 1, "result_contract_invalid"),
    )
    for name, value, reason in cases:
        request = copy.deepcopy(MANIFEST["base_request"])
        request["input_bindings"][name] = value
        assert evaluate_request(request)["reason_code"] == reason


def test_per_action_timeout_cannot_exceed_total_timeout() -> None:
    request = copy.deepcopy(MANIFEST["base_request"])
    request["declared_bounds"]["per_action_timeout_ms"] = 30000
    request["declared_bounds"]["total_timeout_ms"] = 29999

    result = evaluate_request(request)
    assert result["reason_code"] == "request_contract_failed"
    assert result["stage_projection"]["failed_action"] == ACTION_ORDER[0]


def test_result_validation_rejects_unknown_malformed_or_raw_material() -> None:
    valid = evaluate_request(copy.deepcopy(MANIFEST["base_request"]))
    unknown = copy.deepcopy(valid)
    unknown["reason_code"] = "unknown"
    malformed = copy.deepcopy(valid)
    del malformed["gate_effect"]
    raw = copy.deepcopy(valid)
    raw["raw_exception"] = "generated-only"
    wrong_terminal = copy.deepcopy(valid)
    wrong_terminal["terminal"] = False
    wrong_success_type = copy.deepcopy(valid)
    wrong_success_type["succeeded"] = 1
    wrong_nested_type = copy.deepcopy(valid)
    wrong_nested_type["gate_effect"] = []
    inconsistent = copy.deepcopy(valid)
    inconsistent["stage_projection"]["completed_actions"] = 17

    for result in (
        None,
        unknown,
        malformed,
        raw,
        wrong_terminal,
        wrong_success_type,
        wrong_nested_type,
        inconsistent,
    ):
        assert validate_result(result) is False
