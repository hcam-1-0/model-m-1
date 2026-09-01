from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

ACTION_SPEC = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r2-action-spec.json"
)
PROPOSAL = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r2-"
    "authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-runtime-binding-r2-"
    "authorization-package.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-generated-validation-runtime-binding-r2-"
    "authorization-proposal.md"
)
ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r1-implementation-"
    "acceptance.json"
)

DECISION = "D-P3.6-U3P-GENERATED-VALIDATION-RUNTIME-BINDING-R2-AUTH"
PACKAGE_DIGEST = (
    "2AFD1D377A68DC35286FE73E58A2B4733BB91BD225BDDBA443472FF76F5603A3"
)
ACCEPTANCE_DIGEST = (
    "8A6EBD49F71667ECF9961BB02CA891A610497DEBCE23DDDFB9A65FA08F2917EC"
)
HARNESS_DIGEST = (
    "F5A73AC23875C74964C88E83F401E9BCEBE94F743E86FE0376502D16308B2CA3"
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_package_binds_exact_preparation_authority_and_core() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["decision_id"] == DECISION
    assert package["preparation_authority"]["acceptance_record_sha256"] == (
        ACCEPTANCE_DIGEST
    )
    assert package["core_file_count"] == len(package["core_files"]) == 14
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["authorization_may_be_inferred_from_acceptance_continue_package_preparation_or_static_validation"] is False


def test_action_spec_is_single_attempt_exact_and_fail_closed() -> None:
    action = _read(ACTION_SPEC)

    assert action["preparation_authority"]["acceptance_sha256"] == (
        ACCEPTANCE_DIGEST
    )
    assert action["maximum_attempts"] == 1
    assert action["authorization_window_seconds"] == 86400
    assert action["failed_attempt_consumes_authorization"] is True
    assert action["automatic_retry"] is False
    assert action["exact_runtime_candidate"]["alternate_discovery"] is False

    inputs = {item["path"]: item["sha256"] for item in action["exact_accepted_inputs"]}
    assert inputs["tools/phase36_quarantine_generated_validation.ps1"] == (
        HARNESS_DIGEST
    )
    for path, digest in inputs.items():
        assert _sha256(ROOT / path) == digest

    ids = [item["action_id"] for item in action["exact_action_sequence"]]
    assert ids == [
        "U3P-A01-PACKAGE-AUTHORITY-PREFLIGHT",
        "U3P-A02-AUTHORIZATION-RECORD",
        "U3P-A03-RUNTIME-PATH-CLASSIFY",
        "U3P-A04-RUNTIME-BIND",
        "U3P-A05-SOURCE-BINDINGS-PREFLIGHT",
        "U3P-A06-GENERATED-VALIDATION",
        "U3P-A07-SANITIZED-RESULT-CLASSIFICATION",
        "U3P-A08-POSTEXECUTION-BINDING-AND-EVIDENCE",
    ]
    assert action["validation_expectations"]["total_generated_vectors_required_and_passed"] == 84
    assert action["validation_expectations"]["runner_Storage_invocation_count"] == 0
    assert action["validation_expectations"]["windows_adapter_import_or_execution_count"] == 0
    assert action["sanitized_failure_contract"]["allowed_reason_codes"] == [
        "binding_failed",
        "manifest_failed",
        "parser_failed",
        "contract_failed",
        "handler_failed",
        "result_serialization_failed",
    ]
    assert action["current_effect"]["attempts_authorized"] == 0
    assert action["current_effect"][
        "runtime_observation_or_PowerShell_execution_authorized"
    ] is False


def test_proposal_and_package_preserve_non_effective_boundaries() -> None:
    proposal = _read(PROPOSAL)
    package = _read(PACKAGE)

    assert proposal["decision_id"] == DECISION
    assert proposal["current_effect"]["owner_U3P_authorization_pending"] is True
    assert proposal["current_effect"]["attempts_authorized"] == 0
    assert proposal["authorization_may_be_inferred_from_acceptance_continue_or_package_preparation"] is False
    assert "<U3P_R2_AUTHORIZATION_PACKAGE_DIGEST_SHA256>" in proposal[
        "future_owner_authorization_statement_template"
    ]
    assert package["current_gate_effect"][
        "D_P3_6_U3P_GENERATED_VALIDATION_RUNTIME_BINDING_R2_AUTH_requestable"
    ] is True
    assert package["current_gate_effect"]["attempts_authorized"] == 0
    for key, value in package["current_gate_effect"].items():
        if key.endswith("_authorized") and isinstance(value, bool):
            assert value is False
    assert package["current_gate_effect"][
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable"
    ] is False


def test_canonical_ledgers_and_human_records_bind_package() -> None:
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read(CONTRACTS / name)
        state = ledger[
            "quarantine_generated_validation_runtime_binding_r2_"
            "authorization_package"
        ]
        assert state["package_digest_sha256"] == PACKAGE_DIGEST
        assert state["owner_decision_id"] == DECISION
        assert state["owner_U3P_authorization_pending"] is False
        assert state["attempts_authorized"] == 1
        assert state["attempts_consumed"] == 1
        assert state["failed_attempt_consumed"] is True
        assert state["sanitized_failure_reason"] == "result_contract_invalid"
        assert state[
            "D_P3_6_U3P_GENERATED_VALIDATION_RUNTIME_BINDING_R2_AUTH_requestable"
        ] is False
        assert state["PowerShell_parser_import_or_execution_authorized"] is False
        assert state["runtime_observation_authorized"] is False
        assert state["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

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


def test_exact_attempt_outputs_are_consumed_and_fail_closed() -> None:
    expected = {
        "authorization": (
            "4C0E3A4F68BA036E9F55E57F7F413FDE4D13DE0D89BC07F030225093A0FA6C10"
        ),
        "result": (
            "44450DF4D5A199DA34E5343AE043E138B8E046EF4E6FE6EAD6836AC96F7085F4"
        ),
        "evidence": (
            "634674D4C50BB63AAF1A73FFEABB804AC51439002787542E76EB66627A9AD3DE"
        ),
    }
    for suffix in ("authorization", "result", "evidence"):
        path = (
            CONTRACTS
            / "p3-6-quarantine-generated-validation-runtime-binding-r2-"
            f"{suffix}.json"
        )
        assert _sha256(path) == expected[suffix]

    authorization = _read(
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r2-"
        "authorization.json"
    )
    result = _read(
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r2-result.json"
    )
    evidence = _read(
        CONTRACTS
        / "p3-6-quarantine-generated-validation-runtime-binding-r2-evidence.json"
    )
    assert authorization["effective_for_additional_attempt"] is False
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert result["reason_code"] == "result_contract_invalid"
    assert result["automatic_retry_performed"] is False
    assert evidence["gate_effect"]["successful_current_U3P_evidence"] is False
    assert evidence["gate_effect"]["U3K_package_preparation_authorized"] is False

    acceptance = _read(ACCEPTANCE)
    assert _sha256(ACCEPTANCE) == ACCEPTANCE_DIGEST
    assert acceptance["accepted_effect"]["retry_authorized"] is False


def test_line_endings_are_explicit() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (ACTION_SPEC, PROPOSAL, PACKAGE, REVIEW, Path(__file__)):
        assert f"{path.name} text eol=lf" in attributes
