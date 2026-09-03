"""Machine-disabled reference for the Phase 3.6 U4D output contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CONTRACT_VERSION = "1.0.0"
OPERATION = "classify_process_output_v1"
REQUIRED_CASE_COUNT = 416
MAX_STDOUT_BYTES = 4096
MAX_STDERR_BYTES = 0

REQUEST_FIELDS = frozenset(
    {"contract_version", "operation", "observation", "source_identity", "retention"}
)
OBSERVATION_FIELDS = frozenset(
    {
        "process_started",
        "timed_out",
        "exit_code",
        "stdout_bytes",
        "stderr_bytes",
        "stdout_line_count",
        "stdout_utf8_valid",
        "stdout_has_bom",
        "stdout_is_clixml",
        "json_parse_valid",
        "json_duplicate_keys",
        "schema_valid",
        "identity_valid",
        "child_terminal",
        "child_succeeded",
        "required_case_count",
        "accepted_case_count",
    }
)
SOURCE_IDENTITY_FIELDS = frozenset({"preflight_match", "postflight_match"})
RETENTION_FIELDS = frozenset(
    {
        "raw_stdout_retained_bytes",
        "raw_stderr_retained_bytes",
        "raw_stream_hashes_retained",
        "exception_material_retained",
        "fixture_material_retained",
        "identity_material_retained",
        "environment_material_retained",
        "security_material_retained",
    }
)

PROCESS_BOOLEAN_FIELDS = (
    "process_started",
    "timed_out",
    "stdout_utf8_valid",
    "stdout_has_bom",
    "stdout_is_clixml",
    "json_parse_valid",
    "json_duplicate_keys",
    "schema_valid",
    "identity_valid",
    "child_terminal",
    "child_succeeded",
)
PROCESS_INTEGER_FIELDS = (
    "stdout_bytes",
    "stderr_bytes",
    "stdout_line_count",
    "required_case_count",
    "accepted_case_count",
)
RETENTION_BOOLEAN_FIELDS = (
    "raw_stream_hashes_retained",
    "exception_material_retained",
    "fixture_material_retained",
    "identity_material_retained",
    "environment_material_retained",
    "security_material_retained",
)

REASON_STAGE = {
    "terminal_default_deny_internal_failure": "authorization",
    "process_start_failed": "process",
    "process_timeout": "process",
    "process_exit_nonzero": "process",
    "process_stdout_limit_exceeded": "process",
    "process_stderr_nonzero": "process",
    "process_output_empty": "result_validation",
    "process_output_multiple_lines": "result_validation",
    "process_output_JSON_invalid": "result_validation",
    "process_output_BOM_detected": "result_validation",
    "process_output_CLIXML_detected": "result_validation",
    "process_output_schema_invalid": "result_validation",
    "process_output_identity_invalid": "result_validation",
    "process_result_accepted": "evidence_seal",
}


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _has_exact_fields(value: Any, fields: frozenset[str]) -> bool:
    return isinstance(value, Mapping) and frozenset(value) == fields


def _valid_request(request: Any) -> bool:
    if not _has_exact_fields(request, REQUEST_FIELDS):
        return False
    if (
        request["contract_version"] != CONTRACT_VERSION
        or request["operation"] != OPERATION
    ):
        return False

    observation = request["observation"]
    identity = request["source_identity"]
    retention = request["retention"]
    if not _has_exact_fields(observation, OBSERVATION_FIELDS):
        return False
    if not _has_exact_fields(identity, SOURCE_IDENTITY_FIELDS):
        return False
    if not _has_exact_fields(retention, RETENTION_FIELDS):
        return False
    if any(not _is_bool(observation[field]) for field in PROCESS_BOOLEAN_FIELDS):
        return False
    if any(
        not _is_nonnegative_int(observation[field]) for field in PROCESS_INTEGER_FIELDS
    ):
        return False
    exit_code = observation["exit_code"]
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        return False
    if (
        observation["process_started"]
        and not observation["timed_out"]
        and exit_code is None
    ):
        return False
    if any(not _is_bool(identity[field]) for field in SOURCE_IDENTITY_FIELDS):
        return False
    if not _is_nonnegative_int(retention["raw_stdout_retained_bytes"]):
        return False
    if not _is_nonnegative_int(retention["raw_stderr_retained_bytes"]):
        return False
    return not any(not _is_bool(retention[field]) for field in RETENTION_BOOLEAN_FIELDS)


def _default_observed_bounds() -> dict[str, Any]:
    return {
        "process_started": False,
        "timed_out": False,
        "exit_class": "unavailable",
        "stdout_bytes": 0,
        "stderr_bytes": 0,
        "stdout_line_count": 0,
        "required_case_count": 0,
        "accepted_case_count": 0,
    }


def _observed_bounds(observation: Mapping[str, Any]) -> dict[str, Any]:
    exit_code = observation["exit_code"]
    if exit_code is None:
        exit_class = "unavailable"
    elif exit_code == 0:
        exit_class = "zero"
    else:
        exit_class = "nonzero"
    return {
        "process_started": observation["process_started"],
        "timed_out": observation["timed_out"],
        "exit_class": exit_class,
        "stdout_bytes": observation["stdout_bytes"],
        "stderr_bytes": observation["stderr_bytes"],
        "stdout_line_count": observation["stdout_line_count"],
        "required_case_count": observation["required_case_count"],
        "accepted_case_count": observation["accepted_case_count"],
    }


def _zero_retention_result() -> dict[str, Any]:
    return {
        "raw_stdout_retained_bytes": 0,
        "raw_stderr_retained_bytes": 0,
        "raw_stream_hashes_retained": False,
        "exception_material_retained": False,
        "fixture_material_retained": False,
        "identity_material_retained": False,
        "environment_material_retained": False,
        "security_material_retained": False,
    }


def _terminal(reason_code: str, observed_bounds: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "terminal": True,
        "succeeded": reason_code == "process_result_accepted",
        "stage": REASON_STAGE[reason_code],
        "reason_code": reason_code,
        "observed_bounds": dict(observed_bounds),
        "retention": _zero_retention_result(),
    }


def _retention_is_zero(retention: Mapping[str, Any]) -> bool:
    return (
        retention["raw_stdout_retained_bytes"] == 0
        and retention["raw_stderr_retained_bytes"] == 0
        and not any(retention[field] for field in RETENTION_BOOLEAN_FIELDS)
    )


def classify_process_output(request: Any) -> dict[str, Any]:
    """Classify sanitized process observations without machine access."""

    if not _valid_request(request):
        return _terminal(
            "terminal_default_deny_internal_failure", _default_observed_bounds()
        )

    observation = request["observation"]
    bounds = _observed_bounds(observation)
    if not observation["process_started"]:
        return _terminal("process_start_failed", bounds)
    if observation["timed_out"]:
        return _terminal("process_timeout", bounds)
    if observation["exit_code"] != 0:
        return _terminal("process_exit_nonzero", bounds)
    if observation["stdout_bytes"] > MAX_STDOUT_BYTES:
        return _terminal("process_stdout_limit_exceeded", bounds)
    if observation["stderr_bytes"] > MAX_STDERR_BYTES:
        return _terminal("process_stderr_nonzero", bounds)
    if observation["stdout_bytes"] == 0 or observation["stdout_line_count"] == 0:
        return _terminal("process_output_empty", bounds)
    if observation["stdout_line_count"] != 1:
        return _terminal("process_output_multiple_lines", bounds)
    if not observation["stdout_utf8_valid"]:
        return _terminal("process_output_JSON_invalid", bounds)
    if observation["stdout_has_bom"]:
        return _terminal("process_output_BOM_detected", bounds)
    if observation["stdout_is_clixml"]:
        return _terminal("process_output_CLIXML_detected", bounds)
    if not observation["json_parse_valid"] or observation["json_duplicate_keys"]:
        return _terminal("process_output_JSON_invalid", bounds)
    if not observation["schema_valid"] or not observation["child_terminal"]:
        return _terminal("process_output_schema_invalid", bounds)

    identity = request["source_identity"]
    identity_valid = (
        observation["identity_valid"]
        and observation["child_succeeded"]
        and observation["required_case_count"] == REQUIRED_CASE_COUNT
        and observation["accepted_case_count"] == REQUIRED_CASE_COUNT
        and identity["preflight_match"]
        and identity["postflight_match"]
        and _retention_is_zero(request["retention"])
    )
    if not identity_valid:
        return _terminal("process_output_identity_invalid", bounds)
    return _terminal("process_result_accepted", bounds)


def canonical_projection() -> dict[str, Any]:
    """Return the constants mirrored by the inert PowerShell harness."""

    return {
        "child_reason_codes": [
            "generated_validation_accepted",
            "harness_input_invalid",
            "module_bootstrap_failed",
            "source_identity_invalid",
            "vector_manifest_invalid",
            "controller_load_failed",
            "generated_case_mismatch",
            "terminal_default_deny_internal_failure",
        ],
        "contract_version": CONTRACT_VERSION,
        "maximum_stderr_bytes": MAX_STDERR_BYTES,
        "maximum_stdout_bytes": MAX_STDOUT_BYTES,
        "operation": OPERATION,
        "required_case_count": REQUIRED_CASE_COUNT,
        "terminal_line_count": 1,
    }
