from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts/phase-3"
ACTION_SPEC = CONTRACTS / "p3-6-consolidated-runtime-closeout-r2-action-spec.json"
PROPOSAL = (
    CONTRACTS / "p3-6-consolidated-runtime-closeout-r2-authorization-proposal.json"
)
PACKAGE = (
    CONTRACTS / "p3-6-consolidated-runtime-closeout-r2-authorization-package.json"
)
U4D_PACKAGE = (
    CONTRACTS / "p3-6-consolidated-runtime-closeout-u4d-implementation-package.json"
)
U4D_EVIDENCE = (
    CONTRACTS / "p3-6-consolidated-runtime-closeout-u4d-implementation-evidence.json"
)
REVIEW = ROOT / "docs/phase-3/p3-6-consolidated-runtime-closeout-r2-authorization-proposal.md"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_R2_package_binds_every_core_file_and_is_non_effective() -> None:
    package = _read(PACKAGE)

    assert package["core_file_count"] == len(package["core_files"])
    assert len({item["path"] for item in package["core_files"]}) == package[
        "core_file_count"
    ]
    for item in package["core_files"]:
        if item["path"] == (
            "tests/test_phase36_consolidated_runtime_closeout_r2_authorization_proposal.py"
        ):
            assert item["sha256"] == (
                "FCE8DE397F91395014A6009823677F7826B34BE8A42AD3F1325D323ED0BED9D4"
            )
            continue
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["decision_id"] == "D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-R2-AUTH"
    assert package["fixed_authority_if_exactly_accepted"]["maximum_attempts"] == 1
    assert package["fixed_authority_if_exactly_accepted"]["automatic_retry"] is False
    assert package["current_gate_effect"]["owner_runtime_closeout_R2_authorization_pending"] is True
    assert package["current_gate_effect"]["attempts_authorized"] == 0
    assert package["current_gate_effect"]["runtime_machine_storage_U3K_or_closeout_authorized"] is False
    assert package["current_gate_effect"]["commit_push_or_remote_Git_authorized"] is False


def test_R2_action_sequence_is_exact_ordered_and_fail_closed() -> None:
    spec = _read(ACTION_SPEC)
    actions = spec["ordered_action_sequence"]

    assert [item["sequence"] for item in actions] == list(range(1, 14))
    assert len({item["action_id"] for item in actions}) == 13
    assert actions[0]["action_id"] == "R2-A01-PACKAGE-AUTHORITY-PREFLIGHT"
    assert actions[-1]["action_id"] == "R2-A13-CONDITIONAL-PHASE-3-CLOSEOUT"
    policy = spec["attempt_policy"]
    assert policy["maximum_total_runtime_attempts"] == 1
    assert policy["maximum_U3K_storage_attempts"] == 1
    assert policy["automatic_or_manual_retry_under_same_authorization"] is False
    assert policy["failed_attempt_consumes_authorization"] is True
    assert policy["retry_after_any_process_machine_or_storage_action_begins"] is False


def test_R2_runtime_Utility_and_source_bindings_are_exact() -> None:
    spec = _read(ACTION_SPEC)
    runtime = spec["exact_runtime_candidate"]
    utility = spec["exact_Utility_manifest_candidate"]
    closure = spec["Utility_manifest_and_closure_policy"]

    assert runtime["path"] == r"C:\Program Files\PowerShell\7\pwsh.exe"
    assert runtime["required_fixed_parent_components"] == [
        r"C:\Program Files",
        r"C:\Program Files\PowerShell",
        r"C:\Program Files\PowerShell\7",
    ]
    assert runtime["network_or_trust_retrieval"] is False
    assert utility["path"] == (
        r"C:\Program Files\PowerShell\7\Modules\Microsoft.PowerShell.Utility"
        r"\Microsoft.PowerShell.Utility.psd1"
    )
    assert utility["alternate_module_name_PSModulePath_registry_or_directory_search"] is False
    assert closure["ScriptsToProcess_must_be_empty"] is True
    assert closure["maximum_declared_regular_files"] == 64
    assert closure["maximum_total_file_bytes"] == 134217728
    assert closure["preflight_and_postflight_hash_match_required"] is True
    for item in spec["exact_source_bindings"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_R2_generated_process_and_U3K_bounds_are_conservative() -> None:
    spec = _read(ACTION_SPEC)
    generated = spec["generated_validation_bounds"]
    typed = spec["typed_process_output_acceptance"]
    storage = spec["U3K_storage_binding"]

    assert generated["maximum_processes"] == 2
    assert generated["outer_controller_cases"] == 416
    assert generated["runner_contract_cases"] == 20
    assert generated["pure_handler_cases"] == 64
    assert generated["total_generated_cases"] == 500
    assert generated["outer_child_stdout_maximum_bytes"] == 4096
    assert generated["outer_child_stderr_maximum_bytes"] == 0
    assert generated["outer_child_terminal_line_count"] == 1
    assert generated["raw_process_output_exception_fixture_identity_environment_or_security_material_retained"] is False
    assert typed["success_reason"] == "process_result_accepted"
    assert typed["child_success_reason"] == "generated_validation_accepted"
    assert typed["raw_retained_bytes"] == 0
    assert storage["exact_candidate_root"] == r"F:\HCAM-Quarantine"
    assert storage["excluded_project_root"] == r"F:\h cam"
    assert storage["prohibited_volume"] == "B:"
    assert storage["maximum_storage_attempts"] == 1
    assert storage["automatic_retry"] is False


def test_R2_outputs_preserve_consumed_attempt_history_and_closed_gates() -> None:
    spec = _read(ACTION_SPEC)
    outputs = spec["exact_future_outputs"]
    current = spec["current_effect"]

    assert len(outputs) == len(set(outputs)) == 7
    assert all((ROOT / path).exists() for path in outputs[:3])
    assert (ROOT / outputs[3]).exists() is False
    assert all((ROOT / path).is_file() for path in outputs[4:])
    assert _sha256(ROOT / outputs[0]) == (
        "A8F8B8D9DD6DE42948D8B5B9BD2E869A2490D6758578B0D493C6E4C592798B12"
    )
    assert _sha256(ROOT / outputs[1]) == (
        "B49F02F504CF4D02B1D8BA59808154BE180A7EF5B251859F356D18A896E386BC"
    )
    assert _sha256(ROOT / outputs[2]) == (
        "7D76C61B6D2DB5544B3C79BB19B145F27AF371014C174CA8ED8AECDB3AC5D2C6"
    )
    # These are immutable pre-attempt fields in the consumed R2 action spec.
    assert current["owner_runtime_closeout_R2_authorization_pending"] is True
    assert current["attempts_authorized"] == 0
    assert current["PowerShell_parse_import_dot_source_or_execution_authorized"] is False
    assert current["runtime_manifest_hardware_machine_storage_F_or_ACL_action_authorized"] is False
    assert current["U3K_or_Phase_3_closeout_authorized"] is False
    assert current["commit_authorized"] is False
    assert current["push_or_remote_Git_authorized"] is False


def test_R2_proposal_binds_source_evidence_action_spec_and_requires_new_owner_gate() -> None:
    proposal = _read(PROPOSAL)
    required = proposal["required_source_evidence"]
    action = proposal["action_spec"]
    effect = proposal["current_effect"]

    assert required["U4D_implementation_package_sha256"] == _sha256(U4D_PACKAGE)
    assert required["U4D_implementation_evidence_sha256"] == _sha256(U4D_EVIDENCE)
    assert required["immutable_hash_mismatch_count_required"] == 0
    assert required["final_full_generated_static_validation_required"] is True
    assert action["sha256"] == _sha256(ACTION_SPEC)
    assert action["maximum_total_runtime_attempts"] == 1
    assert action["automatic_or_manual_retry"] is False
    assert effect["owner_authorization_pending"] is True
    assert effect["attempts_authorized"] == 0
    assert effect["PowerShell_parser_import_dot_source_or_execution_authorized"] is False
    assert effect["runtime_manifest_hardware_machine_storage_U3K_or_closeout_authorized"] is False
    assert effect["commit_authorized"] is False
    assert effect["push_or_remote_Git_authorized"] is False
    statement = proposal["future_owner_authorization_statement_template"]
    assert statement.count("<THIS_PACKAGE_SHA256>") == 1
    assert "exactly one ordered attempt" in statement
    assert "Any failure consumes this authorization and permits no retry" in statement


def test_R2_records_are_LF_registered_and_review_preserves_non_authorization() -> None:
    paths = [ACTION_SPEC, PROPOSAL, PACKAGE, REVIEW, Path(__file__)]
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")

    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        assert attributes.count(f"{relative} text eol=lf") == 1
        assert "\r\n" not in path.read_text(encoding="utf-8")
    assert "non-effective" in review
    assert "exactly one attempt" in review.lower()
    assert "does not authorize PowerShell" in review
