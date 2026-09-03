from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-harness-implementation-acceptance.json"
)
ACTION_SPEC = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-action-spec.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-authorization-proposal.md"
)

H1_ACCEPTANCE_DECISION = (
    "D-P3.6-U3Z-CONTROLLER-R1-GENERATED-CONTRACT-VALIDATION-HARNESS-"
    "IMPLEMENTATION-ACCEPTANCE"
)
R1_DECISION = (
    "D-P3.6-U3Z-CONTROLLER-R1-GENERATED-CONTRACT-VALIDATION-"
    "RUNTIME-BINDING-R1-AUTH"
)
H1_PACKAGE_DIGEST = "47344ECB697AF05C361D52B3CF05DE6E730B8AF4FC1E91C3AAD682FA514727AF"
H1_ACCEPTANCE_DIGEST = (
    "38B89E53B46F921663879DE0614AF318EDF9B66AB36120663D14F61070AD8477"
)
R1_PACKAGE_DIGEST = "3348ECB80895806A2E63610088EF3178CE38B715910C3B1463D97CB2E8F3C6C5"
U4B_PACKAGE_DIGEST = "E52680B8314FA9A4FC862510BC9570DE3942A791952F22425E61ED61723222AE"
R1_OUTPUT_DIGESTS = {
    "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-authorization.json": (
        "FC1AE35876012CEFDCB52AE5A274FC5787FAE1AE722A9709AC76782C78C530D1"
    ),
    "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-result.json": (
        "C9743F0FC8906E46701E07A01A1C651F4B4B2C0517FAB722A97C1396F40F7303"
    ),
    "p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-runtime-binding-r1-evidence.json": (
        "34BDA40E4450F35AF4A86E3C7566B9AFCA01413D70FE9CA9EB70B35A1B921BFF"
    ),
}
HARNESS_DIGEST = "D9EE5CC7599AACCE3363CE5C29EE479D777F94CF886AE779390B7027C40FA382"
MATERIALIZED_VECTOR_DIGEST = (
    "7BCDFCA583644BD4ED5F4B747C3969B4C9FF4029B48734F8BD4D90BA5D600A21"
)
CONTROLLER_DIGEST = "787655BAC55DDF563E9D1DC43EC37F010C271AB381E541B0734028E3F2B90B31"
CONTROLLER_CONTRACT_DIGEST = (
    "637C5400122874149D9835CC6BC521E5EEC9160222F4A7AC5CA1F6CD99E1BCC4"
)
SOURCE_VECTOR_DIGEST = (
    "D8EDF5C0255B40FB6C28BB014C09DC503D2B53665E69C5AA5AB65C744AEA81E4"
)
REFERENCE_DIGEST = "B5C7328CD666E0A8988F9B616C5B2A914D690A40BF2EA289C1F1C755E42B86F0"


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


def test_exact_H1_acceptance_is_recorded_as_proposal_preparation_only() -> None:
    acceptance = _read(ACCEPTANCE)

    assert _sha256(ACCEPTANCE) == H1_ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == H1_ACCEPTANCE_DECISION
    assert acceptance["accepted_package"]["sha256"] == H1_PACKAGE_DIGEST
    statement = acceptance["canonical_owner_statement"]
    assert len(statement.encode("utf-8")) == 1450
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        "2E1141B3EB2FE91D1208C4E249919023CA81B6810BA66BA76495639CAAC384C5"
    )
    effect = acceptance["accepted_effect"]
    assert (
        effect[
            "prepare_separate_non_effective_U3Z_R1_runtime_binding_and_generated_validation_authorization_proposal"
        ]
        is True
    )
    assert effect["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert effect["generated_validation_attempt_or_another_attempt_authorized"] is False
    assert effect["U3K_profile_activation_or_deployment_authorized"] is False


def test_R1_package_is_digest_bound_and_all_core_files_match() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == R1_PACKAGE_DIGEST
    assert package["decision_id"] == R1_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 16
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_R1_action_spec_is_one_attempt_bounded_and_default_deny() -> None:
    spec = _read(ACTION_SPEC)

    assert spec["decision_id"] == R1_DECISION
    assert spec["logical_node_id"] == "LAB-LAPTOP-01"
    assert spec["maximum_attempts"] == 1
    assert spec["authorization_window_seconds"] == 86400
    assert spec["failed_attempt_consumes_authorization"] is True
    assert spec["automatic_retry"] is False
    assert spec["parallel_processes"] is False
    assert [item["action_id"] for item in spec["exact_action_sequence"]] == [
        "U3Z-R1-A01-PACKAGE-AUTHORITY-PREFLIGHT",
        "U3Z-R1-A02-AUTHORIZATION-RECORD",
        "U3Z-R1-A03-RUNTIME-PATH-CLASSIFICATION",
        "U3Z-R1-A04-RUNTIME-BINDING",
        "U3Z-R1-A05-SOURCE-BINDINGS-PREFLIGHT",
        "U3Z-R1-A06-GENERATED-CONTRACT-VALIDATION",
        "U3Z-R1-A07-SANITIZED-RESULT-CLASSIFICATION",
        "U3Z-R1-A08-POSTPROCESS-BINDING",
        "U3Z-R1-A09-SANITIZED-EVIDENCE",
    ]
    assert spec["allowlisted_terminal_reason_codes"] == [
        "generated_contract_validation_passed",
        "binding_failed",
        "manifest_failed",
        "controller_load_failed",
        "validation_failed",
        "result_serialization_failed",
    ]


def test_exact_runtime_process_and_discovery_bounds_are_closed() -> None:
    spec = _read(ACTION_SPEC)
    runtime = spec["exact_runtime_candidate"]
    bounds = spec["process_bounds"]

    assert runtime["path"] == "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    assert runtime["maximum_file_bytes"] == 134217728
    assert runtime["required_type"] == "local_regular_nonreparse_file"
    assert len(runtime["required_fixed_parent_components"]) == 3
    assert runtime["alternate_runtime_parent_module_or_hardware_discovery"] is False
    assert runtime["PATH_PSModulePath_registry_WMI_package_or_directory_inventory"] is False
    assert runtime["network_or_trust_retrieval"] is False
    assert bounds["maximum_processes"] == bounds["maximum_attempts"] == 1
    assert bounds["total_timeout_seconds"] == 120
    assert bounds["maximum_stdout_bytes"] == 16384
    assert bounds["maximum_stderr_bytes"] == 0
    assert bounds["maximum_result_bytes"] == 32768
    assert bounds["automatic_retry"] is False
    assert bounds["environment_proxy_or_module_path_inheritance"] is False
    assert bounds["PSModuleAutoLoadingPreference"] == "None"


def test_exact_six_source_bindings_remain_immutable() -> None:
    spec = _read(ACTION_SPEC)
    inputs = {item["path"]: item["sha256"] for item in spec["exact_accepted_inputs"]}

    assert inputs == {
        "tools/phase36_quarantine_runtime_controller_r1_generated_validation.ps1": HARNESS_DIGEST,
        "contracts/phase-3/p3-6-quarantine-runtime-controller-u3z-generated-contract-validation-r0-vectors.json": MATERIALIZED_VECTOR_DIGEST,
        "tools/phase36_quarantine_runtime_controller_r1.ps1": CONTROLLER_DIGEST,
        "contracts/phase-3/p3-6-quarantine-runtime-controller-r1-stage-projection-contract.json": CONTROLLER_CONTRACT_DIGEST,
        "contracts/phase-3/p3-6-quarantine-runtime-controller-r1-stage-projection-vectors.json": SOURCE_VECTOR_DIGEST,
        "tools/phase36_quarantine_runtime_controller_r1_reference.py": REFERENCE_DIGEST,
    }
    for relative, expected in inputs.items():
        assert _sha256(ROOT / relative) == expected
    assert spec["source_binding_policy"]["Python_reference_execution"] is False


def test_success_contract_is_exactly_288_generated_cases_and_zero_effects() -> None:
    success = _read(ACTION_SPEC)["success_contract"]

    assert success["terminal_reason_code"] == "generated_contract_validation_passed"
    assert success["cases_loaded"] == success["cases_executed"] == 288
    assert success["cases_passed"] == 288
    assert success["cases_failed"] == 0
    assert success["literal_null_success_match"] is True
    assert success["all_failure_action_reason_match"] is True
    assert success["cross_language_projection_difference_count"] == 0
    assert success["raw_fixture_retained_bytes"] == 0
    assert success["raw_process_material_retained_bytes"] == 0
    assert success["machine_action_count"] == 0
    assert success["network_action_count"] == 0
    assert success["automatic_retry_count"] == 0
    assert success["U3K_authorized"] is False
    assert success["deployment_authorized"] is False


def test_proposal_requests_exact_authorization_without_current_authority() -> None:
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)

    assert proposal["decision_id"] == R1_DECISION
    assert "<U3Z_R1_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in proposal[
        "future_owner_authorization_statement_template"
    ]
    assert (
        proposal[
            "authorization_may_be_inferred_from_acceptance_continue_package_preparation_or_static_validation"
        ]
        is False
    )
    gate = package["current_gate_effect"]
    assert gate["owner_U3Z_R1_authorization_pending"] is True
    assert (
        gate[
            "D_P3_6_U3Z_CONTROLLER_R1_GENERATED_CONTRACT_VALIDATION_RUNTIME_BINDING_R1_AUTH_requestable"
        ]
        is True
    )
    assert gate["attempts_authorized"] == 0
    assert gate["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert gate["runtime_manifest_hardware_or_machine_observation_authorized"] is False
    assert (
        gate[
            "container_Kubernetes_profile_activation_deployment_U3K_commit_push_or_remote_Git_authorized"
        ]
        is False
    )


def test_canonical_ledgers_expose_acceptance_and_consumed_R1_gate() -> None:
    acceptance_key = (
        "quarantine_runtime_controller_u3z_generated_contract_validation_r0_"
        "harness_implementation_acceptance"
    )
    package_key = (
        "quarantine_runtime_controller_u3z_generated_contract_validation_"
        "runtime_binding_r1_authorization_package"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        acceptance = state[acceptance_key]
        assert acceptance["decision_id"] == H1_ACCEPTANCE_DECISION
        assert acceptance["acceptance_record_sha256"] == H1_ACCEPTANCE_DIGEST
        assert acceptance["accepted_package_digest_sha256"] == H1_PACKAGE_DIGEST
        assert acceptance["U3Z_R1_proposal_preparation_authorized"] is True
        assert acceptance["U3Z_R1_attempt_authorized"] is False

        package = state[package_key]
        assert package["owner_decision_id"] == R1_DECISION
        assert package["package_digest_sha256"] == R1_PACKAGE_DIGEST
        assert package["owner_U3Z_R1_authorization_pending"] is False
        assert package["D_P3_6_U3Z_R1_AUTH_requestable"] is False
        assert package["attempts_authorized"] == 0
        assert package["attempts_consumed"] == 1
        assert package["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
        assert package["U3K_requestable"] is False

    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_U4B_outer_attempt_controller_source_implementation_authorization_action"
    ]
    assert action["decision_id"] == (
        "D-P3.6-U4B-OUTER-ATTEMPT-CONTROLLER-R0-IMPLEMENTATION-AUTH"
    )
    assert action["authorization_package_sha256"] == U4B_PACKAGE_DIGEST
    assert action["owner_source_implementation_authorization_pending"] is True
    assert action["attempts_authorized"] == 0


def test_human_records_line_endings_and_attempt_outputs_are_sealed() -> None:
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
        assert H1_ACCEPTANCE_DECISION in text
        assert R1_DECISION in text
        if path != REVIEW:
            assert R1_PACKAGE_DIGEST in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (ACCEPTANCE, ACTION_SPEC, PROPOSAL, PACKAGE, REVIEW, Path(__file__)):
        relative = path.as_posix().removeprefix(ROOT.as_posix() + "/")
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()

    outputs = [ROOT / output for output in _read(ACTION_SPEC)["exact_future_outputs"]]
    assert len(outputs) == len(R1_OUTPUT_DIGESTS) == 3
    for output in outputs:
        assert output.exists()
        assert _sha256(output) == R1_OUTPUT_DIGESTS[output.name]
