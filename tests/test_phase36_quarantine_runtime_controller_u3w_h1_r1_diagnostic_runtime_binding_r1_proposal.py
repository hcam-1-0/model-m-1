from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3v-h1-r1-diagnostic-implementation-acceptance.json"
)
ACTION_SPEC = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-action-spec.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3w-h1-r1-diagnostic-runtime-binding-r1-authorization-proposal.md"
)

U3V_ACCEPTANCE_DECISION = (
    "D-P3.6-U3V-H1-R1-DIAGNOSTIC-IMPLEMENTATION-ACCEPTANCE"
)
U3W_DECISION = "D-P3.6-U3W-H1-R1-DIAGNOSTIC-RUNTIME-BINDING-R1-AUTH"
U3V_PACKAGE_DIGEST = "AB6861A7A3074BD12B36AFE7B8B88BE58EB0A643583D577E586BE1B785E6F0BD"
U3V_ACCEPTANCE_DIGEST = (
    "5B8847FF5E484C40D0630C2E9B91D41D877662D27648BCB951962117C25B7DD5"
)
U3W_PACKAGE_DIGEST = "DDCB7A9C4E6E93BF5252FAFF840E3841C1B9080FE5657AA0037532EE2037B760"
OWNER_STATEMENT_DIGEST = (
    "1A0BC9A1742469A73B1319B22A3513EEA4FE82A05D2D9912667301ECAA3F9866"
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


def test_exact_U3V_acceptance_is_bound_and_grants_proposal_preparation_only() -> None:
    acceptance = _read(ACCEPTANCE)

    assert _sha256(ACCEPTANCE) == U3V_ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == U3V_ACCEPTANCE_DECISION
    assert acceptance["accepted_package"]["sha256"] == U3V_PACKAGE_DIGEST
    assert acceptance["accepted_commit"] == "cacc1cd482ca202500dfeab422efe53451c1cd8b"
    statement = acceptance["canonical_owner_statement"]
    assert len(statement.encode("utf-8")) == 1295
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        OWNER_STATEMENT_DIGEST
    )
    effect = acceptance["accepted_effect"]
    assert effect["U3V_source_and_generated_static_evidence_accepted"] is True
    assert (
        effect[
            "prepare_separate_non_effective_U3W_runtime_diagnostic_authorization_proposal"
        ]
        is True
    )
    assert effect["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert effect["U3W_attempt_or_U3K_authorized"] is False


def test_U3W_package_is_digest_bound_and_all_core_files_match() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == U3W_PACKAGE_DIGEST
    assert package["decision_id"] == U3W_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 11
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_U3W_attempt_contract_is_single_use_bounded_and_default_deny() -> None:
    spec = _read(ACTION_SPEC)
    bounds = spec["authorization_and_attempt_bounds"]
    runtime = spec["exact_runtime_binding"]
    process = spec["exact_process_contract"]

    assert spec["future_authorization_decision_id"] == U3W_DECISION
    assert bounds["maximum_attempts"] == bounds["maximum_processes"] == 1
    assert bounds["authorization_window_seconds"] == 86400
    assert bounds["process_timeout_seconds"] == 30
    assert bounds["maximum_stdout_bytes"] == 4096
    assert bounds["maximum_stderr_bytes"] == 0
    assert bounds["maximum_result_record_bytes"] == 16384
    assert bounds["automatic_retry"] is bounds["parallel_attempts"] is False
    assert bounds["raw_stdout_or_stderr_persisted"] is False
    assert runtime["runtime_path"] == "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    assert runtime["fixed_parent_component_count"] == 3
    assert runtime["alternate_runtime_parent_or_discovery_allowed"] is False
    assert process["arguments"][:4] == ["-NoLogo", "-NoProfile", "-NonInteractive", "-File"]


def test_U3W_source_bindings_taxonomy_and_success_policy_are_exact() -> None:
    spec = _read(ACTION_SPEC)
    bindings = {item["path"]: item["sha256"] for item in spec["exact_source_bindings"]}

    assert len(bindings) == 5
    for relative, expected in bindings.items():
        assert _sha256(ROOT / relative) == expected
    assert spec["allowlisted_terminal_reason_codes"] == [
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
    ]
    success = spec["success_policy"]
    assert success["required_reason_code"] == "controller_projection_valid"
    assert success["required_controller_reason_family"] == "policy_valid"
    assert success["required_checked_group_count"] == 8
    assert success["required_raw_controller_material_retained_bytes"] == 0
    assert success["required_machine_action_authorized"] is False
    assert success["required_U3K_authorized"] is False


def test_U3W_proposal_and_package_grant_zero_current_authority() -> None:
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)

    assert proposal["decision_id"] == U3W_DECISION
    assert "<U3W_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in (
        proposal["future_owner_authorization_statement_template"]
    )
    assert (
        proposal[
            "authorization_may_be_inferred_from_U3V_acceptance_continue_package_preparation_or_static_validation"
        ]
        is False
    )
    for gate in (proposal["current_effect"], package["current_gate_effect"]):
        assert gate["owner_U3W_authorization_pending"] is True
        assert gate["attempts_authorized"] == 0
        assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
        assert gate["runtime_parent_manifest_hardware_or_machine_observation_authorized"] is False
        assert gate["Python_machine_access_or_fallback_authorized"] is False


def test_canonical_ledgers_expose_U3V_acceptance_and_pending_U3W_package() -> None:
    acceptance_key = (
        "quarantine_runtime_controller_u3v_h1_r1_diagnostic_implementation_acceptance"
    )
    package_key = (
        "quarantine_runtime_controller_u3w_h1_r1_diagnostic_runtime_binding_r1_authorization_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        acceptance = state[acceptance_key]
        assert acceptance["owner_decision_id"] == U3V_ACCEPTANCE_DECISION
        assert acceptance["acceptance_record_sha256"] == U3V_ACCEPTANCE_DIGEST
        assert acceptance["accepted_implementation_package_sha256"] == U3V_PACKAGE_DIGEST
        assert acceptance["U3V_source_and_generated_static_evidence_accepted"] is True
        assert acceptance["U3W_attempt_U3K_or_remote_git_authorized"] is False

        pending = state[package_key]
        assert pending["owner_decision_id"] == U3W_DECISION
        assert pending["package_digest_sha256"] == U3W_PACKAGE_DIGEST
        assert pending["owner_U3W_authorization_pending"] is True
        assert pending[
            "D_P3_6_U3W_H1_R1_DIAGNOSTIC_RUNTIME_BINDING_R1_AUTH_requestable"
        ] is True
        assert pending["attempts_authorized"] == pending["attempts_consumed"] == 0
        assert pending["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
        assert pending["another_attempt_U3K_or_remote_git_authorized"] is False


def test_human_records_LF_policy_and_consumed_outputs_are_sealed() -> None:
    index_paths = (
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
    for path in index_paths:
        text = path.read_text(encoding="utf-8")
        assert U3V_ACCEPTANCE_DECISION in text
        assert U3W_DECISION in text
        assert U3W_PACKAGE_DIGEST in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (ACCEPTANCE, ACTION_SPEC, PROPOSAL, PACKAGE, REVIEW, Path(__file__)):
        relative = path.relative_to(ROOT).as_posix()
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()

    outputs = [ROOT / relative for relative in _read(ACTION_SPEC)["exact_future_outputs"]]
    assert [_sha256(path) for path in outputs] == [
        "6471C2CBB298D2090B789037FDCBFB20B843A565D470E0D8C2D0609DE71A0E7D",
        "1B2DA0107938D21AF003DE40CC9B1405D81A5B9C00843B2D7FBB1867F17926EE",
        "84DC68C3800983AFA65EBB19C99A36D02C3D97CD28F6D937C43CF5292AF12A45",
    ]
    authorization, result, evidence = (_read(path) for path in outputs)
    assert authorization["effective_for_attempt"] is False
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert result["reason_code"] == "controller_stage_projection_invalid"
    assert evidence["gate_effect"]["authorization_reusable"] is False
