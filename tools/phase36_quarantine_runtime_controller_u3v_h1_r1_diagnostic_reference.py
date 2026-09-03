"""Machine-disabled U3V H1 R1 diagnostic policy reference.

This module classifies generated in-memory controller projections only. It has
no filesystem, environment, registry, network, native API, subprocess, or
machine-controller surface.
"""

from typing import Any, Mapping


CONTRACT_VERSION = "1.0.0"
GROUP_ORDER = (
    "top_level_shape",
    "contract_identity",
    "terminal_state",
    "reason_family",
    "stage_projection",
    "action_counts",
    "retention_projection",
    "gate_effect",
)
DIAGNOSTIC_REASONS = (
    "source_binding_failed",
    "controller_top_level_shape_invalid",
    "controller_contract_identity_invalid",
    "controller_terminal_state_invalid",
    "controller_reason_family_invalid",
    "controller_stage_projection_invalid",
    "controller_action_counts_invalid",
    "controller_retention_projection_invalid",
    "controller_gate_effect_invalid",
    "controller_projection_valid",
    "diagnostic_internal_contract_invalid",
)
REASON_FAMILIES = (
    "policy_valid",
    "sanitized_failure",
    "unknown_or_unavailable",
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
STAGE_FIELDS = ("completed_actions", "failed_action", "failed_stage")
ACTION_COUNT_FIELDS = ("planned", "completed", "attempts", "retries", "processes")
RETENTION_FIELDS = (
    "raw_material_retained_bytes",
    "sanitized_result_only",
    "cleanup_actions",
)
GATE_FIELDS = (
    "machine_action_authorized",
    "python_machine_fallback",
    "retry_authorized",
    "U3T_preflight_authorized",
    "U3K_authorized",
    "deployment_authorized",
    "next_gate",
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
FAILURE_REASON_BY_ACTION = {
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
FAILURE_ACTION_BY_REASON = {reason: action for action, reason in FAILURE_REASON_BY_ACTION.items()}
CONTROLLER_REASONS = ("policy_valid", *FAILURE_ACTION_BY_REASON)


def _exact_fields(value: Any, expected: tuple[str, ...]) -> bool:
    return isinstance(value, Mapping) and set(value) == set(expected)


def _integer(value: Any) -> bool:
    return type(value) is int


def controller_reason_family(candidate: Any) -> str:
    """Return one sanitized reason family without retaining candidate material."""

    if not isinstance(candidate, Mapping):
        return "unknown_or_unavailable"
    reason = candidate.get("reason_code")
    if reason == "policy_valid":
        return "policy_valid"
    if isinstance(reason, str) and reason in FAILURE_ACTION_BY_REASON:
        return "sanitized_failure"
    return "unknown_or_unavailable"


def classify_candidate(candidate: Any) -> str:
    """Classify one generated controller projection into an allowlisted reason."""

    if not _exact_fields(candidate, RESULT_FIELDS):
        return "controller_top_level_shape_invalid"
    if candidate["contract_version"] != CONTRACT_VERSION:
        return "controller_contract_identity_invalid"
    if type(candidate["terminal"]) is not bool or candidate["terminal"] is not True:
        return "controller_terminal_state_invalid"
    if type(candidate["succeeded"]) is not bool:
        return "controller_terminal_state_invalid"

    reason = candidate["reason_code"]
    if reason not in CONTROLLER_REASONS:
        return "controller_reason_family_invalid"
    if candidate["succeeded"] is not (reason == "policy_valid"):
        return "controller_reason_family_invalid"

    stage = candidate["stage_projection"]
    if not _exact_fields(stage, STAGE_FIELDS):
        return "controller_stage_projection_invalid"
    completed = stage["completed_actions"]
    if not _integer(completed) or completed < 0 or completed > len(ACTION_ORDER):
        return "controller_stage_projection_invalid"
    if reason == "policy_valid":
        if completed != len(ACTION_ORDER):
            return "controller_stage_projection_invalid"
        if stage["failed_action"] is not None or stage["failed_stage"] is not None:
            return "controller_stage_projection_invalid"
    else:
        expected_action = FAILURE_ACTION_BY_REASON[reason]
        if completed != ACTION_ORDER.index(expected_action):
            return "controller_stage_projection_invalid"
        if stage["failed_action"] != expected_action or stage["failed_stage"] != reason:
            return "controller_stage_projection_invalid"

    counts = candidate["action_counts"]
    if not _exact_fields(counts, ACTION_COUNT_FIELDS):
        return "controller_action_counts_invalid"
    if any(not _integer(counts[field]) for field in ACTION_COUNT_FIELDS):
        return "controller_action_counts_invalid"
    if (
        counts["planned"] != len(ACTION_ORDER)
        or counts["completed"] != completed
        or counts["attempts"] != 1
        or counts["retries"] != 0
        or counts["processes"] != 0
    ):
        return "controller_action_counts_invalid"

    retention = candidate["retention_projection"]
    if not _exact_fields(retention, RETENTION_FIELDS):
        return "controller_retention_projection_invalid"
    if (
        not _integer(retention["raw_material_retained_bytes"])
        or retention["raw_material_retained_bytes"] != 0
        or type(retention["sanitized_result_only"]) is not bool
        or retention["sanitized_result_only"] is not True
        or not _integer(retention["cleanup_actions"])
        or retention["cleanup_actions"] != 0
    ):
        return "controller_retention_projection_invalid"

    gate = candidate["gate_effect"]
    if not _exact_fields(gate, GATE_FIELDS):
        return "controller_gate_effect_invalid"
    for field in GATE_FIELDS[:-1]:
        if type(gate[field]) is not bool or gate[field] is not False:
            return "controller_gate_effect_invalid"
    expected_next_gate = (
        "owner_source_implementation_acceptance_required"
        if reason == "policy_valid"
        else "blocked"
    )
    if gate["next_gate"] != expected_next_gate:
        return "controller_gate_effect_invalid"
    return "controller_projection_valid"


def diagnostic_projection(reason_code: str, family: str) -> dict[str, Any]:
    """Return one bounded sanitized output for an allowlisted classification."""

    if reason_code not in DIAGNOSTIC_REASONS or family not in REASON_FAMILIES:
        reason_code = "diagnostic_internal_contract_invalid"
        family = "unknown_or_unavailable"
    succeeded = reason_code == "controller_projection_valid"
    return {
        "contract_version": CONTRACT_VERSION,
        "terminal": True,
        "succeeded": succeeded,
        "reason_code": reason_code,
        "diagnostic_projection": {
            "checked_group_count": len(GROUP_ORDER),
            "controller_reason_family": family,
        },
        "retention_projection": {
            "raw_controller_material_retained_bytes": 0,
            "sanitized_result_only": True,
        },
        "gate_effect": {
            "machine_action_authorized": False,
            "python_machine_fallback": False,
            "retry_authorized": False,
            "U3K_authorized": False,
            "deployment_authorized": False,
            "next_gate": (
                "owner_source_implementation_acceptance_required"
                if succeeded
                else "blocked"
            ),
        },
    }


def evaluate_candidate(candidate: Any) -> dict[str, Any]:
    """Classify and immediately reduce a candidate to a sanitized projection."""

    reason = classify_candidate(candidate)
    return diagnostic_projection(reason, controller_reason_family(candidate))


def contract_projection() -> dict[str, Any]:
    """Return the canonical cross-language projection for static comparison."""

    return {
        "contract_version": CONTRACT_VERSION,
        "diagnostic_group_order": list(GROUP_ORDER),
        "allowlisted_terminal_reason_codes": list(DIAGNOSTIC_REASONS),
        "allowlisted_controller_reason_families": list(REASON_FAMILIES),
        "maximum_output_bytes": 4096,
        "raw_controller_material_retained_bytes": 0,
        "machine_action_authorized": False,
        "python_machine_fallback": False,
        "retry_authorized": False,
        "U3K_authorized": False,
        "deployment_authorized": False,
    }


__all__ = [
    "ACTION_ORDER",
    "CONTRACT_VERSION",
    "DIAGNOSTIC_REASONS",
    "GROUP_ORDER",
    "REASON_FAMILIES",
    "classify_candidate",
    "contract_projection",
    "controller_reason_family",
    "diagnostic_projection",
    "evaluate_candidate",
]
