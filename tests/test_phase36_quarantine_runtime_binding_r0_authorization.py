from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "phase-3"
STEM = "p3-6-quarantine-transaction-runner-r0-runtime-binding"
PACKAGE_DIGEST = (
    "37AA6C0684E291DC66F93FE4EDBC4E6FE0FA44101E63419B382BE59EA9FCFFA9"
)
AUTHORIZATION_DIGEST = (
    "1C3144D82EA1B41B3FBBE7E70F5BF74ED5EE5ACC709CAB272E2CBD287253648F"
)
RESULT_DIGEST = (
    "643226F1436CACB8E12994A6A81CEB1529E34BA5B289C1766E219A714267F7B7"
)
EVIDENCE_DIGEST = (
    "4C628812F9D3B293140B5F2A621922FFC994333D124B5706A9745A9E903C4D8C"
)
RUNTIME_DIGEST = (
    "362A356CE7F0940EC74F73A8FC2C990A2CC24A38A11C90BBD8ECA947110AD139"
)
RUNNER_DIGEST = (
    "C0020A4C53B59486CE8842302C918821F145F0228F4006C3D6B67BF594DB5B15"
)
ACTION_IDS = [
    "U3I-RB-A01-UTC-CLOCK-START",
    "U3I-RB-A02-PACKAGE-AND-AUTHORITY-VERIFY",
    "U3I-RB-A03-AUTHORIZATION-RECORD",
    "U3I-RB-A04-EXACT-RUNTIME-PATH-CLASSIFY",
    "U3I-RB-A05-BOUNDED-METADATA-AND-SHA256",
    "U3I-RB-A06-CACHE-ONLY-WHOLE-CHAIN-TRUST",
    "U3I-RB-A07-RUNNER-SOURCE-BIND",
    "U3I-RB-A08-NORMALIZE-HASH-WRITE",
]


def _path(suffix: str) -> Path:
    return CONTRACTS / f"{STEM}-{suffix}.json"


def _read(suffix: str) -> dict[str, object]:
    return json.loads(_path(suffix).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_exact_single_attempt_authorization_is_recorded_and_consumed() -> None:
    authorization = _read("authorization")

    assert _sha256(_path("authorization")) == AUTHORIZATION_DIGEST
    assert authorization["decision_id"] == (
        "D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH"
    )
    assert authorization["owner_statement_received"] == (
        "D-P3.6-U3I-RUNTIME-BINDING-R0-AUTH\n"
        f"Package: {PACKAGE_DIGEST}"
    )
    assert authorization["status"] == "single_read_only_attempt_started_and_consumed"
    assert authorization["effective_for_additional_attempt"] is False
    assert authorization["package_digest_sha256"] == PACKAGE_DIGEST
    scope = authorization["authorization_scope"]
    assert scope["maximum_attempts"] == 1
    assert scope["attempts_consumed"] == 1
    assert scope["exact_runtime_path"] == (
        "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
    )
    for field in [
        "runtime_or_runner_execution",
        "alternate_runtime_discovery",
        "network_access",
        "F_B_storage_or_ACL_access",
        "Defender_or_scanner_action",
        "remote_git",
    ]:
        assert scope[field] is False


def test_runtime_binding_result_is_exact_bounded_and_successful() -> None:
    result = _read("result")

    assert _sha256(_path("result")) == RESULT_DIGEST
    assert result["status"] == "completed_runtime_binding_issued"
    binding = result["runtime_binding"]
    assert binding["binding_state"] == (
        "bound_until_observed_at_plus_86400_seconds"
    )
    assert binding["reason_code"] == "exact_runtime_and_runner_binding_verified"
    assert all(binding["path_policy"][field] is True for field in [
        "canonical_exact",
        "fixed_components_nonreparse",
        "target_exists",
        "target_regular_online_nondevice",
        "passed",
    ])
    metadata = binding["metadata"]
    assert metadata["file_size_bytes"] == 301368
    assert metadata["file_version"] == "7.6.5.500"
    assert metadata["product_name_is_PowerShell"] is True
    assert metadata["runtime_major_version_is_7"] is True
    assert metadata["runtime_sha256"] == RUNTIME_DIGEST
    assert metadata["file_identity_invariants_unchanged"] is True
    assert metadata["passed"] is True
    trust = binding["trust_policy"]
    assert trust["trust_api"] == "WinVerifyTrust"
    assert trust["cache_only"] is True
    assert trust["whole_chain_excluding_root"] is True
    assert trust["provider_state_closed"] is True
    assert trust["trusted"] is True
    assert trust["passed"] is True
    runner = binding["runner_source"]
    assert runner["runner_source_sha256"] == RUNNER_DIGEST
    assert runner["runner_source_digest_match"] is True
    assert runner["passed"] is True
    assert all(value is False for value in result["execution_and_access"].values())


def test_evidence_binds_records_actions_validity_and_non_actions() -> None:
    evidence = _read("evidence")

    assert _sha256(_path("evidence")) == EVIDENCE_DIGEST
    assert evidence["authorization_sha256"] == AUTHORIZATION_DIGEST
    assert evidence["result_sha256"] == RESULT_DIGEST
    assert evidence["observed_runtime_sha256"] == RUNTIME_DIGEST
    assert evidence["observed_runner_source_sha256"] == RUNNER_DIGEST
    assert evidence["provider_state_closed"] is True
    outcomes = evidence["bounded_action_outcomes"]
    assert [item["action_id"] for item in outcomes] == ACTION_IDS
    assert all(item["state"] == "succeeded" for item in outcomes)
    started = _utc(evidence["attempt_started_at"])
    completed = _utc(evidence["attempt_completed_at"])
    valid_until = _utc(evidence["valid_until"])
    assert 0 <= (completed - started).total_seconds() <= 120
    assert (valid_until - completed).total_seconds() == 86400
    for field in [
        "pwsh_executed",
        "runner_executed",
        "alternate_discovery_performed",
        "network_access_performed",
        "F_or_B_access_performed",
        "storage_or_ACL_access_performed",
        "Defender_or_scanner_action_performed",
        "model_inference_media_or_data_access_performed",
        "container_or_Kubernetes_action_performed",
        "deployment_performed",
        "remote_git_performed",
        "raw_output_persisted",
    ]:
        assert evidence[field] is False


def test_outputs_remain_within_sealed_size_and_sanitization_bounds() -> None:
    assert _path("authorization").stat().st_size <= 32768
    assert _path("result").stat().st_size <= 16384
    assert _path("evidence").stat().st_size <= 32768

    combined = "\n".join(
        _path(suffix).read_text(encoding="utf-8")
        for suffix in ["authorization", "result", "evidence"]
    )
    for forbidden in [
        '"hostname"',
        '"user_or_account_name"',
        '"SID"',
        '"raw_ACL_SDDL_or_security_descriptor"',
        '"certificate_subject"',
        '"certificate_issuer"',
        '"certificate_serial"',
        '"certificate_thumbprint"',
        '"raw_exception"',
        '"stdout"',
        '"stderr"',
        "C:\\Users\\Lenovo",
    ]:
        assert forbidden not in combined
