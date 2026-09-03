import ast
import copy
import json
from pathlib import Path

import pytest

import tools.phase36_quarantine_runtime_binding_outer_attempt_controller_r0_reference as reference
from tools.phase36_quarantine_runtime_binding_outer_attempt_controller_r0_reference import (
    PARENT_INDEXES,
    PROCESS_LIMITS,
    STAGES,
    canonical_sha256,
    evaluate_request,
    expected_parent_reason,
    validate_parent_record,
    validate_parent_set,
    validate_request,
    validate_result,
)


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / (
    "tools/phase36_quarantine_runtime_binding_outer_attempt_controller_r0_reference.py"
)
VECTORS = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-binding-outer-attempt-controller-r0-vectors.json"
)


def _manifest() -> dict[str, object]:
    return json.loads(VECTORS.read_text(encoding="utf-8"))


def _base_request() -> dict[str, object]:
    return copy.deepcopy(_manifest()["vectors"][0]["request"])


@pytest.mark.parametrize("vector", _manifest()["vectors"], ids=lambda item: item["id"])
def test_generated_vector_matches_machine_disabled_reference(vector: dict[str, object]) -> None:
    result = evaluate_request(vector["request"])

    assert validate_request(vector["request"]) is vector["request_valid"]
    assert result == vector["expected_result"]
    assert canonical_sha256(result) == vector["expected_result_sha256"]
    assert validate_result(result)


def test_exact_three_parent_reduction_reports_first_invalid_index() -> None:
    request = _base_request()
    records = request["parent_records"]

    assert validate_parent_set(records) == (True, None)
    for index in PARENT_INDEXES:
        candidate = copy.deepcopy(records)
        candidate[index]["canonical_match"] = False
        candidate[index]["valid"] = False
        candidate[index]["reason_code"] = "parent_canonical_mismatch"
        assert validate_parent_set(candidate) == (False, index)


def test_parent_reason_priority_is_deterministic() -> None:
    request = _base_request()
    record = request["parent_records"][0]

    assert expected_parent_reason(record) == "parent_valid"
    record["present"] = False
    record["regular_directory"] = False
    record["nonreparse"] = False
    record["canonical_match"] = False
    record["valid"] = False
    record["reason_code"] = "parent_missing"
    assert expected_parent_reason(record) == "parent_missing"
    assert validate_parent_record(record, 0)


def test_process_boundaries_are_inclusive_and_fail_one_unit_over() -> None:
    for field, limit_name in (
        ("elapsed_ms", "timeout_ms"),
        ("stdout_bytes", "max_stdout_bytes"),
        ("stderr_bytes", "max_stderr_bytes"),
        ("result_bytes", "max_result_bytes"),
        ("processes", "max_processes"),
    ):
        request = _base_request()
        request["process_observation"][field] = PROCESS_LIMITS[limit_name]
        assert evaluate_request(request)["succeeded"] is True
        request["process_observation"][field] = PROCESS_LIMITS[limit_name] + 1
        result = evaluate_request(request)
        assert result["stage"] == "process"
        assert result["succeeded"] is False


def test_failure_projection_is_ordered_and_zero_retention() -> None:
    for stage in STAGES[2:]:
        request = _base_request()
        request["stage_signals"][stage] = False
        result = evaluate_request(request)

        assert result["stage"] == stage
        failed_index = STAGES.index(stage)
        assert result["predicate_flags"] == {
            item: index < failed_index for index, item in enumerate(STAGES)
        }
        assert set(result) == {
            "terminal",
            "succeeded",
            "stage",
            "reason_code",
            "parent_index",
            "predicate_flags",
            "attempts_consumed",
        }
        assert all(
            forbidden not in result
            for forbidden in (
                "stdout",
                "stderr",
                "exception",
                "path",
                "identity_material",
            )
        )


def test_reference_import_surface_is_machine_disabled() -> None:
    tree = ast.parse(REFERENCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".", 1)[0])

    assert imported == {"hashlib", "json", "typing"}
    assert imported.isdisjoint(
        {
            "ctypes",
            "importlib",
            "os",
            "pathlib",
            "platform",
            "requests",
            "socket",
            "subprocess",
            "urllib",
            "winreg",
        }
    )


def test_malformed_results_are_rejected_without_exception() -> None:
    result = evaluate_request(_base_request())
    assert validate_result(result)

    for field in tuple(result):
        candidate = copy.deepcopy(result)
        candidate.pop(field)
        assert not validate_result(candidate)
    candidate = copy.deepcopy(result)
    candidate["unknown"] = True
    assert not validate_result(candidate)
    assert not validate_result(None)
    assert not validate_result([])


@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("missing_authorization_field", None),
        ("unknown_attempt_state", "unknown"),
        ("first_attempt_wrong_index", 2),
        ("retry_attempt_wrong_index", 1),
        ("wrong_typed_retry_flag", 1),
    ),
)
def test_authorization_rejects_every_structural_boundary(
    mutation: str, value: object
) -> None:
    request = _base_request()
    authorization = request["authorization"]
    if mutation == "missing_authorization_field":
        authorization.pop("same_package_digest")
    elif mutation == "unknown_attempt_state":
        authorization["attempt_state"] = value
    elif mutation == "first_attempt_wrong_index":
        authorization["attempt_index"] = value
    elif mutation == "retry_attempt_wrong_index":
        authorization["attempt_state"] = "retry"
        authorization["attempt_index"] = value
    else:
        authorization["same_package_digest"] = value

    assert not validate_request(request)
    assert evaluate_request(request)["reason_code"] == (
        "terminal_default_deny_internal_failure"
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "prohibited_nested_field",
        "non_string_key",
        "stage_signal_missing",
        "stage_signal_wrong_type",
        "process_limit_missing",
        "process_limit_changed",
        "observation_missing",
        "observation_negative",
        "retention_missing",
        "retention_wrong_type",
    ),
)
def test_request_rejects_malformed_nested_contracts(mutation: str) -> None:
    request = _base_request()
    if mutation == "prohibited_nested_field":
        request["authorization"]["path"] = "redacted"
    elif mutation == "non_string_key":
        request["retention"][1] = False
    elif mutation == "stage_signal_missing":
        request["stage_signals"].pop("runtime_hash")
    elif mutation == "stage_signal_wrong_type":
        request["stage_signals"]["runtime_hash"] = 1
    elif mutation == "process_limit_missing":
        request["process_limits"].pop("timeout_ms")
    elif mutation == "process_limit_changed":
        request["process_limits"]["timeout_ms"] += 1
    elif mutation == "observation_missing":
        request["process_observation"].pop("elapsed_ms")
    elif mutation == "observation_negative":
        request["process_observation"]["elapsed_ms"] = -1
    elif mutation == "retention_missing":
        request["retention"].pop("sanitized_only")
    else:
        request["retention"]["sanitized_only"] = 1

    assert not validate_request(request)


def test_parent_record_rejects_index_type_predicate_and_consistency_errors() -> None:
    record = _base_request()["parent_records"][0]

    assert not validate_parent_record(None, 0)
    candidate = copy.deepcopy(record)
    candidate["parent_index"] = True
    assert not validate_parent_record(candidate, 0)
    candidate = copy.deepcopy(record)
    candidate["present"] = 1
    assert not validate_parent_record(candidate, 0)
    candidate = copy.deepcopy(record)
    candidate["valid"] = False
    candidate["reason_code"] = "parent_predicate_inconsistent"
    assert validate_parent_record(candidate, 0)
    candidate = copy.deepcopy(record)
    candidate["present"] = False
    candidate["valid"] = True
    candidate["reason_code"] = "parent_predicate_inconsistent"
    assert not validate_parent_record(candidate, 0)


def test_evaluator_handles_non_mapping_and_untrusted_attempt_candidates() -> None:
    assert evaluate_request(None)["attempts_consumed"] == 0
    assert evaluate_request([])["attempts_consumed"] == 0

    request = _base_request()
    request["authorization"] = []
    assert evaluate_request(request)["attempts_consumed"] == 0
    request = _base_request()
    request["authorization"]["attempt_index"] = "1"
    assert evaluate_request(request)["attempts_consumed"] == 0
    request = _base_request()
    request["authorization"]["attempt_index"] = 4
    assert evaluate_request(request)["attempts_consumed"] == 0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("terminal", False),
        ("succeeded", 1),
        ("stage", "unknown"),
        ("reason_code", "unknown"),
        ("parent_index", "zero"),
        ("parent_index", 3),
        ("attempts_consumed", "1"),
        ("attempts_consumed", 4),
    ),
)
def test_result_rejects_invalid_top_level_values(field: str, value: object) -> None:
    result = evaluate_request(_base_request())
    result[field] = value
    assert not validate_result(result)


def test_result_rejects_parent_index_outside_parent_failure_and_bad_flags() -> None:
    result = evaluate_request(_base_request())
    result["parent_index"] = 0
    assert not validate_result(result)

    result = evaluate_request(_base_request())
    result["predicate_flags"].pop("authorization")
    assert not validate_result(result)
    result = evaluate_request(_base_request())
    result["predicate_flags"]["authorization"] = 1
    assert not validate_result(result)
    result = evaluate_request(_base_request())
    result["succeeded"] = False
    result["reason_code"] = "policy_valid"
    assert not validate_result(result)
    result = evaluate_request(_base_request())
    result["predicate_flags"]["authorization"] = False
    assert not validate_result(result)


def test_private_validation_helpers_cover_digest_and_prohibited_recursion() -> None:
    assert not reference._uppercase_sha256(None)
    assert not reference._uppercase_sha256("A" * 63)
    assert not reference._uppercase_sha256("G" * 64)
    assert reference._uppercase_sha256("A" * 64)
    assert reference._contains_prohibited_field({"nested": [{"path": "redacted"}]})
    assert reference._contains_prohibited_field({1: False})
    assert not reference._contains_prohibited_field({"safe": [1, 2, 3]})
