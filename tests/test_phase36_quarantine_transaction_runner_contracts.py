from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
RUNNER_PATH = ROOT / "tools" / "phase36_quarantine_transaction_runner.ps1"
VECTORS_PATH = (
    CONTRACTS / "p3-6-quarantine-transaction-runner-r0-contract-tests.json"
)
RUNNER_AUTH_PATH = (
    CONTRACTS
    / "p3-6-quarantine-transaction-runner-r0-implementation-authorization.json"
)
STORAGE_ACCEPTANCE_PATH = (
    CONTRACTS / "p3-6-quarantine-storage-r2-proposal-acceptance.json"
)
RUNNER_AUTH_DIGEST = (
    "CD81871C6B6F560CDC01E9D6AA919B71F9E108DEB3AEA3C04B17BAF28C60D525"
)
STORAGE_ACCEPTANCE_DIGEST = (
    "6F68EB164DC662086F7444D49638FFAB95F7FF1586469BB5E5E2DC876185AAA5"
)
ALLOWED_ACTIONS = [
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
OUTPUT_PATHS = [
    "contracts/phase-3/p3-6-quarantine-storage-r2-authorization.json",
    "contracts/phase-3/p3-6-quarantine-storage-r2-result.json",
    "contracts/phase-3/p3-6-quarantine-storage-r2-evidence.json",
]


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _base_fixture() -> dict[str, object]:
    return {
        "package_digest_match": True,
        "core_hashes_match": True,
        "owner_statement_match": True,
        "authorization_window_valid": True,
        "attempt_unused": True,
        "runner_binding_match": True,
        "runtime_binding_match": True,
        "action_ids": list(ALLOWED_ACTIONS),
        "path_policy": "exact",
        "candidate_volume": "F:",
        "candidate_root": "F:\\HCAM-Quarantine",
        "probe_bytes": 4096,
        "per_action_timeout_seconds": 30,
        "total_timeout_seconds": 120,
        "output_paths": list(OUTPUT_PATHS),
        "forbidden_output_present": False,
        "candidate_absent": True,
        "acl_case": "none",
        "current_process_rights": ["Modify", "Synchronize"],
        "unauthorized_principal": False,
        "inherited_rule": False,
        "deny_rule": False,
        "inheritance_pass": True,
        "propagation_pass": True,
        "access_type_pass": True,
        "probe_case": "none",
    }


def _fixture(vector_id: str) -> dict[str, object]:
    fixture = _base_fixture()
    mutations: dict[str, dict[str, object]] = {
        "R0-T001-PACKAGE-DIGEST-MISMATCH": {"package_digest_match": False},
        "R0-T002-CORE-HASH-MISMATCH": {"core_hashes_match": False},
        "R0-T003-OWNER-STATEMENT-MISMATCH": {"owner_statement_match": False},
        "R0-T004-EXPIRED-OR-CONSUMED": {"authorization_window_valid": False},
        "R0-T005-RUNNER-OR-RUNTIME-BINDING-MISMATCH": {
            "runner_binding_match": False
        },
        "R0-T006-UNKNOWN-ACTION": {
            "action_ids": [*ALLOWED_ACTIONS[:-1], "U3K-A99-UNKNOWN"]
        },
        "R0-T007-MISSING-DUPLICATE-OR-REORDERED-ACTION": {
            "action_ids": [ALLOWED_ACTIONS[0], *ALLOWED_ACTIONS]
        },
        "R0-T008-PATH-OR-LIMIT-OVERRIDE": {"probe_bytes": 8192},
        "R0-T009-B-OR-PROJECT-PATH": {
            "path_policy": "prohibited",
            "candidate_volume": "B:",
        },
        "R0-T010-EXISTING-ROOT": {"candidate_absent": False},
        "R0-T011-MODIFY-SYNCHRONIZE-EXACT": {"acl_case": "exact"},
        "R0-T012-EXCESSIVE-CURRENT-PROCESS-RIGHTS": {
            "acl_case": "excessive",
            "current_process_rights": [
                "Modify",
                "Synchronize",
                "ChangePermissions",
            ],
        },
        "R0-T013-TUPLE-CLASSIFICATION-INDEPENDENCE": {
            "acl_case": "tuple_independence",
            "current_process_rights": ["Modify"],
        },
        "R0-T014-UNAUTHORIZED-PRINCIPAL": {
            "acl_case": "unauthorized",
            "unauthorized_principal": True,
        },
        "R0-T015-INHERITED-DENY-OR-FLAG-MISMATCH": {
            "acl_case": "flags",
            "inherited_rule": True,
        },
        "R0-T016-PROBE-GENERATED-ZERO-RETENTION": {"probe_case": "success"},
        "R0-T017-PROBE-FAILURE-CLEANUP-BOUND": {"probe_case": "failure"},
        "R0-T018-DEFENDER-ACTION-REQUESTED": {
            "action_ids": [*ALLOWED_ACTIONS[:-1], "U3K-A10-DEFENDER-STATUS"]
        },
        "R0-T019-RAW-DATA-IN-OUTPUT": {"forbidden_output_present": True},
        "R0-T020-OUTPUT-PATH-EXPANSION": {
            "output_paths": [*OUTPUT_PATHS, "unsealed-output.json"]
        },
    }
    fixture.update(deepcopy(mutations[vector_id]))
    return fixture


def _evaluate(fixture: dict[str, object]) -> dict[str, object]:
    authority_fields = [
        "package_digest_match",
        "core_hashes_match",
        "owner_statement_match",
        "authorization_window_valid",
        "attempt_unused",
        "runner_binding_match",
        "runtime_binding_match",
    ]
    if not all(fixture[field] is True for field in authority_fields):
        return {"outcome": "deny_before_machine_access"}

    if fixture["action_ids"] != ALLOWED_ACTIONS:
        return {"outcome": "default_deny_before_machine_access"}
    if fixture["path_policy"] == "prohibited":
        return {"outcome": "deny_without_access"}
    if (
        fixture["path_policy"] != "exact"
        or fixture["candidate_volume"] != "F:"
        or fixture["candidate_root"] != "F:\\HCAM-Quarantine"
        or fixture["probe_bytes"] != 4096
        or fixture["per_action_timeout_seconds"] != 30
        or fixture["total_timeout_seconds"] != 120
    ):
        return {"outcome": "deny_before_machine_access"}
    if fixture["output_paths"] != OUTPUT_PATHS:
        return {"outcome": "default_deny_and_no_additional_write"}
    if fixture["forbidden_output_present"] is True:
        return {"outcome": "output_schema_reject_and_fail_closed"}
    if fixture["candidate_absent"] is False:
        return {"outcome": "fail_without_ACL_or_content_modification"}

    if fixture["acl_case"] != "none":
        rights_pass = sorted(set(fixture["current_process_rights"])) == [
            "Modify",
            "Synchronize",
        ]
        if fixture["unauthorized_principal"] is True:
            return {
                "outcome": "rule_count_and_unauthorized_principal_checks_fail",
                "unauthorized_principal_absent": False,
            }
        if (
            fixture["inherited_rule"] is True
            or fixture["deny_rule"] is True
            or fixture["inheritance_pass"] is False
            or fixture["propagation_pass"] is False
            or fixture["access_type_pass"] is False
        ):
            return {"outcome": "overall_DACL_check_fail"}
        if not rights_pass and fixture["acl_case"] == "tuple_independence":
            return {
                "outcome": (
                    "rights_fail_and_unauthorized_principal_absence_remains_true"
                ),
                "unauthorized_principal_absent": True,
            }
        if not rights_pass:
            return {"outcome": "current_process_rights_check_fail"}
        return {"outcome": "current_process_rights_check_pass"}

    if fixture["probe_case"] == "success":
        return {
            "outcome": "two_hash_checks_pass_and_no_probe_content_retained"
        }
    if fixture["probe_case"] == "failure":
        return {
            "outcome": "storage_blocked_no_retry_cleanup_scope_does_not_expand"
        }
    return {"outcome": "contract_valid_no_machine_execution"}


def _sealed_vectors() -> list[dict[str, object]]:
    return _read(VECTORS_PATH)["required_vectors"]


def test_exact_owner_acceptances_are_bounded_and_non_executable() -> None:
    runner = _read(RUNNER_AUTH_PATH)
    storage = _read(STORAGE_ACCEPTANCE_PATH)

    assert _sha256(RUNNER_AUTH_PATH) == RUNNER_AUTH_DIGEST
    assert _sha256(STORAGE_ACCEPTANCE_PATH) == STORAGE_ACCEPTANCE_DIGEST
    assert runner["package_digest_sha256"] == (
        "712B2A424E156659E85066E1D9393CDD6E41263FAC1138588531E49FE1739AE3"
    )
    assert storage["package_digest_sha256"] == (
        "8BC20745C4D00AED19C26D2C5FA82876DFE079427B1A6FA944E52FFA41F26398"
    )
    assert runner["accepted_effect"]["runner_source_implementation_authorized"]
    assert runner["accepted_effect"]["generated_contract_vector_execution_authorized"]
    assert runner["accepted_effect"]["runner_execution_authorized"] is False
    assert runner["accepted_effect"]["F_or_ACL_action_authorized"] is False
    assert storage["accepted_effect"]["storage_R2_design_accepted_as_planning_policy"]
    assert storage["accepted_effect"]["final_U3K_package_preparation_authorized_now"] is False
    assert storage["accepted_effect"]["storage_attempt_authorized"] is False


def test_runner_preserves_contract_surface_and_adds_default_off_storage() -> None:
    source = RUNNER_PATH.read_text(encoding="utf-8")

    assert "[ValidateSet('Contract', 'Storage')]" in source
    assert "$script:AllowedActionIds" in source
    assert "P36_MACHINE_HANDLER_NOT_IMPLEMENTED" not in source
    assert "P36_DEFAULT_DENY_UNKNOWN_ACTION" in source
    assert "if ($Mode -ceq 'Contract')" in source
    assert "Test-P36StorageEnvelope -Request $request" in source
    for action_id in ALLOWED_ACTIONS:
        assert source.count(f"'{action_id}'") >= 2
    for prohibited in [
        "Invoke-Expression",
        "Start-Process",
        "Get-MpComputerStatus",
        "MpCmdRun",
        "WinVerifyTrust",
        "Get-Acl",
        "Set-Acl",
        "System.IO.DriveInfo",
        "FileSystemAclExtensions.CreateDirectory",
    ]:
        assert prohibited not in source


def test_all_sealed_vectors_have_exactly_one_generated_fixture() -> None:
    vectors = _sealed_vectors()
    vector_ids = [item["vector_id"] for item in vectors]

    assert len(vector_ids) == 20
    assert len(set(vector_ids)) == 20
    for vector_id in vector_ids:
        assert _fixture(vector_id)


@pytest.mark.parametrize("vector", _sealed_vectors(), ids=lambda item: item["vector_id"])
def test_generated_contract_vector(vector: dict[str, object]) -> None:
    result = _evaluate(_fixture(vector["vector_id"]))

    assert result["outcome"] == vector["expected_outcome"]


def test_reference_harness_never_models_machine_access_or_execution() -> None:
    for vector in _sealed_vectors():
        fixture = _fixture(vector["vector_id"])
        assert "machine_access" not in fixture
        assert "execute" not in fixture
        assert "secret" not in json.dumps(fixture).lower()
