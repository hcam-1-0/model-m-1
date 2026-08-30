from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
PROPOSAL_PATH = CONTRACTS / "p3-6-portable-cpu-profile-proposal.json"
SOURCES_PATH = CONTRACTS / "p3-6-portable-cpu-research-sources.json"
PACKAGE_PATH = CONTRACTS / "p3-6-portable-cpu-profile-package.json"
DOCUMENT_PATH = DOCS / "p3-6-portable-cpu-profile-proposal.md"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_portable_proposal_binds_exact_shared_profile_and_inventory() -> None:
    proposal = _read(PROPOSAL_PATH)

    assert proposal["profile_identity"] == {
        "profile_class": "portable_cpu",
        "profile_id": "hcam-portable-cpu",
        "proposed_revision": "P36-PROFILE-PORTABLE-CPU-R0",
        "lifecycle": "proposal",
        "resolver_eligible": False,
        "activation_authorized": False,
    }
    assert proposal["phase_minus_1_binding"]["shared_contracts_merge_commit"] == (
        "d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8"
    )
    assert proposal["phase_minus_1_binding"]["deployment_merge_commit"] == (
        "71095fe89d2b711e4982ddc0130fcaedda8703e7"
    )
    assert proposal["inventory_binding"]["sha256"] == (
        "0E702718390FB6C373F0FC189CB58D0E79BB7FE3B3EA39B5E5AFE0DE4D47CA1F"
    )


def test_reference_runtime_is_exact_but_not_installed_or_approved() -> None:
    proposal = _read(PROPOSAL_PATH)
    runtime = proposal["candidate_runtime"]

    assert runtime["execution_providers"] == ["CPUExecutionProvider"]
    assert runtime["provider_priority_must_match_exactly"] is True
    assert runtime["execution_mode"] == "sequential"
    assert runtime["intra_op_threads"] == 1
    assert runtime["inter_op_threads"] == 1
    assert runtime["graph_optimization"] == "basic"
    assert runtime["thread_spinning"].startswith("unresolved")
    assert runtime["current_installation_state"].startswith("not_established")
    assert runtime["candidate_windows_wheel"]["artifact_acquired_or_verified_for_p3_6"] is False


def test_historical_smoke_is_not_reused_as_performance_evidence() -> None:
    proposal = _read(PROPOSAL_PATH)
    historical = proposal["historical_reference_evidence"]

    assert historical["duration_ms"] == 206
    assert historical["allowed_reuse"] == "behavior_and_contract_reference_only"
    assert set(historical["not_valid_for"]) == {
        "p3_6_latency_threshold",
        "p3_6_throughput_threshold",
        "p3_6_freshness_threshold",
        "p3_6_capacity_claim",
        "real_world_quality_claim",
        "production_or_deployment_claim",
    }


def test_conservative_envelope_is_bounded_and_still_unapproved() -> None:
    proposal = _read(PROPOSAL_PATH)
    envelope = proposal["proposed_conservative_envelope"]

    assert envelope["status"] == "planning_values_not_performance_approved"
    assert envelope["active_assignments"] == 1
    assert envelope["worker_processes"] == 1
    assert envelope["worker_concurrency"] == 1
    assert envelope["detector_batch_size"] == 1
    assert envelope["in_flight_inference_requests"] == 1
    assert envelope["queue_capacity_items"] == 2
    assert envelope["oversubscription"] == "forbidden"
    assert envelope["required_pipeline_stages_may_be_bypassed"] is False
    assert envelope["queue_age_limit_ms"].startswith("unresolved")


def test_workload_is_generated_infer_only_and_non_executable() -> None:
    proposal = _read(PROPOSAL_PATH)
    workload = proposal["proposed_workload"]

    assert workload["evidence_tier"] == "C1"
    assert workload["evidence_layer"] == "INFER"
    assert workload["external_media"] is False
    assert workload["decode_stage"] is False
    assert workload["camera_or_stream"] is False
    assert workload["input_shape"] == [1, 3, 416, 416]
    assert workload["execution_authorized"] is False
    assert workload["duration_seconds"] == "unresolved"
    assert workload["repetitions"] == "unresolved"


def test_all_execution_and_activation_authorities_are_false() -> None:
    proposal = _read(PROPOSAL_PATH)

    assert proposal["artifact_download_authorized"] is False
    assert proposal["profile_activation_authorized"] is False
    assert proposal["implementation_authorized"] is False
    assert proposal["runtime_execution_authorized"] is False
    assert proposal["deployment_authorized"] is False
    assert proposal["remote_git_authorized"] is False
    assert "p36_g5_implementation_and_runtime_execution_authority_blocked" in (
        proposal["blocked_reasons"]
    )


def test_source_record_contains_only_read_only_research() -> None:
    sources = _read(SOURCES_PATH)

    assert sources["artifact_downloads"] == 0
    assert sources["runtime_executions"] == 0
    assert sources["hardware_queries_or_tests"] == 0
    assert len(sources["sources"]) == 4
    assert all(item["url"].startswith("https://onnxruntime.ai/") for item in sources["sources"])


def test_package_binds_exact_core_files_without_self_hash() -> None:
    package = _read(PACKAGE_PATH)
    expected_paths = {
        "contracts/phase-3/p3-6-portable-cpu-profile-proposal.json": PROPOSAL_PATH,
        "contracts/phase-3/p3-6-portable-cpu-research-sources.json": SOURCES_PATH,
        "docs/phase-3/p3-6-portable-cpu-profile-proposal.md": DOCUMENT_PATH,
    }
    package_hashes = {
        item["path"]: item["sha256"] for item in package["core_files"]
    }

    assert package["core_file_count"] == 3
    assert package_hashes == {
        path: _sha256(file_path) for path, file_path in expected_paths.items()
    }
    assert package["owner_review_decision_id"] == (
        "D-P3.6-PORTABLE-PROPOSAL-R0-ACCEPTANCE"
    )
    assert package["implementation_authorized"] is False
    assert package["runtime_execution_authorized"] is False
    assert package["profile_activation_authorized"] is False


def test_gate_and_profile_records_link_the_sealed_non_executable_package() -> None:
    digest = "56A7C816C108802948E24C84D481572D8EF10CA7B1EAE1AA3D389B4234A51D7B"
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")

    gate_proposal = gates["portable_cpu_profile_proposal"]
    assert gate_proposal["digest_sha256"] == digest
    assert gate_proposal["profile_activation_authorized"] is False
    assert next(
        gate for gate in gates["gates"] if gate["gate_id"] == "P36-G2"
    )["state"] == "blocked"

    policy_proposal = policy["portable_cpu_profile_proposal"]
    assert policy_proposal["package_digest_sha256"] == digest
    assert policy_proposal["resolver_eligible"] is False

    unblock_proposal = unblock["portable_cpu_profile_proposal"]
    assert unblock_proposal["package_digest_sha256"] == digest
    assert unblock_proposal["profile_activation_authorized"] is False
    u3 = next(
        item for item in unblock["work_items"] if item["work_item_id"] == "P36-U3"
    )
    assert u3["output_package_digest_sha256"] == digest
    assert u3["state"].startswith(
        "portable_cpu_R0_inventory_admission_AAAA_and_portable_R1_U3B_AAAA_"
        "planning_accepted"
    )


def test_portable_proposal_is_indexed_as_pending_owner_review() -> None:
    phase_readme = (DOCS / "README.md").read_text(encoding="utf-8")
    contracts_readme = (CONTRACTS / "README.md").read_text(encoding="utf-8")
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    profile_policy = (DOCS / "p3-6-capability-profiles.md").read_text(
        encoding="utf-8"
    )

    assert "p3-6-portable-cpu-profile-proposal.md" in phase_readme
    assert "p3-6-portable-cpu-profile-package.json" in contracts_readme
    assert "DR-0052: P3.6 Portable CPU Profile Proposal R0" in decision_register
    assert "D-P3.6-PORTABLE-PROPOSAL-R0-ACCEPTANCE" in profile_policy
