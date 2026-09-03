import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
ACTION_SPEC = CONTRACTS / "p3-6-consolidated-runtime-closeout-action-spec.json"
PROPOSAL = CONTRACTS / "p3-6-consolidated-runtime-closeout-authorization-proposal.json"
PACKAGE = CONTRACTS / "p3-6-consolidated-runtime-closeout-authorization-package.json"
BUILD_PACKAGE = CONTRACTS / "p3-6-consolidated-build-package.json"
REVIEW = ROOT / "docs/phase-3/p3-6-consolidated-runtime-closeout-authorization-proposal.md"


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


def test_runtime_package_binds_every_core_file_and_has_no_placeholder() -> None:
    package = _read(PACKAGE)

    assert package["core_file_count"] == len(package["core_files"])
    assert len({item["path"] for item in package["core_files"]}) == package[
        "core_file_count"
    ]
    for item in package["core_files"]:
        if item["path"] == Path(__file__).relative_to(ROOT).as_posix():
            assert item["sha256"] == (
                "E8001AFD5B558EEBA51A0714C02DCD2C9F22B65F93A74AF4D3323130983B82EF"
            )
            continue
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    for path in (ACTION_SPEC, PROPOSAL, PACKAGE):
        assert "<FINAL_" not in path.read_text(encoding="utf-8")


def test_action_spec_has_ordered_fail_closed_runtime_and_U3K_sequence() -> None:
    spec = _read(ACTION_SPEC)
    actions = spec["ordered_action_sequence"]

    assert [item["sequence"] for item in actions] == list(range(1, 11))
    assert len({item["action_id"] for item in actions}) == 10
    assert spec["logical_node_id"] == "LAB-LAPTOP-01"
    assert spec["generated_validation_bounds"]["total_generated_cases"] == 500
    assert spec["generated_validation_bounds"]["outer_controller_cases"] == 416
    assert spec["generated_validation_bounds"]["runner_contract_cases"] == 20
    assert spec["generated_validation_bounds"]["pure_handler_cases"] == 64
    assert spec["U3K_storage_binding"]["maximum_storage_attempts"] == 1
    assert spec["U3K_storage_binding"]["automatic_retry"] is False
    assert spec["U3K_storage_binding"]["prohibited_volume"] == "B:"


def test_retry_policy_is_bounded_transient_pre_U3K_and_same_digest_only() -> None:
    policy = _read(ACTION_SPEC)["attempt_policy"]

    assert policy["maximum_total_runtime_attempts"] == 3
    assert policy["automatic_retry"] is False
    assert policy["parallel_attempts"] is False
    assert policy["retry_requires_same_action_spec_source_and_package_digests"] is True
    assert len(policy["allowlisted_transient_retry_reasons"]) == 3
    assert policy["U3K_storage_attempt_maximum"] == 1
    assert policy["retry_after_U3K_machine_or_storage_action_begins"] is False
    assert "source_or_package_hash_mismatch" in policy["non_retryable_reasons"]
    assert "U3K_attempt_consumed" in policy["non_retryable_reasons"]


def test_runtime_and_all_exact_source_bindings_are_current() -> None:
    spec = _read(ACTION_SPEC)

    assert spec["exact_runtime_candidate"]["path"] == (
        "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    )
    assert len(spec["exact_runtime_candidate"]["required_fixed_parent_components"]) == 3
    assert len(spec["exact_source_bindings"]) == 11
    for item in spec["exact_source_bindings"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]


def test_proposal_is_non_effective_and_requires_exact_owner_statement() -> None:
    proposal = _read(PROPOSAL)
    effect = proposal["current_effect"]

    assert proposal["decision_id"] == "D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-AUTH"
    assert proposal["status"] == "non_effective_owner_authorization_pending"
    assert effect["owner_authorization_pending"] is True
    assert effect["D_P3_6_CONSOLIDATED_RUNTIME_CLOSEOUT_AUTH_requestable"] is True
    assert effect["PowerShell_runtime_machine_storage_U3K_or_closeout_authorized"] is False
    assert effect["commit_authorized"] is False
    assert effect["push_or_remote_Git_authorized"] is False
    assert "I, mayank-admin" in proposal["future_owner_authorization_statement_template"]


def test_output_paths_preserve_consumed_attempt_and_pending_acceptance() -> None:
    outputs = _read(ACTION_SPEC)["exact_future_outputs"]
    consumed_outputs = {
        "contracts/phase-3/p3-6-consolidated-runtime-closeout-authorization.json",
        "contracts/phase-3/p3-6-consolidated-runtime-closeout-result.json",
        "contracts/phase-3/p3-6-consolidated-runtime-closeout-evidence.json",
    }
    consumed_attempt_outputs = {
        "contracts/phase-3/p3-6-quarantine-storage-r2-authorization.json",
        "contracts/phase-3/p3-6-quarantine-storage-r2-result.json",
        "contracts/phase-3/p3-6-quarantine-storage-r2-evidence.json",
    }
    accepted_outputs = {
        "contracts/phase-3/p3-6-consolidated-runtime-closeout-acceptance.json",
    }

    assert len(outputs) == len(set(outputs)) == 7
    assert set(outputs) == consumed_outputs | consumed_attempt_outputs | accepted_outputs
    assert all((ROOT / path).is_file() for path in consumed_outputs)
    assert all((ROOT / path).is_file() for path in consumed_attempt_outputs)
    assert all((ROOT / path).is_file() for path in accepted_outputs)


def test_package_and_human_review_preserve_non_authorization() -> None:
    package = _read(PACKAGE)
    gate = package["current_gate_effect"]
    review = REVIEW.read_text(encoding="utf-8")

    assert package["decision_id"] == "D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-AUTH"
    assert package["build_package_sha256"] == _sha256(BUILD_PACKAGE)
    assert gate["owner_runtime_closeout_authorization_pending"] is True
    assert gate["runtime_machine_storage_U3K_or_closeout_authorized"] is False
    assert gate["commit_push_or_remote_Git_authorized"] is False
    assert "non-effective" in review
    assert "No retry" in review


def test_new_closeout_files_are_lf_terminated() -> None:
    for path in (ACTION_SPEC, PROPOSAL, PACKAGE, REVIEW, Path(__file__)):
        payload = path.read_bytes()
        assert payload.endswith(b"\n")
        assert b"\r\n" not in payload
