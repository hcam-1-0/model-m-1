from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
SOURCES_PATH = (
    CONTRACTS / "p3-6-portable-compatibility-validation-research-sources.json"
)
PROPOSAL_PATH = CONTRACTS / "p3-6-portable-compatibility-validation-proposal.json"
DECISIONS_PATH = (
    CONTRACTS / "p3-6-portable-compatibility-validation-decision-packet.json"
)
DOCUMENT_PATH = DOCS / "p3-6-portable-compatibility-validation-proposal.md"
PACKAGE_PATH = CONTRACTS / "p3-6-portable-compatibility-validation-package.json"
PACKAGE_DIGEST = "9727D15FDAA49A0DEE06327A41E772762F3D7A2560A5F4BDEFAA6EC3FDEFCD3A"
U3G_PACKAGE_DIGEST = (
    "C3EE058DF2B49BCEE552AF6B084E2D05C810F2C8EE11773872E9EC9A72DE080B"
)
U3B_ACCEPTANCE_DIGEST = (
    "7695027BB68878ED7CE41B6BD940EB777CD280279294E5C35B99614C3C57F5FA"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_package_binds_exact_core_files_and_accepted_U3B_policy() -> None:
    package = _read(PACKAGE_PATH)
    expected_paths = {
        "contracts/phase-3/"
        "p3-6-portable-compatibility-validation-research-sources.json": SOURCES_PATH,
        "contracts/phase-3/"
        "p3-6-portable-compatibility-validation-proposal.json": PROPOSAL_PATH,
        "contracts/phase-3/"
        "p3-6-portable-compatibility-validation-decision-packet.json": DECISIONS_PATH,
        "docs/phase-3/"
        "p3-6-portable-compatibility-validation-proposal.md": DOCUMENT_PATH,
    }
    package_hashes = {
        item["path"]: item["sha256"] for item in package["core_files"]
    }

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["core_file_count"] == 4
    assert package_hashes == {
        path: _sha256(file_path) for path, file_path in expected_paths.items()
    }
    assert package["accepted_input_policy"] == {
        "acceptance_record": (
            "contracts/phase-3/p3-6-portable-r1-owner-decisions.json"
        ),
        "acceptance_sha256": U3B_ACCEPTANCE_DIGEST,
        "selection": "A/A/A/A",
    }


def test_research_ledger_is_official_read_only_and_zero_action() -> None:
    sources = _read(SOURCES_PATH)
    actions = sources["research_actions"]

    assert len(sources["official_external_sources"]) == 5
    assert all(
        item["url"].startswith("https://onnxruntime.ai/")
        for item in sources["official_external_sources"]
    )
    assert actions["public_document_pages_read"] == 5
    assert all(
        actions[field] == 0
        for field in [
            "artifact_downloads",
            "dependency_installs",
            "runtime_or_model_imports",
            "inference_or_benchmarks",
            "hardware_queries_or_tests",
            "inventory_collection_attempts",
            "container_or_kubernetes_actions",
            "camera_media_or_data_accesses",
            "remote_git_actions",
        ]
    )


def test_runtime_candidate_is_exact_deterministic_and_low_contention() -> None:
    runtime = _read(PROPOSAL_PATH)["recommended_runtime_candidate_A"]

    assert runtime["provider_order"] == ["CPUExecutionProvider"]
    assert runtime["unexpected_provider"] == "reject_and_safe_pause"
    assert runtime["precision"] == "fp32"
    assert runtime["execution_mode"] == "ORT_SEQUENTIAL"
    assert runtime["intra_op_num_threads"] == 1
    assert runtime["inter_op_num_threads"] == 1
    assert runtime["intra_op_allow_spinning"] is False
    assert runtime["inter_op_allow_spinning"] is False
    assert runtime["thread_affinity"] == "unset_OS_managed"
    assert runtime["graph_optimization_level"] == "ORT_ENABLE_BASIC"
    assert runtime["enable_profiling"] is False
    assert runtime["session_count"] == 1
    assert runtime["in_flight_requests"] == 1
    assert runtime["batch_size"] == 1
    assert runtime["queue_capacity_items"] == 2
    assert runtime["oversubscription"] == "forbidden"


def test_generated_C1_workload_is_exact_bounded_and_zero_retention() -> None:
    workload = _read(PROPOSAL_PATH)["recommended_workload_candidate_A"]

    assert workload["evidence_layers"] == ["CONTRACT", "INFER"]
    assert workload["evidence_tier"] == "C1"
    assert workload["input_source"] == (
        "deterministic_generated_in_memory_tensor_only"
    )
    assert workload["input_shape"] == [1, 3, 416, 416]
    assert workload["input_dtype"] == "float32"
    assert workload["seeds"] == [36001, 36002, 36003]
    assert workload["contract_cases"] == 64
    assert workload["cold_start_repetitions"] == 3
    assert workload["warmup_iterations_per_seed"] == 5
    assert workload["measured_iterations_per_seed_per_repetition"] == 30
    assert workload["steady_repetitions"] == 3
    assert workload["bounded_burst_submissions"] == 8
    assert workload["bounded_burst_max_admitted"] == 3
    assert workload["bounded_burst_expected_excess_rejections"] == 5
    assert len(workload["dependency_loss_cases"]) == 3
    assert workload["safe_shutdown_repetitions"] == 3
    assert workload["total_validation_timeout_seconds"] == 900
    assert workload["raw_tensor_or_output_retention"] == "zero"
    assert workload["camera_media_or_dataset_inputs"] is False


def test_gate_architecture_separates_safety_calibration_and_validation() -> None:
    gates = _read(PROPOSAL_PATH)["recommended_gate_architecture_A"]
    hard = gates["predeclared_hard_safety_gates"]

    assert gates["stage_0_contract"].startswith("schema_shape_dtype")
    assert gates["stage_1_calibration"].startswith("separately_authorized")
    assert gates["stage_2_validation"].startswith("new_sealed_threshold")
    assert hard["unexpected_fallback_count"] == 0
    assert hard["schema_valid_fraction"] == 1.0
    assert hard["finite_output_fraction"] == 1.0
    assert hard["same_bundle_same_input_repeat_digest_match_fraction"] == 1.0
    assert hard["excess_work_rejected_fraction"] == 1.0
    assert hard["raw_tensor_or_output_retention_count"] == 0
    assert hard["network_attempt_count"] == 0
    assert hard["minimum_available_memory_preflight_mib"] == 1024
    assert hard["maximum_process_RSS_mib"] == 2048
    assert hard["maximum_queue_age_ms"] == 2000
    assert hard["maximum_dependency_failure_detection_ms"] == 2000
    assert hard["maximum_safe_shutdown_ms"] == 10000
    assert hard["maximum_total_validation_seconds"] == 900
    assert gates["real_world_quality_claim"] is False
    assert gates["hardware_capacity_claim"] is False
    assert gates["thermal_or_power_claim"] is False


def test_compatibility_lifecycle_is_immutable_R0_through_R4() -> None:
    proposal = _read(PROPOSAL_PATH)
    revisions = proposal["recommended_bundle_lifecycle_A"]

    assert [item["revision"] for item in revisions] == [
        "R0",
        "R1",
        "R2",
        "R3",
        "R4",
    ]
    assert revisions[0]["state"] == "candidate_skeleton_unavailable"
    assert revisions[1]["state"] == "artifacts_and_supply_chain_reviewed"
    assert revisions[2]["state"] == (
        "generated_calibration_complete_non_promotional"
    )
    assert revisions[3]["state"] == (
        "held_out_validation_reviewed_candidate_only"
    )
    assert revisions[4]["state"] == "eligible_or_rejected"
    assert proposal["compatibility_bundle_candidate"]["lifecycle"] == (
        "candidate_unavailable"
    )
    assert proposal["current_effect"]["compatibility_manifest_exists"] is False


def test_U3C_decisions_are_independent_unselected_and_recommend_AAAA() -> None:
    decisions = _read(DECISIONS_PATH)
    items = decisions["decisions"]

    assert [item["decision_id"] for item in items] == [
        "D-P3.6-U3C-001",
        "D-P3.6-U3C-002",
        "D-P3.6-U3C-003",
        "D-P3.6-U3C-004",
    ]
    assert all(item["recommended_option"] == "A" for item in items)
    assert all(item["selected_option"] is None for item in items)
    assert all([option["option"] for option in item["options"]] == list("ABCD") for item in items)
    assert decisions["recommended_selection"] == "A/A/A/A"
    assert decisions[
        "owner_acceptance_may_be_inferred_from_continue_or_other_decision"
    ] is False


def test_package_grants_no_execution_acquisition_or_implementation() -> None:
    for record in [
        _read(PROPOSAL_PATH),
        _read(DECISIONS_PATH),
        _read(PACKAGE_PATH),
    ]:
        runtime_authorized = record.get(
            "runtime_or_model_execution_authorized",
            record.get("runtime_execution_authorized"),
        )
        assert runtime_authorized is False
        assert record["implementation_authorized"] is False
        profile_authorized = record.get(
            "profile_activation_authorized",
            record.get("profile_resolution_or_activation_authorized"),
        )
        assert profile_authorized is False
        assert record["deployment_authorized"] is False
        assert record["remote_git_authorized"] is False

    package = _read(PACKAGE_PATH)
    assert package["inventory_collection_authorized"] is False
    assert package["artifact_or_dependency_acquisition_authorized"] is False
    assert package["hardware_testing_authorized"] is False
    assert package["container_or_kubernetes_action_authorized"] is False
    assert package["camera_media_or_data_access_authorized"] is False


def test_canonical_ledgers_link_package_without_opening_P36_G2() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    gate_states = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert gate_states["P36-G2"] == "blocked"
    for ledger in [gates, policy, unblock]:
        state = ledger["portable_compatibility_validation_package"]
        digest = state.get("digest_sha256", state.get("package_digest_sha256"))
        assert digest == PACKAGE_DIGEST
        assert state["recommended_selection"] == "A/A/A/A"
        resolver_eligible = state.get(
            "profile_resolver_eligible", state.get("resolver_eligible")
        )
        assert resolver_eligible is False
        assert state["profile_activation_authorized"] is False
    assert policy["portable_compatibility_validation_package"][
        "owner_selections_pending"
    ] is False
    assert policy["portable_compatibility_validation_package"][
        "selected_options"
    ] == "A/A/A/A"
    assert unblock["next_portable_planning_action"][
        "package_digest_sha256"
    ] == U3G_PACKAGE_DIGEST
    assert unblock["next_portable_planning_action"][
        "owner_authorization_pending"
    ] is True
    assert unblock["next_portable_planning_action"][
        "another_attempt_authority"
    ] is False
    assert unblock["next_portable_planning_action"][
        "implementation_or_runtime_authority"
    ] is False
    assert unblock["runtime_execution_authorized"] is False


def test_human_records_and_indexes_are_synchronized() -> None:
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    plan = (DOCS / "p3-6-plan.md").read_text(encoding="utf-8")
    unblock = (DOCS / "p3-6-unblock-plan.md").read_text(encoding="utf-8")
    profile = (DOCS / "p3-6-capability-profiles.md").read_text(encoding="utf-8")
    contracts_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    assert "DR-0059: Portable compatibility" in decision_register
    assert "D-P3.6-U3C-001" in decision_register
    for text in [decision_register, backlog, phase_index, plan, unblock]:
        assert PACKAGE_DIGEST in text
    assert "U3C `A/A/A/A` planning policies are owner accepted" in profile
    assert "p3-6-portable-compatibility-validation-package.json" in (
        contracts_index
    )
