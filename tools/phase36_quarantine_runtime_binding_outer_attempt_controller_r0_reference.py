"""Machine-disabled reference for the Phase 3.6 outer attempt controller.

The module consumes generated mappings only. It has no filesystem, registry,
environment, network, native API, subprocess, machine-controller, or fallback
surface.
"""

import hashlib
import json
from typing import Any, Mapping, Sequence


CONTRACT_VERSION = "1.0.0"
SOURCE_BUILD_AUTHORIZATION = "D-P3.6-CONSOLIDATED-BUILD-AUTH"
RUNTIME_AUTHORIZATION = "D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-AUTH"
SUPPORTED_OPERATIONS = ("generated_contract_validation_v1",)
STAGES = (
    "authorization",
    "fixed_parent_set",
    "runtime_candidate",
    "runtime_hash",
    "runtime_trust",
    "source_preflight",
    "process",
    "result_validation",
    "source_postflight",
    "runtime_postflight",
    "evidence_seal",
)
REQUEST_FIELDS = (
    "contract_version",
    "operation",
    "authorization",
    "parent_records",
    "stage_signals",
    "process_limits",
    "process_observation",
    "retention",
)
AUTHORIZATION_FIELDS = (
    "decision_id",
    "package_digest_sha256",
    "attempt_index",
    "max_attempts",
    "attempt_state",
    "same_package_digest",
    "retry_reason_allowlisted",
    "machine_authority",
    "automatic_retry",
)
PARENT_FIELDS = (
    "parent_index",
    "present",
    "regular_directory",
    "nonreparse",
    "canonical_match",
    "valid",
    "reason_code",
)
PARENT_PREDICATE_FIELDS = (
    "present",
    "regular_directory",
    "nonreparse",
    "canonical_match",
    "valid",
)
PARENT_INDEXES = (0, 1, 2)
PARENT_REASON_CODES = (
    "parent_valid",
    "parent_missing",
    "parent_not_directory",
    "parent_reparse",
    "parent_canonical_mismatch",
    "parent_predicate_inconsistent",
)
STAGE_SIGNAL_FIELDS = STAGES[2:]
PROCESS_LIMIT_FIELDS = (
    "timeout_ms",
    "max_stdout_bytes",
    "max_stderr_bytes",
    "max_result_bytes",
    "max_processes",
)
PROCESS_OBSERVATION_FIELDS = (
    "elapsed_ms",
    "stdout_bytes",
    "stderr_bytes",
    "result_bytes",
    "processes",
)
RETENTION_FIELDS = ("raw_retained_bytes", "sanitized_only")
RESULT_FIELDS = (
    "terminal",
    "succeeded",
    "stage",
    "reason_code",
    "parent_index",
    "predicate_flags",
    "attempts_consumed",
)
PREDICATE_FLAG_FIELDS = STAGES
PROCESS_LIMITS = {
    "timeout_ms": 120000,
    "max_stdout_bytes": 16384,
    "max_stderr_bytes": 0,
    "max_result_bytes": 32768,
    "max_processes": 1,
}
STAGE_FAILURE_REASONS = {
    "authorization": "authorization_invalid",
    "fixed_parent_set": "fixed_parent_set_invalid",
    "runtime_candidate": "runtime_candidate_invalid",
    "runtime_hash": "runtime_hash_invalid",
    "runtime_trust": "runtime_trust_invalid",
    "source_preflight": "source_preflight_failed",
    "process": "process_failed",
    "result_validation": "result_contract_invalid",
    "source_postflight": "source_identity_changed",
    "runtime_postflight": "runtime_identity_changed",
    "evidence_seal": "evidence_seal_failed",
}
ADDITIONAL_FAILURE_REASONS = (
    "process_timeout",
    "process_output_bounds_failed",
    "terminal_default_deny_internal_failure",
)
FAILURE_REASONS = (*STAGE_FAILURE_REASONS.values(), *ADDITIONAL_FAILURE_REASONS)
PROHIBITED_FIELDS = frozenset(
    {
        "acl",
        "credentials",
        "environment",
        "exception",
        "hostname",
        "ip_address",
        "mac",
        "native_status",
        "owner",
        "password",
        "path",
        "raw",
        "sddl",
        "secret",
        "serial",
        "sid",
        "stack",
        "stderr",
        "stdout",
        "user",
        "username",
    }
)


def _exact_fields(value: Any, fields: Sequence[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == set(fields)


def _nonnegative_integer(value: Any) -> bool:
    return type(value) is int and value >= 0


def _uppercase_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789ABCDEF" for character in value)


def _contains_prohibited_field(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or key.casefold() in PROHIBITED_FIELDS:
                return True
            if _contains_prohibited_field(item):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_prohibited_field(item) for item in value)
    return False


def canonical_json(value: Any) -> str:
    """Return the compact, sorted generated-only canonical projection."""

    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def canonical_sha256(value: Any) -> str:
    """Hash a generated-only canonical projection without machine access."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest().upper()


def expected_parent_reason(record: Mapping[str, Any]) -> str:
    """Return the deterministic reason for a typed parent observation."""

    if record["present"] is not True:
        return "parent_missing"
    if record["regular_directory"] is not True:
        return "parent_not_directory"
    if record["nonreparse"] is not True:
        return "parent_reparse"
    if record["canonical_match"] is not True:
        return "parent_canonical_mismatch"
    return "parent_valid"


def validate_parent_record(record: Any, expected_index: int) -> bool:
    if not _exact_fields(record, PARENT_FIELDS):
        return False
    if record["parent_index"] != expected_index or type(record["parent_index"]) is not int:
        return False
    if not all(type(record[field]) is bool for field in PARENT_PREDICATE_FIELDS):
        return False
    derived_valid = all(record[field] is True for field in PARENT_PREDICATE_FIELDS[:-1])
    if record["valid"] is not derived_valid:
        return record["reason_code"] == "parent_predicate_inconsistent" and not record["valid"]
    return record["reason_code"] == expected_parent_reason(record)


def validate_parent_set(records: Any) -> tuple[bool, int | None]:
    """Apply exact three-record, ordered, literal-true reduction."""

    if not isinstance(records, list) or len(records) != 3:
        return False, None
    for expected_index, record in enumerate(records):
        if not validate_parent_record(record, expected_index):
            return False, expected_index
    for record in records:
        if record["valid"] is not True:
            return False, record["parent_index"]
    return True, None


def _validate_authorization(value: Any) -> bool:
    if not _exact_fields(value, AUTHORIZATION_FIELDS):
        return False
    if value["decision_id"] != RUNTIME_AUTHORIZATION:
        return False
    if not _uppercase_sha256(value["package_digest_sha256"]):
        return False
    if value["max_attempts"] != 3 or type(value["max_attempts"]) is not int:
        return False
    attempt_index = value["attempt_index"]
    if type(attempt_index) is not int or attempt_index not in (1, 2, 3):
        return False
    if value["attempt_state"] not in ("first", "retry"):
        return False
    if value["attempt_state"] == "first" and attempt_index != 1:
        return False
    if value["attempt_state"] == "retry" and attempt_index <= 1:
        return False
    typed_flags = (
        "same_package_digest",
        "retry_reason_allowlisted",
        "machine_authority",
        "automatic_retry",
    )
    if not all(type(value[field]) is bool for field in typed_flags):
        return False
    if value["machine_authority"] is not True or value["automatic_retry"] is not False:
        return False
    if value["attempt_state"] == "retry" and (
        value["same_package_digest"] is not True
        or value["retry_reason_allowlisted"] is not True
    ):
        return False
    return True


def validate_request(request: Any) -> bool:
    """Validate the generated-only policy request without retaining raw input."""

    if not _exact_fields(request, REQUEST_FIELDS) or _contains_prohibited_field(request):
        return False
    if request["contract_version"] != CONTRACT_VERSION:
        return False
    if request["operation"] not in SUPPORTED_OPERATIONS:
        return False
    if not _validate_authorization(request["authorization"]):
        return False
    parent_valid, _ = validate_parent_set(request["parent_records"])
    if not parent_valid and not (
        isinstance(request["parent_records"], list)
        and len(request["parent_records"]) == 3
        and all(
            validate_parent_record(record, index)
            for index, record in enumerate(request["parent_records"])
        )
    ):
        return False
    if not _exact_fields(request["stage_signals"], STAGE_SIGNAL_FIELDS):
        return False
    if not all(type(request["stage_signals"][field]) is bool for field in STAGE_SIGNAL_FIELDS):
        return False
    if not _exact_fields(request["process_limits"], PROCESS_LIMIT_FIELDS):
        return False
    if request["process_limits"] != PROCESS_LIMITS:
        return False
    observation = request["process_observation"]
    if not _exact_fields(observation, PROCESS_OBSERVATION_FIELDS):
        return False
    if not all(_nonnegative_integer(observation[field]) for field in PROCESS_OBSERVATION_FIELDS):
        return False
    retention = request["retention"]
    if not _exact_fields(retention, RETENTION_FIELDS):
        return False
    return _nonnegative_integer(retention["raw_retained_bytes"]) and type(
        retention["sanitized_only"]
    ) is bool


def _predicate_projection(failed_stage: str | None) -> dict[str, bool]:
    if failed_stage is None:
        return {stage: True for stage in STAGES}
    failed_index = STAGES.index(failed_stage)
    return {stage: index < failed_index for index, stage in enumerate(STAGES)}


def _terminal(
    *,
    succeeded: bool,
    stage: str,
    reason_code: str,
    parent_index: int | None,
    attempts_consumed: int,
) -> dict[str, Any]:
    failed_stage = None if succeeded else stage
    return {
        "terminal": True,
        "succeeded": succeeded,
        "stage": stage,
        "reason_code": reason_code,
        "parent_index": parent_index,
        "predicate_flags": _predicate_projection(failed_stage),
        "attempts_consumed": attempts_consumed,
    }


def _default_deny(attempts_consumed: int = 0) -> dict[str, Any]:
    return _terminal(
        succeeded=False,
        stage="authorization",
        reason_code="terminal_default_deny_internal_failure",
        parent_index=None,
        attempts_consumed=attempts_consumed,
    )


def evaluate_request(request: Any) -> dict[str, Any]:
    """Evaluate one generated policy projection and always fail closed."""

    attempts = 0
    if isinstance(request, Mapping):
        authorization = request.get("authorization")
        if isinstance(authorization, Mapping):
            candidate = authorization.get("attempt_index")
            if type(candidate) is int and candidate in (1, 2, 3):
                attempts = candidate
    if not validate_request(request):
        return _default_deny(attempts)
    authorization = request["authorization"]
    attempts = authorization["attempt_index"]
    parents_valid, parent_index = validate_parent_set(request["parent_records"])
    if not parents_valid:
        return _terminal(
            succeeded=False,
            stage="fixed_parent_set",
            reason_code=STAGE_FAILURE_REASONS["fixed_parent_set"],
            parent_index=parent_index,
            attempts_consumed=attempts,
        )
    signals = request["stage_signals"]
    for stage in STAGE_SIGNAL_FIELDS[:4]:
        if signals[stage] is not True:
            return _terminal(
                succeeded=False,
                stage=stage,
                reason_code=STAGE_FAILURE_REASONS[stage],
                parent_index=None,
                attempts_consumed=attempts,
            )
    process = request["process_observation"]
    limits = request["process_limits"]
    if signals["process"] is not True:
        reason = STAGE_FAILURE_REASONS["process"]
    elif process["elapsed_ms"] > limits["timeout_ms"]:
        reason = "process_timeout"
    elif (
        process["stdout_bytes"] > limits["max_stdout_bytes"]
        or process["stderr_bytes"] > limits["max_stderr_bytes"]
        or process["result_bytes"] > limits["max_result_bytes"]
        or process["processes"] > limits["max_processes"]
    ):
        reason = "process_output_bounds_failed"
    else:
        reason = None
    if reason is not None:
        return _terminal(
            succeeded=False,
            stage="process",
            reason_code=reason,
            parent_index=None,
            attempts_consumed=attempts,
        )
    retention = request["retention"]
    if (
        signals["result_validation"] is not True
        or retention["raw_retained_bytes"] != 0
        or retention["sanitized_only"] is not True
    ):
        return _terminal(
            succeeded=False,
            stage="result_validation",
            reason_code=STAGE_FAILURE_REASONS["result_validation"],
            parent_index=None,
            attempts_consumed=attempts,
        )
    for stage in STAGE_SIGNAL_FIELDS[6:]:
        if signals[stage] is not True:
            return _terminal(
                succeeded=False,
                stage=stage,
                reason_code=STAGE_FAILURE_REASONS[stage],
                parent_index=None,
                attempts_consumed=attempts,
            )
    return _terminal(
        succeeded=True,
        stage="evidence_seal",
        reason_code="policy_valid",
        parent_index=None,
        attempts_consumed=attempts,
    )


def validate_result(result: Any) -> bool:
    """Validate the exact sanitized terminal projection."""

    if not _exact_fields(result, RESULT_FIELDS) or _contains_prohibited_field(result):
        return False
    if result["terminal"] is not True or type(result["succeeded"]) is not bool:
        return False
    if result["stage"] not in STAGES:
        return False
    if result["reason_code"] not in ("policy_valid", *FAILURE_REASONS):
        return False
    if result["parent_index"] is not None and (
        type(result["parent_index"]) is not int or result["parent_index"] not in PARENT_INDEXES
    ):
        return False
    if not (result["stage"] == "fixed_parent_set" and not result["succeeded"]) and result[
        "parent_index"
    ] is not None:
        return False
    if not _exact_fields(result["predicate_flags"], PREDICATE_FLAG_FIELDS):
        return False
    if not all(type(result["predicate_flags"][stage]) is bool for stage in STAGES):
        return False
    if type(result["attempts_consumed"]) is not int or result["attempts_consumed"] not in (0, 1, 2, 3):
        return False
    if result["succeeded"]:
        return (
            result["stage"] == "evidence_seal"
            and result["reason_code"] == "policy_valid"
            and result["parent_index"] is None
            and all(result["predicate_flags"][stage] is True for stage in STAGES)
        )
    if result["reason_code"] == "policy_valid":
        return False
    failed_index = STAGES.index(result["stage"])
    expected = {stage: index < failed_index for index, stage in enumerate(STAGES)}
    return result["predicate_flags"] == expected


def contract_projection() -> dict[str, Any]:
    """Return constants mirrored by the inert PowerShell source."""

    return {
        "authorization_fields": list(AUTHORIZATION_FIELDS),
        "contract_version": CONTRACT_VERSION,
        "failure_reasons": list(FAILURE_REASONS),
        "parent_fields": list(PARENT_FIELDS),
        "parent_indexes": list(PARENT_INDEXES),
        "parent_reason_codes": list(PARENT_REASON_CODES),
        "predicate_flag_fields": list(PREDICATE_FLAG_FIELDS),
        "process_limits": PROCESS_LIMITS,
        "request_fields": list(REQUEST_FIELDS),
        "result_fields": list(RESULT_FIELDS),
        "runtime_authorization": RUNTIME_AUTHORIZATION,
        "source_build_authorization": SOURCE_BUILD_AUTHORIZATION,
        "stage_failure_reasons": STAGE_FAILURE_REASONS,
        "stage_signal_fields": list(STAGE_SIGNAL_FIELDS),
        "stages": list(STAGES),
        "supported_operations": list(SUPPORTED_OPERATIONS),
    }


def projections_equal(left: Any, right: Any) -> bool:
    return canonical_json(left) == canonical_json(right)


__all__ = [
    "ADDITIONAL_FAILURE_REASONS",
    "AUTHORIZATION_FIELDS",
    "CONTRACT_VERSION",
    "FAILURE_REASONS",
    "PARENT_FIELDS",
    "PARENT_INDEXES",
    "PARENT_PREDICATE_FIELDS",
    "PARENT_REASON_CODES",
    "PREDICATE_FLAG_FIELDS",
    "PROCESS_LIMITS",
    "REQUEST_FIELDS",
    "RESULT_FIELDS",
    "RUNTIME_AUTHORIZATION",
    "SOURCE_BUILD_AUTHORIZATION",
    "STAGES",
    "STAGE_FAILURE_REASONS",
    "STAGE_SIGNAL_FIELDS",
    "SUPPORTED_OPERATIONS",
    "canonical_json",
    "canonical_sha256",
    "contract_projection",
    "evaluate_request",
    "expected_parent_reason",
    "projections_equal",
    "validate_parent_record",
    "validate_parent_set",
    "validate_request",
    "validate_result",
]
