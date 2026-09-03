from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3x-stage-projection-remediation-planning-acceptance.json"
)
IMPLEMENTATION_CONTRACT = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-stage-projection-source-implementation-contract.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3y-stage-projection-source-implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3y-stage-projection-source-implementation-authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3y-stage-projection-source-implementation-authorization-proposal.md"
)
R1_EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-stage-projection-implementation-evidence.json"
)
R1_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r1-stage-projection-implementation-package.json"
)

U3X_PACKAGE_DIGEST = (
    "80CA25BC1F1EE77E5A9ED8ADEF76C695D5169544CB75B6A57A03692463FFA460"
)
U3X_ACCEPTANCE_DIGEST = (
    "56FE994A8F3EDCB17B673E63CB3773B17EB63FA8B3E23F04A3A58A9E7105D91E"
)
U3X_STATEMENT_DIGEST = (
    "26536D7D4921317528A8F2ED72F6D3D6720CAE767AF2E3531C7B19FFEA26670B"
)
U3Y_PACKAGE_DIGEST = (
    "35086DDC152DDF659097F6841AA364B965E0851833C339DCF2736BEF1AA0940A"
)
U3Y_PROVISIONAL_IMPLEMENTATION_PACKAGE_DIGEST = (
    "643540124398CF4F531597C2EB688BBB5D92F113776A1DFEDBFBF419636BBE5B"
)
U3Y_COMPATIBILITY_AMENDMENT_STATEMENT_DIGEST = (
    "791BD3E84396936CA50C8CCA23392A54C519763827E9CF6C3F5793FB78DCFE7D"
)
U3Y_DECISION = "D-P3.6-U3Y-CONTROLLER-R1-STAGE-PROJECTION-IMPLEMENTATION-AUTH"


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


def test_exact_U3X_acceptance_records_A_A_A_A_and_proposal_only_scope() -> None:
    acceptance = _read(ACCEPTANCE)
    statement = acceptance["canonical_owner_statement"]

    assert _sha256(ACCEPTANCE) == U3X_ACCEPTANCE_DIGEST
    assert acceptance["accepted_package"]["sha256"] == U3X_PACKAGE_DIGEST
    assert acceptance["canonical_owner_statement_utf8_bytes"] == 904
    assert len(statement.encode("utf-8")) == 904
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        U3X_STATEMENT_DIGEST
    )
    assert acceptance["selected_decisions"] == {
        "D-P3.6-U3X-001": "A",
        "D-P3.6-U3X-002": "A",
        "D-P3.6-U3X-003": "A",
        "D-P3.6-U3X-004": "A",
    }
    authority = acceptance["authority_granted"]
    assert authority[
        "prepare_separate_source_only_additive_controller_R1_implementation_authorization_proposal"
    ] is True
    assert authority[
        "controller_diagnostic_contract_vector_test_model_or_product_implementation"
    ] is False
    assert authority["PowerShell_parse_import_dot_source_or_execution"] is False
    assert authority[
        "container_Kubernetes_profile_activation_deployment_another_attempt_U3K_or_remote_Git"
    ] is False


def test_U3Y_package_digest_and_all_eleven_core_bindings_match() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == U3Y_PACKAGE_DIGEST
    assert package["decision_id"] == U3Y_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 11
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["preparation_authority"]["selected_options"] == "A/A/A/A"
    assert package["exact_future_implementation_path_count"] == 11
    assert package["required_generated_vector_minimum"] == 256
    assert package[
        "required_machine_disabled_Python_reference_branch_coverage_percent"
    ] == 95


def test_authorized_implementation_paths_are_present_and_inputs_immutable() -> None:
    contract = _read(IMPLEMENTATION_CONTRACT)
    paths = contract["exact_future_implementation_paths"]

    assert len(paths) == len(set(paths)) == 11
    assert all((ROOT / path).is_file() for path in paths)
    for item in contract["immutable_accepted_inputs"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]

    evidence = _read(R1_EVIDENCE)
    package = _read(R1_PACKAGE)
    transition = evidence["compatibility_transition"]
    statement = evidence["canonical_owner_compatibility_amendment"]

    assert transition["decision_id"] == (
        "D-P3.6-U3Y-COMPATIBILITY-TEST-ALLOWLIST-AMENDMENT"
    )
    assert transition["accepted_provisional_implementation_package_sha256"] == (
        U3Y_PROVISIONAL_IMPLEMENTATION_PACKAGE_DIGEST
    )
    assert transition["allowlisted_existing_path"] == Path(__file__).relative_to(
        ROOT
    ).as_posix()
    assert transition["currently_authorized"] is True
    assert transition["completed"] is True
    assert transition["source_implementation_complete"] is True
    assert transition["source_owner_acceptance_pending"] is True
    assert transition["source_owner_acceptance_requestable"] is False
    assert transition["post_transition_source_owner_acceptance_requestable"] is True
    assert transition["full_suite_clean"] is True

    assert statement["utf8_bytes"] == len(statement["statement"].encode("utf-8")) == 1542
    assert statement["sha256"] == U3Y_COMPATIBILITY_AMENDMENT_STATEMENT_DIGEST
    assert hashlib.sha256(statement["statement"].encode("utf-8")).hexdigest().upper() == (
        U3Y_COMPATIBILITY_AMENDMENT_STATEMENT_DIGEST
    )

    gate = package["current_gate_effect"]
    assert gate["source_implementation_complete"] is True
    assert gate["focused_generated_static_validation_complete"] is True
    assert gate["compatibility_amendment_authorization_pending"] is True
    assert gate["post_transition_compatibility_amendment_authorization_pending"] is False
    assert gate["compatibility_transition_complete"] is True
    assert gate["owner_source_implementation_acceptance_pending"] is True
    assert gate["owner_source_implementation_acceptance_requestable"] is False
    assert gate[
        "post_transition_owner_source_implementation_acceptance_requestable"
    ] is True
    assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert gate["Python_machine_access_or_fallback_authorized"] is False
    assert gate["runtime_or_machine_observation_authorized"] is False
    assert gate["another_attempt_or_U3K_authorized"] is False
    assert gate["deployment_or_remote_Git_authorized"] is False


def test_contract_requires_exact_null_success_and_staged_later_gates() -> None:
    contract = _read(IMPLEMENTATION_CONTRACT)
    semantics = contract["required_wire_semantics"]
    projection = semantics["policy_valid_stage_projection"]

    assert semantics["contract_version"] == "1.0.0"
    assert projection == {
        "completed_actions": 18,
        "failed_action": None,
        "failed_stage": None,
    }
    assert semantics["null_and_empty_string_are_equivalent"] is False
    design = contract["required_successor_design"]
    assert design["additive_successor_not_in_place_historical_edit"] is True
    assert design[
        "success_projection_constructs_literal_nulls_without_string_typed_nullable_boundary"
    ] is True
    evidence = contract["required_generated_static_evidence"]
    assert evidence["minimum_generated_vector_count"] == 256
    assert evidence[
        "minimum_machine_disabled_Python_reference_branch_coverage_percent"
    ] == 95
    later = contract["later_separate_gates"]
    assert later["owner_source_implementation_acceptance_required"] is True
    assert later[
        "generated_only_PowerShell_contract_validation_requires_separate_package_and_authorization"
    ] is True
    assert later[
        "system_diagnostic_requires_successful_contract_validation_acceptance_and_separate_authorization"
    ] is True


def test_U3Y_proposal_is_requestable_but_currently_non_effective() -> None:
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)

    assert proposal["decision_id"] == package["decision_id"] == U3Y_DECISION
    assert proposal["status"] == "non_effective_owner_authorization_pending"
    assert "<U3Y_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in proposal[
        "future_owner_authorization_statement_template"
    ]
    effect = proposal["current_effect"]
    assert effect["owner_U3Y_source_implementation_authorization_pending"] is True
    assert effect[
        "D_P3_6_U3Y_CONTROLLER_R1_STAGE_PROJECTION_IMPLEMENTATION_AUTH_requestable"
    ] is True
    assert effect["source_or_test_implementation_authorized"] is False
    assert effect["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert effect["Python_machine_access_or_fallback_authorized"] is False
    assert effect["runtime_or_machine_observation_authorized"] is False
    assert effect["another_attempt_or_U3K_authorized"] is False
    assert effect["deployment_or_remote_Git_authorized"] is False


def test_canonical_ledgers_append_acceptance_and_pending_U3Y_without_rewriting_U3X() -> None:
    historical_key = (
        "quarantine_runtime_controller_u3x_stage_projection_remediation_planning_package"
    )
    acceptance_key = (
        "quarantine_runtime_controller_u3x_stage_projection_remediation_planning_acceptance"
    )
    package_key = (
        "quarantine_runtime_controller_u3y_stage_projection_source_implementation_authorization_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        assert state[historical_key]["owner_decisions_pending"] is True
        accepted = state[acceptance_key]
        assert accepted["acceptance_record_sha256"] == U3X_ACCEPTANCE_DIGEST
        assert accepted["selected_options"] == "A/A/A/A"
        assert accepted[
            "U3Y_source_implementation_authorization_proposal_preparation_authorized"
        ] is True
        pending = state[package_key]
        assert pending["package_digest_sha256"] == U3Y_PACKAGE_DIGEST
        assert pending["owner_source_implementation_authorization_pending"] is True
        assert pending[
            "D_P3_6_U3Y_CONTROLLER_R1_STAGE_PROJECTION_IMPLEMENTATION_AUTH_requestable"
        ] is True
        assert pending["source_or_test_implementation_authorized"] is False
        assert pending["retry_or_U3K_authorized"] is False


def test_human_records_and_LF_registry_expose_current_gate() -> None:
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
        assert "D-P3.6-U3X" in text
        assert U3X_PACKAGE_DIGEST in text
        assert U3Y_DECISION in text
        assert U3Y_PACKAGE_DIGEST in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    paths = (ACCEPTANCE, IMPLEMENTATION_CONTRACT, PROPOSAL, PACKAGE, REVIEW, Path(__file__))
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()
