from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

U3Y_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-stage-projection-implementation-package.json"
)
U3Y_ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-stage-projection-implementation-acceptance.json"
)
PLANNING_CONTRACT = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-planning-contract.json"
)
AUTHORIZATION_PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-source-implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-planning-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-proposal.md"
)

U3Y_PACKAGE_DIGEST = (
    "ED306CDFAA604675DAC42AF3137C566EC82EC2BEBCA9B68BE60DE4B8D6D1DC78"
)
U3Y_ACCEPTANCE_DIGEST = (
    "1D4F58F792CDA447E0DB369924BB2004F6CC7300484D2660755FC545ABC3C1F5"
)
U3Y_STATEMENT_DIGEST = (
    "0C000AEE9AD45DD2301CB32D57B96BC1493BEA2D133D6E1CB8707FEB0C52CBCE"
)
U3Z_PACKAGE_DIGEST = (
    "B9696A95EF14D186C7D2CC8D949EE711C2621E907DAD28AF4FC192B2A1A1F09A"
)
U3Y_DECISION = (
    "D-P3.6-U3Y-CONTROLLER-R1-STAGE-PROJECTION-IMPLEMENTATION-ACCEPTANCE"
)
U3Z_DECISION = (
    "D-P3.6-U3Z-CONTROLLER-R1-GENERATED-CONTRACT-VALIDATION-HARNESS-IMPLEMENTATION-AUTH"
)


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


def test_exact_U3Y_acceptance_is_bound_and_non_executable() -> None:
    acceptance = _read(U3Y_ACCEPTANCE)
    statement = acceptance["canonical_owner_statement"]

    assert _sha256(U3Y_PACKAGE) == U3Y_PACKAGE_DIGEST
    assert _sha256(U3Y_ACCEPTANCE) == U3Y_ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == U3Y_DECISION
    assert acceptance["accepted_package"]["sha256"] == U3Y_PACKAGE_DIGEST
    assert acceptance["canonical_owner_statement_utf8_bytes"] == 1446
    assert len(statement.encode("utf-8")) == 1446
    assert acceptance["canonical_owner_statement_sha256"] == U3Y_STATEMENT_DIGEST
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        U3Y_STATEMENT_DIGEST
    )

    for item in acceptance["accepted_artifacts"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]

    effect = acceptance["accepted_effect"]
    assert effect["U3Y_source_and_generated_static_evidence_accepted"] is True
    assert effect[
        "prepare_separate_non_effective_U3Z_generated_PowerShell_contract_validation_planning_and_authorization_proposal"
    ] is True
    assert effect["U3Z_harness_or_test_implementation_authorized"] is False
    assert effect[
        "PowerShell_parse_import_dot_source_or_execution_authorized"
    ] is False
    assert effect["runtime_manifest_hardware_or_machine_observation_authorized"] is False
    assert effect[
        "container_Kubernetes_profile_activation_deployment_attempt_U3K_commit_push_or_remote_Git_authorized"
    ] is False


def test_U3Z_planning_contract_separates_source_and_runtime_gates() -> None:
    contract = _read(PLANNING_CONTRACT)

    assert [gate["gate"] for gate in contract["two_future_gates"]] == [
        "U3Z_H1_SOURCE_HARNESS",
        "U3Z_R1_RUNTIME_BOUND_GENERATED_VALIDATION",
    ]
    harness = contract["H1_harness_contract"]
    assert harness["request_mode"] == "Policy"
    assert harness["controller_Preflight_machine_authority"] is False
    assert harness["exact_generated_case_count"] == 288
    assert harness["exact_success_projection"] == {
        "completed_actions": 18,
        "failed_action": None,
        "failed_stage": None,
    }

    vectors = contract["H1_generated_vector_plan"]
    assert vectors["exact_vectors"] == 288
    assert len(vectors["groups"]) == 9
    assert set(vectors["groups"].values()) == {32}
    assert sum(vectors["groups"].values()) == 288
    assert vectors["all_generated_only"] is True

    runtime = contract["future_R1_runtime_binding_policy"]
    assert runtime["candidate_path_is_planning_data_not_current_runtime_evidence"] is True
    assert runtime["maximum_runtime_processes"] == 1
    assert runtime["maximum_attempts"] == 1
    assert runtime["automatic_retry"] is False
    assert runtime["process_timeout_seconds"] == 120


def test_U3Z_package_is_sealed_requestable_and_non_effective() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == U3Z_PACKAGE_DIGEST
    assert package["decision_id"] == U3Z_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 11
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]

    gate = package["current_gate_effect"]
    assert gate["package_prepared"] is True
    assert gate["U3Y_source_implementation_accepted"] is True
    assert gate[
        "owner_U3Z_H1_source_harness_implementation_authorization_pending"
    ] is True
    assert gate[
        "D_P3_6_U3Z_CONTROLLER_R1_GENERATED_CONTRACT_VALIDATION_HARNESS_IMPLEMENTATION_AUTH_requestable"
    ] is True
    for key in (
        "U3Z_H1_source_or_test_implementation_authorized",
        "PowerShell_parse_import_dot_source_or_execution_authorized",
        "Python_machine_access_or_fallback_authorized",
        "runtime_manifest_hardware_or_machine_observation_authorized",
        "generated_validation_attempt_or_U3K_authorized",
        "deployment_commit_push_or_remote_Git_authorized",
    ):
        assert gate[key] is False


def test_future_U3Z_H1_paths_are_unique_and_transitioned() -> None:
    contract = _read(PLANNING_CONTRACT)
    proposal = _read(AUTHORIZATION_PROPOSAL)
    paths = proposal["exact_future_implementation_paths"]

    assert len(paths) == len(set(paths)) == 6
    assert sorted(contract["future_H1_source_paths"].values()) == sorted(paths)
    assert all((ROOT / path).is_file() for path in paths)
    implementation_key = (
        "quarantine_runtime_controller_u3z_generated_contract_validation_r0_harness_implementation"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        implementation = _read(CONTRACTS / name)[implementation_key]
        assert implementation["source_implementation_complete"] is True
        assert implementation["compatibility_transition_recorded"] is True
        assert implementation["compatibility_transition_pending"] is False
        assert implementation["owner_implementation_acceptance_pending"] is True
        assert implementation[
            "PowerShell_parse_import_dot_source_or_execution_authorized"
        ] is False
        assert implementation[
            "runtime_binding_or_generated_validation_attempt_authorized"
        ] is False
        assert implementation[
            "U3K_deployment_commit_push_or_remote_git_authorized"
        ] is False
    assert proposal["decision_id"] == U3Z_DECISION
    assert "<U3Z_H1_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in proposal[
        "future_owner_authorization_statement_template"
    ]
    assert proposal["current_effect"][
        "U3Z_H1_source_or_test_implementation_authorized"
    ] is False
    assert proposal[
        "authorization_may_be_inferred_from_U3Y_acceptance_continue_silence_or_proposal_preparation"
    ] is False


def test_canonical_ledgers_expose_U3Y_acceptance_and_pending_U3Z() -> None:
    acceptance_key = (
        "quarantine_runtime_controller_r1_stage_projection_implementation_acceptance"
    )
    package_key = (
        "quarantine_runtime_controller_u3z_generated_contract_validation_r0_planning_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        acceptance = state[acceptance_key]
        assert acceptance["owner_decision_id"] == U3Y_DECISION
        assert acceptance["acceptance_record_sha256"] == U3Y_ACCEPTANCE_DIGEST
        assert acceptance["accepted_package_digest_sha256"] == U3Y_PACKAGE_DIGEST
        assert acceptance[
            "U3Z_planning_and_authorization_proposal_preparation_authorized"
        ] is True
        assert acceptance["U3Z_harness_or_test_implementation_authorized"] is False

        pending = state[package_key]
        assert pending["owner_decision_id"] == U3Z_DECISION
        assert pending["package_digest_sha256"] == U3Z_PACKAGE_DIGEST
        assert pending["exact_future_implementation_path_count"] == 6
        assert pending["exact_materialized_generated_vector_count"] == 288
        assert pending[
            "owner_U3Z_H1_source_harness_implementation_authorization_pending"
        ] is True
        assert pending[
            "D_P3_6_U3Z_CONTROLLER_R1_GENERATED_CONTRACT_VALIDATION_HARNESS_IMPLEMENTATION_AUTH_requestable"
        ] is True
        assert pending["U3Z_H1_source_or_test_implementation_authorized"] is False
        assert pending[
            "PowerShell_parse_import_dot_source_or_execution_authorized"
        ] is False
        assert pending["generated_validation_attempt_or_U3K_authorized"] is False
        assert pending["deployment_commit_push_or_remote_git_authorized"] is False


def test_human_records_and_LF_registry_are_synchronized() -> None:
    human_records = (
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
    )
    for path in human_records:
        text = path.read_text(encoding="utf-8")
        assert U3Y_DECISION in text
        assert U3Y_PACKAGE_DIGEST in text
        assert U3Z_DECISION in text
        assert U3Z_PACKAGE_DIGEST in text

    review = REVIEW.read_text(encoding="utf-8")
    assert "Gate H1: Source Harness" in review
    assert "Gate R1: Future Runtime-Bound Validation" in review
    assert "does not authorize that" in review

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    paths = (
        U3Y_ACCEPTANCE,
        PLANNING_CONTRACT,
        AUTHORIZATION_PROPOSAL,
        PACKAGE,
        REVIEW,
        Path(__file__),
    )
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()
