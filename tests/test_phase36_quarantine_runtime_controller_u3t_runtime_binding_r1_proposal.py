from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-harness-implementation-acceptance.json"
)
ACTION_SPEC = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-action-spec.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-runtime-controller-u3t-runtime-binding-r1-authorization-proposal.md"
)

H1_ACCEPTANCE_DECISION = "D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-ACCEPTANCE"
R1_DECISION = "D-P3.6-U3T-RUNTIME-BINDING-R1-AUTH"
H1_PACKAGE_DIGEST = "AF16FFBD8214B7509FA634FBF5897B9CD4E0AE54E50B05F95678187E6CF00788"
H1_ACCEPTANCE_DIGEST = (
    "7868C38EAF59595A72AC61D209EA398D3477237D750F234B8F9E5712F0AA9AB3"
)
R1_PACKAGE_DIGEST = "C80CBFD14E3727FC0203357982B90FD7A09CF561E447EE383F8D800158D24C53"
H1_HARNESS_DIGEST = "69CBF4637A22BB7859ED07D19804C8576D76FB1270FF58D0D182EED2592FCE7B"
H1_VECTOR_DIGEST = "394A4564D54B531EBBC7C16BEA6F66D0D41DEDA757E5E979C796B350462DAB4F"
CONTROLLER_DIGEST = "78EE382E1538E8E1E482598A812B3CF32C2C75C4B4D324F34C368849217290EB"
CONTROLLER_CONTRACT_DIGEST = (
    "3F2A0975F92892A96FBC67B951B226D5AB958AE067F55B697ABA43669B8FB00E"
)
CONTROLLER_VECTOR_DIGEST = (
    "31335510565E4C74908C674B88951E81B7A7983331C6DE2E91964C1F8B48C20B"
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


def test_exact_H1_acceptance_is_recorded_with_planning_authority_only() -> None:
    acceptance = _read(ACCEPTANCE)

    assert _sha256(ACCEPTANCE) == H1_ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == H1_ACCEPTANCE_DECISION
    assert acceptance["accepted_package_sha256"] == H1_PACKAGE_DIGEST
    assert acceptance["accepted_commit"] == ("07d551789df00c32b54d42eb121ba8b865794ef7")
    statement = acceptance["canonical_owner_statement"]
    assert len(statement.encode("utf-8")) == 1307
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        "5298B054EF403B60D491F5D4BA3B12C3119878880D7C454E81E820095D8199D7"
    )
    authority = acceptance["authority_granted"]
    assert (
        authority[
            "prepare_separate_non_effective_U3T_R1_runtime_binding_and_one_attempt_authorization_proposal"
        ]
        is True
    )
    assert authority["PowerShell_parse_import_dot_source_or_execution"] is False
    assert authority["runtime_manifest_hardware_or_machine_observation"] is False
    assert authority["U3T_R1_attempt_U3R_retry_or_U3K"] is False


def test_R1_package_is_digest_bound_and_all_core_files_match() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == R1_PACKAGE_DIGEST
    assert package["decision_id"] == R1_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 13
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_R1_action_spec_is_single_attempt_bounded_and_default_deny() -> None:
    spec = _read(ACTION_SPEC)

    assert spec["decision_id"] == R1_DECISION
    assert spec["maximum_attempts"] == 1
    assert spec["authorization_window_seconds"] == 86400
    assert spec["failed_attempt_consumes_authorization"] is True
    assert spec["automatic_retry"] is False
    assert spec["parallel_processes"] is False
    assert [item["action_id"] for item in spec["exact_action_sequence"]] == [
        "U3T-R1-A01-PACKAGE-AUTHORITY-PREFLIGHT",
        "U3T-R1-A02-AUTHORIZATION-RECORD",
        "U3T-R1-A03-RUNTIME-PATH-CLASSIFICATION",
        "U3T-R1-A04-RUNTIME-BINDING",
        "U3T-R1-A05-SOURCE-BINDINGS-PREFLIGHT",
        "U3T-R1-A06-PREFLIGHT-PROCESS",
        "U3T-R1-A07-SANITIZED-RESULT-CLASSIFICATION",
        "U3T-R1-A08-POSTPROCESS-BINDING",
        "U3T-R1-A09-SANITIZED-EVIDENCE",
    ]
    assert len(spec["allowlisted_terminal_reason_codes"]) == 13


def test_exact_runtime_has_no_discovery_manifest_or_hardware_surface() -> None:
    spec = _read(ACTION_SPEC)
    runtime = spec["exact_runtime_candidate"]
    bounds = spec["process_bounds"]

    assert runtime["path"] == "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    assert runtime["maximum_file_bytes"] == 134217728
    assert runtime["required_type"] == "local_regular_nonreparse_file"
    assert len(runtime["required_fixed_parent_components"]) == 3
    assert runtime["alternate_runtime_or_parent_discovery"] is False
    assert (
        runtime[
            "PATH_PSModulePath_registry_WMI_package_directory_or_hardware_inventory"
        ]
        is False
    )
    assert runtime["network_or_trust_retrieval"] is False
    assert bounds == {
        "maximum_processes": 1,
        "maximum_attempts": 1,
        "total_timeout_seconds": 30,
        "maximum_stdout_bytes": 16384,
        "maximum_stderr_bytes": 0,
        "maximum_result_bytes": 65536,
        "automatic_retry": False,
        "process_tree_termination_on_timeout": True,
        "environment_proxy_or_module_path_inheritance": False,
        "PSModuleAutoLoadingPreference": "None",
    }
    prohibited = spec["explicitly_not_authorized"]
    assert "PowerShell_module_manifest_closure_or_Aggregate_validation" in prohibited
    assert "model_loading_inference_benchmark_or_hardware_testing" in prohibited


def test_exact_accepted_source_bindings_remain_immutable() -> None:
    spec = _read(ACTION_SPEC)
    inputs = {item["path"]: item["sha256"] for item in spec["exact_accepted_inputs"]}

    assert inputs == {
        "tools/phase36_quarantine_runtime_controller_u3t_preflight.ps1": (
            H1_HARNESS_DIGEST
        ),
        "contracts/phase-3/p3-6-quarantine-runtime-controller-u3t-preflight-r0-vectors.json": (
            H1_VECTOR_DIGEST
        ),
        "tools/phase36_quarantine_runtime_controller.ps1": CONTROLLER_DIGEST,
        "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-contract.json": (
            CONTROLLER_CONTRACT_DIGEST
        ),
        "contracts/phase-3/p3-6-quarantine-runtime-controller-r0-vectors.json": (
            CONTROLLER_VECTOR_DIGEST
        ),
    }
    for relative, expected in inputs.items():
        assert _sha256(ROOT / relative) == expected


def test_proposal_requests_exact_authorization_without_current_authority() -> None:
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)

    assert proposal["decision_id"] == R1_DECISION
    assert (
        "<U3T_R1_AUTHORIZATION_PACKAGE_DIGEST_SHA256>"
        in proposal["future_owner_authorization_statement_template"]
    )
    assert (
        proposal[
            "authorization_may_be_inferred_from_H1_acceptance_continue_package_preparation_or_static_validation"
        ]
        is False
    )
    assert (
        package["current_gate_effect"]["D_P3_6_U3T_RUNTIME_BINDING_R1_AUTH_requestable"]
        is True
    )
    assert package["current_gate_effect"]["attempts_authorized"] == 0
    assert (
        package["current_gate_effect"][
            "PowerShell_parse_import_dot_source_or_execution_authorized"
        ]
        is False
    )
    assert (
        package["current_gate_effect"][
            "runtime_parent_manifest_hardware_or_machine_observation_authorized"
        ]
        is False
    )


def test_canonical_ledgers_expose_H1_acceptance_and_requestable_R1_package() -> None:
    acceptance_key = (
        "quarantine_runtime_controller_u3t_preflight_r0_H1_implementation_acceptance"
    )
    package_key = (
        "quarantine_runtime_controller_u3t_runtime_binding_r1_authorization_package"
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
        assert acceptance["U3T_R1_proposal_preparation_authorized"] is True
        assert acceptance["U3T_R1_attempt_authorized"] is False

        package = state[package_key]
        assert package["owner_decision_id"] == R1_DECISION
        assert package["package_digest_sha256"] == R1_PACKAGE_DIGEST
        assert package["owner_U3T_R1_authorization_pending"] is True
        assert package["D_P3_6_U3T_RUNTIME_BINDING_R1_AUTH_requestable"] is True
        assert package["attempts_authorized"] == 0
        assert (
            package["PowerShell_parse_import_dot_source_or_execution_authorized"]
            is False
        )
        assert package["U3R_retry_or_U3K_requestable"] is False

    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_U3T_R1_runtime_binding_authorization_action"
    ]
    assert action["decision_id"] == R1_DECISION
    assert action["authorization_package_sha256"] == R1_PACKAGE_DIGEST
    assert action["owner_U3T_R1_authorization_pending"] is True
    assert action["attempts_authorized"] == 0


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
    assert all(not output.exists() for output in outputs)
