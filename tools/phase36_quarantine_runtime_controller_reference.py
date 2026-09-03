"""Pure Phase 3.6 runtime-controller policy reference.

This module is intentionally machine-disabled. It evaluates generated mappings
only and has no filesystem, environment, registry, network, native, or process
surface.
"""

import hashlib
import json
from typing import Any, Mapping


CONTRACT_VERSION = "1.0.0"
AUTHORIZATION_DECISION = "D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-AUTH"
MODES = ("Policy", "Preflight")
REQUEST_FIELDS = (
    "contract_version",
    "mode",
    "authorization_binding",
    "declared_bounds",
    "action_plan",
    "input_bindings",
)
RESULT_FIELDS = (
    "contract_version",
    "terminal",
    "succeeded",
    "reason_code",
    "stage_projection",
    "action_counts",
    "retention_projection",
    "gate_effect",
)
AUTHORIZATION_FIELDS = (
    "decision_id",
    "package_digest_sha256",
    "attempt_index",
    "attempt_state",
    "expires_at_utc",
    "authorization_window_state",
    "source_hashes",
    "machine_authority",
    "automatic_retry",
)
SOURCE_HASH_FIELDS = ("contract", "vectors", "powershell", "python")
BOUND_FIELDS = (
    "per_action_timeout_ms",
    "total_timeout_ms",
    "max_stdout_bytes",
    "max_stderr_bytes",
    "max_result_bytes",
    "max_closure_files",
    "max_closure_bytes",
    "max_processes",
    "max_cleanup_actions",
)
INPUT_FIELDS = (
    "stage_outcomes",
    "elapsed_ms",
    "stdout_bytes",
    "stderr_bytes",
    "result_bytes",
    "closure_file_count",
    "closure_total_bytes",
    "retained_raw_bytes",
    "cleanup_count",
    "process_count",
    "source_binding_match",
    "cross_language_match",
)
ACTION_ORDER = (
    "validate_request_contract",
    "validate_authorization_binding",
    "classify_runtime_path",
    "read_runtime_metadata",
    "hash_runtime",
    "initialize_runtime_trust",
    "verify_runtime_trust",
    "close_runtime_trust",
    "reverify_runtime_identity",
    "classify_utility_manifest_path",
    "parse_utility_manifest",
    "bind_utility_manifest_closure",
    "bind_sources",
    "start_validation_process",
    "enforce_process_timeout",
    "validate_process_output_bounds",
    "validate_result_contract",
    "compare_cross_language_projection",
)
ACTION_FAILURE_REASONS = {
    "validate_request_contract": "request_contract_failed",
    "validate_authorization_binding": "authorization_binding_failed",
    "classify_runtime_path": "runtime_path_classification_failed",
    "read_runtime_metadata": "runtime_metadata_failed",
    "hash_runtime": "runtime_hash_failed",
    "initialize_runtime_trust": "runtime_trust_initialization_failed",
    "verify_runtime_trust": "runtime_trust_verification_failed",
    "close_runtime_trust": "runtime_trust_close_failed",
    "reverify_runtime_identity": "runtime_identity_changed",
    "classify_utility_manifest_path": "utility_manifest_path_failed",
    "parse_utility_manifest": "utility_manifest_parser_failed",
    "bind_utility_manifest_closure": "utility_manifest_closure_failed",
    "bind_sources": "source_binding_failed",
    "start_validation_process": "process_start_failed",
    "enforce_process_timeout": "process_timeout",
    "validate_process_output_bounds": "process_output_bounds_failed",
    "validate_result_contract": "result_contract_invalid",
    "compare_cross_language_projection": "cross_language_projection_diverged",
}
FAILURE_REASONS = tuple(ACTION_FAILURE_REASONS[action] for action in ACTION_ORDER)
PROHIBITED_FIELDS = frozenset(
    {
        "raw_exception",
        "exception",
        "stack",
        "native_status",
        "manifest_text",
        "manifest_tokens",
        "parser_objects",
        "stdout",
        "stderr",
        "fixture_payload",
        "hostname",
        "username",
        "user",
        "serial",
        "mac",
        "ip_address",
        "personal_path",
        "credentials",
        "password",
        "secret",
        "environment",
        "sid",
        "acl",
        "sddl",
    }
)
BOUND_LIMITS = {
    "per_action_timeout_ms": (1, 30000),
    "total_timeout_ms": (1, 120000),
    "max_stdout_bytes": (0, 65536),
    "max_stderr_bytes": (0, 65536),
    "max_result_bytes": (1024, 65536),
    "max_closure_files": (0, 64),
    "max_closure_bytes": (0, 134217728),
    "max_processes": (0, 1),
    "max_cleanup_actions": (0, 4),
}
HEX_DIGITS = frozenset("0123456789ABCDEF")


def canonical_json(value: Any) -> str:
    """Return the one canonical JSON representation used for policy hashes."""

    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def canonical_sha256(value: Any) -> str:
    """Return uppercase SHA-256 over canonical UTF-8 JSON."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest().upper()


def contract_projection() -> dict[str, Any]:
    """Return the cross-language constants that both controllers must expose."""

    return {
        "action_failure_reasons": dict(ACTION_FAILURE_REASONS),
        "action_order": list(ACTION_ORDER),
        "authorization_fields": list(AUTHORIZATION_FIELDS),
        "bound_fields": list(BOUND_FIELDS),
        "contract_version": CONTRACT_VERSION,
        "failure_reason_codes": list(FAILURE_REASONS),
        "input_fields": list(INPUT_FIELDS),
        "modes": list(MODES),
        "prohibited_field_names": sorted(PROHIBITED_FIELDS),
        "request_fields": list(REQUEST_FIELDS),
        "result_fields": list(RESULT_FIELDS),
        "source_hash_fields": list(SOURCE_HASH_FIELDS),
    }


def projections_equal(candidate: Any) -> bool:
    """Compare an implementation projection to the canonical projection."""

    return isinstance(candidate, Mapping) and dict(candidate) == contract_projection()


def _exact_fields(value: Any, expected: tuple[str, ...]) -> bool:
    return isinstance(value, Mapping) and set(value) == set(expected)


def _is_nonnegative_integer(value: Any) -> bool:
    return type(value) is int and value >= 0


def _is_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in HEX_DIGITS for character in value)
    )


def _contains_prohibited_field(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if isinstance(key, str) and key.casefold() in PROHIBITED_FIELDS:
                return True
            if _contains_prohibited_field(child):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_prohibited_field(item) for item in value)
    return False


def _valid_authorization_shape(value: Any) -> bool:
    if not _exact_fields(value, AUTHORIZATION_FIELDS):
        return False
    source_hashes = value["source_hashes"]
    if not _exact_fields(source_hashes, SOURCE_HASH_FIELDS):
        return False
    return (
        isinstance(value["decision_id"], str)
        and isinstance(value["package_digest_sha256"], str)
        and type(value["attempt_index"]) is int
        and isinstance(value["attempt_state"], str)
        and isinstance(value["expires_at_utc"], str)
        and isinstance(value["authorization_window_state"], str)
        and all(isinstance(source_hashes[name], str) for name in SOURCE_HASH_FIELDS)
        and type(value["machine_authority"]) is bool
        and type(value["automatic_retry"]) is bool
    )


def _authorization_bound(value: Mapping[str, Any]) -> bool:
    source_hashes = value["source_hashes"]
    if value["decision_id"] != AUTHORIZATION_DECISION:
        return False
    if not _is_digest(value["package_digest_sha256"]):
        return False
    if not all(_is_digest(source_hashes[name]) for name in SOURCE_HASH_FIELDS):
        return False
    if value["attempt_index"] != 1 or value["attempt_state"] != "unused":
        return False
    expires_at = value["expires_at_utc"]
    if not isinstance(expires_at, str) or len(expires_at) != 20:
        return False
    if expires_at[4] != "-" or expires_at[7] != "-" or not expires_at.endswith("Z"):
        return False
    if value["authorization_window_state"] != "synthetic_valid":
        return False
    return value["machine_authority"] is False and value["automatic_retry"] is False


def _valid_bounds(value: Any) -> bool:
    if not _exact_fields(value, BOUND_FIELDS):
        return False
    for name, limits in BOUND_LIMITS.items():
        candidate = value[name]
        if type(candidate) is not int or candidate < limits[0] or candidate > limits[1]:
            return False
    return value["per_action_timeout_ms"] <= value["total_timeout_ms"]


def _valid_inputs(value: Any) -> bool:
    if not _exact_fields(value, INPUT_FIELDS):
        return False
    if not isinstance(value["stage_outcomes"], Mapping):
        return False
    for name in (
        "elapsed_ms",
        "stdout_bytes",
        "stderr_bytes",
        "result_bytes",
        "closure_file_count",
        "closure_total_bytes",
        "retained_raw_bytes",
        "cleanup_count",
        "process_count",
    ):
        if not _is_nonnegative_integer(value[name]):
            return False
    return type(value["source_binding_match"]) is bool and type(
        value["cross_language_match"]
    ) is bool


def validate_request(request: Any) -> bool:
    """Validate only the versioned, bounded, machine-independent envelope."""

    if not _exact_fields(request, REQUEST_FIELDS):
        return False
    if _contains_prohibited_field(request):
        return False
    if request["contract_version"] != CONTRACT_VERSION or request["mode"] not in MODES:
        return False
    if not _valid_authorization_shape(request["authorization_binding"]):
        return False
    if not _valid_bounds(request["declared_bounds"]):
        return False
    if request["action_plan"] != list(ACTION_ORDER):
        return False
    return _valid_inputs(request["input_bindings"])


def _terminal_result(
    reason_code: str,
    failed_action: str | None,
    completed_actions: int,
    process_count: int = 0,
    cleanup_count: int = 0,
) -> dict[str, Any]:
    succeeded = reason_code == "policy_valid"
    return {
        "contract_version": CONTRACT_VERSION,
        "terminal": True,
        "succeeded": succeeded,
        "reason_code": reason_code,
        "stage_projection": {
            "completed_actions": completed_actions,
            "failed_action": failed_action,
            "failed_stage": None if succeeded else reason_code,
        },
        "action_counts": {
            "planned": len(ACTION_ORDER),
            "completed": completed_actions,
            "attempts": 1,
            "retries": 0,
            "processes": process_count,
        },
        "retention_projection": {
            "raw_material_retained_bytes": 0,
            "sanitized_result_only": True,
            "cleanup_actions": cleanup_count,
        },
        "gate_effect": {
            "machine_action_authorized": False,
            "python_machine_fallback": False,
            "retry_authorized": False,
            "U3T_preflight_authorized": False,
            "U3K_authorized": False,
            "deployment_authorized": False,
            "next_gate": (
                "owner_source_implementation_acceptance_required" if succeeded else "blocked"
            ),
        },
    }


def _failure(action: str, inputs: Mapping[str, Any]) -> dict[str, Any]:
    return _terminal_result(
        ACTION_FAILURE_REASONS[action],
        action,
        ACTION_ORDER.index(action),
        inputs.get("process_count", 0),
        inputs.get("cleanup_count", 0),
    )


def evaluate_request(request: Any) -> dict[str, Any]:
    """Evaluate one generated policy request without touching machine state."""

    if not validate_request(request):
        return _terminal_result("request_contract_failed", ACTION_ORDER[0], 0)

    authorization = request["authorization_binding"]
    inputs = request["input_bindings"]
    bounds = request["declared_bounds"]
    if request["mode"] == "Preflight" or not _authorization_bound(authorization):
        return _failure("validate_authorization_binding", inputs)

    stage_outcomes = inputs["stage_outcomes"]
    for action, outcome in stage_outcomes.items():
        if action not in ACTION_FAILURE_REASONS:
            return _failure("validate_result_contract", inputs)
        if outcome not in ("pass", ACTION_FAILURE_REASONS[action]):
            return _failure("validate_result_contract", inputs)

    failures = {
        action
        for action, outcome in stage_outcomes.items()
        if outcome == ACTION_FAILURE_REASONS[action]
    }
    if inputs["closure_file_count"] > bounds["max_closure_files"]:
        failures.add("bind_utility_manifest_closure")
    if inputs["closure_total_bytes"] > bounds["max_closure_bytes"]:
        failures.add("bind_utility_manifest_closure")
    if not inputs["source_binding_match"]:
        failures.add("bind_sources")
    if inputs["process_count"] > bounds["max_processes"]:
        failures.add("start_validation_process")
    if inputs["elapsed_ms"] > bounds["total_timeout_ms"]:
        failures.add("enforce_process_timeout")
    if (
        inputs["stdout_bytes"] > bounds["max_stdout_bytes"]
        or inputs["stderr_bytes"] > bounds["max_stderr_bytes"]
        or inputs["result_bytes"] > bounds["max_result_bytes"]
    ):
        failures.add("validate_process_output_bounds")
    if inputs["retained_raw_bytes"] != 0 or inputs["cleanup_count"] > bounds[
        "max_cleanup_actions"
    ]:
        failures.add("validate_result_contract")
    if not inputs["cross_language_match"]:
        failures.add("compare_cross_language_projection")

    for action in ACTION_ORDER:
        if action in failures:
            return _failure(action, inputs)
    return _terminal_result(
        "policy_valid",
        None,
        len(ACTION_ORDER),
        inputs["process_count"],
        inputs["cleanup_count"],
    )


def validate_result(result: Any) -> bool:
    """Validate a sanitized terminal result without retaining its input."""

    if not _exact_fields(result, RESULT_FIELDS) or _contains_prohibited_field(result):
        return False
    if result["contract_version"] != CONTRACT_VERSION or result["terminal"] is not True:
        return False
    if type(result["succeeded"]) is not bool:
        return False
    if result["reason_code"] not in ("policy_valid", *FAILURE_REASONS):
        return False
    if not all(
        isinstance(result[name], Mapping)
        for name in ("stage_projection", "action_counts", "retention_projection", "gate_effect")
    ):
        return False
    return result == _terminal_result(
        result["reason_code"],
        result["stage_projection"].get("failed_action"),
        result["stage_projection"].get("completed_actions"),
        result["action_counts"].get("processes", 0),
        result["retention_projection"].get("cleanup_actions", 0),
    )


__all__ = [
    "ACTION_FAILURE_REASONS",
    "ACTION_ORDER",
    "AUTHORIZATION_DECISION",
    "CONTRACT_VERSION",
    "FAILURE_REASONS",
    "PROHIBITED_FIELDS",
    "canonical_json",
    "canonical_sha256",
    "contract_projection",
    "evaluate_request",
    "projections_equal",
    "validate_request",
    "validate_result",
]
