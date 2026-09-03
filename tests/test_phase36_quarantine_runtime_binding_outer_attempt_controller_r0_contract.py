import hashlib
import json
from collections import Counter
from pathlib import Path

from tools.phase36_quarantine_runtime_binding_outer_attempt_controller_r0_reference import (
    CONTRACT_VERSION,
    PARENT_FIELDS,
    PARENT_INDEXES,
    PREDICATE_FLAG_FIELDS,
    PROCESS_LIMITS,
    REQUEST_FIELDS,
    RESULT_FIELDS,
    RUNTIME_AUTHORIZATION,
    SOURCE_BUILD_AUTHORIZATION,
    STAGES,
    STAGE_FAILURE_REASONS,
    SUPPORTED_OPERATIONS,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-binding-outer-attempt-controller-r0-contract.json"
)
VECTORS = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-binding-outer-attempt-controller-r0-vectors.json"
)
AUTHORIZATION_PACKAGE = ROOT / (
    "contracts/phase-3/p3-6-consolidated-build-authorization-planning-package.json"
)
AUTHORIZATION_PACKAGE_SHA256 = (
    "DC0C28564207F87E64441CEF146CB711E203B11694D08997E82C1962CCD0414C"
)
GROUPS = (
    "exact_three_parent_all_valid",
    "each_single_invalid_parent_index",
    "multiple_invalid_parents",
    "zero_one_two_and_four_record_cardinality_rejected",
    "missing_wrong_type_and_unknown_parent_fields_rejected",
    "unknown_stage_operation_and_reason_default_denied",
    "ordered_stage_transition_and_no_stage_skipping",
    "attempt_count_and_retry_authority_bounds",
    "process_timeout_stdout_stderr_result_size_bounds",
    "source_and_runtime_preflight_postflight_identity_failures",
    "sanitized_terminal_projection_and_zero_raw_retention",
    "PowerShell_Python_canonical_projection_equivalence",
    "all_runtime_machine_U3K_deployment_and_Git_gates_closed",
)
IMMUTABLE_INPUTS = {
    "tools/phase36_quarantine_runtime_controller_r1_generated_validation.ps1": (
        "D9EE5CC7599AACCE3363CE5C29EE479D777F94CF886AE779390B7027C40FA382"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-vectors.json": (
        "7BCDFCA583644BD4ED5F4B747C3969B4C9FF4029B48734F8BD4D90BA5D600A21"
    ),
    "tools/phase36_quarantine_runtime_controller_r1.ps1": (
        "787655BAC55DDF563E9D1DC43EC37F010C271AB381E541B0734028E3F2B90B31"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-r1-stage-projection-contract.json": (
        "637C5400122874149D9835CC6BC521E5EEC9160222F4A7AC5CA1F6CD99E1BCC4"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-r1-stage-projection-vectors.json": (
        "D8EDF5C0255B40FB6C28BB014C09DC503D2B53665E69C5AA5AB65C744AEA81E4"
    ),
    "tools/phase36_quarantine_runtime_controller_r1_reference.py": (
        "B5C7328CD666E0A8988F9B616C5B2A914D690A40BF2EA289C1F1C755E42B86F0"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-authorization.json": (
        "FC1AE35876012CEFDCB52AE5A274FC5787FAE1AE722A9709AC76782C78C530D1"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-result.json": (
        "C9743F0FC8906E46701E07A01A1C651F4B4B2C0517FAB722A97C1396F40F7303"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-evidence.json": (
        "34BDA40E4450F35AF4A86E3C7566B9AFCA01413D70FE9CA9EB70B35A1B921BFF"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-failure-analysis-r0.json": (
        "F8ED63FB9410B6DCBB37A82A9CF667FF09067CBB502B8F23A213B784DD431667"
    ),
}


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read(path: Path) -> dict[str, object]:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_contract_is_bound_to_exact_consolidated_build_authorization() -> None:
    contract = _read(CONTRACT)

    assert _sha256(AUTHORIZATION_PACKAGE) == AUTHORIZATION_PACKAGE_SHA256
    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["source_build_authorization"] == {
        "decision_id": SOURCE_BUILD_AUTHORIZATION,
        "authorization_package": (
            "contracts/phase-3/"
            "p3-6-consolidated-build-authorization-planning-package.json"
        ),
        "authorization_package_sha256": AUTHORIZATION_PACKAGE_SHA256,
        "selected_options": "A/A/A/A/A/A",
        "canonical_owner_statement_utf8_bytes": 1855,
        "canonical_owner_statement_sha256": (
            "9740F2BD6FBF4D51DF154350788DB702EBE4BE7407C9A4B80C7806DEAE9F9ECC"
        ),
    }
    assert contract["runtime_authorization_decision_id"] == RUNTIME_AUTHORIZATION


def test_contract_has_exact_typed_state_machine_and_wire_fields() -> None:
    contract = _read(CONTRACT)

    assert contract["supported_operations"] == list(SUPPORTED_OPERATIONS)
    assert contract["ordered_stages"] == list(STAGES)
    assert contract["request_schema"]["required_fields"] == list(REQUEST_FIELDS)
    assert contract["result_schema"]["required_fields"] == list(RESULT_FIELDS)
    assert contract["result_schema"]["predicate_flag_fields"] == list(
        PREDICATE_FLAG_FIELDS
    )
    assert contract["stage_failure_reasons"] == STAGE_FAILURE_REASONS
    assert contract["process_policy"] | {"all_observation_counters_nonnegative_integers": True} == contract["process_policy"]
    assert {
        key: contract["process_policy"][key] for key in PROCESS_LIMITS
    } == PROCESS_LIMITS


def test_fixed_parent_contract_uses_exact_ordered_literal_true_reduction() -> None:
    parent = _read(CONTRACT)["fixed_parent_record_schema"]

    assert parent["exact_record_count"] == 3
    assert parent["ordered_parent_indexes"] == list(PARENT_INDEXES)
    assert parent["required_fields"] == list(PARENT_FIELDS)
    assert parent["all_predicates_boolean_typed"] is True
    assert parent["pipeline_filter_count_null_or_scalar_cardinality_semantics_used"] is False
    assert parent["raw_path_ACL_owner_identity_attribute_or_exception_retention"] is False


def test_generated_manifest_has_416_unique_vectors_and_all_required_groups() -> None:
    manifest = _read(VECTORS)
    vectors = manifest["vectors"]

    assert manifest["contract_version"] == CONTRACT_VERSION
    assert manifest["vector_count"] == len(vectors) == 416
    assert manifest["group_counts"] == {group: 32 for group in GROUPS}
    assert Counter(item["group"] for item in vectors) == Counter(
        {group: 32 for group in GROUPS}
    )
    assert len({item["id"] for item in vectors}) == 416
    assert manifest["generator"] == {
        "algorithm": "deterministic_outer_controller_matrix_v1",
        "random_seed": None,
        "external_input_or_data": False,
        "machine_or_runtime_observation": False,
    }


def test_all_package_bound_historical_inputs_remain_byte_exact() -> None:
    for relative, expected in IMMUTABLE_INPUTS.items():
        assert _sha256(ROOT / relative) == expected


def test_new_contract_and_vectors_are_lf_terminated() -> None:
    for path in (CONTRACT, VECTORS):
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload

