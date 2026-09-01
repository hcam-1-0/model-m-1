from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
STEM = "p3-6-portable-r1-supply-chain-prerequisite"
SOURCES_PATH = CONTRACTS / f"{STEM}-research-sources.json"
PROPOSAL_PATH = CONTRACTS / f"{STEM}-proposal.json"
DECISIONS_PATH = CONTRACTS / f"{STEM}-decision-packet.json"
DOCUMENT_PATH = DOCS / f"{STEM}-proposal.md"
PACKAGE_PATH = CONTRACTS / f"{STEM}-package.json"
PACKAGE_DIGEST = "496F4A9C7D6325868283589EAA108F4A26C9CAE3F7BE49102685706CCC2AA16B"
ACCEPTANCE_DIGEST = (
    "F68BDE02AF96E3992A8C64F1F01A85CAC960F529946EA12FA4899D9EBFC197A9"
)
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
        f"contracts/phase-3/{STEM}-proposal.json": PROPOSAL_PATH,
        f"contracts/phase-3/{STEM}-decision-packet.json": DECISIONS_PATH,
        f"docs/phase-3/{STEM}-proposal.md": DOCUMENT_PATH,
    }
    package_hashes = {
        item["path"]: item["sha256"] for item in package["core_files"]
    }

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["core_file_count"] == 4
    assert package_hashes == {
        path: _sha256(file_path) for path, file_path in expected_paths.items()
    }
    assert package["accepted_U3C_policy"]["selection"] == "A/A/A/A"


def test_research_ledger_is_primary_source_and_zero_action() -> None:
    sources = _read(SOURCES_PATH)
    source_urls = {item["url"] for item in sources["official_external_sources"]}
    actions = sources["research_actions"]

    assert source_urls == {
        "https://learn.microsoft.com/en-us/defender-endpoint/"
        "command-line-arguments-microsoft-defender-antivirus",
        "https://github.com/protectai/modelscan",
        "https://docs.pytorch.org/docs/2.13/generated/torch.load.html",
        "https://cyclonedx.org/guides/"
        "OWASP-CycloneDX-Authoritative-Guide-to-AI-ML-BOM-en.pdf",
    }
    assert actions["public_document_pages_read"] == 4
    for field in [
        "storage_or_hardware_queries",
        "scanner_or_security_product_queries",
        "scanner_executions",
        "artifact_downloads",
        "dependency_installs",
        "runtime_or_model_imports",
        "checkpoint_loading_or_unpickling",
        "inference_calibration_validation_or_benchmarks",
        "inventory_collection_attempts",
        "container_or_kubernetes_actions",
        "camera_media_or_data_accesses",
        "remote_git_actions",
    ]:
        assert actions[field] == 0


def test_storage_policy_is_unbound_local_and_fail_closed() -> None:
    proposal = _read(PROPOSAL_PATH)
    blockers = proposal["current_blocker_state"]
    storage = proposal["recommended_storage_readiness_policy_A"]

    assert blockers["exact_physical_root"] is None
    assert blockers["owner_prohibited_volume"] == "B:"
    assert blockers["historically_observed_ineligible_volumes"] == [
        "C:",
        "E:",
        "F:",
    ]
    assert blockers["historical_observation_is_current_authority"] is False
    assert storage["allowed_volume_class"] == "local_fixed_physical_volume_only"
    assert storage["allowed_filesystems"] == ["NTFS", "ReFS"]
    assert storage["minimum_free_bytes"] == 5 * 1024**3
    assert storage["minimum_free_percent"] == 15
    assert storage["fresh_bounded_storage_attestation_required"] is True
    assert storage["attestation_max_age_at_R1_authorization_minutes"] == 60
    assert storage["write_probe_authorized_now"] is False
    assert "root_with_symlink_junction_mountpoint_or_other_reparse_component" in (
        storage["prohibited"]
    )


def test_scanner_chain_requires_three_exact_passive_layers() -> None:
    scanner = _read(PROPOSAL_PATH)["recommended_scanner_chain_policy_A"]
    defender = scanner["layer_1_platform_antimalware_candidate"]
    modelscan = scanner["layer_2_model_serialization_scanner_candidate"]
    inspector = scanner["layer_3_passive_structure_inspector_candidate"]

    assert defender["command_argv_template"][-2:] == [
        "-DisableRemediation",
        "-ReturnHR",
    ]
    assert defender["zero_exit_alone_is_pass"] is False
    assert defender["version"] is None
    assert defender["executable_path"] is None
    assert modelscan["candidate_version"] == "0.8.8"
    assert modelscan["installed_or_verified"] is False
    assert modelscan["pass_exit_code"] == 0
    assert modelscan["reject_exit_codes"] == [1, 2, 3, 4]
    assert inspector["implementation"] is None
    assert {
        "torch_load",
        "pickle_load_or_unpickle",
        "framework_import_or_model_constructor",
        "GPU_or_accelerator_access",
        "network_access",
    }.issubset(inspector["forbidden_operations"])
    assert scanner["scanner_success_is_safety_proof"] is False
    assert scanner["scanner_success_is_profile_or_promotion_evidence"] is False


def test_verdict_is_complete_fail_closed_and_not_overridable() -> None:
    verdict = _read(PROPOSAL_PATH)["recommended_verdict_policy_A"]

    assert "platform_antimalware_clean_unambiguous" in verdict["pass_requires"]
    assert "model_serialization_scan_clean_supported_and_complete" in (
        verdict["pass_requires"]
    )
    assert "passive_structure_inspection_clean_supported_and_complete" in (
        verdict["pass_requires"]
    )
    assert "unsupported_skipped_truncated_or_malformed_result" in (
        verdict["fail_closed_on"]
    )
    assert "ambiguous_Defender_zero_or_remediation_result" in (
        verdict["fail_closed_on"]
    )
    assert verdict["manual_override_of_hard_failure"] is False
    assert verdict["cleanup_or_deletion_authorized"] is False


def test_acquisition_lifecycle_is_sequential_atomic_and_bom_bound() -> None:
    lifecycle = _read(PROPOSAL_PATH)["recommended_acquisition_lifecycle_A"]

    assert lifecycle["concurrency"] == 1
    assert lifecycle["parallel_downloads"] is False
    assert lifecycle["direct_download_to_final_name"] is False
    assert lifecycle["automatic_retry"] is False
    assert lifecycle["automatic_delete_or_cleanup"] is False
    assert lifecycle["sequence"][1] == (
        "create_exact_candidate_partial_file_exclusively"
    )
    assert "compute_SHA_256_and_verify_publisher_identity_metadata" in (
        lifecycle["sequence"]
    )
    assert "write_bounded_redacted_reports_and_CycloneDX_1_6_ML_BOM" in (
        lifecycle["sequence"]
    )
    assert lifecycle["checkpoint_loading_conversion_export_inference_or_benchmark"] is False


def test_R1_and_R2_are_immutable_and_separately_authorized() -> None:
    separation = _read(PROPOSAL_PATH)["recommended_R1_R2_separation_policy_A"]

    assert "torch_load_even_with_weights_only" in separation["R1_forbidden"]
    assert "inference_calibration_validation_or_benchmark" in (
        separation["R1_forbidden"]
    )
    assert "separate_digest_bound_generated_only_runtime_authority" in (
        separation["R2_requires"]
    )
    assert "network_denied_isolated_execution_environment" in (
        separation["R2_requires"]
    )
    assert separation["R2_is_non_promotional"] is True
    assert separation["R3_held_out_validation_requires_later_separate_authority"] is True


def test_U3D_proposal_packet_stays_unselected_and_recommends_AAAAA() -> None:
    decisions = _read(DECISIONS_PATH)
    items = decisions["decisions"]

    assert [item["decision_id"] for item in items] == [
        "D-P3.6-U3D-001",
        "D-P3.6-U3D-002",
        "D-P3.6-U3D-003",
        "D-P3.6-U3D-004",
        "D-P3.6-U3D-005",
    ]
    assert all(item["recommended_option"] == "A" for item in items)
    assert all(item["selected_option"] is None for item in items)
    assert all(
        [option["option"] for option in item["options"]] == list("ABCD")
        for item in items
    )
    assert decisions["recommended_selection"] == "A/A/A/A/A"
    assert decisions[
        "owner_acceptance_may_be_inferred_from_continue_or_other_decision"
    ] is False


def test_package_grants_no_query_acquisition_execution_or_implementation() -> None:
    for record in [_read(PROPOSAL_PATH), _read(DECISIONS_PATH), _read(PACKAGE_PATH)]:
        assert record["storage_or_hardware_query_authorized"] is False
        assert record["scanner_query_install_or_execution_authorized"] is False
        acquisition = record.get(
            "artifact_or_dependency_acquisition_authorized",
            record.get("artifact_acquisition_authorized"),
        )
        assert acquisition is False
        assert record["runtime_or_model_execution_authorized"] is False
        assert record["hardware_testing_authorized"] is False
        assert record["implementation_authorized"] is False
        assert record["deployment_authorized"] is False
        assert record["remote_git_authorized"] is False

    package = _read(PACKAGE_PATH)
    assert package["container_or_kubernetes_action_authorized"] is False
    assert package["camera_media_or_data_access_authorized"] is False


def test_ledgers_and_human_records_are_synchronized_and_blocked() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    gate_states = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert gate_states["P36-G2"] == "blocked"
    assert gate_states["P36-G4"] == "blocked"
    for ledger in [gates, policy, unblock]:
        state = ledger["portable_r1_supply_chain_prerequisite_package"]
        digest = state.get("digest_sha256", state.get("package_digest_sha256"))
        assert digest == PACKAGE_DIGEST
        assert state["recommended_selection"] == "A/A/A/A/A"
        assert state["selected_options"] == "A/A/A/A/A"
        assert state["owner_selections_pending"] is False
        assert state["acceptance_record"].endswith(
            f"{STEM}-owner-decisions.json"
        )
        assert state["acceptance_sha256"] == ACCEPTANCE_DIGEST
        assert state["profile_activation_authorized"] is False

    assert unblock["next_portable_planning_action"][
        "owner_implementation_acceptance_pending"
    ] is True
    assert unblock["next_portable_planning_action"][
        "runtime_binding_proposal_preparation_authority"
    ] is False
    assert unblock["next_portable_planning_action"][
        "runtime_binding_observation_authority"
    ] is False
    assert unblock["next_portable_planning_action"][
        "Defender_only_proposal_preparation_authority_now"
    ] is False
    assert unblock["next_portable_planning_action"]["retry_authorized"] is False
    assert unblock["next_portable_planning_action"][
        "another_attempt_authority"
    ] is False

    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    contracts_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")
    for text in [decision_register, backlog, phase_index]:
        assert PACKAGE_DIGEST in text
    assert "DR-0060: Portable R1 supply-chain prerequisite" in decision_register
    assert f"{STEM}-package.json" in contracts_index
