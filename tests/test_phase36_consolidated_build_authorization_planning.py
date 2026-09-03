from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"

DECISIONS = CONTRACTS / "p3-6-consolidated-two-authorization-policy-decision-packet.json"
PACKAGE = CONTRACTS / "p3-6-consolidated-build-authorization-planning-package.json"
REVIEW = DOCS / "p3-6-consolidated-two-authorization-policy-decision-packet.md"

PACKAGE_DIGEST = "DC0C28564207F87E64441CEF146CB711E203B11694D08997E82C1962CCD0414C"
U4B_PACKAGE_DIGEST = "E52680B8314FA9A4FC862510BC9570DE3942A791952F22425E61ED61723222AE"
BUILD_DECISION = "D-P3.6-CONSOLIDATED-BUILD-AUTH"
RUNTIME_DECISION = "D-P3.6-CONSOLIDATED-RUNTIME-CLOSEOUT-AUTH"


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


def test_policy_has_six_complete_A_to_D_choices_without_inferred_selection() -> None:
    packet = _read(DECISIONS)
    decisions = packet["decisions"]

    assert [item["decision_id"] for item in decisions] == [
        "D-P3.6-CA-001",
        "D-P3.6-CA-002",
        "D-P3.6-CA-003",
        "D-P3.6-CA-004",
        "D-P3.6-CA-005",
        "D-P3.6-CA-006",
    ]
    for decision in decisions:
        assert decision["recommended_option"] == "A"
        assert decision["selected_option"] is None
        assert set(decision["options"]) == {"A", "B", "C", "D"}
    assert packet["recommended_selection"] == "A/A/A/A/A/A"
    assert packet["current_effect"]["owner_policy_selection_pending"] is True


def test_policy_defines_exactly_two_future_special_authorizations() -> None:
    packet = _read(DECISIONS)
    authorizations = packet["two_special_authorizations"]

    assert len(authorizations) == 2
    assert [item["decision_id"] for item in authorizations] == [
        BUILD_DECISION,
        RUNTIME_DECISION,
    ]
    assert authorizations[0]["machine_runtime_or_PowerShell_execution"] is False
    assert authorizations[1][
        "requires_exact_successfully_validated_build_and_action_package_digest"
    ] is True


def test_package_digest_and_all_nine_core_bindings_match() -> None:
    package = _read(PACKAGE)

    assert _sha256(PACKAGE) == PACKAGE_DIGEST
    assert package["decision_id"] == BUILD_DECISION
    assert package["core_file_count"] == len(package["core_files"]) == 9
    assert len({item["path"] for item in package["core_files"]}) == 9
    for item in package["core_files"]:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert package["core_files"][2]["sha256"] == U4B_PACKAGE_DIGEST


def test_build_scope_is_exact_unique_implemented_and_bounded() -> None:
    package = _read(PACKAGE)
    future_paths = package["exact_future_additive_paths"]
    sync_paths = package["bounded_existing_synchronization_paths"]

    assert len(future_paths) == len(set(future_paths)) == 20
    assert len(sync_paths) == len(set(sync_paths)) == 13
    assert all((ROOT / path).exists() and (ROOT / path).is_file() for path in future_paths)
    assert all((ROOT / path).exists() for path in sync_paths)
    authority = package["consolidated_build_authority_if_exactly_accepted"]
    assert authority["maximum_source_revision_cycles"] == 8
    assert authority["exact_future_additive_path_count"] == 20
    assert authority["bounded_existing_synchronization_path_count"] == 13
    assert authority[
        "prepare_non_effective_exact_digest_bound_D_P3_6_CONSOLIDATED_RUNTIME_CLOSEOUT_AUTH_package"
    ] is True


def test_build_and_second_authorization_boundaries_remain_fail_closed() -> None:
    package = _read(PACKAGE)
    build = package["consolidated_build_authority_if_exactly_accepted"]
    second = package["second_authorization_package_requirements"]
    gate = package["current_gate_effect"]

    assert build["PowerShell_parse_import_dot_source_or_execution"] is False
    assert build[
        "Python_filesystem_runtime_registry_environment_network_native_API_subprocess_machine_controller_or_fallback_access"
    ] is False
    assert build[
        "runtime_manifest_hardware_machine_storage_scanner_network_model_media_or_data_action"
    ] is False
    assert build["container_Kubernetes_profile_activation_deployment_commit_push_or_remote_Git"] is False
    assert second["prepared_only_after_all_consolidated_build_gates_pass"] is True
    assert second["bind_exact_source_evidence_action_spec_runtime_and_output_paths"] is True
    assert second["maximum_total_attempts"] == 3
    assert second["retry_allowlist_transient_and_same_digest_only"] is True
    assert second[
        "deterministic_policy_hash_trust_source_or_scope_failure_stops_without_retry"
    ] is True
    assert second["push_or_remote_Git"] is False
    assert gate["D_P3_6_CONSOLIDATED_BUILD_AUTH_requestable"] is True
    assert gate["source_contract_vector_test_or_evidence_implementation_authorized"] is False
    assert gate["runtime_machine_storage_retry_U3K_or_closeout_authorized"] is False
    assert gate["commit_push_or_remote_Git_authorized"] is False


def test_canonical_ledgers_expose_consolidated_gate_and_U4B_fallback() -> None:
    key = "p3_6_consolidated_build_authorization_planning_package"
    for name in (
        "p3-6-entry-gates.json",
        "p3-6-capability-profile-policy.json",
        "p3-6-unblock-plan.json",
    ):
        state = _read(CONTRACTS / name)
        gate = state[key]
        assert gate["decision_id"] == BUILD_DECISION
        assert gate["package_digest_sha256"] == PACKAGE_DIGEST
        assert gate["recommended_selection"] == "A/A/A/A/A/A"
        assert gate["owner_policy_selection_and_build_authorization_pending"] is True
        assert gate["U4B_granular_authorization_remains_available_as_fallback"] is True
        assert gate["implementation_or_runtime_authorized"] is False

    action = _read(CONTRACTS / "p3-6-unblock-plan.json")[
        "next_consolidated_build_authorization_action"
    ]
    assert action["decision_id"] == BUILD_DECISION
    assert action["authorization_package_sha256"] == PACKAGE_DIGEST
    assert action["owner_authorization_pending"] is True


def test_human_records_and_LF_registry_expose_current_consolidated_gate() -> None:
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
        assert BUILD_DECISION in text
        assert RUNTIME_DECISION in text
        assert PACKAGE_DIGEST in text or path == REVIEW

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for path in (DECISIONS, PACKAGE, REVIEW, Path(__file__)):
        relative = path.relative_to(ROOT).as_posix()
        assert f"{relative} text eol=lf" in attributes
        assert b"\r\n" not in path.read_bytes()
