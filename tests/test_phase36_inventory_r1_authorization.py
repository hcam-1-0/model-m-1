from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
SOURCES_PATH = CONTRACTS / "p3-6-inventory-r1-research-sources.json"
TRUST_PATH = CONTRACTS / "p3-6-inventory-r1-trust-policy.json"
SPEC_PATH = CONTRACTS / "p3-6-inventory-r1-collector-spec.json"
PROPOSAL_PATH = CONTRACTS / "p3-6-inventory-r1-authorization-proposal.json"
PACKAGE_PATH = CONTRACTS / "p3-6-inventory-r1-authorization-package.json"
DOCUMENT_PATH = DOCS / "p3-6-inventory-r1-authorization-proposal.md"
PACKAGE_DIGEST = "710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7"
TRUST_DIGEST = "E76D0C56476A98AADDBC7880AD75858B5B61D45CE95802E3FB39557E226C6106"
SHARED_SCHEMA_DIGEST = (
    "C9947BE12888C0A05B29DA0266E2359B107024AF07E536AE10BAC55457C5C7D3"
)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_source_ledger_records_research_without_collection_or_execution() -> None:
    sources = _read(SOURCES_PATH)

    assert sources["status"] == "complete_for_non_executable_authorization_proposal"
    assert sources["remote_git_actions"] == 0
    assert sources["inventory_collection_actions"] == 0
    assert sources["runtime_or_model_executions"] == 0
    assert sources["hardware_queries_or_tests"] == 0
    assert sources["network_actions_against_lab_laptop"] == 0
    assert len(sources["official_external_sources"]) == 5
    assert all(
        item["url"].startswith(
            (
                "https://learn.microsoft.com/",
                "https://docs.python.org/",
                "https://ffmpeg.org/",
            )
        )
        for item in sources["official_external_sources"]
    )


def test_trust_policy_is_exact_generated_only_and_non_effective() -> None:
    trust = _read(TRUST_PATH)

    assert _sha256(TRUST_PATH) == TRUST_DIGEST
    assert trust["policy_id"] == "hcam-owned-local-generated-only-r0"
    assert trust["status"] == "proposed_owner_acceptance_pending_non_effective"
    assert trust["network_boundary"] == {
        "network_access": "denied",
        "remote_CIM_or_WMI": "denied",
        "remote_service_or_API": "denied",
        "proxy_or_redirect_use": "denied",
        "localhost_network_service_contact": "denied",
    }
    assert trust["admission_boundary"]["inventory_validity_window_seconds"] == 86400
    assert trust["admission_boundary"]["profile_resolver_eligible_now"] is False
    assert trust["effective"] is False
    assert trust["inventory_collection_authorized"] is False
    assert trust["runtime_execution_authorized"] is False


def test_collector_spec_binds_exact_shared_schema_and_trust_snapshot() -> None:
    spec = _read(SPEC_PATH)

    assert spec["status"].endswith("no_collector_implemented")
    assert spec["shared_contract"]["revision"] == (
        "d71cdc9c51d01d746d5195bcb2ac639e0fdf11c8"
    )
    assert spec["shared_contract"]["schema_version"] == (
        "hcam.platform.node-capability-inventory/v1alpha1"
    )
    assert spec["shared_contract"]["sha256"] == SHARED_SCHEMA_DIGEST
    assert spec["trust_policy"]["sha256"] == TRUST_DIGEST
    assert spec["collector_identity"]["reusable_collector_code_created"] is False
    assert spec["current_effect"]["inventory_collection_authorized"] is False
    assert spec["current_effect"]["R1_exists"] is False


def test_action_allowlist_is_exact_local_minimized_and_bounded() -> None:
    spec = _read(SPEC_PATH)
    actions = {item["action_id"]: item for item in spec["action_allowlist"]}

    assert list(actions) == [
        f"R1-A{index:02d}-{suffix}"
        for index, suffix in [
            (1, "UTC-CLOCK-START"),
            (2, "WINDOWS-OS-MEMORY"),
            (3, "CPU"),
            (4, "PYTHON-VERSION"),
            (5, "ONNXRUNTIME-DISTRIBUTION-VERSION"),
            (6, "FFMPEG-VERSION"),
            (7, "OPAQUE-ID"),
            (8, "UTC-CLOCK-COMPLETE"),
            (9, "NORMALIZE-VALIDATE-HASH-WRITE"),
        ]
    ]
    assert actions["R1-A02-WINDOWS-OS-MEMORY"]["allowed_source_fields"] == [
        "Version",
        "BuildNumber",
        "OSArchitecture",
        "TotalVisibleMemorySize",
        "FreePhysicalMemory",
    ]
    assert actions["R1-A03-CPU"]["allowed_source_fields"] == [
        "Architecture",
        "NumberOfCores",
        "NumberOfLogicalProcessors",
    ]
    assert "-ComputerName" not in actions["R1-A02-WINDOWS-OS-MEMORY"]["exact_action"]
    assert "-CimSession" not in actions["R1-A03-CPU"]["exact_action"]
    assert (
        actions["R1-A05-ONNXRUNTIME-DISTRIBUTION-VERSION"][
            "target_runtime_or_model_import_allowed"
        ]
        is False
    )
    assert "python -I -S" in actions["R1-A04-PYTHON-VERSION"]["exact_action"]
    assert (
        "python -I -S"
        in actions["R1-A05-ONNXRUNTIME-DISTRIBUTION-VERSION"]["exact_action"]
    )
    assert (
        actions["R1-A06-FFMPEG-VERSION"][
            "media_input_output_device_protocol_or_probe_allowed"
        ]
        is False
    )
    assert spec["transaction_bounds"]["maximum_authorized_attempts"] == 1
    assert (
        spec["transaction_bounds"][
            "authorization_use_window_seconds_after_owner_acceptance"
        ]
        == 86400
    )
    assert spec["transaction_bounds"]["per_action_timeout_seconds"] == 10
    assert spec["transaction_bounds"]["total_transaction_timeout_seconds"] == 60
    assert spec["transaction_bounds"]["maximum_version_process_stdout_bytes"] == 16384
    assert spec["transaction_bounds"]["maximum_version_process_stderr_bytes"] == 16384
    assert spec["transaction_bounds"]["network_access"] is False
    assert spec["transaction_bounds"]["parallel_actions"] is False


def test_unobserved_capabilities_remain_explicit_unknowns() -> None:
    projection = _read(SPEC_PATH)["projection_rules"]

    assert projection["cpu"]["instruction_sets"] == ["unknown"]
    assert projection["accelerators"] == {"state": "unknown", "items": []}
    assert projection["container_support"] == {
        "state": "unknown",
        "engines": [],
        "compose": "unknown",
        "gpu_passthrough": "unknown",
    }
    assert set(projection["scheduler_capabilities"].values()) == {"unknown"}
    assert projection["runtimes"]["state"] == "unknown"
    assert "no_compatibility_claim" in projection["runtimes"]["items_rule"]


def test_prohibited_actions_cover_identifiers_gpu_containers_media_and_runtime() -> (
    None
):
    prohibited = "\n".join(_read(SPEC_PATH)["prohibited_sources_and_actions"])

    for required_fragment in [
        "serial",
        "drive",
        "display",
        "network",
        "personal_path",
        "nvidia_smi",
        "Docker_containerd_Kubernetes",
        "camera_stream_media",
        "benchmark_or_inference",
        "remote_git",
    ]:
        assert required_fragment in prohibited


def test_proposal_requests_one_attempt_but_is_not_authorization() -> None:
    proposal = _read(PROPOSAL_PATH)

    assert proposal["decision_id"] == "D-P3.6-INVENTORY-R1-AUTH"
    assert proposal["status"] == "owner_review_pending_non_effective"
    assert proposal["requested_owner_effect"]["maximum_attempts"] == 1
    assert (
        proposal["requested_owner_effect"]["authorization_use_window_seconds"] == 86400
    )
    assert (
        proposal["requested_owner_effect"]["failed_attempt_requires_new_authorization"]
        is True
    )
    assert "<PACKAGE_DIGEST_SHA256>" in proposal["owner_acceptance_statement_template"]
    assert proposal["current_effect"] == {
        "effective": False,
        "owner_acceptance_record_exists": False,
        "trust_policy_accepted": False,
        "inventory_collection_authorized": False,
        "collector_implementation_authorized": False,
        "profile_activation_authorized": False,
        "runtime_execution_authorized": False,
        "deployment_authorized": False,
        "remote_git_authorized": False,
    }


def test_package_binds_exact_core_files_and_is_non_effective() -> None:
    package = _read(PACKAGE_PATH)
    expected = {
        "contracts/phase-3/p3-6-inventory-r1-research-sources.json": SOURCES_PATH,
        "contracts/phase-3/p3-6-inventory-r1-trust-policy.json": TRUST_PATH,
        "contracts/phase-3/p3-6-inventory-r1-collector-spec.json": SPEC_PATH,
        "contracts/phase-3/p3-6-inventory-r1-authorization-proposal.json": PROPOSAL_PATH,
        "docs/phase-3/p3-6-inventory-r1-authorization-proposal.md": DOCUMENT_PATH,
    }
    recorded = {item["path"]: item["sha256"] for item in package["core_files"]}

    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST
    assert package["core_file_count"] == 5
    assert recorded == {
        path: _sha256(file_path) for path, file_path in expected.items()
    }
    assert package["status"] == "sealed_non_effective_owner_authorization_pending"
    assert (
        package["owner_acceptance_may_be_inferred_from_continue_or_prior_decision"]
        is False
    )
    assert package["inventory_collection_authorized"] is False
    assert package["runtime_or_model_execution_authorized"] is False
    assert package["network_access_authorized"] is False


def test_historical_R0_and_sealed_authorization_package_are_unchanged() -> None:
    historical = CONTRACTS / "p3-6-inventory-lab-laptop-01-r0.json"

    assert _sha256(historical) == (
        "0E702718390FB6C373F0FC189CB58D0E79BB7FE3B3EA39B5E5AFE0DE4D47CA1F"
    )
    assert _sha256(PACKAGE_PATH) == PACKAGE_DIGEST


def test_canonical_ledgers_link_consumed_attempt_and_keep_G2_blocked() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")

    states = {item["gate_id"]: item["state"] for item in gates["gates"]}
    assert states["P36-G2"] == "blocked"
    assert (
        gates["inventory_r1_authorization_package"]["digest_sha256"] == PACKAGE_DIGEST
    )
    assert (
        gates["inventory_r1_authorization_package"]["inventory_collection_authorized"]
        is False
    )
    assert gates["inventory_r1_authorization_package"]["single_attempt_consumed"]
    assert not gates["inventory_r1_authorization_package"][
        "profile_resolver_eligible"
    ]
    assert (
        policy["inventory_r1_authorization_package"]["package_digest_sha256"]
        == PACKAGE_DIGEST
    )
    assert not policy["inventory_r1_authorization_package"][
        "owner_acceptance_pending"
    ]
    assert policy["inventory_r1_authorization_package"]["fresh_R1_exists"]
    assert (
        unblock["inventory_r1_authorization_package"]["package_digest_sha256"]
        == PACKAGE_DIGEST
    )
    assert (
        unblock["next_inventory_planning_action"][
            "implementation_or_collection_authority"
        ]
        is False
    )
    assert unblock["inventory_r1_authorization_package"][
        "single_attempt_consumed"
    ]


def test_decision_backlog_and_indexes_show_completed_one_time_attempt() -> None:
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_readme = (DOCS / "README.md").read_text(encoding="utf-8")
    contracts_readme = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    assert (
        "DR-0055: P3.6 Minimized Inventory R1 Authorization Package R0"
        in decision_register
    )
    assert "DR-0056: P3.6 Inventory R1 One-Time Authorization And Result" in (
        decision_register
    )
    assert PACKAGE_DIGEST in decision_register
    assert PACKAGE_DIGEST in backlog
    assert "p3-6-inventory-r1-authorization-proposal.md" in phase_readme
    assert "p3-6-inventory-r1-collection.md" in phase_readme
    assert "p3-6-inventory-r1-authorization-package.json" in contracts_readme
    assert "p3-6-inventory-r1-collection-evidence.json" in contracts_readme
