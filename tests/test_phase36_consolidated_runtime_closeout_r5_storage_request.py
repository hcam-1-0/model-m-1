from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts/phase-3"
PACKAGE = CONTRACTS / "p3-6-consolidated-runtime-closeout-r5-storage-execution-package.json"
REQUEST = CONTRACTS / "p3-6-consolidated-runtime-closeout-r5-storage-request.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_r5_request_binds_exact_execution_package() -> None:
    package = _load(PACKAGE)
    request = _load(REQUEST)
    digest = _sha256(PACKAGE)

    assert digest == "26F974340A720DEC52C629A75394DDD0FE5A1B9A546998C9241F29D1BAC89554"
    assert request["execution_package_digest_sha256"] == digest
    assert request["execution_package_files"] == [
        {
            "path": str(PACKAGE.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest,
        }
    ]
    assert package["manifest_hash_rule"].startswith("uppercase_SHA_256")


def test_r5_package_and_request_bind_every_declared_input() -> None:
    package = _load(PACKAGE)
    request = _load(REQUEST)
    declared = [
        *package["prerequisite_evidence"],
        *package["exact_sources"],
        *request["source_binding_files"],
    ]
    predecessor = package["consumed_predecessor"]
    for prefix in ("package", "request", "authorization", "result", "evidence"):
        declared.append(
            {
                "path": predecessor[f"{prefix}_path"],
                "sha256": predecessor[f"{prefix}_sha256"],
            }
        )

    for binding in declared:
        path = ROOT / binding["path"]
        assert path.is_file(), binding["path"]
        assert _sha256(path) == binding["sha256"], binding["path"]


def test_r5_request_window_is_literal_and_bounded() -> None:
    package = _load(PACKAGE)
    request = _load(REQUEST)
    not_before = datetime.fromisoformat(request["authorization_not_before"])
    expires_at = datetime.fromisoformat(request["authorization_expires_at"])

    assert (expires_at - not_before).total_seconds() == 24 * 60 * 60
    assert request["authorization_expires_at"] == request["runtime_binding"]["valid_until"]
    assert package["request_wire_contract"]["authorization_not_before"] == request["authorization_not_before"]
    assert package["request_wire_contract"]["authorization_expires_at"] == request["authorization_expires_at"]
    assert package["request_wire_contract"]["PowerShell_JSON_date_kind"] == "String"


def test_r5_transaction_is_single_attempt_and_exactly_bounded() -> None:
    package = _load(PACKAGE)
    request = _load(REQUEST)
    transaction = package["transaction"]

    assert request["candidate_volume"] == transaction["candidate_volume"] == "F:"
    assert request["candidate_root"] == transaction["candidate_root"] == r"F:\HCAM-Quarantine"
    assert request["action_ids"] == transaction["action_ids"]
    assert len(request["action_ids"]) == 10
    assert request["output_paths"] == transaction["output_paths"]
    assert len(set(request["output_paths"])) == 3
    assert transaction["maximum_attempts"] == 1
    assert transaction["automatic_retry"] is False
    assert request["probe_bytes"] == 4096
    assert request["total_timeout_seconds"] == 120


def test_r5_binds_fixed_sources_and_preserves_r4_history() -> None:
    package = _load(PACKAGE)
    request = _load(REQUEST)
    sources = {entry["path"]: entry["sha256"] for entry in package["exact_sources"]}

    assert sources["tools/phase36_quarantine_transaction_runner_r2.ps1"] == request["source_binding_files"][11]["sha256"]
    assert request["handler_module_sha256"] == sources["tools/phase36_quarantine_machine_handlers_r1.psm1"]
    assert request["windows_adapter_sha256"] == sources["tools/phase36_quarantine_windows_storage_adapter_r1.psm1"]
    assert package["consumed_predecessor"]["root_created"] is False
    assert package["consumed_predecessor"]["same_package_retry_performed"] is False
    for kind in ("authorization", "result", "evidence"):
        assert (CONTRACTS / f"p3-6-quarantine-storage-r2-{kind}.json").is_file()
        assert (CONTRACTS / f"p3-6-quarantine-storage-r5-{kind}.json").is_file()


def test_r5_storage_result_is_ready_and_zero_retention() -> None:
    result = _load(CONTRACTS / "p3-6-quarantine-storage-r5-result.json")
    evidence = _load(CONTRACTS / "p3-6-quarantine-storage-r5-evidence.json")

    assert result["reason_code"] == "ok"
    assert result["drive_ready"] is True
    assert result["canonical_path_policy_pass"] is True
    assert result["candidate_absent_before_attempt"] is True
    assert result["root_created_by_attempt"] is True
    assert result["root_retained_after_attempt"] is True
    assert result["bounded_DACL_policy_booleans"]["overall_DACL_pass"] is True
    assert all(result["bounded_DACL_policy_booleans"].values())
    assert all(result["bounded_probe_policy_booleans"].values())
    assert evidence["result_sha256"] == _sha256(
        CONTRACTS / "p3-6-quarantine-storage-r5-result.json"
    )
    assert evidence["probe_content_retained"] is False
    assert evidence["raw_error_persisted"] is False
    assert evidence["identity_or_security_material_persisted"] is False
    assert evidence["automatic_retry_authorized"] is False
    assert evidence["deployment_authorized"] is False
    assert evidence["remote_git_authorized"] is False


def test_r5_keeps_security_and_remote_surfaces_closed() -> None:
    package = _load(PACKAGE)
    authority = package["authority"]
    exclusions = set(package["continuing_exclusions"])

    assert authority["routine_step_approval_required"] is False
    assert authority["security_bypass_or_privilege_escalation"] is False
    assert authority["remote_Git"] is False
    assert "no_security_bypass_or_privilege_escalation" in exclusions
    assert "no_credentials_secrets_private_or_Government_data" in exclusions
    assert "no_camera_media_model_dataset_or_inference" in exclusions
    assert "no_scanner_network_container_Kubernetes_or_deployment" in exclusions
