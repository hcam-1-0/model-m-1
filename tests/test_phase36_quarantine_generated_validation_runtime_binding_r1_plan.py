from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

RESEARCH_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r1-research-sources.json"
)
PLAN_PATH = (
    CONTRACTS / "p3-6-quarantine-generated-validation-runtime-binding-r1-plan.json"
)
PROPOSAL_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r0-implementation-"
    "authorization-proposal.json"
)
PACKAGE_PATH = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r0-implementation-"
    "authorization-package.json"
)
REVIEW_PATH = (
    DOCS / "p3-6-quarantine-generated-validation-runtime-binding-r1-plan.md"
)

DECISION_ID = "D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-AUTH"
PACKAGE_DIGEST = (
    "F92CB073156BDEFF1832D2BB0634D25005E89D58EE01CA130073F2466A0DCEE1"
)
IMPLEMENTATION_PACKAGE_DIGEST = (
    "D34FF5AA704DE4A0215C0EA5FDE440B8A4311E31CCC3EA6BB77939E7D3223F6A"
)
IMPLEMENTATION_ACCEPTANCE_DECISION_ID = (
    "D-P3.6-U3M-VALIDATION-HARNESS-R0-IMPLEMENTATION-ACCEPTANCE"
)
IMPLEMENTATION_ACCEPTANCE_DIGEST = (
    "25FE4348FA7A38A7B8625463CBAEE1E2536340D4D2F7638F19404B9F76832AA9"
)
U3N_DECISION_ID = "D-P3.6-U3N-GENERATED-VALIDATION-RUNTIME-BINDING-R1-AUTH"
U3N_PACKAGE_DIGEST = (
    "E980CDD3CF6D560EFD832188B8659BE5C0B89C528CEDE46FF1726645CE569C2E"
)
U3L_ACCEPTANCE_DIGEST = (
    "06085F3E296B450204FC0E8171314581F40853A11B0AA74161238C390A05B631"
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


def test_planning_package_is_exact_non_effective_and_complete() -> None:
    package = _read(PACKAGE_PATH)

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["future_authorization_decision_id"] == DECISION_ID
    assert package["status"] == (
        "sealed_non_effective_owner_harness_implementation_authorization_pending"
    )
    assert package["core_file_count"] == len(package["core_files"]) == 8
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]

    gate = package["current_gate_effect"]
    assert gate["owner_harness_implementation_authorization_pending"] is True
    for field in (
        "harness_source_or_test_implementation_authorized",
        "PowerShell_parser_import_or_execution_authorized",
        "runtime_or_hardware_observation_authorized",
        "runner_or_module_execution_authorized",
        "machine_storage_F_ACL_probe_cleanup_or_scanner_action_authorized",
        "D_P3_6_U3N_GENERATED_VALIDATION_RUNTIME_BINDING_R1_AUTH_requestable",
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable",
        "deployment_authorized",
        "remote_git_authorized",
    ):
        assert gate[field] is False


def test_plan_binds_accepted_sources_and_rejects_historical_binding() -> None:
    plan = _read(PLAN_PATH)

    assert plan["preparation_authority"]["acceptance_record_sha256"] == (
        U3L_ACCEPTANCE_DIGEST
    )
    sources = {item["path"]: item for item in plan["fixed_accepted_sources"]}
    assert sources["tools/phase36_quarantine_transaction_runner.ps1"][
        "sha256"
    ] == RUNNER_DIGEST
    assert sources["tools/phase36_quarantine_machine_handlers.psm1"][
        "sha256"
    ] == HANDLER_DIGEST
    assert sources["tools/phase36_quarantine_windows_storage_adapter.psm1"][
        "sha256"
    ] == ADAPTER_DIGEST
    assert _sha256(ROOT / "tools/phase36_quarantine_transaction_runner.ps1") == (
        RUNNER_DIGEST
    )
    assert _sha256(ROOT / "tools/phase36_quarantine_machine_handlers.psm1") == (
        HANDLER_DIGEST
    )
    assert _sha256(
        ROOT / "tools/phase36_quarantine_windows_storage_adapter.psm1"
    ) == ADAPTER_DIGEST

    historical = plan["historical_runtime_binding"]
    assert historical["reusable"] is False
    assert historical["historical_runner_sha256"] != historical[
        "current_runner_sha256"
    ]


def test_future_validation_is_layered_generated_and_machine_free() -> None:
    plan = _read(PLAN_PATH)
    layers = {
        item["layer_id"]: item for item in plan["future_generated_validation_layers"]
    }

    assert set(layers) == {
        "GV-R1-L1-PARSER",
        "GV-R1-L2-CONTRACT",
        "GV-R1-L3-PURE-HANDLERS",
        "GV-R1-L4-AGGREGATE",
    }
    assert layers["GV-R1-L1-PARSER"]["adapter_import_or_execution"] is False
    assert layers["GV-R1-L2-CONTRACT"]["vector_count"] == 20
    assert layers["GV-R1-L2-CONTRACT"]["Storage_mode_allowed"] is False
    assert layers["GV-R1-L3-PURE-HANDLERS"]["vector_count"] == 64
    assert layers["GV-R1-L3-PURE-HANDLERS"][
        "windows_adapter_import_or_execution"
    ] is False
    assert plan["future_evidence_requirements"][
        "total_generated_vectors_required"
    ] == 84
    assert plan["future_evidence_requirements"][
        "windows_adapter_import_or_execution_count_required"
    ] == 0
    assert plan["future_evidence_requirements"][
        "machine_storage_F_ACL_probe_cleanup_or_scanner_action_count_required"
    ] == 0


def test_gate_sequence_separates_implementation_execution_and_storage() -> None:
    plan = _read(PLAN_PATH)
    gates = {item["gate"]: item for item in plan["gate_sequence"]}

    assert gates["U3M-G1"]["requestable_now"] is True
    assert gates["U3M-G1"]["PowerShell_parser_import_or_execution"] is False
    assert gates["U3M-G2"]["requestable_now"] is False
    assert gates["U3N-G1"]["requestable_now"] is False
    assert gates["U3N-G2"]["requestable_now"] is False
    assert gates["U3K-G3"]["requestable_now"] is False

    bounds = plan["future_process_and_resource_bounds"]
    assert bounds["maximum_authorized_attempts"] == 1
    assert bounds["UseShellExecute"] is False
    assert bounds["parallel_processes"] is False
    assert bounds["automatic_retry"] is False
    assert bounds["raw_stdout_or_stderr_persisted"] is False


def test_owner_proposal_requests_source_only_implementation() -> None:
    proposal = _read(PROPOSAL_PATH)
    effect = proposal["requested_owner_effect_if_exact_package_digest_is_accepted"]

    assert proposal["decision_id"] == DECISION_ID
    assert effect[
        "authorize_exact_generated_validation_harness_source_implementation_only"
    ] is True
    assert effect["authorize_Python_static_and_generated_reference_tests_only"] is True
    for field in (
        "accepted_runner_handler_or_adapter_source_change_authorized",
        "PowerShell_parser_import_or_execution_authorized",
        "runtime_or_hardware_observation_authorized",
        "runner_Contract_or_Storage_mode_execution_authorized",
        "pure_handler_or_windows_adapter_import_or_execution_authorized",
        "machine_storage_F_ACL_probe_cleanup_or_scanner_action_authorized",
        "network_download_artifact_dependency_model_media_or_data_action_authorized",
        "container_Kubernetes_deployment_or_remote_git_authorized",
    ):
        assert effect[field] is False
    assert proposal["owner_statement_template"].startswith(f"{DECISION_ID}:")
    assert (
        "<U3M_VALIDATION_HARNESS_IMPLEMENTATION_AUTHORIZATION_PACKAGE_"
        "DIGEST_SHA256>"
    ) in proposal["owner_statement_template"]


def test_research_record_reports_no_prohibited_action() -> None:
    research = _read(RESEARCH_PATH)
    actions = research["actions_performed_while_preparing_this_record"]

    assert len(research["sources"]) == 6
    assert actions["public_documentation_research"] is True
    assert actions["PowerShell_parsed_imported_or_executed"] is False
    assert actions["runtime_or_hardware_observed"] is False
    assert actions["machine_storage_F_ACL_probe_cleanup_or_scanner_action"] is False
    assert actions["remote_git_action"] is False


def test_canonical_ledgers_expose_only_implementation_acceptance_as_next_action() -> None:
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read(CONTRACTS / name)
        state = ledger[
            "quarantine_generated_validation_harness_r0_implementation_"
            "authorization_package"
        ]
        assert state["implementation_authorization_package_digest_sha256"] == (
            PACKAGE_DIGEST
        )
        assert state["implementation_package_digest_sha256"] == (
            IMPLEMENTATION_PACKAGE_DIGEST
        )
        assert state["implementation_authority_decision_id"] == DECISION_ID
        assert state["owner_acceptance_decision_id"] == (
            IMPLEMENTATION_ACCEPTANCE_DECISION_ID
        )
        assert state["owner_harness_implementation_authorization_pending"] is False
        assert state["implementation_authority_consumed"] is True
        assert state["harness_source_and_generated_vectors_implemented"] is True
        assert state["implementation_acceptance_sha256"] == (
            IMPLEMENTATION_ACCEPTANCE_DIGEST
        )
        assert state["owner_implementation_acceptance_pending"] is False
        assert state[
            "harness_source_and_generated_static_evidence_accepted"
        ] is True
        assert state["harness_source_or_test_implementation_authorized"] is False
        assert state["PowerShell_parser_import_or_execution_authorized"] is False
        assert state["runtime_or_hardware_observation_authorized"] is False
        assert state["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

        u3n = ledger[
            "quarantine_generated_validation_runtime_binding_r1_"
            "authorization_package"
        ]
        assert u3n["package_digest_sha256"] == U3N_PACKAGE_DIGEST
        assert u3n["owner_decision_id"] == U3N_DECISION_ID
        assert u3n["owner_U3N_authorization_pending"] is True
        assert u3n[
            "D_P3_6_U3N_GENERATED_VALIDATION_RUNTIME_BINDING_R1_AUTH_requestable"
        ] is True
        assert u3n["runtime_observation_authorized"] is False
        assert u3n["PowerShell_parser_import_or_execution_authorized"] is False
        assert u3n["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    action = unblock["next_generated_validation_runtime_binding_action"]
    assert action["action"] == (
        "owner_review_of_exact_U3N_generated_validation_and_fresh_runtime_"
        "binding_single_attempt_authorization_package"
    )
    assert action["decision_id"] == U3N_DECISION_ID
    assert action["owner_U3N_authorization_pending"] is True
    assert action["authorization_package_digest_sha256"] == U3N_PACKAGE_DIGEST
    assert action["PowerShell_parser_import_or_execution_authority"] is False
    assert action["runtime_observation_authority"] is False
    assert action["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False


def test_human_indexes_and_line_endings_are_synchronized() -> None:
    paths = [
        CONTRACTS / "README.md",
        DOCS / "README.md",
        DOCS / "acceptance-checklist.md",
        DOCS / "decision-register.md",
        DOCS / "implementation-backlog.md",
        DOCS / "p3-6-capability-profiles.md",
        DOCS / "p3-6-plan.md",
        DOCS / "p3-6-planning-acceptances.md",
        DOCS / "p3-6-unblock-plan.md",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert DECISION_ID in text
        assert PACKAGE_DIGEST in text
        assert IMPLEMENTATION_ACCEPTANCE_DECISION_ID in text
        assert IMPLEMENTATION_PACKAGE_DIGEST in text
        assert U3N_DECISION_ID in text
        assert U3N_PACKAGE_DIGEST in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for name in (
        "p3-6-quarantine-generated-validation-runtime-binding-r1-research-sources.json",
        "p3-6-quarantine-generated-validation-runtime-binding-r1-plan.json",
        "p3-6-quarantine-generated-validation-harness-r0-implementation-authorization-proposal.json",
        "p3-6-quarantine-generated-validation-harness-r0-implementation-authorization-package.json",
        "p3-6-quarantine-generated-validation-runtime-binding-r1-plan.md",
        "test_phase36_quarantine_generated_validation_runtime_binding_r1_plan.py",
        "phase36_quarantine_generated_validation.ps1",
        "p3-6-quarantine-generated-powershell-validation-r0-vectors.json",
        "test_phase36_quarantine_generated_powershell_validation_harness.py",
        "p3-6-quarantine-generated-validation-harness-r0-implementation-evidence.json",
        "p3-6-quarantine-generated-validation-harness-r0-implementation-package.json",
        "p3-6-quarantine-generated-validation-harness-r0-implementation-evidence-review.md",
    ):
        assert f"{name} text eol=lf" in attributes
