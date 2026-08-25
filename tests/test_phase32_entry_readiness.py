from __future__ import annotations

import copy
import io
import json
import re
from contextlib import redirect_stdout

from tools import phase32_entry_readiness as readiness


def test_current_entry_state_is_valid_and_generated_only_authorized() -> None:
    report = readiness.build_readiness_report()

    assert report.status == "implementation_authorized_generated_only"
    assert report.scope == "phase3.p3_2.portable_detection.generated_only_start"
    assert report.failures == 0
    assert report.manual_gates == 0
    assert re.fullmatch(r"[0-9A-F]{64}", report.record_digest)
    assert report.record_digest == readiness.EXPECTED_RECORD_DIGEST


def test_default_and_strict_cli_accept_completed_entry_decisions() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        default_exit = readiness.main(["--json"])
        strict_exit = readiness.main(["--strict"])

    payload = json.loads(output.getvalue().split("Phase 3 P3.2 entry readiness:")[0])
    assert default_exit == 0
    assert strict_exit == 0
    assert payload["status"] == "implementation_authorized_generated_only"
    assert payload["failures"] == 0
    assert payload["manual_gates"] == 0


def test_all_structured_checks_pass() -> None:
    checks = (
        readiness.check_required_files(),
        readiness.check_entry_record(),
        readiness.check_research_authorization(),
        readiness.check_research_evidence(),
        readiness.check_accepted_dependencies(),
        readiness.check_reference_candidate_blocked(),
        readiness.check_model_approval(),
        readiness.check_dataset_approval(),
        readiness.check_runtime_approval(),
        readiness.check_start_authorization(),
        readiness.check_documentation_boundary(),
        readiness.check_ci_integration(),
    )

    assert all(check.status == readiness.PASS for check in checks)


def test_entry_record_rejects_start_reference_drift(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.ENTRY_RECORD:
            value["start_authorization"]["status"] = "not_authorized"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_entry_record()

    assert result.status == readiness.FAIL
    assert "start authorization reference changed" in result.detail


def test_entry_record_rejects_decision_promotion(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.ENTRY_RECORD:
            value["decisions"][1]["status"] = "owner_approved"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_entry_record()

    assert result.status == readiness.FAIL
    assert "approval states changed" in result.detail


def test_research_authorization_rejects_public_dataset_promotion(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.RESEARCH_MANIFEST:
            value["dataset_candidates"][1]["status"] = "approved"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_research_authorization()

    assert result.status == readiness.FAIL
    assert "dataset gate" in result.detail


def test_research_evidence_rejects_accuracy_claim(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.RESEARCH_EVIDENCE:
            value["experiment"]["accuracy"] = "measured"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_research_evidence()

    assert result.status == readiness.FAIL
    assert "claim boundary" in result.detail


def test_entry_record_rejects_removed_non_authorization(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.ENTRY_RECORD:
            value["non_authorization"].remove(
                "physical_camera_onvif_media_or_sentinel_stream_access"
            )
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_entry_record()

    assert result.status == readiness.FAIL
    assert "non-authorization boundary changed" in result.detail


def test_dependency_check_rejects_p3_1_digest_drift(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == "contracts/phase-3/p3-1-acceptance.json":
            value["evidence_package_digest"] = "0" * 64
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_accepted_dependencies()

    assert result.status == readiness.FAIL
    assert "P3.1 acceptance identity changed" in result.detail


def test_reference_candidate_cannot_become_eligible_silently(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.CANDIDATE:
            value["eligibility"] = "eligible"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_reference_candidate_blocked()

    assert result.status == readiness.FAIL
    assert "no longer blocked" in result.detail


def test_model_approval_rejects_wrong_artifact_hash(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.MODEL_APPROVAL:
            value["artifact"]["sha256"] = "0" * 64
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_model_approval()

    assert result.status == readiness.FAIL
    assert "exact model approval identity" in result.detail


def test_dataset_approval_rejects_real_data_source(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.DATASET_APPROVAL:
            value["candidate_id"] = "DATA-REAL-R0"
            value["provenance"] = "team-owned camera media"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_dataset_approval()

    assert result.status == readiness.FAIL
    assert "generated-only dataset decision changed" in result.detail


def test_runtime_approval_rejects_provider_fallback(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.RUNTIME_APPROVAL:
            value["runtime"]["execution_provider"] = "CUDAExecutionProvider"
            value["fail_closed"]["silent_execution_provider_fallback"] = "allowed"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_runtime_approval()

    assert result.status == readiness.FAIL
    assert "CPU-only runtime" in result.detail
    assert "fallback is no longer fail-closed" in result.detail


def test_start_authorization_rejects_remote_git_or_deployment_widening(
    monkeypatch,
) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.START_AUTHORIZATION:
            value["still_prohibited"].remove("remote_git_push_pull_request_or_merge")
            value["still_prohibited"].remove(
                "pilot_production_statewide_deployment_or_performance_claim"
            )
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_start_authorization()

    assert result.status == readiness.FAIL
    assert "continuing start prohibitions changed" in result.detail


def test_documentation_check_rejects_missing_live_link(monkeypatch) -> None:
    original = readiness._read

    def changed(relative_path: str) -> str:
        value = original(relative_path)
        if relative_path == "docs/phase-3/README.md":
            return value.replace(
                "[P3.2 entry decision packet](p3-2-entry-decision-packet.md)",
                "P3.2 entry decision packet",
            )
        return value

    monkeypatch.setattr(readiness, "_read", changed)
    result = readiness.check_documentation_boundary()

    assert result.status == readiness.FAIL
    assert "not linked" in result.detail


def test_ci_check_rejects_missing_entry_command(monkeypatch) -> None:
    original = readiness._read

    def changed(relative_path: str) -> str:
        value = original(relative_path)
        if relative_path == ".github/workflows/python-ci.yml":
            return value.replace("python tools/phase32_entry_readiness.py", "true")
        return value

    monkeypatch.setattr(readiness, "_read", changed)
    result = readiness.check_ci_integration()

    assert result.status == readiness.FAIL
    assert "does not verify" in result.detail
