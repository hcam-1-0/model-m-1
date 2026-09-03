from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
DOCS = ROOT / "docs" / "phase-3"
AUTHORIZATION_PATH = CONTRACTS / "p3-6-inventory-r1-authorization.json"
INVENTORY_PATH = CONTRACTS / "p3-6-inventory-lab-laptop-01-r1.json"
EVIDENCE_PATH = CONTRACTS / "p3-6-inventory-r1-collection-evidence.json"
PACKAGE_DIGEST = "710D52D5BC9A24A42CCB379355C062095795554F261316C37714819F0DFDDAA7"
INVENTORY_DIGEST = "FB061C906D1CE5F7FE3B32B70F6CA5134C486F474E2618B23884466C2E58C76F"
EVIDENCE_DIGEST = "3658758FCC7342B7865C7C0FD340FD408B38562BB1D365B757A74C8B6347FA72"
SCHEMA_DIGEST = "C9947BE12888C0A05B29DA0266E2359B107024AF07E536AE10BAC55457C5C7D3"
TRUST_DIGEST = "E76D0C56476A98AADDBC7880AD75858B5B61D45CE95802E3FB39557E226C6106"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        result = set(value)
        for child in value.values():
            result.update(_keys(child))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for child in value:
            result.update(_keys(child))
        return result
    return set()


def test_owner_authorization_is_exact_completed_consumed_and_closed() -> None:
    authorization = _read(AUTHORIZATION_PATH)

    assert authorization["decision_id"] == "D-P3.6-INVENTORY-R1-AUTH"
    assert authorization["authorized_by"] == "mayank-admin"
    assert authorization["package_digest_sha256"] == PACKAGE_DIGEST
    assert authorization["trust_policy_sha256"] == TRUST_DIGEST
    assert authorization["shared_schema"]["sha256"] == SCHEMA_DIGEST
    assert authorization["status"] == "completed_single_attempt_consumed"
    assert authorization["effective"] is False
    assert authorization["authorization_scope"]["maximum_attempts"] == 1
    assert authorization["authorization_scope"]["attempts_consumed"] == 1
    assert authorization["result"]["attempts_consumed"] == 1
    assert authorization["result"]["authorization_consumed"] is True
    assert authorization["result"]["retry_authorized"] is False
    assert authorization["result"]["raw_output_persisted"] is False
    assert all(
        authorization[field] is False
        for field in [
            "collector_implementation_authorized",
            "profile_activation_authorized",
            "runtime_or_model_execution_authorized",
            "hardware_testing_authorized",
            "accelerator_probe_authorized",
            "container_or_kubernetes_action_authorized",
            "camera_media_or_data_access_authorized",
            "network_access_authorized",
            "deployment_authorized",
            "remote_git_authorized",
        ]
    )


def test_attempt_ran_once_inside_the_authorized_window_and_bounds() -> None:
    authorization = _read(AUTHORIZATION_PATH)
    evidence = _read(EVIDENCE_PATH)
    authorized_at = _timestamp(authorization["authorized_at"])
    expires_at = _timestamp(authorization["authorization_expires_at"])
    started_at = _timestamp(evidence["attempt_started_at"])
    completed_at = _timestamp(evidence["attempt_completed_at"])

    assert authorized_at <= started_at <= completed_at <= expires_at
    assert (completed_at - started_at).total_seconds() <= 60
    assert evidence["status"] == "succeeded_sanitized_R1_written"
    assert [item["action_id"] for item in evidence["bounded_action_outcomes"]] == [
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
    assert all(item["duration_ms"] <= 10_000 for item in evidence["bounded_action_outcomes"])
    assert evidence["raw_output_persisted"] is False


def test_evidence_binds_exact_package_schema_trust_and_inventory() -> None:
    evidence = _read(EVIDENCE_PATH)

    assert _sha256(EVIDENCE_PATH) == EVIDENCE_DIGEST
    assert _sha256(INVENTORY_PATH) == INVENTORY_DIGEST
    assert evidence["package_digest_sha256"] == PACKAGE_DIGEST
    assert evidence["trust_policy_sha256"] == TRUST_DIGEST
    assert evidence["shared_schema_sha256"] == SCHEMA_DIGEST
    assert evidence["schema_validation_status"] == "passed_exact_shared_v1alpha1"
    assert evidence["R1_sha256_or_null"] == INVENTORY_DIGEST
    assert evidence["R1_path_or_null"] == (
        "contracts/phase-3/p3-6-inventory-lab-laptop-01-r1.json"
    )


def test_R1_is_sanitized_shared_shape_with_bounded_freshness() -> None:
    inventory = _read(INVENTORY_PATH)
    observed_at = _timestamp(inventory["observed_at"])
    valid_until = _timestamp(inventory["valid_until"])

    assert set(inventory) == {
        "accelerators",
        "container_support",
        "cpu",
        "findings",
        "inventory_id",
        "memory",
        "node_class",
        "observed_at",
        "operating_system",
        "provenance",
        "redaction",
        "runtimes",
        "scheduler_capabilities",
        "schema_version",
        "valid_until",
    }
    assert inventory["schema_version"] == (
        "hcam.platform.node-capability-inventory/v1alpha1"
    )
    assert inventory["inventory_id"].startswith("inv_")
    assert inventory["node_class"] == "cpu_laptop"
    assert (valid_until - observed_at).total_seconds() == 86_400
    assert inventory["provenance"] == {
        "collection_mode": "local_read_only",
        "collector_version": "hcam-p36-r1-spec-1.0.0",
        "trust_level": "observed",
    }
    assert set(inventory["redaction"]["omitted_categories"]) == {
        "hostname",
        "user_identity",
        "serial_number",
        "network_address",
        "personal_path",
        "raw_device_identifier",
        "secret_reference",
    }


def test_R1_does_not_claim_unobserved_compatibility_or_identifiers() -> None:
    inventory = _read(INVENTORY_PATH)
    prohibited_key_fragments = {
        "hostname",
        "username",
        "serial",
        "mac_address",
        "ip_address",
        "personal_path",
        "device_id",
        "secret_ref",
    }

    assert not (_keys(inventory) & prohibited_key_fragments)
    assert inventory["cpu"]["instruction_sets"] == ["unknown"]
    assert inventory["accelerators"] == {"items": [], "state": "unknown"}
    assert inventory["container_support"]["state"] == "unknown"
    assert set(inventory["scheduler_capabilities"].values()) == {"unknown"}
    assert inventory["runtimes"]["state"] == "unknown"
    assert all(item["state"] == "unknown" for item in inventory["runtimes"]["items"])


def test_R1_is_linked_but_profile_activation_and_G2_remain_closed() -> None:
    gates = _read(CONTRACTS / "p3-6-entry-gates.json")
    policy = _read(CONTRACTS / "p3-6-capability-profile-policy.json")
    unblock = _read(CONTRACTS / "p3-6-unblock-plan.json")
    gate_states = {item["gate_id"]: item["state"] for item in gates["gates"]}

    assert gate_states["P36-G2"] == "blocked"
    assert gates["implementation_authorized"] is False
    assert gates["runtime_execution_authorized"] is False
    assert gates["inventory_records"][-1].endswith(
        "p3-6-inventory-lab-laptop-01-r1.json"
    )
    assert policy["inventory_r1_authorization_package"]["resolver_eligible"] is False
    assert policy["future_operator_controls"]["implementation_status"] == (
        "not_authorized"
    )
    assert unblock["implementation_authorized"] is False
    assert unblock["runtime_execution_authorized"] is False
    assert unblock["inventory_r1_authorization_package"][
        "inventory_collection_authorized"
    ] is False


def test_collection_record_and_contract_indexes_are_synchronized() -> None:
    collection_doc = DOCS / "p3-6-inventory-r1-collection.md"
    decision_register = (DOCS / "decision-register.md").read_text(encoding="utf-8")
    backlog = (DOCS / "implementation-backlog.md").read_text(encoding="utf-8")
    phase_index = (DOCS / "README.md").read_text(encoding="utf-8")
    phase_plan = (DOCS / "p3-6-plan.md").read_text(encoding="utf-8")
    acceptances = (DOCS / "p3-6-planning-acceptances.md").read_text(
        encoding="utf-8"
    )
    unblock_doc = (DOCS / "p3-6-unblock-plan.md").read_text(encoding="utf-8")
    contract_index = (CONTRACTS / "README.md").read_text(encoding="utf-8")

    assert collection_doc.exists()
    assert PACKAGE_DIGEST in collection_doc.read_text(encoding="utf-8")
    assert "DR-0056: P3.6 Inventory R1 One-Time Authorization And Result" in (
        decision_register
    )
    assert "single authorized local read-only attempt succeeded" in " ".join(
        backlog.split()
    )
    assert "p3-6-inventory-r1-collection.md" in phase_index
    assert "D-P3.6-INVENTORY-R1-AUTH` remains pending" not in phase_plan
    assert "p3-6-inventory-r1-collection.md" in phase_plan
    assert "p3-6-inventory-r1-authorization.json" in acceptances
    assert "That attempt is consumed" in unblock_doc
    assert "p3-6-inventory-r1-authorization.json" in contract_index
