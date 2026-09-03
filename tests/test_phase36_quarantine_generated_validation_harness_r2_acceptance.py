from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
TOOLS = ROOT / "tools"

ACCEPTANCE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-implementation-"
    "acceptance.json"
)
PACKAGE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-implementation-"
    "package.json"
)
EVIDENCE = (
    CONTRACTS
    / "p3-6-quarantine-generated-validation-harness-r2-implementation-"
    "evidence.json"
)
REVIEW = (
    DOCS
    / "p3-6-quarantine-generated-validation-harness-r2-implementation-"
    "evidence-review.md"
)
HARNESS = TOOLS / "phase36_quarantine_generated_validation.ps1"

DECISION = (
    "D-P3.6-U3Q-VALIDATION-HARNESS-R2-BOOTSTRAP-REMEDIATION-"
    "IMPLEMENTATION-ACCEPTANCE"
)
ACCEPTANCE_DIGEST = (
    "32BA42A51029920AE163866A923547CD16054D6C41ECD3C8EC5549B78FB3ED2E"
)
PACKAGE_DIGEST = (
    "2D59FA211DE5DFE331128F189400A28D0D30FAF1BD5C01F077EB6FECF4C236FF"
)
EVIDENCE_DIGEST = (
    "90F3F6F42C73F573A82D1BF5C790B217F891B23D97198916A17FD436B94A8591"
)
HARNESS_DIGEST = (
    "830D88F8915B084DEF1089927FF785C9C0E7BDB6F0755B5315EE85E9DA8A8B8A"
)
OWNER_STATEMENT_DIGEST = (
    "3DAC170ABD42E3416909062AC6BBAA80A4131FC8FDF28B11EC12160219F4DE12"
)
IMMUTABLE_HASHES = {
    "contracts/phase-3/"
    "p3-6-quarantine-generated-powershell-validation-r0-vectors.json": (
        "5C9C9CF9AF61D7AE6F20B4150592B57A4AC540AA983A35CB8384BBD82C764C0C"
    ),
    "tools/phase36_quarantine_transaction_runner.ps1": (
        "22F2A530C5D1CFC8109F2F3A2F8D7458A3E035A12DD7CFFF00EE49CA0E2C212A"
    ),
    "tools/phase36_quarantine_machine_handlers.psm1": (
        "41C93756BDDFDFE55B99CC6C1308FAD5EE34E2962BA99D40B9EFEDEDDDC9A721"
    ),
    "tools/phase36_quarantine_windows_storage_adapter.psm1": (
        "232F21819F845E35C6D576AA499B05699033E439CB9223742C21FD08FFF262A9"
    ),
}


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


def test_exact_owner_acceptance_is_digest_bound() -> None:
    acceptance = _read(ACCEPTANCE)
    statement = acceptance["owner_statement"].encode("utf-8")

    assert _sha256(ACCEPTANCE) == ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == DECISION
    assert acceptance["accepted_by"] == "mayank-admin"
    assert len(statement) == acceptance["owner_statement_utf8_bytes"] == 1212
    assert hashlib.sha256(statement).hexdigest().upper() == OWNER_STATEMENT_DIGEST
    assert acceptance["owner_statement_sha256"] == OWNER_STATEMENT_DIGEST


def test_acceptance_binds_exact_immutable_package_and_evidence() -> None:
    acceptance = _read(ACCEPTANCE)

    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert _sha256(EVIDENCE) == EVIDENCE_DIGEST
    assert _sha256(HARNESS) == HARNESS_DIGEST
    assert acceptance["accepted_package"] == {
        "path": (
            "contracts/phase-3/p3-6-quarantine-generated-validation-harness-"
            "r2-implementation-package.json"
        ),
        "sha256": PACKAGE_DIGEST,
        "accepted_commit": "2770637c4d0d728a1b8584af2a25c18b365a13b4",
        "mutated_by_this_acceptance": False,
    }
    assert acceptance["accepted_evidence"]["sha256"] == EVIDENCE_DIGEST
    assert acceptance["accepted_evidence"]["review_sha256"] == _sha256(REVIEW)


def test_accepted_sources_remain_byte_exact() -> None:
    for path, expected in IMMUTABLE_HASHES.items():
        assert _sha256(ROOT / path) == expected


def test_acceptance_authorizes_planning_only() -> None:
    effect = _read(ACCEPTANCE)["accepted_effect"]

    assert effect["harness_R2_source_accepted"] is True
    assert effect["generated_static_evidence_accepted"] is True
    assert effect["compatibility_transitions_accepted"] is True
    assert effect[
        "separate_non_effective_U3R_runtime_binding_planning_package_"
        "preparation_authorized"
    ] is True
    assert effect["U3R_planning_contracts_static_tests_ledgers_and_docs_authorized"]
    for field in (
        "accepted_harness_runner_handler_or_adapter_source_change_authorized",
        "PowerShell_parser_import_or_execution_authorized",
        "runtime_or_hardware_observation_authorized",
        "retry_or_generated_validation_attempt_authorized",
        "machine_storage_F_B_ACL_probe_cleanup_or_scanner_action_authorized",
        "network_download_artifact_model_inference_camera_media_or_data_action_authorized",
        "container_Kubernetes_profile_activation_deployment_or_remote_git_authorized",
        "D_P3_6_U3R_GENERATED_VALIDATION_RUNTIME_BINDING_R3_AUTH_requestable_before_package",
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable",
    ):
        assert effect[field] is False


def test_canonical_ledgers_add_acceptance_without_mutating_history() -> None:
    historical_key = (
        "quarantine_generated_validation_harness_r2_bootstrap_remediation_"
        "implementation_authorization_package"
    )
    acceptance_key = (
        "quarantine_generated_validation_harness_r2_implementation_acceptance"
    )
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read(CONTRACTS / name)
        historical = ledger[historical_key]
        current = ledger[acceptance_key]

        assert historical["implementation_package_sha256"] == PACKAGE_DIGEST
        assert historical["owner_implementation_acceptance_pending"] is True
        assert current["acceptance_sha256"] == ACCEPTANCE_DIGEST
        assert current["accepted_package_sha256"] == PACKAGE_DIGEST
        assert current["owner_implementation_acceptance_pending"] is False
        assert current["source_and_generated_static_evidence_accepted"] is True
        assert current["U3R_planning_package_preparation_authorized"] is True
        assert current[
            "D_P3_6_U3R_GENERATED_VALIDATION_RUNTIME_BINDING_R3_AUTH_requestable"
        ] is False
        assert current["PowerShell_parser_import_or_execution_authorized"] is False
        assert current["runtime_or_retry_authorized"] is False
        assert current["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False


def test_unblock_plan_exposes_only_non_effective_U3R_planning() -> None:
    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_U3R_runtime_binding_planning_action"
    ]

    assert action["authority"] == "U3Q_owner_acceptance_planning_only"
    assert action["U3R_planning_package_preparation_authority"] is True
    assert action["owner_U3Q_implementation_acceptance_recorded"] is True
    for field in (
        "PowerShell_parser_import_or_execution_authority",
        "runtime_or_hardware_observation_authority",
        "retry_or_generated_validation_attempt_authority",
        "machine_storage_network_or_scanner_authority",
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable",
        "deployment_authority",
        "remote_git_authority",
    ):
        assert action[field] is False


def test_human_records_and_line_endings_are_synchronized() -> None:
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
        assert DECISION in text
        assert PACKAGE_DIGEST in text
        assert ACCEPTANCE_DIGEST in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (ACCEPTANCE, Path(__file__)):
        assert f"{path.name} text eol=lf" in attributes
