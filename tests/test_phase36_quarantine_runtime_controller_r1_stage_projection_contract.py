import hashlib
import json
from collections import Counter
from pathlib import Path

from tools.phase36_quarantine_runtime_controller_r1_reference import (
    ACTION_FAILURE_REASONS,
    ACTION_ORDER,
    AUTHORIZATION_DECISION,
    CONTRACT_VERSION,
    FAILURE_REASONS,
    contract_projection,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    ROOT
    / "contracts/phase-3/p3-6-quarantine-runtime-controller-r1-stage-projection-contract.json"
)
VECTORS = (
    ROOT
    / "contracts/phase-3/p3-6-quarantine-runtime-controller-r1-stage-projection-vectors.json"
)
AUTHORIZATION_PACKAGE = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-controller-u3y-stage-projection-source-implementation-authorization-package.json"
)
AUTHORIZATION_PACKAGE_DIGEST = (
    "35086DDC152DDF659097F6841AA364B965E0851833C339DCF2736BEF1AA0940A"
)
EVIDENCE = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-controller-r1-stage-projection-implementation-evidence.json"
)
IMPLEMENTATION_PACKAGE = ROOT / (
    "contracts/phase-3/"
    "p3-6-quarantine-runtime-controller-r1-stage-projection-implementation-package.json"
)
REVIEW = ROOT / (
    "docs/phase-3/"
    "p3-6-quarantine-runtime-controller-r1-stage-projection-evidence-review.md"
)
GROUP_COUNTS = {
    "policy_valid_exact_null_success": 32,
    "empty_string_rejected": 32,
    "missing_field_rejected": 32,
    "wrong_type_rejected": 32,
    "completed_action_bounds": 32,
    "all_eighteen_failure_actions": 32,
    "all_eighteen_failure_reasons": 32,
    "cross_language_canonical_projection": 32,
    "zero_retention_and_closed_gates": 32,
}
IMMUTABLE_INPUTS = {
    "tools/phase36_quarantine_runtime_controller.ps1": (
        "78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB"
    ),
    "tools/phase36_quarantine_runtime_controller_u3v_h1_r1_diagnostic.ps1": (
        "CD868E3F06CA12AC424B2C4C221F6425FCD0DA289C527DED462121333513B1C9"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-contract.json": (
        "F0E41634760E3697F74EA2DEA44E7B2004392557E3167504BD69F2D78A4DC3CB"
    ),
    "contracts/phase-3/p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-evidence.json": (
        "84DC68C3800983AFA65EBB19C99A36D02C3D97CD28F6D937C43CF5292AF12A45"
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


def test_contract_is_bound_to_exact_U3Y_authorization() -> None:
    contract = _read(CONTRACT)
    authorization = _read(AUTHORIZATION_PACKAGE)

    assert _sha256(AUTHORIZATION_PACKAGE) == AUTHORIZATION_PACKAGE_DIGEST
    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["implementation_authorization"]["decision_id"] == (
        AUTHORIZATION_DECISION
    )
    assert contract["implementation_authorization"][
        "authorization_package_sha256"
    ] == AUTHORIZATION_PACKAGE_DIGEST
    assert authorization["decision_id"] == AUTHORIZATION_DECISION
    assert contract["implementation_authorization"][
        "canonical_owner_statement_utf8_bytes"
    ] == 1514


def test_contract_preserves_action_reason_and_wire_field_sets() -> None:
    contract = _read(CONTRACT)
    projection = contract_projection()

    assert contract["action_order"] == list(ACTION_ORDER)
    assert contract["action_failure_reasons"] == ACTION_FAILURE_REASONS
    assert contract["failure_reason_codes"] == list(FAILURE_REASONS)
    assert contract["request_schema"]["required_fields"] == projection[
        "request_fields"
    ]
    assert contract["result_schema"]["required_fields"] == projection[
        "result_fields"
    ]
    assert contract["stage_projection_schema"]["required_fields"] == projection[
        "stage_projection_fields"
    ]


def test_contract_requires_literal_null_success_and_exact_failure_strings() -> None:
    stage = _read(CONTRACT)["stage_projection_schema"]

    assert stage["policy_valid"] == {
        "completed_actions": 18,
        "failed_action": None,
        "failed_stage": None,
        "literal_nulls_constructed_without_string_typed_nullable_boundary": True,
    }
    assert stage["null_and_empty_string_equivalent"] is False
    assert stage["empty_string_valid_on_success"] is False
    assert stage["field_omission_valid"] is False
    assert stage["failure"]["failed_action"] == (
        "exact_nonempty_allowlisted_action"
    )
    assert stage["failure"]["failed_stage"] == (
        "exact_nonempty_reason_mapped_from_failed_action"
    )


def test_generated_manifest_contains_288_unique_vectors_in_nine_groups() -> None:
    manifest = _read(VECTORS)
    vectors = manifest["vectors"]

    assert manifest["contract_version"] == CONTRACT_VERSION
    assert manifest["vector_count"] == len(vectors) == 288
    assert manifest["group_counts"] == GROUP_COUNTS
    assert Counter(vector["group"] for vector in vectors) == Counter(GROUP_COUNTS)
    assert len({vector["id"] for vector in vectors}) == 288
    assert manifest["generator"] == {
        "algorithm": "deterministic_explicit_stage_projection_matrix_v1",
        "random_seed": None,
        "external_input_or_data": False,
        "machine_or_runtime_observation": False,
    }


def test_all_four_historical_inputs_remain_byte_exact() -> None:
    for relative, expected in IMMUTABLE_INPUTS.items():
        assert _sha256(ROOT / relative) == expected


def test_contract_and_vectors_are_LF_only() -> None:
    for path in (CONTRACT, VECTORS):
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload


def test_evidence_and_package_seal_only_nonexecuted_source_scope() -> None:
    evidence = _read(EVIDENCE)
    package = _read(IMPLEMENTATION_PACKAGE)

    assert evidence["implementation_authorization_package_sha256"] == (
        AUTHORIZATION_PACKAGE_DIGEST
    )
    assert evidence["generated_static_validation"]["generated_vectors"] == 288
    assert evidence["generated_static_validation"][
        "Python_reference_branch_coverage_percent"
    ] == 100.0
    assert evidence["generated_static_validation"]["focused_tests_failed"] == 0
    assert evidence["compatibility_transition"]["required"] is True
    assert evidence["compatibility_transition"][
        "source_owner_acceptance_requestable"
    ] is False
    assert not any(evidence["non_observational_boundaries"].values())

    assert package["core_file_count"] == len(package["core_files"]) == 16
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["current_gate_effect"][
        "compatibility_amendment_authorization_pending"
    ] is True
    assert package["current_gate_effect"][
        "owner_source_implementation_acceptance_requestable"
    ] is False
    assert package["current_gate_effect"][
        "PowerShell_parse_import_dot_source_or_execution_authorized"
    ] is False


def test_evidence_review_and_all_eleven_implementation_paths_exist_with_LF() -> None:
    authorization_contract = _read(
        ROOT
        / "contracts/phase-3/"
        "p3-6-quarantine-runtime-controller-r1-stage-projection-source-implementation-contract.json"
    )
    paths = [ROOT / path for path in authorization_contract["exact_future_implementation_paths"]]

    assert len(paths) == len(set(paths)) == 11
    assert all(path.exists() and path.is_file() for path in paths)
    assert "D-P3.6-U3Y-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT" in REVIEW.read_text(
        encoding="utf-8"
    )
    for path in paths:
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload
