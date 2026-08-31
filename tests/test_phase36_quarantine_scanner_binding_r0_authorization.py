from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
STEM = "p3-6-quarantine-scanner-binding-r0"
SOURCES_PATH = CONTRACTS / f"{STEM}-research-sources.json"
ACTION_SPEC_PATH = CONTRACTS / f"{STEM}-action-spec.json"
PROPOSAL_PATH = CONTRACTS / f"{STEM}-authorization-proposal.json"
DOCUMENT_PATH = DOCS / f"{STEM}-authorization-proposal.md"
PACKAGE_PATH = CONTRACTS / f"{STEM}-authorization-package.json"
PACKAGE_DIGEST = "9978206EC0FAFA96D557FE371065B3FC5F7D38A85C74F3CC6708F873EC100B39"
U3H_PACKAGE_DIGEST = (
    "19D4580E86AF04C0ABFB2D082678491F4551360A6A4C71DAE5C6481F98C32C7B"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_package_binds_exact_core_files() -> None:
    package = _read(PACKAGE_PATH)
    expected_paths = {
        f"contracts/phase-3/{STEM}-research-sources.json": SOURCES_PATH,
        f"contracts/phase-3/{STEM}-action-spec.json": ACTION_SPEC_PATH,
        f"contracts/phase-3/{STEM}-authorization-proposal.json": PROPOSAL_PATH,
        f"docs/phase-3/{STEM}-authorization-proposal.md": DOCUMENT_PATH,
    }
    package_hashes = {
        item["path"]: item["sha256"] for item in package["core_files"]
    }

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["core_file_count"] == 4
    assert package_hashes == {
        path: _sha256(file_path) for path, file_path in expected_paths.items()
    }
    assert package["owner_decision_id"] == "D-P3.6-U3E-BINDING-R0-AUTH"


def test_owner_input_is_candidate_only_and_zero_action() -> None:
    sources = _read(SOURCES_PATH)
    owner_input = sources["owner_input"]
    actions = sources["research_actions"]

    assert owner_input["interpreted_candidate_volume"] == "F:"
    assert owner_input["proposed_isolated_root"] == "F:\\HCAM-Quarantine"
    assert owner_input["owner_asserted_free_space_gb"] == 50
    assert owner_input["assertion_is_attested_evidence"] is False
    assert owner_input["volume_or_path_query_performed"] is False
    assert owner_input["directory_created_or_modified"] is False
    for field in [
        "F_volume_or_path_queries",
        "storage_or_hardware_queries",
        "directory_creation_write_probe_or_cleanup",
        "scanner_or_security_product_queries",
        "scanner_executions",
        "artifact_downloads",
        "dependency_installs",
        "runtime_or_model_imports",
        "checkpoint_loading_or_unpickling",
        "inference_calibration_validation_or_benchmarks",
        "container_or_kubernetes_actions",
        "camera_media_or_data_accesses",
        "remote_git_actions",
    ]:
        assert actions[field] == 0


def test_target_is_exact_isolated_local_root_with_both_space_thresholds() -> None:
    target = _read(ACTION_SPEC_PATH)["target"]

    assert target["candidate_volume"] == "F:"
    assert target["candidate_root"] == "F:\\HCAM-Quarantine"
    assert target["excluded_existing_project_root"] == "F:\\h cam"
    assert target["owner_prohibited_volume"] == "B:"
    assert target["required_volume_type"] == "Fixed"
    assert target["allowed_filesystems"] == ["NTFS", "ReFS"]
    assert target["minimum_free_bytes"] == 5 * 1024**3
    assert target["minimum_free_percent"] == 15
    assert target["remote_or_alternate_target_allowed"] is False


def test_transaction_is_one_attempt_bounded_offline_and_ephemeral() -> None:
    bounds = _read(ACTION_SPEC_PATH)["transaction_bounds"]

    assert bounds["maximum_authorized_attempts"] == 1
    assert bounds["authorization_use_window_seconds_after_owner_acceptance"] == 86400
    assert bounds["storage_attestation_validity_seconds_after_success"] == 3600
    assert bounds["per_action_timeout_seconds"] == 30
    assert bounds["total_transaction_timeout_seconds"] == 180
    assert bounds["maximum_probe_bytes"] == 4096
    assert bounds["parallel_actions"] is False
    assert bounds["network_access"] is False
    assert bounds["automatic_retry"] is False
    assert bounds["failed_attempt_requires_new_authorization"] is True


def test_action_allowlist_is_exact_and_probe_has_zero_retention() -> None:
    actions = _read(ACTION_SPEC_PATH)["action_allowlist"]
    by_id = {item["action_id"]: item for item in actions}

    assert list(by_id) == [f"U3E-A{i:02d}-{suffix}" for i, suffix in [
        (1, "UTC-CLOCK-START"),
        (2, "PACKAGE-VERIFY"),
        (3, "F-DRIVE-INFO"),
        (4, "CANONICAL-PATH-SAFETY"),
        (5, "EXACT-ROOT-CREATE"),
        (6, "BOUNDED-ACL-CLASSIFICATION"),
        (7, "ATOMIC-CAPABILITY-PROBE"),
        (8, "DEFENDER-STATUS-METADATA"),
        (9, "DEFENDER-BINARY-CANDIDATE"),
        (10, "MODELSCAN-DISTRIBUTION-METADATA"),
        (11, "HCAM-PASSIVE-INSPECTOR-STATE"),
        (12, "NORMALIZE-HASH-WRITE"),
    ]]
    probe = by_id["U3E-A07-ATOMIC-CAPABILITY-PROBE"]
    assert probe["partial_path"].startswith("F:\\HCAM-Quarantine\\")
    assert probe["verified_path"].startswith("F:\\HCAM-Quarantine\\")
    assert probe["probe_bytes"] == 4096
    assert probe["probe_or_content_retention"] == (
        "zero_after_success_or_bounded_failure_cleanup"
    )
    assert probe["other_file_or_directory_access_allowed"] is False


def test_scanner_actions_are_metadata_only_and_cannot_complete_chain() -> None:
    spec = _read(ACTION_SPEC_PATH)
    actions = {item["action_id"]: item for item in spec["action_allowlist"]}
    defender = actions["U3E-A08-DEFENDER-STATUS-METADATA"]
    defender_binary = actions["U3E-A09-DEFENDER-BINARY-CANDIDATE"]
    modelscan = actions["U3E-A10-MODELSCAN-DISTRIBUTION-METADATA"]
    inspector = actions["U3E-A11-HCAM-PASSIVE-INSPECTOR-STATE"]
    result_policy = spec["scanner_binding_result_policy"]

    assert defender["scan_or_remediation_allowed"] is False
    assert defender["signature_or_platform_update_allowed"] is False
    assert defender_binary["executable_execution_allowed"] is False
    assert modelscan["candidate_version"] == "0.8.8"
    assert modelscan["modelscan_import_or_execution_allowed"] is False
    assert modelscan["installation_download_or_update_allowed"] is False
    assert inspector["repository_or_filesystem_query"] is False
    assert inspector["implementation_or_execution_allowed"] is False
    assert result_policy["scanner_chain_ready_only_when_all_three_complete"] is True
    assert result_policy["this_attempt_may_make_scanner_chain_ready"] is False


def test_sanitization_and_path_prohibitions_are_explicit() -> None:
    spec = _read(ACTION_SPEC_PATH)
    sanitization = spec["sanitization"]
    prohibited = spec["continuing_non_authorization"]

    assert sanitization["persist_exact_operational_locators"][0] == (
        "F:\\HCAM-Quarantine"
    )
    assert "hostname" in sanitization["never_persist"]
    assert "volume_label_or_serial" in sanitization["never_persist"]
    assert "raw_ACL_identity_or_SID" in sanitization["never_persist"]
    assert "Defender_threat_history_preferences_exclusions_quarantine_or_events" in (
        sanitization["never_persist"]
    )
    assert "B_drive_or_F_h_cam_access_or_modification" in prohibited
    assert "remote_git" in prohibited


def test_proposal_and_package_grant_no_current_action() -> None:
    proposal = _read(PROPOSAL_PATH)
    package = _read(PACKAGE_PATH)

    assert proposal["status"] == "owner_review_pending_non_effective"
    assert proposal["current_effect"]["F_volume_attested"] is False
    assert proposal["current_effect"]["candidate_root_created_or_queried"] is False
    assert proposal["current_effect"]["storage_write_probe_authorized"] is False
    assert proposal["current_effect"]["scanner_metadata_query_authorized"] is False
    assert package["owner_acceptance_may_be_inferred_from_continue_or_prior_permission"] is False
    for field in [
        "storage_or_hardware_query_authorized",
        "storage_directory_creation_write_probe_or_cleanup_authorized",
        "scanner_query_authorized",
        "scanner_install_update_or_execution_authorized",
        "artifact_or_dependency_acquisition_authorized",
        "runtime_or_model_execution_authorized",
        "hardware_testing_authorized",
        "profile_resolution_or_activation_authorized",
        "container_or_kubernetes_action_authorized",
        "camera_media_or_data_access_authorized",
        "implementation_authorized",
        "deployment_authorized",
        "remote_git_authorized",
    ]:
        assert package[field] is False


def test_canonical_ledgers_record_consumed_attempt_and_keep_gates_blocked() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    gate_states = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert gate_states["P36-G2"] == "blocked"
    assert gate_states["P36-G4"] == "blocked"
    for ledger in [gates, policy, unblock]:
        state = ledger["quarantine_scanner_binding_r0_authorization_package"]
        digest = state.get("digest_sha256", state.get("package_digest_sha256"))
        assert digest == PACKAGE_DIGEST
        assert state["exact_candidate_root"] == "F:\\HCAM-Quarantine"
        assert state["owner_authorization_pending"] is False
        assert state["attempt_consumed"] is True
        assert state["retry_authorized"] is False
        assert state["artifact_or_dependency_acquisition_authorized"] is False
        assert state["profile_activation_authorized"] is False

    action = unblock["next_portable_planning_action"]
    assert action["runner_implementation_authorization_pending"] is True
    assert action["storage_R2_planning_acceptance_pending"] is True
    assert action["Defender_only_proposal_preparation_authority_now"] is False
    assert action["retry_authorized"] is False
    assert action["another_attempt_authority"] is False


def test_human_records_and_indexes_are_synchronized() -> None:
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    plan = (DOCS / "p3-6-plan.md").read_text(encoding="utf-8")
    unblock = (DOCS / "p3-6-unblock-plan.md").read_text(encoding="utf-8")
    contracts_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    for text in [decision_register, backlog, phase_index, plan, unblock]:
        assert PACKAGE_DIGEST in text
    assert "DR-0061: F: quarantine" in decision_register
    assert "D-P3.6-U3E-BINDING-R0-AUTH" in backlog
    assert f"{STEM}-authorization-package.json" in contracts_index
