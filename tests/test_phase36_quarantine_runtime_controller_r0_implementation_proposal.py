from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-dual-architecture-acceptance.json"
)
CONTRACT = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-contract.json"
)
TEST_PLAN = (
    CONTRACTS / "p3-6-quarantine-runtime-controller-r0-generated-test-plan.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-authorization-proposal.md"
)
IMPLEMENTED_CONTRACT = (
    CONTRACTS / "p3-6-quarantine-runtime-controller-r0-contract.json"
)
IMPLEMENTED_VECTORS = (
    CONTRACTS / "p3-6-quarantine-runtime-controller-r0-vectors.json"
)
IMPLEMENTATION_EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-evidence.json"
)
IMPLEMENTATION_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-package.json"
)
IMPLEMENTATION_REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-evidence-review.md"
)
PACKAGE_DIGEST = (
    "3CBE50F50171907E2ADF65B03CD5012E33B759D8BF5B8270694468DD59CBFFFC"
)
DECISION = "D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-AUTH"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_architecture_acceptance_is_single_exact_and_planning_only() -> None:
    acceptance = _read(ACCEPTANCE)
    statement = acceptance["canonical_owner_statement"]
    assert acceptance["duplicate_transport_copy_count"] == 2
    assert acceptance["duplicate_transport_copies_identical"] is True
    assert acceptance["authorization_multiplication_from_duplicate_copy"] is False
    assert len(statement.encode("utf-8")) == 950
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        "E9FA3C2590A646D4115E04AF10E3F33E8CD3BA02EAF4DBC922F1E277CA5F9D57"
    )
    authority = acceptance["authority_granted"]
    assert authority["prepare_separate_source_only_implementation_authorization_proposal"] is True
    assert authority["source_or_test_implementation"] is False
    assert authority["PowerShell_or_Python_execution"] is False


def test_source_contract_preserves_non_overlapping_controller_authority() -> None:
    contract = _read(CONTRACT)
    powershell = contract["PowerShell_controller_contract"]
    python = contract["Python_reference_controller_contract"]
    assert powershell["future_role"] == "authoritative_Windows_machine_controller"
    assert powershell["implementation_time_role"] == "source_only_never_parsed_imported_or_executed"
    assert python["role"] == "pure_portable_policy_reference_and_cross_language_oracle"
    assert python["machine_API_or_subprocess_surface"] is False
    assert python["Python_machine_fallback"] is False
    assert contract["cross_language_contract"]["projection_difference"] == (
        "terminal_cross_language_projection_diverged"
    )


def test_generated_plan_requires_192_vectors_and_machine_independence() -> None:
    plan = _read(TEST_PLAN)
    assert plan["minimum_vector_count"] == 192
    assert sum(group["minimum_count"] for group in plan["vector_groups"]) == 192
    policy = plan["implementation_time_execution_policy"]
    assert policy["PowerShell_controller_parse_import_or_execution"] is False
    assert policy["Python_machine_API_filesystem_environment_registry_network_native_or_subprocess"] is False
    assert policy["runtime_or_hardware_observation"] is False
    assert plan["acceptance_thresholds"]["Python_reference_branch_coverage_percent"] == 95


def test_authorization_package_binds_inputs_and_grants_zero_current_authority() -> None:
    package = _read(PACKAGE)
    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["decision_id"] == DECISION
    assert package["core_file_count"] == 11
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    gate = package["current_gate_effect"]
    assert gate["owner_implementation_authorization_pending"] is True
    assert gate["D_P3_6_U3S_DUAL_CONTROLLER_R0_IMPLEMENTATION_AUTH_requestable"] is True
    assert gate["source_or_test_implementation_authorized"] is False
    assert gate["Python_pure_reference_or_test_execution_authorized"] is False
    assert gate["PowerShell_parse_import_or_execution_authorized"] is False
    assert gate["runtime_manifest_hardware_or_machine_observation_authorized"] is False
    assert gate["retry_U3T_or_U3K_authorized"] is False


def test_canonical_ledgers_expose_same_pending_package() -> None:
    key = "quarantine_runtime_controller_r0_source_implementation_authorization_package"
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)[key]
        assert state["decision_id"] == DECISION
        assert state["package_digest_sha256"] == PACKAGE_DIGEST
        assert state["owner_implementation_authorization_pending"] is True
        assert state["source_or_test_implementation_authorized"] is False
        assert state["PowerShell_parse_import_or_execution_authorized"] is False
        assert state["runtime_manifest_hardware_or_machine_observation_authorized"] is False

    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_U3S_dual_controller_source_implementation_action"
    ]
    assert action["decision_id"] == DECISION
    assert action["package_digest_sha256"] == PACKAGE_DIGEST
    assert action["U3T_U3R_retry_or_U3K_authorized"] is False


def test_exact_authorized_implementation_paths_are_present_and_non_executable() -> None:
    contract = _read(CONTRACT)
    future_paths = list(contract["future_source_paths"].values())
    future_paths.extend(contract["exact_future_test_paths"])
    future_paths.extend(
        [
            "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-source-implementation-evidence.json",
            "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-source-implementation-package.json",
            "docs/phase-3/p3-6-quarantine-runtime-controller-r0-source-implementation-evidence-review.md",
        ]
    )
    for path in future_paths:
        assert (ROOT / path).is_file()

    evidence = _read(IMPLEMENTATION_EVIDENCE)
    assert evidence["implementation_authorization"][
        "authorization_package_digest_sha256"
    ] == PACKAGE_DIGEST
    assert evidence["compatibility_test_allowlist_amendment"]["authorized_path"] == (
        "tests/test_phase36_quarantine_runtime_controller_r0_implementation_proposal.py"
    )
    assert evidence["non_observational_boundaries"]["PowerShell_parsed"] is False
    assert evidence["non_observational_boundaries"]["PowerShell_imported_or_executed"] is False

    package = _read(IMPLEMENTATION_PACKAGE)
    gate = package["current_gate_effect"]
    assert gate["source_implementation_complete"] is True
    assert gate["owner_source_implementation_acceptance_pending"] is True
    for key in (
        "PowerShell_parse_import_or_execution_authorized",
        "Python_machine_access_or_fallback_authorized",
        "runtime_manifest_hardware_or_machine_observation_authorized",
        "retry_U3T_or_U3K_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ):
        assert gate[key] is False

    assert IMPLEMENTED_CONTRACT.is_file()
    assert IMPLEMENTED_VECTORS.is_file()
    assert IMPLEMENTATION_REVIEW.is_file()


def test_docs_and_line_ending_policy_are_synchronized() -> None:
    for path in (
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert DECISION in text
        assert PACKAGE_DIGEST in text

    review_text = REVIEW.read_text(encoding="utf-8")
    assert "P3.6 U3S Dual Runtime Controller R0" in review_text
    assert "same R1 acceptance statement twice" in review_text
    assert "Repetition does not" in review_text
    assert "create additional authority" in review_text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (ACCEPTANCE, CONTRACT, TEST_PLAN, PROPOSAL, PACKAGE, REVIEW, Path(__file__)):
        relative = path.as_posix().removeprefix(ROOT.as_posix() + "/")
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()
