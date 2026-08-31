from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-transaction-runner-r0-runtime-binding-acceptance.json"
)
PROPOSAL = CONTRACTS / "p3-6-quarantine-storage-r2-final-u3k-authorization-proposal.json"
PACKAGE = CONTRACTS / "p3-6-quarantine-storage-r2-final-u3k-authorization-package.json"
REVIEW = DOCS / "p3-6-quarantine-storage-r2-final-u3k-authorization-proposal.md"
ACCEPTANCE_DIGEST = (
    "F19E6660FBD9545F74B8B532F6A9EB4D01ACF0543DE45CD54C8CB41C868DB54E"
)
PROPOSAL_DIGEST = (
    "CF63D854A38A7DA53D701ED696BE403BBC3180F7A99AB83C182A7D8B7BAECFB5"
)
REVIEW_DIGEST = (
    "778B73A4491A982A7DE7CA641CEDC0457708CA36272DACA0B24B0ECD2901E72B"
)
PACKAGE_DIGEST = (
    "4120AFF4823B1F10AC0BE902BCE7D3709EE02DFA5202A6B8A954EF83C69B837E"
)
EVIDENCE_DIGEST = (
    "4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C"
)
RUNTIME_DIGEST = (
    "362A356CE7F0940EC74F73A8FC2C990A2CC24A38A11C90BBD8ECA947110AD139"
)
RUNNER_DIGEST = (
    "C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15"
)
ACTION_IDS = [f"U3K-A{number:02d}-{suffix}" for number, suffix in [
    (1, "UTC-CLOCK-START"),
    (2, "PACKAGE-RUNNER-AUTHORITY-VERIFY"),
    (3, "AUTHORIZATION-RECORD"),
    (4, "F-DRIVE-INFO"),
    (5, "CANONICAL-PATH-AND-ABSENCE"),
    (6, "PROTECTED-DACL-CONSTRUCT"),
    (7, "SECURITY-AT-CREATE-ROOT"),
    (8, "NORMALIZED-DACL-VERIFY"),
    (9, "ATOMIC-CAPABILITY-PROBE"),
    (10, "NORMALIZE-HASH-WRITE"),
]]


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_exact_runtime_binding_acceptance_authorizes_only_package_preparation() -> None:
    acceptance = _read(ACCEPTANCE)

    assert _sha256(ACCEPTANCE) == ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == (
        "D-P3.6-U3I-RUNTIME-BINDING-R0-ACCEPTANCE"
    )
    assert acceptance["accepted_evidence"]["evidence_record_sha256"] == (
        EVIDENCE_DIGEST
    )
    assert acceptance["accepted_evidence"]["runtime_sha256"] == RUNTIME_DIGEST
    assert acceptance["accepted_evidence"]["runner_source_sha256"] == RUNNER_DIGEST
    effect = acceptance["accepted_effect"]
    assert effect["runtime_binding_evidence_accepted"] is True
    assert effect["final_U3K_storage_package_preparation_authorized"] is True
    assert effect["final_U3K_execution_authorization_requestable_now"] is False
    for field in [
        "machine_action_handler_implementation_authorized",
        "runner_execution_authorized",
        "storage_attempt_authorized",
        "F_or_ACL_action_authorized",
        "storage_probe_authorized",
        "Defender_or_scanner_action_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "runtime_or_model_execution_authorized",
        "profile_activation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert effect[field] is False


def test_final_u3k_proposal_binds_design_runtime_runner_and_blocker() -> None:
    proposal = _read(PROPOSAL)

    assert _sha256(PROPOSAL) == PROPOSAL_DIGEST
    assert proposal["status"] == (
        "prepared_non_effective_execution_authorization_not_requestable_"
        "machine_handlers_unimplemented"
    )
    assert proposal["accepted_storage_design"]["action_ids"] == ACTION_IDS
    assert proposal["accepted_storage_design"]["exact_candidate_root"] == (
        "F:\\HCAM-Quarantine"
    )
    assert proposal["accepted_runner_binding"]["runner_source_sha256"] == (
        RUNNER_DIGEST
    )
    assert proposal["accepted_runner_binding"][
        "machine_action_handlers_implemented"
    ] is False
    readiness = proposal["readiness_reconciliation"]
    assert readiness["final_U3K_package_preparation_complete"] is True
    assert readiness["execution_authorization_requestable"] is False
    assert readiness["D_P3_6_U3K_STORAGE_R2_AUTH_currently_usable"] is False
    assert readiness["blocking_reason_codes"] == [
        "runner_machine_action_handlers_unimplemented",
        "machine_action_handler_implementation_not_authorized",
        "machine_action_handler_evidence_not_sealed_or_accepted",
    ]
    assert all(
        proposal["gate_effect"][field] is False
        for field in [
            "machine_action_handler_implementation_authorized",
            "runner_execution_authorized",
            "storage_attempt_authorized",
            "F_or_ACL_action_authorized",
            "Defender_or_scanner_action_authorized",
            "artifact_acquisition_authorized",
            "profile_activation_authorized",
            "deployment_authorized",
            "remote_git_authorized",
        ]
    )


def test_final_u3k_package_core_hashes_and_non_effective_state_are_exact() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["core_file_count"] == 14
    assert package["core_file_count"] == len(package["core_files"])
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["readiness"]["final_U3K_package_preparation_complete"] is True
    assert package["readiness"]["machine_action_handlers_implemented"] is False
    assert package["readiness"]["execution_authorization_requestable"] is False
    assert package["readiness"]["storage_attempt_authorized"] is False
    assert package["current_gate_effect"][
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable"
    ] is False
    assert package[
        "authorization_may_be_inferred_from_runtime_binding_acceptance_"
        "continue_or_prior_storage_acceptance"
    ] is False


def test_canonical_ledgers_and_human_records_point_to_handler_proposal_gate() -> None:
    ledgers = [
        _read(CONTRACTS / "p3-6-entry-gates.json"),
        _read(CONTRACTS / "p3-6-capability-profile-policy.json"),
        _read(CONTRACTS / "p3-6-unblock-plan.json"),
    ]

    for ledger in ledgers:
        runtime = ledger[
            "quarantine_transaction_runner_r0_runtime_binding_authorization_package"
        ]
        assert runtime["acceptance_sha256"] == ACCEPTANCE_DIGEST
        assert runtime["owner_evidence_acceptance_pending"] is False
        assert runtime["final_U3K_package_preparation_authorized"] is True
        final_u3k = ledger["quarantine_storage_r2_final_u3k_authorization_package"]
        assert final_u3k["package_digest_sha256"] == PACKAGE_DIGEST
        assert final_u3k["final_U3K_package_preparation_complete"] is True
        assert final_u3k["machine_action_handlers_implemented"] is False
        assert final_u3k["execution_authorization_requestable"] is False
        assert final_u3k["storage_attempt_authorized"] is False

    action = ledgers[2]["next_portable_planning_action"]
    assert action["decision_ids"] == [
        "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-AUTH"
    ]
    assert action["final_U3K_package_digest_sha256"] == PACKAGE_DIGEST
    assert action["machine_handler_proposal_package_digest_sha256"] == (
        "EDD9CA84573B31B33B17250611EE07C555FD2E6CB95AE026200210D7F87AB311"
    )
    assert action["owner_machine_handler_implementation_authorization_pending"]
    assert action["machine_handler_proposal_preparation_authority"] is False
    assert action["machine_handler_implementation_authority"] is False
    assert action["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False

    documents = [
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
    for path in documents:
        assert PACKAGE_DIGEST in path.read_text(encoding="utf-8")
    assert _sha256(REVIEW) == REVIEW_DIGEST
    assert _read(PACKAGE)["core_files"][-2]["sha256"] == PROPOSAL_DIGEST
    assert "DR-0074" in (DOCS / "decision-register.md").read_text(
        encoding="utf-8"
    )
