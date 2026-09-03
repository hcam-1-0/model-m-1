import copy
import json
from pathlib import Path

import pytest

from tools import phase36_quarantine_runtime_controller_r1_reference as reference
from tools.phase36_quarantine_runtime_controller_r1_reference import (
    ACTION_FAILURE_REASONS,
    ACTION_ORDER,
    canonical_json,
    canonical_sha256,
    contract_projection,
    evaluate_request,
    projections_equal,
    validate_request,
    validate_result,
    validate_stage_projection,
)


ROOT = Path(__file__).resolve().parents[1]
VECTORS_PATH = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-controller-r1-stage-projection-vectors.json"
)
MANIFEST = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
VECTORS = MANIFEST["vectors"]


def _apply(root: object, mutation: dict[str, object]) -> None:
    operation = mutation["op"]
    if operation == "none":
        return
    if operation == "multi":
        for child in mutation["mutations"]:
            _apply(root, child)
        return
    node = root
    for part in mutation["path"][:-1]:
        node = node[part]
    key = mutation["path"][-1]
    if operation in {"set", "add"}:
        node[key] = copy.deepcopy(mutation["value"])
    elif operation == "delete":
        del node[key]
    elif operation == "swap":
        left, right = mutation["indices"]
        node[key][left], node[key][right] = node[key][right], node[key][left]
    else:
        raise AssertionError(operation)


@pytest.mark.parametrize("vector", VECTORS, ids=lambda vector: vector["id"])
def test_all_288_generated_vectors(vector: dict[str, object]) -> None:
    kind = vector["kind"]
    if kind == "request":
        request = copy.deepcopy(MANIFEST["base_request"])
        _apply(request, vector["mutation"])
        actual = evaluate_request(request)
        assert actual == vector["expected_projection"]
        assert validate_result(actual)
    elif kind == "result":
        candidate = copy.deepcopy(MANIFEST["base_success_result"])
        _apply(candidate, vector["mutation"])
        assert validate_result(candidate) is vector["expected_valid"]
    elif kind == "contract_projection":
        candidate = contract_projection()
        _apply(candidate, vector["mutation"])
        assert projections_equal(candidate) is vector["expected_equal"]
    else:
        raise AssertionError(kind)


def test_success_projection_uses_exact_nulls_and_empty_strings_fail() -> None:
    success = evaluate_request(copy.deepcopy(MANIFEST["base_request"]))
    assert success["stage_projection"] == {
        "completed_actions": 18,
        "failed_action": None,
        "failed_stage": None,
    }
    assert validate_stage_projection(
        success["stage_projection"], succeeded=True, reason_code="policy_valid"
    )
    for field in ("failed_action", "failed_stage"):
        candidate = copy.deepcopy(success["stage_projection"])
        candidate[field] = ""
        assert not validate_stage_projection(
            candidate, succeeded=True, reason_code="policy_valid"
        )


@pytest.mark.parametrize("action", ACTION_ORDER)
def test_each_failure_is_nonempty_allowlisted_and_indexed(action: str) -> None:
    request = copy.deepcopy(MANIFEST["base_request"])
    request["input_bindings"]["stage_outcomes"][action] = ACTION_FAILURE_REASONS[
        action
    ]
    result = evaluate_request(request)

    assert result["succeeded"] is False
    assert result["stage_projection"] == {
        "completed_actions": ACTION_ORDER.index(action),
        "failed_action": action,
        "failed_stage": ACTION_FAILURE_REASONS[action],
    }
    assert validate_result(result)


def test_request_validation_and_default_deny_branches() -> None:
    request = copy.deepcopy(MANIFEST["base_request"])
    assert validate_request(request)

    cases = []
    for mutation in (
        {"op": "delete", "path": ["mode"]},
        {"op": "set", "path": ["mode"], "value": "Unknown"},
        {
            "op": "set",
            "path": ["authorization_binding", "machine_authority"],
            "value": True,
        },
        {"op": "set", "path": ["action_plan"], "value": []},
        {
            "op": "add",
            "path": ["input_bindings", "stage_outcomes", "unknown"],
            "value": "pass",
        },
        {
            "op": "add",
            "path": ["input_bindings", "stage_outcomes", ACTION_ORDER[2]],
            "value": "unknown_reason",
        },
    ):
        candidate = copy.deepcopy(request)
        _apply(candidate, mutation)
        cases.append(candidate)

    assert evaluate_request(cases[0])["reason_code"] == "request_contract_failed"
    assert evaluate_request(cases[1])["reason_code"] == "request_contract_failed"
    assert evaluate_request(cases[2])["reason_code"] == "authorization_binding_failed"
    assert evaluate_request(cases[3])["reason_code"] == "request_contract_failed"
    assert evaluate_request(cases[4])["reason_code"] == "result_contract_invalid"
    assert evaluate_request(cases[5])["reason_code"] == "result_contract_invalid"


def test_resource_and_closed_gate_branches_fail_deterministically() -> None:
    cases = (
        ("closure_file_count", 65, "utility_manifest_closure_failed"),
        ("closure_total_bytes", 134217729, "utility_manifest_closure_failed"),
        ("process_count", 2, "process_start_failed"),
        ("elapsed_ms", 120001, "process_timeout"),
        ("stdout_bytes", 65537, "process_output_bounds_failed"),
        ("stderr_bytes", 65537, "process_output_bounds_failed"),
        ("result_bytes", 65537, "process_output_bounds_failed"),
        ("retained_raw_bytes", 1, "result_contract_invalid"),
        ("cleanup_count", 5, "result_contract_invalid"),
    )
    for field, value, expected in cases:
        request = copy.deepcopy(MANIFEST["base_request"])
        request["input_bindings"][field] = value
        assert evaluate_request(request)["reason_code"] == expected

    for field, expected in (
        ("source_binding_match", "source_binding_failed"),
        ("cross_language_match", "cross_language_projection_diverged"),
    ):
        request = copy.deepcopy(MANIFEST["base_request"])
        request["input_bindings"][field] = False
        assert evaluate_request(request)["reason_code"] == expected


def test_result_validation_rejects_inconsistent_shapes_and_types() -> None:
    success = evaluate_request(copy.deepcopy(MANIFEST["base_request"]))
    candidates = [None, [], {"unexpected": True}]
    mutations = (
        {"op": "set", "path": ["terminal"], "value": False},
        {"op": "set", "path": ["succeeded"], "value": 1},
        {"op": "set", "path": ["reason_code"], "value": "unknown"},
        {"op": "set", "path": ["action_counts", "planned"], "value": 17},
        {"op": "set", "path": ["action_counts", "attempts"], "value": 2},
        {"op": "set", "path": ["action_counts", "processes"], "value": -1},
        {
            "op": "set",
            "path": ["retention_projection", "raw_material_retained_bytes"],
            "value": 1,
        },
        {"op": "set", "path": ["gate_effect", "retry_authorized"], "value": True},
    )
    for mutation in mutations:
        candidate = copy.deepcopy(success)
        _apply(candidate, mutation)
        candidates.append(candidate)
    assert all(not validate_result(candidate) for candidate in candidates)


def test_canonical_serialization_is_stable_and_nan_is_rejected() -> None:
    left = {"z": [3, 2, 1], "a": {"b": True}}
    right = {"a": {"b": True}, "z": [3, 2, 1]}

    assert canonical_json(left) == canonical_json(right)
    assert canonical_sha256(left) == canonical_sha256(right)
    with pytest.raises(ValueError):
        canonical_json({"value": float("nan")})


def test_request_shape_and_nested_prohibited_branches_fail_closed() -> None:
    base = MANIFEST["base_request"]
    candidates = []

    missing_authorization_field = copy.deepcopy(base)
    del missing_authorization_field["authorization_binding"]["attempt_state"]
    candidates.append(missing_authorization_field)

    bad_source_shape = copy.deepcopy(base)
    del bad_source_shape["authorization_binding"]["source_hashes"]["python"]
    candidates.append(bad_source_shape)

    missing_bound = copy.deepcopy(base)
    del missing_bound["declared_bounds"]["max_processes"]
    candidates.append(missing_bound)

    invalid_bound = copy.deepcopy(base)
    invalid_bound["declared_bounds"]["max_processes"] = True
    candidates.append(invalid_bound)

    missing_input = copy.deepcopy(base)
    del missing_input["input_bindings"]["elapsed_ms"]
    candidates.append(missing_input)

    bad_stage_outcomes = copy.deepcopy(base)
    bad_stage_outcomes["input_bindings"]["stage_outcomes"] = []
    candidates.append(bad_stage_outcomes)

    negative_input = copy.deepcopy(base)
    negative_input["input_bindings"]["elapsed_ms"] = -1
    candidates.append(negative_input)

    nested_prohibited = copy.deepcopy(base)
    nested_prohibited["input_bindings"]["stage_outcomes"] = {
        "safe": [{"nested": {"PASSWORD": "generated-only"}}]
    }
    candidates.append(nested_prohibited)

    assert all(not validate_request(candidate) for candidate in candidates)


def test_each_authorization_binding_rejection_branch_is_generated_only() -> None:
    cases = (
        (["decision_id"], "wrong-decision"),
        (["package_digest_sha256"], "not-a-digest"),
        (["source_hashes", "contract"], "not-a-digest"),
        (["attempt_index"], 2),
        (["attempt_state"], "consumed"),
        (["expires_at_utc"], "short"),
        (["expires_at_utc"], "2026/09/02T23:59:59Z"),
        (["authorization_window_state"], "expired"),
        (["machine_authority"], True),
        (["automatic_retry"], True),
    )
    for path, value in cases:
        request = copy.deepcopy(MANIFEST["base_request"])
        node = request["authorization_binding"]
        for part in path[:-1]:
            node = node[part]
        node[path[-1]] = value
        result = evaluate_request(request)
        assert result["reason_code"] == "authorization_binding_failed"


def test_stage_projection_rejects_unknown_or_inconsistent_failure_values() -> None:
    valid_failure = {
        "completed_actions": 0,
        "failed_action": ACTION_ORDER[0],
        "failed_stage": ACTION_FAILURE_REASONS[ACTION_ORDER[0]],
    }
    candidates = (
        ({"completed_actions": 0}, "request_contract_failed"),
        ({**valid_failure, "completed_actions": -1}, "request_contract_failed"),
        ({**valid_failure, "completed_actions": 19}, "request_contract_failed"),
        ({**valid_failure, "completed_actions": True}, "request_contract_failed"),
        (valid_failure, "unknown_reason"),
        ({**valid_failure, "failed_action": ""}, "request_contract_failed"),
        ({**valid_failure, "failed_action": "unknown"}, "request_contract_failed"),
        ({**valid_failure, "failed_stage": "wrong"}, "request_contract_failed"),
        ({**valid_failure, "completed_actions": 1}, "request_contract_failed"),
    )
    for candidate, reason in candidates:
        assert not validate_stage_projection(
            candidate, succeeded=False, reason_code=reason
        )


def test_result_consistency_and_unknown_failure_default_deny_branches() -> None:
    success = evaluate_request(copy.deepcopy(MANIFEST["base_request"]))
    succeeded_with_failure_reason = copy.deepcopy(success)
    succeeded_with_failure_reason["reason_code"] = "request_contract_failed"
    failed_with_success_reason = copy.deepcopy(success)
    failed_with_success_reason["succeeded"] = False

    assert not validate_result(succeeded_with_failure_reason)
    assert not validate_result(failed_with_success_reason)
    unknown = reference._failure_result("unknown_action")
    assert unknown["reason_code"] == "result_contract_invalid"
    assert unknown["stage_projection"]["failed_action"] == "validate_result_contract"
