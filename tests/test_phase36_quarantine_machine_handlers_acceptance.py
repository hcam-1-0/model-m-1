from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
ACCEPTANCE_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-implementation-acceptance.json"
)
PACKAGE_PATH = (
    CONTRACTS / "p3-6-quarantine-machine-handlers-r0-implementation-package.json"
)

DECISION_ID = "D-P3.6-U3L-MACHINE-HANDLERS-R0-IMPLEMENTATION-ACCEPTANCE"
ACCEPTANCE_DIGEST = (
    "06085F3E296B450204FC0E8171314581F40853A11B0AA74161238C390A05B631"
)
PACKAGE_DIGEST = (
    "79F29A6828DDBBE5E0967C4498C753DD19D547714CF8934AEFD93A9D6299B3D7"
)
OWNER_STATEMENT_DIGEST = (
    "B8BFC6E6F78217D535AF2EDCF95038B0C35ABE1132B88BB4A471BED493823499"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_exact_owner_statement_accepts_the_immutable_package() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert _sha256(ACCEPTANCE_PATH) == ACCEPTANCE_DIGEST
    assert acceptance["decision_id"] == DECISION_ID
    assert acceptance["accepted_by"] == "mayank-admin"
    assert acceptance["status"] == (
        "accepted_non_executable_source_and_generated_static_evidence_"
        "separate_planning_only"
    )
    assert hashlib.sha256(
        acceptance["owner_statement"].encode("utf-8")
    ).hexdigest().upper() == OWNER_STATEMENT_DIGEST
    assert acceptance["owner_statement_sha256"] == OWNER_STATEMENT_DIGEST
    assert acceptance["accepted_package"]["sha256"] == PACKAGE_DIGEST
    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert acceptance["accepted_package"]["accepted_commit"] == (
        "7e1acb9f0ed5b616b4d66de670bd83eda7ab133b"
    )
    assert acceptance["accepted_package"]["mutated_by_this_acceptance"] is False


def test_exact_source_hashes_and_generated_evidence_are_accepted() -> None:
    acceptance = _read(ACCEPTANCE_PATH)

    assert len(acceptance["accepted_source_artifacts"]) == 3
    for item in acceptance["accepted_source_artifacts"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    evidence = acceptance["accepted_evidence"]
    assert _sha256(ROOT / evidence["path"]) == evidence["sha256"]
    assert evidence["generated_vectors_passed"] == 64
    assert evidence["generated_and_static_tests_passed"] == 76
    assert evidence["full_Phase_3_6_tests_passed"] == 279
    assert evidence["PowerShell_parsed_imported_or_executed"] is False
    assert evidence["machine_or_network_access"] is False


def test_acceptance_effect_is_planning_only_and_fail_closed() -> None:
    effect = _read(ACCEPTANCE_PATH)["accepted_effect"]

    assert effect["machine_handler_implementation_accepted"] is True
    assert effect["generated_and_static_evidence_accepted"] is True
    assert effect[
        "separate_generated_PowerShell_validation_and_fresh_runtime_binding_"
        "planning_package_preparation_authorized"
    ] is True
    for field in (
        "source_or_test_change_authorized",
        "PowerShell_parser_import_or_execution_authorized",
        "runner_handler_or_adapter_execution_authorized",
        "runtime_or_hardware_observation_authorized",
        "fresh_runtime_binding_exists",
        "new_executable_U3K_package_preparation_authorized",
        "D_P3_6_U3K_STORAGE_R2_AUTH_requestable",
        "storage_attempt_authorized",
        "F_or_ACL_action_authorized",
        "Defender_or_scanner_action_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "model_inference_media_or_data_access_authorized",
        "container_or_Kubernetes_action_authorized",
        "profile_activation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ):
        assert effect[field] is False
    for gate in ("P36_G1", "P36_G2", "P36_G4", "P36_G5"):
        assert effect[gate] == "blocked"


def test_canonical_ledgers_record_acceptance_without_execution_authority() -> None:
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        ledger = _read(CONTRACTS / name)
        state = ledger[
            "quarantine_machine_handlers_r0_implementation_authorization_package"
        ]
        assert state["implementation_package_digest_sha256"] == PACKAGE_DIGEST
        assert state["implementation_acceptance_sha256"] == ACCEPTANCE_DIGEST
        assert state["owner_acceptance_statement_sha256"] == OWNER_STATEMENT_DIGEST
        assert state["owner_implementation_acceptance_pending"] is False
        assert state["machine_handler_implementation_accepted"] is True
        assert state[
            "separate_validation_and_fresh_runtime_binding_planning_authorized"
        ] is True
        assert state["source_or_test_change_authorized"] is False
        assert state["PowerShell_or_runner_execution_authorized"] is False
        assert state["windows_adapter_import_or_execution_authorized"] is False
        assert state["storage_attempt_authorized"] is False
        assert state["F_or_ACL_action_authorized"] is False

    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_portable_planning_action"
    ]
    assert action["action"] == (
        "prepare_separate_non_effective_generated_PowerShell_validation_and_"
        "fresh_runtime_binding_planning_package"
    )
    assert action["machine_handler_implementation_acceptance_sha256"] == (
        ACCEPTANCE_DIGEST
    )
    assert action["owner_implementation_acceptance_pending"] is False
    assert action[
        "generated_PowerShell_validation_planning_package_preparation_authority"
    ] is True
    assert action["runtime_binding_proposal_preparation_authority"] is True
    assert action["PowerShell_or_runner_execution_authority"] is False
    assert action["runtime_binding_observation_authority"] is False
    assert action["D_P3_6_U3K_STORAGE_R2_AUTH_requestable"] is False
    assert action["F_or_ACL_action_authority"] is False


def test_human_indexes_are_synchronized_to_the_exact_acceptance() -> None:
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
        assert ACCEPTANCE_DIGEST in text

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert (
        "p3-6-quarantine-machine-handlers-r0-implementation-acceptance.json "
        "text eol=lf"
    ) in attributes
