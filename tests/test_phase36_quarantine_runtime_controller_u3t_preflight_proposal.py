from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
SOURCE_PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-package.json"
)
ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-r0-source-implementation-acceptance.json"
)
PLANNING_CONTRACT = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-planning-contract.json"
)
AUTHORIZATION_PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-source-implementation-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-planning-package.json"
)
REVIEW = DOCS / "p3-6-quarantine-runtime-controller-u3t-preflight-r0-proposal.md"
SOURCE_PACKAGE_DIGEST = (
    "484A6FB71216F43A1EAF668DC59091D4FD42EF8543585BFBB588CFCDE089BE30"
)
ACCEPTANCE_DIGEST = "8A688EA3542D2F5D8CD2EF9BA86204F8AE7B997C06351E1178CF6545B52CE125"
PACKAGE_DIGEST = "26B8A0A6FF1B8DA556BB68D6E1EA13B51FFF4460D5CA2F50F3E64952528E69F2"
ACCEPTANCE_DECISION = "D-P3.6-U3S-DUAL-CONTROLLER-R0-IMPLEMENTATION-ACCEPTANCE"
H1_DECISION = "D-P3.6-U3T-PREFLIGHT-R0-HARNESS-IMPLEMENTATION-AUTH"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_exact_u3s_acceptance_is_recorded_without_runtime_authority() -> None:
    acceptance = _read(ACCEPTANCE)
    assert _sha256(SOURCE_PACKAGE) == SOURCE_PACKAGE_DIGEST
    assert _sha256(ACCEPTANCE) == ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == ACCEPTANCE_DECISION
    assert acceptance["accepted_package_sha256"] == SOURCE_PACKAGE_DIGEST
    statement = acceptance["canonical_owner_statement"]
    assert len(statement.encode("utf-8")) == 1354
    assert hashlib.sha256(statement.encode("utf-8")).hexdigest().upper() == (
        "3C0B50A27C489A979C5218551AE312FFA54BB09271CB417F0DEDE6EE3C648E44"
    )
    authority = acceptance["authority_granted"]
    assert (
        authority[
            "prepare_separate_non_effective_U3T_preflight_planning_and_authorization_proposal"
        ]
        is True
    )
    assert authority["implement_U3T_harness_or_tests"] is False
    assert authority["PowerShell_parse_import_or_execution"] is False
    assert authority["runtime_manifest_hardware_or_machine_observation"] is False


def test_u3t_planning_contract_separates_source_and_runtime_gates() -> None:
    contract = _read(PLANNING_CONTRACT)
    assert [gate["gate"] for gate in contract["two_future_gates"]] == [
        "U3T_H1_SOURCE_HARNESS",
        "U3T_R1_RUNTIME_BOUND_PREFLIGHT",
    ]
    assert contract["H1_harness_contract"]["request_mode"] == "Policy"
    assert (
        contract["H1_harness_contract"]["controller_Preflight_machine_authority"]
        is False
    )
    assert contract["H1_generated_vector_plan"]["minimum_vectors"] == 48
    assert sum(contract["H1_generated_vector_plan"]["groups"].values()) == 48
    runtime = contract["future_R1_runtime_binding_policy"]
    assert runtime["maximum_runtime_processes"] == 1
    assert runtime["maximum_attempts"] == 1
    assert runtime["automatic_retry"] is False
    assert runtime["process_timeout_seconds"] == 30
    assert runtime["utility_manifest_module_or_closure_access"] is False


def test_u3t_h1_authorization_package_is_sealed_and_non_effective() -> None:
    package = _read(PACKAGE)
    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["decision_id"] == H1_DECISION
    assert package["core_file_count"] == 9
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    gate = package["current_gate_effect"]
    assert gate["owner_H1_source_harness_implementation_authorization_pending"] is True
    assert (
        gate["D_P3_6_U3T_PREFLIGHT_R0_HARNESS_IMPLEMENTATION_AUTH_requestable"] is True
    )
    for key in (
        "H1_source_or_test_implementation_authorized",
        "PowerShell_parse_import_or_execution_authorized",
        "Python_machine_access_or_fallback_authorized",
        "runtime_manifest_hardware_or_machine_observation_authorized",
        "U3T_R1_attempt_U3R_retry_or_U3K_authorized",
        "deployment_or_remote_git_authorized",
    ):
        assert gate[key] is False


def test_future_h1_paths_do_not_exist_before_exact_authorization() -> None:
    contract = _read(PLANNING_CONTRACT)
    proposal = _read(AUTHORIZATION_PROPOSAL)
    assert sorted(contract["future_H1_source_paths"].values()) == sorted(
        proposal["exact_future_implementation_paths"]
    )
    for relative in proposal["exact_future_implementation_paths"]:
        assert not (ROOT / relative).exists()
    assert (
        proposal["current_effect"]["H1_source_or_test_implementation_authorized"]
        is False
    )
    assert (
        proposal[
            "authorization_may_be_inferred_from_U3S_acceptance_continue_silence_or_proposal_preparation"
        ]
        is False
    )


def test_canonical_ledgers_expose_u3s_acceptance_and_pending_u3t_h1_package() -> None:
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        acceptance = state[
            "quarantine_runtime_controller_r0_source_implementation_acceptance"
        ]
        assert acceptance["decision_id"] == ACCEPTANCE_DECISION
        assert acceptance["accepted_package_digest_sha256"] == SOURCE_PACKAGE_DIGEST
        assert acceptance["acceptance_record_sha256"] == ACCEPTANCE_DIGEST
        assert acceptance["U3T_planning_preparation_authorized"] is True
        assert acceptance["U3T_H1_implementation_or_R1_attempt_authorized"] is False

        u3t = state["quarantine_runtime_controller_u3t_preflight_r0_planning_package"]
        assert u3t["decision_id"] == H1_DECISION
        assert u3t["package_digest_sha256"] == PACKAGE_DIGEST
        assert (
            u3t["owner_H1_source_harness_implementation_authorization_pending"] is True
        )
        assert u3t["H1_source_or_test_implementation_authorized"] is False
        assert u3t["U3T_R1_attempt_U3R_retry_or_U3K_authorized"] is False

    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_U3T_H1_source_harness_implementation_action"
    ]
    assert action["decision_id"] == H1_DECISION
    assert action["package_digest_sha256"] == PACKAGE_DIGEST
    assert action["H1_source_or_test_implementation_authorized"] is False


def test_docs_and_line_endings_are_synchronized() -> None:
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
        assert ACCEPTANCE_DECISION in text
        assert SOURCE_PACKAGE_DIGEST in text
        assert H1_DECISION in text
        assert PACKAGE_DIGEST in text

    review = REVIEW.read_text(encoding="utf-8")
    assert "Gate H1: Source Harness" in review
    assert "Gate R1: Future Runtime-Bound Preflight" in review
    assert "grants no H1 implementation and no R1 attempt" in review

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (
        ACCEPTANCE,
        PLANNING_CONTRACT,
        AUTHORIZATION_PROPOSAL,
        PACKAGE,
        REVIEW,
        Path(__file__),
    ):
        relative = path.as_posix().removeprefix(ROOT.as_posix() + "/")
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()
