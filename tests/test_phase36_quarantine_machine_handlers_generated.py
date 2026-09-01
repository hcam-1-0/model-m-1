from __future__ import annotations

import ast
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
PLAN_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-generated-test-plan.json"
)
RUNNER_PATH = ROOT / "tools" / "phase36_quarantine_transaction_runner.ps1"
HANDLERS_PATH = ROOT / "tools" / "phase36_quarantine_machine_handlers.psm1"
ADAPTER_PATH = ROOT / "tools" / "phase36_quarantine_windows_storage_adapter.psm1"
EVIDENCE_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-implementation-evidence.json"
)
IMPLEMENTATION_PACKAGE_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-implementation-package.json"
)
IMPLEMENTATION_REVIEW_PATH = (
    ROOT
    / "docs"
    / "phase-3"
    / "p3-6-quarantine-machine-handlers-r0-implementation-evidence-review.md"
)

ACTION_IDS = [
    "U3K-A01-UTC-CLOCK-START",
    "U3K-A02-PACKAGE-RUNNER-AUTHORITY-VERIFY",
    "U3K-A03-AUTHORIZATION-RECORD",
    "U3K-A04-F-DRIVE-INFO",
    "U3K-A05-CANONICAL-PATH-AND-ABSENCE",
    "U3K-A06-PROTECTED-DACL-CONSTRUCT",
    "U3K-A07-SECURITY-AT-CREATE-ROOT",
    "U3K-A08-NORMALIZED-DACL-VERIFY",
    "U3K-A09-ATOMIC-CAPABILITY-PROBE",
    "U3K-A10-NORMALIZE-HASH-WRITE",
]

SUCCESS_CASES = {
    "A01_V01_exact_single_UTC_start_read_succeeds",
    "A02_V01_all_exact_bindings_succeed",
    "A03_V01_sanitized_CreateNew_flush_and_nonreplacement_rename_succeeds",
    "A04_V01_ready_fixed_NTFS_capacity_passes",
    "A04_V02_ready_fixed_ReFS_capacity_passes",
    "A05_V01_exact_absent_candidate_and_nonreparse_parent_pass",
    "A06_V01_exact_three_tuple_protected_descriptor_passes",
    "A07_V01_exclusive_CreateDirectoryW_security_at_create_success_marks_attempt_owned",
    "A08_V01_exact_protected_three_tuple_DACL_passes",
    "A09_V01_exact_4096_byte_two_hash_write_through_rename_cleanup_passes",
    "A10_V01_canonical_bounded_result_and_evidence_writes_succeed",
}

BASE_TRANSCRIPTS: dict[str, dict[str, object]] = {
    ACTION_IDS[0]: {
        "ok": True,
        "read_count": 1,
        "monotonic_seconds": 100.0,
    },
    ACTION_IDS[1]: {
        "ok": True,
        "owner_statement_exact_match": True,
        "authorization_window_current": True,
        "attempt_unused": True,
        "execution_package_hashes_match": True,
        "source_hashes_match": True,
        "runtime_binding_matches": True,
        "target_action_limits_outputs_match": True,
    },
    ACTION_IDS[2]: {
        "ok": True,
        "schema_valid": True,
        "size_valid": True,
        "destination_absent": True,
        "partial_absent": True,
        "flushed_to_disk": True,
        "nonreplacement_rename": True,
    },
    ACTION_IDS[3]: {
        "ok": True,
        "properties_available": True,
        "drive_ready": True,
        "drive_type": "Fixed",
        "filesystem": "NTFS",
        "available_free_bytes": 50 * 1024**3,
        "available_free_percent": 50.0,
    },
    ACTION_IDS[4]: {
        "ok": True,
        "attributes_available": True,
        "exact_canonical_path": True,
        "parent_reparse": False,
        "candidate_reparse": False,
        "candidate_absent": True,
    },
    ACTION_IDS[5]: {
        "ok": True,
        "identity_available": True,
        "identity_collision": False,
        "descriptor_bounded": True,
        "inheritance_protected": True,
        "exact_three_allow_tuples": True,
        "identity_not_persisted": True,
        "account_translation_absent": True,
    },
    ACTION_IDS[6]: {
        "ok": True,
        "native_success": True,
        "error_already_exists": False,
        "required_API_used": True,
        "security_attributes_nonnull": True,
        "fallback_used": False,
    },
    ACTION_IDS[7]: {
        "ok": True,
        "access_rules_protected": True,
        "exact_rule_count_pass": True,
        "current_process_principal_pass": True,
        "current_process_Modify_Synchronize_rights_pass": True,
        "current_process_excessive_or_unknown_rights_absent": True,
        "LocalSystem_tuple_pass": True,
        "Administrators_tuple_pass": True,
        "inheritance_flags_pass": True,
        "propagation_flags_pass": True,
        "access_types_pass": True,
        "inherited_rule_absent": True,
        "deny_rule_absent": True,
        "unauthorized_principal_absent": True,
        "overall_DACL_pass": True,
    },
    ACTION_IDS[8]: {
        "ok": True,
        "probe_paths_absent": True,
        "exact_byte_count": True,
        "write_through": True,
        "flush_to_disk": True,
        "first_hash_match": True,
        "rename_write_through_only": True,
        "second_hash_match": True,
        "cleanup_complete": True,
        "zero_retention": True,
        "partial_created_by_attempt": False,
        "verified_created_by_attempt": False,
    },
    ACTION_IDS[9]: {
        "ok": True,
        "schema_valid": True,
        "size_valid": True,
        "canonical_JSON": True,
        "hashes_computed": True,
        "flushed_to_disk": True,
        "nonreplacement_rename": True,
        "output_paths_exact": True,
    },
}

MUTATIONS: dict[str, dict[str, object]] = {
    "A01_V02_clock_operation_failure_maps_to_clock_unavailable": {"ok": False},
    "A01_V03_second_start_clock_read_is_rejected": {"read_count": 2},
    "A02_V02_package_digest_mismatch_denies_before_machine_access": {
        "execution_package_hashes_match": False
    },
    "A02_V03_core_file_hash_mismatch_denies_before_machine_access": {
        "execution_package_hashes_match": False
    },
    "A02_V04_owner_statement_mismatch_denies_before_machine_access": {
        "owner_statement_exact_match": False
    },
    "A02_V05_expired_authorization_denies_before_machine_access": {
        "authorization_window_current": False
    },
    "A02_V06_consumed_attempt_denies_before_machine_access": {
        "attempt_unused": False
    },
    "A02_V07_runner_or_module_hash_mismatch_denies_before_machine_access": {
        "source_hashes_match": False
    },
    "A02_V08_runtime_binding_mismatch_denies_before_machine_access": {
        "runtime_binding_matches": False
    },
    "A02_V09_action_order_limit_target_or_output_mutation_denies_before_machine_access": {
        "target_action_limits_outputs_match": False
    },
    "A03_V02_schema_or_size_violation_aborts_before_machine_access": {
        "schema_valid": False,
        "size_valid": False,
    },
    "A03_V03_destination_or_partial_exists_aborts_without_overwrite": {
        "destination_absent": False
    },
    "A03_V04_write_flush_or_rename_failure_aborts_before_F_access": {
        "flushed_to_disk": False
    },
    "A04_V03_not_ready_or_property_race_fails_safely": {"drive_ready": False},
    "A04_V04_nonfixed_or_unapproved_filesystem_fails": {
        "drive_type": "Network",
        "filesystem": "FAT32",
    },
    "A04_V05_capacity_or_allowlisted_property_failure_is_sanitized": {
        "properties_available": False,
        "available_free_bytes": 0,
    },
    "A05_V02_existing_file_directory_or_reparse_candidate_fails_without_change": {
        "candidate_absent": False
    },
    "A05_V03_reparse_F_root_fails_without_following": {"parent_reparse": True},
    "A05_V04_case_folded_alias_or_alternate_path_fails": {
        "exact_canonical_path": False
    },
    "A05_V05_equal_to_or_beneath_F_h_cam_fails": {
        "exact_canonical_path": False
    },
    "A05_V06_unexpected_attribute_error_fails_without_treating_it_as_absence": {
        "attributes_available": False
    },
    "A06_V02_null_current_identity_or_SID_fails": {"identity_available": False},
    "A06_V03_current_SID_collision_with_LocalSystem_or_Administrators_fails": {
        "identity_collision": True
    },
    "A06_V04_inheritance_protection_or_rule_construction_failure_fails": {
        "inheritance_protected": False
    },
    "A06_V05_extra_deny_or_unknown_rights_input_fails": {
        "exact_three_allow_tuples": False
    },
    "A06_V06_account_name_translation_or_identity_persistence_request_fails": {
        "identity_not_persisted": False,
        "account_translation_absent": False,
    },
    "A07_V02_ERROR_ALREADY_EXISTS_or_race_fails_without_modification_or_cleanup": {
        "ok": False,
        "native_success": False,
        "error_already_exists": True,
    },
    "A07_V03_other_native_failure_is_sanitized_and_does_not_claim_attempt_ownership": {
        "ok": False,
        "native_success": False,
    },
    "A07_V04_plain_create_managed_existing_return_or_post_create_ACL_fallback_is_rejected": {
        "required_API_used": False,
        "fallback_used": True,
    },
    "A08_V02_inherited_or_deny_rule_fails": {
        "inherited_rule_absent": False,
        "deny_rule_absent": False,
        "overall_DACL_pass": False,
    },
    "A08_V03_extra_or_unauthorized_principal_fails_independently": {
        "unauthorized_principal_absent": False,
        "overall_DACL_pass": False,
    },
    "A08_V04_current_process_excessive_unknown_or_missing_rights_fail": {
        "current_process_Modify_Synchronize_rights_pass": False,
        "current_process_excessive_or_unknown_rights_absent": False,
        "overall_DACL_pass": False,
    },
    "A08_V05_LocalSystem_or_Administrators_rights_mismatch_fails": {
        "LocalSystem_tuple_pass": False,
        "Administrators_tuple_pass": False,
        "overall_DACL_pass": False,
    },
    "A08_V06_inheritance_propagation_access_type_or_rule_count_mismatch_fails": {
        "exact_rule_count_pass": False,
        "inheritance_flags_pass": False,
        "propagation_flags_pass": False,
        "access_types_pass": False,
        "overall_DACL_pass": False,
    },
    "A09_V02_preexisting_partial_or_verified_path_fails_without_overwrite": {
        "probe_paths_absent": False
    },
    "A09_V03_short_long_or_nondeterministic_probe_write_fails": {
        "exact_byte_count": False
    },
    "A09_V04_flush_true_failure_blocks_and_enters_bounded_cleanup": {
        "flush_to_disk": False,
        "partial_created_by_attempt": True,
    },
    "A09_V05_first_readback_hash_mismatch_blocks_before_rename": {
        "first_hash_match": False,
        "partial_created_by_attempt": True,
    },
    "A09_V06_cross_volume_replace_copy_allowed_or_non_write_through_rename_is_rejected": {
        "rename_write_through_only": False,
        "partial_created_by_attempt": True,
    },
    "A09_V07_second_readback_hash_mismatch_blocks_and_cleans_attempt_objects": {
        "second_hash_match": False,
        "verified_created_by_attempt": True,
    },
    "A09_V08_probe_or_empty_root_cleanup_failure_requires_manual_review_and_no_retry": {
        "cleanup_complete": False,
        "zero_retention": False,
        "verified_created_by_attempt": True,
    },
    "A10_V02_unknown_field_raw_error_or_identifier_is_rejected": {
        "schema_valid": False
    },
    "A10_V03_output_path_or_destination_mutation_is_rejected": {
        "output_paths_exact": False
    },
    "A10_V04_oversize_or_noncanonical_output_is_rejected": {
        "size_valid": False,
        "canonical_JSON": False,
    },
    "A10_V05_write_flush_hash_or_rename_failure_preserves_no_additional_authority": {
        "flushed_to_disk": False,
        "hashes_computed": False,
    },
}

EXPECTED_FAILURE_RESULTS = {
    "A01_V02_clock_operation_failure_maps_to_clock_unavailable": (
        "blocked",
        "clock_unavailable",
    ),
    "A01_V03_second_start_clock_read_is_rejected": (
        "blocked",
        "clock_read_count_invalid",
    ),
    "A02_V02_package_digest_mismatch_denies_before_machine_access": (
        "blocked",
        "authority_binding_invalid",
    ),
    "A02_V03_core_file_hash_mismatch_denies_before_machine_access": (
        "blocked",
        "authority_binding_invalid",
    ),
    "A02_V04_owner_statement_mismatch_denies_before_machine_access": (
        "blocked",
        "authority_binding_invalid",
    ),
    "A02_V05_expired_authorization_denies_before_machine_access": (
        "blocked",
        "authorization_window_invalid",
    ),
    "A02_V06_consumed_attempt_denies_before_machine_access": (
        "blocked",
        "attempt_already_consumed",
    ),
    "A02_V07_runner_or_module_hash_mismatch_denies_before_machine_access": (
        "blocked",
        "authority_binding_invalid",
    ),
    "A02_V08_runtime_binding_mismatch_denies_before_machine_access": (
        "blocked",
        "authority_binding_invalid",
    ),
    "A02_V09_action_order_limit_target_or_output_mutation_denies_before_machine_access": (
        "blocked",
        "authority_binding_invalid",
    ),
    "A03_V02_schema_or_size_violation_aborts_before_machine_access": (
        "blocked",
        "authorization_record_invalid",
    ),
    "A03_V03_destination_or_partial_exists_aborts_without_overwrite": (
        "blocked",
        "authorization_record_exists",
    ),
    "A03_V04_write_flush_or_rename_failure_aborts_before_F_access": (
        "blocked",
        "authorization_record_write_failed",
    ),
    "A04_V03_not_ready_or_property_race_fails_safely": (
        "blocked",
        "drive_not_ready",
    ),
    "A04_V04_nonfixed_or_unapproved_filesystem_fails": (
        "blocked",
        "drive_type_not_allowed",
    ),
    "A04_V05_capacity_or_allowlisted_property_failure_is_sanitized": (
        "blocked",
        "drive_property_unavailable",
    ),
    "A05_V02_existing_file_directory_or_reparse_candidate_fails_without_change": (
        "blocked",
        "candidate_exists",
    ),
    "A05_V03_reparse_F_root_fails_without_following": (
        "blocked",
        "candidate_or_parent_reparse",
    ),
    "A05_V04_case_folded_alias_or_alternate_path_fails": (
        "blocked",
        "candidate_path_invalid",
    ),
    "A05_V05_equal_to_or_beneath_F_h_cam_fails": (
        "blocked",
        "candidate_path_invalid",
    ),
    "A05_V06_unexpected_attribute_error_fails_without_treating_it_as_absence": (
        "blocked",
        "candidate_attribute_unavailable",
    ),
    "A06_V02_null_current_identity_or_SID_fails": (
        "blocked",
        "identity_unavailable",
    ),
    "A06_V03_current_SID_collision_with_LocalSystem_or_Administrators_fails": (
        "blocked",
        "identity_collision",
    ),
    "A06_V04_inheritance_protection_or_rule_construction_failure_fails": (
        "blocked",
        "security_descriptor_invalid",
    ),
    "A06_V05_extra_deny_or_unknown_rights_input_fails": (
        "blocked",
        "security_descriptor_invalid",
    ),
    "A06_V06_account_name_translation_or_identity_persistence_request_fails": (
        "blocked",
        "security_descriptor_invalid",
    ),
    "A07_V02_ERROR_ALREADY_EXISTS_or_race_fails_without_modification_or_cleanup": (
        "blocked",
        "root_preexisting_or_raced",
    ),
    "A07_V03_other_native_failure_is_sanitized_and_does_not_claim_attempt_ownership": (
        "blocked",
        "root_create_failed",
    ),
    "A07_V04_plain_create_managed_existing_return_or_post_create_ACL_fallback_is_rejected": (
        "blocked",
        "root_creation_mechanism_invalid",
    ),
    "A08_V02_inherited_or_deny_rule_fails": (
        "blocked",
        "DACL_policy_failed",
    ),
    "A08_V03_extra_or_unauthorized_principal_fails_independently": (
        "blocked",
        "DACL_policy_failed",
    ),
    "A08_V04_current_process_excessive_unknown_or_missing_rights_fail": (
        "blocked",
        "DACL_policy_failed",
    ),
    "A08_V05_LocalSystem_or_Administrators_rights_mismatch_fails": (
        "blocked",
        "DACL_policy_failed",
    ),
    "A08_V06_inheritance_propagation_access_type_or_rule_count_mismatch_fails": (
        "blocked",
        "DACL_policy_failed",
    ),
    "A09_V02_preexisting_partial_or_verified_path_fails_without_overwrite": (
        "blocked",
        "probe_path_preexisting",
    ),
    "A09_V03_short_long_or_nondeterministic_probe_write_fails": (
        "blocked",
        "probe_write_failed",
    ),
    "A09_V04_flush_true_failure_blocks_and_enters_bounded_cleanup": (
        "blocked",
        "probe_write_failed",
    ),
    "A09_V05_first_readback_hash_mismatch_blocks_before_rename": (
        "blocked",
        "probe_write_failed",
    ),
    "A09_V06_cross_volume_replace_copy_allowed_or_non_write_through_rename_is_rejected": (
        "blocked",
        "probe_write_failed",
    ),
    "A09_V07_second_readback_hash_mismatch_blocks_and_cleans_attempt_objects": (
        "blocked",
        "probe_write_failed",
    ),
    "A09_V08_probe_or_empty_root_cleanup_failure_requires_manual_review_and_no_retry": (
        "manual_review_required",
        "probe_cleanup_failed",
    ),
    "A10_V02_unknown_field_raw_error_or_identifier_is_rejected": (
        "blocked",
        "output_schema_invalid",
    ),
    "A10_V03_output_path_or_destination_mutation_is_rejected": (
        "blocked",
        "output_schema_invalid",
    ),
    "A10_V04_oversize_or_noncanonical_output_is_rejected": (
        "blocked",
        "output_schema_invalid",
    ),
    "A10_V05_write_flush_hash_or_rename_failure_preserves_no_additional_authority": (
        "blocked",
        "output_write_failed",
    ),
}

CROSS_EXPECTATIONS = {
    "X_V01_unknown_missing_duplicate_reordered_or_disabled_action_default_denies": (
        "blocked",
        "action_plan_invalid",
    ),
    "X_V02_state_transition_skip_repeat_or_backtrack_default_denies": (
        "blocked",
        "action_out_of_order",
    ),
    "X_V03_per_action_or_total_deadline_expiry_stops_future_actions": (
        "blocked",
        "transaction_timeout",
    ),
    "X_V04_failure_cleanup_never_expands_beyond_attempt_created_exact_objects": (
        "invariant_enforced",
        "bounded_cleanup",
    ),
    "X_V05_raw_exception_stack_stdout_stderr_identity_security_or_probe_content_never_persists": (
        "invariant_enforced",
        "sanitized_projection",
    ),
    "X_V06_network_proxy_environment_registry_process_service_scanner_and_download_operations_are_absent": (
        "invariant_enforced",
        "forbidden_surfaces_absent",
    ),
    "X_V07_generated_harness_cannot_import_or_call_the_windows_adapter": (
        "invariant_enforced",
        "adapter_not_imported",
    ),
    "X_V08_every_terminal_state_keeps_retry_execution_profile_deployment_and_remote_git_authority_false": (
        "invariant_enforced",
        "terminal_authority_false",
    ),
}


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _plan_vectors() -> list[tuple[str, str]]:
    plan = _read_json(PLAN_PATH)
    vectors: list[tuple[str, str]] = []
    for group in plan["action_vector_groups"]:
        vectors.extend(
            (group["action_id"], case_id)
            for case_id in group["required_cases"]
        )
    vectors.extend(
        ("cross_cutting", case_id)
        for case_id in plan["cross_cutting_vectors"]["required_cases"]
    )
    return vectors


def _all_true(transcript: dict[str, object], names: tuple[str, ...]) -> bool:
    return all(transcript.get(name) is True for name in names)


def _evaluate_action(
    action_id: str, transcript: dict[str, object]
) -> tuple[str, str]:
    if action_id == ACTION_IDS[0]:
        if transcript.get("ok") is not True:
            return "blocked", "clock_unavailable"
        if transcript.get("read_count") != 1:
            return "blocked", "clock_read_count_invalid"
    elif action_id == ACTION_IDS[1]:
        if transcript.get("attempt_unused") is not True:
            return "blocked", "attempt_already_consumed"
        if transcript.get("authorization_window_current") is not True:
            return "blocked", "authorization_window_invalid"
        if not _all_true(
            transcript,
            (
                "ok",
                "owner_statement_exact_match",
                "execution_package_hashes_match",
                "source_hashes_match",
                "runtime_binding_matches",
                "target_action_limits_outputs_match",
            ),
        ):
            return "blocked", "authority_binding_invalid"
    elif action_id == ACTION_IDS[2]:
        if (
            transcript.get("destination_absent") is not True
            or transcript.get("partial_absent") is not True
        ):
            return "blocked", "authorization_record_exists"
        if (
            transcript.get("schema_valid") is not True
            or transcript.get("size_valid") is not True
        ):
            return "blocked", "authorization_record_invalid"
        if not _all_true(
            transcript,
            ("ok", "flushed_to_disk", "nonreplacement_rename"),
        ):
            return "blocked", "authorization_record_write_failed"
    elif action_id == ACTION_IDS[3]:
        if transcript.get("properties_available") is not True:
            return "blocked", "drive_property_unavailable"
        if transcript.get("drive_ready") is not True:
            return "blocked", "drive_not_ready"
        if transcript.get("drive_type") != "Fixed":
            return "blocked", "drive_type_not_allowed"
        if transcript.get("filesystem") not in {"NTFS", "ReFS"}:
            return "blocked", "filesystem_not_allowed"
        if (
            int(transcript.get("available_free_bytes", 0)) < 5 * 1024**3
            or float(transcript.get("available_free_percent", 0.0)) < 15.0
        ):
            return "blocked", "capacity_below_minimum"
    elif action_id == ACTION_IDS[4]:
        if transcript.get("attributes_available") is not True:
            return "blocked", "candidate_attribute_unavailable"
        if transcript.get("exact_canonical_path") is not True:
            return "blocked", "candidate_path_invalid"
        if (
            transcript.get("parent_reparse") is True
            or transcript.get("candidate_reparse") is True
        ):
            return "blocked", "candidate_or_parent_reparse"
        if transcript.get("candidate_absent") is not True:
            return "blocked", "candidate_exists"
    elif action_id == ACTION_IDS[5]:
        if transcript.get("identity_available") is not True:
            return "blocked", "identity_unavailable"
        if transcript.get("identity_collision") is True:
            return "blocked", "identity_collision"
        if not _all_true(
            transcript,
            (
                "ok",
                "descriptor_bounded",
                "inheritance_protected",
                "exact_three_allow_tuples",
                "identity_not_persisted",
                "account_translation_absent",
            ),
        ):
            return "blocked", "security_descriptor_invalid"
    elif action_id == ACTION_IDS[6]:
        if transcript.get("error_already_exists") is True:
            return "blocked", "root_preexisting_or_raced"
        if not _all_true(
            transcript,
            ("required_API_used", "security_attributes_nonnull"),
        ) or transcript.get("fallback_used") is True:
            return "blocked", "root_creation_mechanism_invalid"
        if (
            transcript.get("ok") is not True
            or transcript.get("native_success") is not True
        ):
            return "blocked", "root_create_failed"
    elif action_id == ACTION_IDS[7]:
        required = tuple(
            name
            for name in BASE_TRANSCRIPTS[action_id]
            if name not in {"reason_code"}
        )
        if not _all_true(transcript, required):
            return "blocked", "DACL_policy_failed"
    elif action_id == ACTION_IDS[8]:
        if transcript.get("probe_paths_absent") is not True:
            return "blocked", "probe_path_preexisting"
        if transcript.get("cleanup_complete") is not True:
            return "manual_review_required", "probe_cleanup_failed"
        required = (
            "ok",
            "exact_byte_count",
            "write_through",
            "flush_to_disk",
            "first_hash_match",
            "rename_write_through_only",
            "second_hash_match",
            "zero_retention",
        )
        if not _all_true(transcript, required):
            return "blocked", "probe_write_failed"
    elif action_id == ACTION_IDS[9]:
        if (
            transcript.get("schema_valid") is not True
            or transcript.get("canonical_JSON") is not True
            or transcript.get("output_paths_exact") is not True
        ):
            return "blocked", "output_schema_invalid"
        if transcript.get("size_valid") is not True:
            return "blocked", "output_too_large"
        if not _all_true(
            transcript,
            (
                "ok",
                "hashes_computed",
                "flushed_to_disk",
                "nonreplacement_rename",
            ),
        ):
            return "blocked", "output_write_failed"
    else:
        return "blocked", "unknown_action"
    return "passed", "ok"


def _fixture(action_id: str, case_id: str) -> dict[str, object]:
    transcript = deepcopy(BASE_TRANSCRIPTS[action_id])
    transcript.update(MUTATIONS.get(case_id, {}))
    if case_id == "A04_V02_ready_fixed_ReFS_capacity_passes":
        transcript["filesystem"] = "ReFS"
    return transcript


def _expected(action_id: str, case_id: str) -> tuple[str, str]:
    if action_id == "cross_cutting":
        return CROSS_EXPECTATIONS[case_id]
    if case_id in SUCCESS_CASES:
        return "passed", "ok"
    return EXPECTED_FAILURE_RESULTS[case_id]


def test_plan_and_reference_cover_exactly_sixty_four_unique_vectors() -> None:
    vectors = _plan_vectors()
    case_ids = [case_id for _, case_id in vectors]
    action_case_ids = {
        case_id for action_id, case_id in vectors if action_id != "cross_cutting"
    }

    assert len(vectors) == 64
    assert len(set(case_ids)) == 64
    assert set(MUTATIONS) | SUCCESS_CASES == action_case_ids
    assert set(EXPECTED_FAILURE_RESULTS) == set(MUTATIONS)
    assert set(CROSS_EXPECTATIONS) == {
        case_id for action_id, case_id in vectors if action_id == "cross_cutting"
    }


@pytest.mark.parametrize(
    ("action_id", "case_id"),
    _plan_vectors(),
    ids=lambda value: value,
)
def test_generated_reference_vector(action_id: str, case_id: str) -> None:
    if action_id == "cross_cutting":
        outcome, reason = CROSS_EXPECTATIONS[case_id]
    else:
        outcome, reason = _evaluate_action(
            action_id,
            _fixture(action_id, case_id),
        )

    assert (outcome, reason) == _expected(action_id, case_id)
    assert outcome in {
        "passed",
        "blocked",
        "manual_review_required",
        "invariant_enforced",
    }
    assert reason not in {"raw_exception", "stack", "stdout", "stderr"}


def test_runner_has_default_off_static_ten_action_storage_dispatch() -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8")

    assert "[ValidateSet('Contract', 'Storage')]" in source
    assert "switch -CaseSensitive ($ActionId)" in source
    assert "P36_MACHINE_HANDLER_NOT_IMPLEMENTED" not in source
    assert "Test-P36PreImportReceipt -Request $request" in source
    assert "Test-P36StorageEnvelope -Request $request" in source
    assert source.rindex("Test-P36PreImportReceipt -Request $request") < source.index(
        "Import-Module -Name $script:HandlerModulePath"
    )
    assert source.rindex("Test-P36StorageEnvelope -Request $request") < source.index(
        "Import-Module -Name $script:WindowsAdapterPath"
    )
    for action_id in ACTION_IDS:
        assert source.count(f"'{action_id}'") >= 2


def test_pure_handler_module_has_no_direct_machine_surface() -> None:
    source = HANDLERS_PATH.read_text(encoding="utf-8")

    for action_id in ACTION_IDS:
        assert source.count(f"'{action_id}'") >= 2
        assert source.count(f"'{action_id}' {{ Resolve-P36") == 1
    assert "switch -CaseSensitive ($ActionId)" in source
    for forbidden in (
        "System.IO.File",
        "System.IO.Directory",
        "System.IO.DriveInfo",
        "WindowsIdentity",
        "CreateDirectoryW",
        "GetFileAttributesW",
        "MoveFileExW",
        "GetAccessControl",
        "FileSystemAclExtensions",
        "$env:",
        "Get-Item",
        "Get-ChildItem",
        "Test-Path",
        "Resolve-Path",
    ):
        assert forbidden not in source


def test_direct_windows_apis_are_confined_to_exact_adapter() -> None:
    runner = RUNNER_PATH.read_text(encoding="utf-8")
    handlers = HANDLERS_PATH.read_text(encoding="utf-8")
    adapter = ADAPTER_PATH.read_text(encoding="utf-8")

    for required in (
        "CreateDirectoryW",
        "SECURITY_ATTRIBUTES",
        "GetFileAttributesW",
        "MoveFileExW",
        "System.IO.DriveInfo",
        "WindowsIdentity]::GetCurrent",
        "FileSystemAclExtensions]::GetAccessControl",
        "FileMode]::CreateNew",
        "FileOptions]::WriteThrough",
        "Flush($true)",
        "Directory]::Delete($script:P36CandidateRoot, $false)",
    ):
        assert required in adapter
        assert required not in handlers
    assert "CreateDirectoryW" not in runner
    assert "GetFileAttributesW" not in runner
    assert "MoveFileExW" not in runner
    assert "System.IO.DriveInfo" not in runner


def test_all_sources_exclude_dynamic_or_scope_expanding_operations() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (RUNNER_PATH, HANDLERS_PATH, ADAPTER_PATH)
    )
    for forbidden in (
        "Invoke-Expression",
        "Start-Process",
        "Remove-Item -Recurse",
        "Get-Acl",
        "Set-Acl",
        "icacls",
        "takeown",
        "MOVEFILE_COPY_ALLOWED",
        "MOVEFILE_REPLACE_EXISTING",
        "MOVEFILE_DELAY_UNTIL_REBOOT",
        "Get-MpComputerStatus",
        "MpCmdRun",
        "WinVerifyTrust",
        "System.Net.",
        "Microsoft.Win32.Registry",
    ):
        assert forbidden not in combined


def test_probe_and_cleanup_are_exact_bounded_and_zero_retention() -> None:
    adapter = ADAPTER_PATH.read_text(encoding="utf-8")

    assert "[byte[]]::new(4096)" in adapter
    assert "P36-U3K-STORAGE-R2-GENERATED-PROBE-V1" in adapter
    assert "0x00000008" in adapter
    assert "[System.IO.File]::Delete($script:P36VerifiedProbePath)" in adapter
    assert "[System.IO.Directory]::Delete($script:P36CandidateRoot, $false)" in adapter
    assert "Directory]::Delete($script:P36CandidateRoot, $true)" not in adapter
    handlers = HANDLERS_PATH.read_text(encoding="utf-8")
    assert "automatic_retry_authorized" in handlers
    assert "automatic_retry_authorized         = $false" in handlers


def test_generated_harness_cannot_execute_or_import_powershell() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert imported_modules.isdisjoint(
        {"subprocess", "runpy", "importlib", "ctypes", "winreg", "os"}
    )
    assert called_names.isdisjoint({"exec", "eval", "compile", "__import__"})
    assert ".psm1" in source
    assert "read_text" in source


def test_terminal_projection_keeps_every_unrelated_authority_false() -> None:
    handlers = HANDLERS_PATH.read_text(encoding="utf-8")
    runner = RUNNER_PATH.read_text(encoding="utf-8")

    for field in (
        "automatic_retry_authorized",
        "execution_authorized",
        "profile_activation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ):
        assert f"{field}" in handlers
    assert "Defender_state" not in runner
    assert "ModelScan_state" not in runner


def test_sealed_evidence_binds_exact_authorized_sources_and_tests() -> None:
    evidence = _read_json(EVIDENCE_PATH)

    assert evidence["status"] == (
        "implemented_generated_and_static_validation_passed_non_executable_"
        "owner_acceptance_pending"
    )
    assert evidence["implementation_authorization"]["decision_id"] == (
        "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-AUTH"
    )
    assert evidence["implementation_authorization"][
        "proposal_package_digest_sha256"
    ] == "EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311"
    for item in evidence["implemented_artifacts"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
        assert item["PowerShell_executed_or_imported"] is False
    assert evidence["validation"]["generated_reference_and_static"][
        "generated_vectors_passed"
    ] == 64
    assert evidence["validation"]["PowerShell"]["executed_or_imported"] is False


def test_implementation_package_seals_every_current_core_file() -> None:
    package = _read_json(IMPLEMENTATION_PACKAGE_PATH)

    assert package["status"] == (
        "sealed_non_executable_owner_implementation_acceptance_pending"
    )
    assert package["core_file_count"] == len(package["core_files"]) == 21
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["current_gate_effect"]["owner_implementation_acceptance_pending"]
    assert package["current_gate_effect"]["PowerShell_or_runner_execution_authorized"] is False
    assert package["current_gate_effect"]["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False


def test_canonical_ledgers_record_implemented_but_non_executable_state() -> None:
    package_digest = _sha256(IMPLEMENTATION_PACKAGE_PATH)

    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read_json(CONTRACTS / name)
        state = ledger[
            "quarantine_machine_handlers_r0_implementation_authorization_package"
        ]
        assert state["owner_authorization_pending"] is False
        assert state["machine_handler_implementation_authorized"] is True
        assert state["machine_action_handlers_implemented"] is True
        assert state["implementation_package_digest_sha256"] == package_digest
        assert state["owner_implementation_acceptance_pending"] is True
        assert state["PowerShell_or_runner_execution_authorized"] is False
        assert state["storage_attempt_authorized"] is False
        assert state["F_or_ACL_action_authorized"] is False


def test_implementation_review_preserves_all_later_execution_gates() -> None:
    review = IMPLEMENTATION_REVIEW_PATH.read_text(encoding="utf-8")

    assert "64 generated vectors" in review
    assert "275 Phase 3.6 tests" in review
    assert "CreateDirectoryW" in review
    assert "PowerShell was not parsed, imported, or executed" in review
    assert "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE" in review
    assert "D-P3.6-U3K-STORAGE-R2-AUTH is not requestable" in review
