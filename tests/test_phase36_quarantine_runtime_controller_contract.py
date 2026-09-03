import json
from collections import Counter
from pathlib import Path

from tools.phase36_quarantine_runtime_controller_reference import (
    ACTION_FAILURE_REASONS,
    ACTION_ORDER,
    CONTRACT_VERSION,
    FAILURE_REASONS,
    contract_projection,
    validate_result,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-contract.json"
)
VECTORS_PATH = (
    ROOT / "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-vectors.json"
)
AUTHORIZATION_PACKAGE_PATH = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-controller-r0-source-implementation-authorization-package.json"
)
AUTHORIZATION_PACKAGE_DIGEST = (
    "3CBE50F50171907E2ADF65B03CD5012E33B759D8BF5B8270694468DD59CBFFFC"
)
GROUP_COUNTS = {
    "request_schema": 32,
    "authorization_and_binding": 24,
    "stage_transitions": 48,
    "redaction_and_prohibited_fields": 32,
    "resource_timeout_and_output_bounds": 24,
    "cross_language_projection": 32,
}


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def _read_strict(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def test_contract_is_bound_to_the_exact_authorization() -> None:
    contract = _read_strict(CONTRACT_PATH)
    authorization_package = _read_strict(AUTHORIZATION_PACKAGE_PATH)

    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["implementation_authorization"]["decision_id"] == (
        "D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-AUTH"
    )
    assert contract["implementation_authorization"]["authorization_package_sha256"] == (
        AUTHORIZATION_PACKAGE_DIGEST
    )
    assert authorization_package["decision_id"] == (
        "D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-AUTH"
    )
    assert authorization_package["implementation_scope_if_exactly_authorized"][
        "minimum_generated_vectors"
    ] == 192


def test_contract_and_reference_sets_are_identical() -> None:
    contract = _read_strict(CONTRACT_PATH)
    projection = contract_projection()

    assert contract["action_order"] == list(ACTION_ORDER)
    assert contract["action_failure_reasons"] == ACTION_FAILURE_REASONS
    assert contract["failure_reason_codes"] == list(FAILURE_REASONS)
    assert contract["request_schema"]["required_fields"] == projection["request_fields"]
    assert contract["result_schema"]["required_fields"] == projection["result_fields"]
    assert contract["request_schema"]["modes"] == projection["modes"]
    assert sorted(contract["prohibited_field_names"]) == projection[
        "prohibited_field_names"
    ]


def test_contract_keeps_every_runtime_and_machine_gate_closed() -> None:
    contract = _read_strict(CONTRACT_PATH)

    assert contract["controller_roles"] == {
        "PowerShell": "authoritative_Windows_machine_controller_source_not_executed",
        "Python": "machine_disabled_portable_policy_reference_and_cross_language_oracle",
        "default_machine_controller": "PowerShell_only",
        "automatic_failover": False,
        "simultaneous_machine_execution": False,
        "Python_machine_fallback": False,
    }
    assert contract["request_schema"]["Preflight_machine_authority_in_R0_source"] is False
    assert not any(contract["terminal_gate_effect"][name] for name in (
        "machine_action_authorized",
        "python_machine_fallback",
        "retry_authorized",
        "U3T_preflight_authorized",
        "U3K_authorized",
        "deployment_authorized",
    ))
    assert not any(contract["implementation_boundaries"].values())


def test_generated_manifest_has_exact_unique_grouped_vectors() -> None:
    manifest = _read_strict(VECTORS_PATH)
    vectors = manifest["vectors"]
    counts = Counter(vector["group"] for vector in vectors)

    assert manifest["contract_version"] == CONTRACT_VERSION
    assert manifest["vector_count"] == 192
    assert manifest["group_counts"] == GROUP_COUNTS
    assert counts == Counter(GROUP_COUNTS)
    assert len(vectors) == len({vector["id"] for vector in vectors}) == 192
    assert manifest["generator"] == {
        "algorithm": "deterministic_explicit_mutation_matrix_v1",
        "random_seed": None,
        "external_input_or_data": False,
        "machine_or_runtime_observation": False,
    }


def test_every_vector_has_one_sanitized_canonical_expected_projection() -> None:
    manifest = _read_strict(VECTORS_PATH)

    for vector in manifest["vectors"]:
        assert set(vector) == {
            "id",
            "group",
            "description",
            "mutation",
            "expected_projection",
        }
        assert validate_result(vector["expected_projection"])
        assert vector["expected_projection"]["terminal"] is True
        assert vector["expected_projection"]["gate_effect"]["machine_action_authorized"] is False
        assert vector["expected_projection"]["retention_projection"][
            "raw_material_retained_bytes"
        ] == 0


def test_all_new_contract_artifacts_are_lf_terminated() -> None:
    for path in (CONTRACT_PATH, VECTORS_PATH):
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload
