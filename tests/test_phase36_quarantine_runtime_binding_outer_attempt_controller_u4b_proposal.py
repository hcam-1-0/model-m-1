from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u4a-binding-classification-remediation-planning-acceptance.json"
)
IMPLEMENTATION_CONTRACT = (
    CONTRACTS
    / "p3-6-quarantine-runtime-binding-outer-attempt-controller-r0-source-implementation-contract.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u4b-outer-attempt-controller-r0-source-implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u4b-outer-attempt-controller-r0-source-implementation-authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u4b-outer-attempt-controller-r0-source-implementation-authorization-proposal.md"
)

U4A_PACKAGE_DIGEST = "0918CD9775DA870C530233BD8728325164159A53777A42FAA8DB5B4A7C8DA5D9"
U4A_ACCEPTANCE_DIGEST = (
    "F8C39C761A8B0359CDB50F13AF0935A481C8A881A02A6F325E722137FCB75E36"
)
U4A_STATEMENT_DIGEST = (
    "EE16DBC0A50E6B0CC9C4A656988F37C5C1236C3F7EEB1A79F5B7D12021502927"
)
U4B_PACKAGE_DIGEST = "E52680B8314FA9A4FC862510BC9570DE3942A791952F22425E61ED61723222AE"
U4B_DECISION = "D-P3.6-U4B-OUTER-ATTEMPT-CONTROLLER-R0-IMPLEMENTATION-AUTH"


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


def test_exact_U4A_acceptance_records_A_A_A_A_and_proposal_only_scope() -> None:
    acceptance = _read(ACCEPTANCE)
    statement = acceptance["canonical_owner_statement"]

    assert _sha256(ACCEPTANCE) == U4A_ACCEPTANCE_DIGEST
    assert acceptance["accepted_package"]["sha256"] == U4A_PACKAGE_DIGEST
    assert acceptance["canonical_owner_statement_utf8_bytes"] == 966
    assert len(statement.encode("utf-8")) == 966
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        U4A_STATEMENT_DIGEST
    )
    assert acceptance["selected_decisions"] == {
        "D-P3.6-U4A-001": "A",
        "D-P3.6-U4A-002": "A",
        "D-P3.6-U4A-003": "A",
        "D-P3.6-U4A-004": "A",
    }
    authority = acceptance["authority_granted"]
    assert authority[
        "prepare_separate_source_only_additive_outer_attempt_controller_implementation_authorization_proposal"
    ] is True
    assert authority[
        "outer_controller_harness_contract_vector_test_model_or_product_implementation"
    ] is False
    assert authority["PowerShell_parse_import_dot_source_or_execution"] is False
    assert authority[
        "container_Kubernetes_profile_activation_deployment_another_attempt_U3K_commit_push_or_remote_Git"
    ] is False


def test_U4B_package_digest_and_all_seventeen_core_bindings_match() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == U4B_PACKAGE_DIGEST
    assert package["decision_id"] == U4B_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 17
    assert len({item["path"] for item in package["core_files"]}) == 17
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["preparation_authority"]["selected_options"] == "A/A/A/A"
    assert package["exact_future_implementation_path_count"] == 11
    assert package["bounded_existing_synchronization_path_count"] == 13
    assert package["required_generated_vector_minimum"] == 384
    assert package[
        "required_machine_disabled_Python_reference_branch_coverage_percent"
    ] == 95


def test_contract_binds_immutable_inputs_and_exact_implemented_surface() -> None:
    contract = _read(IMPLEMENTATION_CONTRACT)
    immutable = contract["immutable_accepted_inputs"]
    future_paths = contract["exact_future_implementation_paths"]
    sync_paths = contract["bounded_existing_synchronization_paths"]

    assert len(immutable) == len({item["path"] for item in immutable}) == 10
    for item in immutable:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert len(future_paths) == len(set(future_paths)) == 11
    assert len(sync_paths) == len(set(sync_paths)) == 13
    assert all((ROOT / path).exists() and (ROOT / path).is_file() for path in future_paths)
    assert all((ROOT / path).exists() for path in sync_paths)


def test_contract_requires_typed_state_machine_and_fixed_three_parent_reduction() -> None:
    contract = _read(IMPLEMENTATION_CONTRACT)
    architecture = contract["required_controller_architecture"]
    state_machine = contract["required_typed_state_machine"]
    parents = contract["required_fixed_parent_contract"]
    taxonomy = contract["required_sanitized_taxonomy"]

    assert architecture["PowerShell_is_authoritative_Windows_machine_controller"] is True
    assert architecture["Python_is_machine_disabled_policy_reference_and_cross_language_oracle"] is True
    assert architecture["supported_operation_allowlist"] == [
        "generated_contract_validation_v1"
    ]
    assert architecture["unknown_operation_or_stage_default_denied"] is True
    assert len(state_machine["ordered_stages"]) == 11
    assert state_machine["stage_skipping"] is False
    assert state_machine["retry_requires_new_digest_bound_authorization"] is True
    assert parents["exact_record_count"] == 3
    assert parents["ordered_parent_indexes"] == [0, 1, 2]
    assert parents["all_predicates_boolean_typed"] is True
    assert parents[
        "pipeline_filter_count_null_or_scalar_cardinality_semantics_used"
    ] is False
    assert parents["paths_ACLs_owner_identity_raw_attributes_or_exceptions_retained"] is False
    assert taxonomy["allowlisted_stages_only"] is True
    assert taxonomy["parent_index_values"] == [0, 1, 2]
    assert taxonomy[
        "raw_path_output_exception_fixture_environment_identity_or_security_material"
    ] is False


def test_U4B_proposal_is_requestable_but_currently_non_effective() -> None:
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)

    assert proposal["decision_id"] == package["decision_id"] == U4B_DECISION
    assert proposal["status"] == "non_effective_owner_authorization_pending"
    assert "<U4B_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in proposal[
        "future_owner_authorization_statement_template"
    ]
    effect = proposal["current_effect"]
    assert effect["owner_U4B_source_implementation_authorization_pending"] is True
    assert effect[
        "D_P3_6_U4B_OUTER_ATTEMPT_CONTROLLER_R0_IMPLEMENTATION_AUTH_requestable"
    ] is True
    assert effect["source_contract_vector_or_test_implementation_authorized"] is False
    assert effect["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert effect["Python_machine_access_or_fallback_authorized"] is False
    assert effect["runtime_or_machine_observation_authorized"] is False
    assert effect["another_attempt_or_U3K_authorized"] is False
    assert effect["deployment_commit_push_or_remote_Git_authorized"] is False


def test_canonical_ledgers_append_U4A_acceptance_and_pending_U4B() -> None:
    historical_key = (
        "quarantine_runtime_controller_u4a_binding_classification_remediation_planning_package"
    )
    acceptance_key = (
        "quarantine_runtime_controller_u4a_binding_classification_remediation_planning_acceptance"
    )
    package_key = (
        "quarantine_runtime_controller_u4b_outer_attempt_controller_r0_source_implementation_authorization_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        assert state[historical_key]["owner_decisions_pending"] is True
        accepted = state[acceptance_key]
        assert accepted["acceptance_record_sha256"] == U4A_ACCEPTANCE_DIGEST
        assert accepted["selected_options"] == "A/A/A/A"
        assert accepted[
            "U4B_source_implementation_authorization_proposal_preparation_authorized"
        ] is True
        pending = state[package_key]
        assert pending["package_digest_sha256"] == U4B_PACKAGE_DIGEST
        assert pending["owner_source_implementation_authorization_pending"] is True
        assert pending[
            "D_P3_6_U4B_OUTER_ATTEMPT_CONTROLLER_R0_IMPLEMENTATION_AUTH_requestable"
        ] is True
        assert pending["source_contract_vector_or_test_implementation_authorized"] is False
        assert pending["retry_or_U3K_authorized"] is False


def test_human_records_and_LF_registry_expose_current_U4B_gate() -> None:
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
        assert "D-P3.6-U4A" in text
        assert U4A_PACKAGE_DIGEST in text
        assert U4B_DECISION in text
        assert U4B_PACKAGE_DIGEST in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    paths = (ACCEPTANCE, IMPLEMENTATION_CONTRACT, PROPOSAL, PACKAGE, REVIEW, Path(__file__))
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()
