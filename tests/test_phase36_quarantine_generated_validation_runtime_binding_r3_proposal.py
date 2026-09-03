from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

RESEARCH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r3-research-"
    "sources.json"
)
ACTION_SPEC = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r3-action-spec.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r3-authorization-"
    "proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r3-authorization-"
    "package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-generated-validation-runtime-binding-r3-authorization-"
    "proposal.md"
)

DECISION = "D-P3.6-U3R-GENERATED-VALIDATION-RUNTIME-BINDING-R3-AUTH"
PACKAGE_DIGEST = (
    "A912EF51629A3E73FFF2ECE7AAB8A7D3017A659F9FB75F5402A90027D4B53D98"
)
ACCEPTANCE_DIGEST = (
    "32BA42A51029920AE163866A923547CD16054D6C41ECD3C8EC5549B78FB3ED2E"
)
HARNESS_DIGEST = (
    "830D88F8915B084DEF1089927FF785C9C0E7BDB6F0755B5315EE85E9DA8A8B8A"
)
VECTOR_DIGEST = (
    "5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C"
)
RUNNER_DIGEST = (
    "22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A"
)
HANDLER_DIGEST = (
    "41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721"
)
ADAPTER_DIGEST = (
    "232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9"
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


def test_package_is_digest_bound_and_all_core_files_match() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["decision_id"] == DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 17
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_U3Q_acceptance_is_the_only_planning_authority() -> None:
    for record in (_read(RESEARCH), _read(ACTION_SPEC), _read(PROPOSAL), _read(PACKAGE)):
        authority = record["preparation_authority"]
        acceptance_hash = authority.get(
            "acceptance_sha256", authority.get("acceptance_record_sha256")
        )
        assert authority["decision_id"] == (
            "D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-"
            "IMPLEMENTATION-ACCEPTANCE"
        )
        assert acceptance_hash == ACCEPTANCE_DIGEST


def test_exact_runtime_and_Utility_manifest_have_no_discovery_surface() -> None:
    spec = _read(ACTION_SPEC)
    runtime = spec["exact_runtime_candidate"]
    manifest = spec["exact_Utility_manifest_candidate"]

    assert runtime["path"] == "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    assert runtime["PSHome"] == "C:\\Program Files\\PowerShell\\7"
    assert runtime["alternate_discovery"] is False
    assert runtime["PATH_registry_WMI_package_directory_or_hardware_inventory"] is False
    assert manifest["path"].endswith(
        "Modules\\Microsoft.PowerShell.Utility\\Microsoft.PowerShell.Utility.psd1"
    )
    assert manifest["maximum_manifest_bytes"] == 131072
    assert manifest["alternate_module_name_PSModulePath_registry_or_directory_search"] is False


def test_Utility_manifest_closure_is_literal_contained_bounded_and_trusted() -> None:
    spec = _read(ACTION_SPEC)
    analysis = spec["Utility_manifest_static_analysis"]
    bounds = spec["Utility_closure_bounds"]

    assert analysis["parser"] == "System.Management.Automation.Language.Parser.ParseFile"
    assert analysis["execution_or_semantic_evaluation"] is False
    assert analysis["required_top_level_shape"] == "single_literal_hashtable"
    assert analysis["ScriptsToProcess_must_be_empty"] is True
    assert analysis["all_resolved_paths_must_remain_under_exact_PSHome"] is True
    assert analysis[
        "commands_scriptblocks_interpolation_environment_expansion_wildcards_or_expressions_allowed"
    ] is False
    assert bounds["maximum_declared_regular_files"] == 64
    assert bounds["maximum_individual_file_bytes"] == 67108864
    assert bounds["maximum_total_file_bytes"] == 134217728
    assert bounds["directories_or_files_with_reparse_points_allowed"] is False
    assert bounds[
        "load_bearing_code_requires_cache_only_no_UI_whole_chain_excluding_root_trust"
    ] is True
    assert bounds["trust_retrieval_allowed"] is False


def test_action_sequence_is_exact_single_attempt_and_default_deny() -> None:
    spec = _read(ACTION_SPEC)
    actions = spec["exact_action_sequence"]

    assert spec["maximum_attempts"] == 1
    assert spec["authorization_window_seconds"] == 86400
    assert spec["failed_attempt_consumes_authorization"] is True
    assert spec["automatic_retry"] is False
    assert spec["parallel_processes"] is False
    assert [item["action_id"] for item in actions] == [
        "U3R-A01-PACKAGE-AUTHORITY-PREFLIGHT",
        "U3R-A02-AUTHORIZATION-RECORD",
        "U3R-A03-RUNTIME-PATH-CLASSIFY",
        "U3R-A04-RUNTIME-BIND",
        "U3R-A05-UTILITY-MANIFEST-CLASSIFY",
        "U3R-A06-UTILITY-CLOSURE-BIND",
        "U3R-A07-SOURCE-BINDINGS-PREFLIGHT",
        "U3R-A08-GENERATED-VALIDATION",
        "U3R-A09-SANITIZED-RESULT-CLASSIFICATION",
        "U3R-A10-POSTEXECUTION-BINDING",
        "U3R-A11-SANITIZED-EVIDENCE",
    ]
    assert actions[7]["runner_mode"] == "Contract_only"
    assert actions[7]["windows_adapter_role"].endswith("never_import_or_execute")


def test_inputs_arguments_outputs_and_success_contract_are_exact() -> None:
    spec = _read(ACTION_SPEC)
    inputs = {item["path"]: item["sha256"] for item in spec["exact_accepted_inputs"]}

    assert inputs == {
        "tools/phase36_quarantine_generated_validation.ps1": HARNESS_DIGEST,
        "contracts/phase-3/"
        "p3-6-quarantine-generated-powershell-validation-r0-vectors.json": (
            VECTOR_DIGEST
        ),
        "tools/phase36_quarantine_transaction_runner.ps1": RUNNER_DIGEST,
        "tools/phase36_quarantine_machine_handlers.psm1": HANDLER_DIGEST,
        "tools/phase36_quarantine_windows_storage_adapter.psm1": ADAPTER_DIGEST,
    }
    assert spec["exact_runtime_arguments"][-2:] == [
        "-ExpectedVectorManifestSha256",
        VECTOR_DIGEST,
    ]
    assert len(spec["exact_future_outputs"]) == 3
    expectations = spec["validation_expectations"]
    assert expectations["total_generated_vectors_required_and_passed"] == 84
    assert expectations["runner_Storage_invocation_count"] == 0
    assert expectations["windows_adapter_import_or_execution_count"] == 0


def test_proposal_requests_exact_owner_authorization_without_inference() -> None:
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)

    assert proposal["decision_id"] == DECISION
    assert "<U3R_R3_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in proposal[
        "future_owner_authorization_statement_template"
    ]
    assert proposal[
        "authorization_may_be_inferred_from_acceptance_continue_package_preparation_or_static_validation"
    ] is False
    assert package["current_gate_effect"][
        "D_P3_6_U3R_GENERATED_VALIDATION_RUNTIME_BINDING_R3_AUTH_requestable"
    ] is True
    assert package["current_gate_effect"]["attempts_authorized"] == 0
    assert package["current_gate_effect"][
        "PowerShell_parser_import_or_execution_authorized"
    ] is False


def test_canonical_ledgers_expose_requestable_package_but_zero_authority() -> None:
    key = "quarantine_generated_validation_runtime_binding_r3_authorization_package"
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)[key]
        assert state["package_digest_sha256"] == PACKAGE_DIGEST
        assert state["owner_decision_id"] == DECISION
        assert state["owner_U3R_authorization_pending"] is True
        assert state[
            "D_P3_6_U3R_GENERATED_VALIDATION_RUNTIME_BINDING_R3_AUTH_requestable"
        ] is True
        assert state["attempts_authorized"] == 0
        assert state["PowerShell_parser_import_or_execution_authorized"] is False
        assert state["runtime_manifest_closure_or_hardware_observation_authorized"] is False
        assert state["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_U3R_runtime_binding_authorization_action"
    ]
    assert action["U3R_authorization_package_sha256"] == PACKAGE_DIGEST
    assert action["owner_U3R_authorization_pending"] is True
    assert action["U3R_planning_package_preparation_authority"] is False


def test_human_records_line_endings_and_future_outputs_are_closed() -> None:
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
        REVIEW,
    ):
        text = path.read_text(encoding="utf-8")
        assert DECISION in text
        if path != REVIEW:
            assert PACKAGE_DIGEST in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (RESEARCH, ACTION_SPEC, PROPOSAL, PACKAGE, REVIEW, Path(__file__)):
        assert f"{path.as_posix().removeprefix(ROOT.as_posix() + '/')} text eol=lf" in attributes

    outputs = [ROOT / output for output in _read(ACTION_SPEC)["exact_future_outputs"]]
    if not any(path.exists() for path in outputs):
        return

    assert all(path.exists() for path in outputs)
    authorization, result, evidence = (_read(path) for path in outputs)
    assert authorization["decision_id"] == DECISION
    assert authorization["package_digest_sha256"] == PACKAGE_DIGEST
    assert authorization["effective_for_additional_attempt"] is False
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert result["attempt_consumed"] is True
    assert result["automatic_retry_performed"] is False
    assert result["additional_attempt_authorized"] is False
    assert evidence["authority_binding"]["authorization_record_sha256"] == _sha256(
        outputs[0]
    )
    assert evidence["authority_binding"]["result_record_sha256"] == _sha256(
        outputs[1]
    )
    assert evidence["gate_effect"]["authorization_reusable"] is False
    assert evidence["gate_effect"]["U3K_package_preparation_authorized"] is False
