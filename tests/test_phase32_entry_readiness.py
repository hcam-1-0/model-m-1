from __future__ import annotations

import copy
import io
import json
import re
from contextlib import redirect_stdout

from tools import phase32_entry_readiness as readiness


def test_current_entry_state_is_valid_and_blocked() -> None:
    report = readiness.build_readiness_report()

    assert report.status == "blocked_pending_owner_decisions"
    assert report.scope == "phase3.p3_2.portable_detection.pre_entry"
    assert report.failures == 0
    assert report.manual_gates == 5
    assert re.fullmatch(r"[0-9A-F]{64}", report.record_digest)
    assert report.record_digest == readiness.EXPECTED_RECORD_DIGEST


def test_default_cli_accepts_valid_block_while_strict_requires_owner_decisions() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        default_exit = readiness.main(["--json"])
        strict_exit = readiness.main(["--strict"])

    payload = json.loads(output.getvalue().split("Phase 3 P3.2 entry readiness:")[0])
    assert default_exit == 0
    assert strict_exit == 2
    assert payload["status"] == "blocked_pending_owner_decisions"
    assert payload["failures"] == 0
    assert payload["manual_gates"] == 5


def test_all_structured_checks_pass() -> None:
    checks = (
        readiness.check_required_files(),
        readiness.check_entry_record(),
        readiness.check_accepted_dependencies(),
        readiness.check_reference_candidate_blocked(),
        readiness.check_documentation_boundary(),
        readiness.check_ci_integration(),
    )

    assert all(check.status == readiness.PASS for check in checks)


def test_entry_record_rejects_unauthorized_start(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.ENTRY_RECORD:
            value["start_authorization"] = "authorized"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_entry_record()

    assert result.status == readiness.FAIL
    assert "fail-closed" in result.detail


def test_entry_record_rejects_decision_promotion(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.ENTRY_RECORD:
            value["decisions"][0]["status"] = "owner_approved"
        return value

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_entry_record()

    assert result.status == readiness.FAIL
    assert "pending states changed" in result.detail


def test_entry_record_rejects_removed_non_authorization(monkeypatch) -> None:
    original = readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == readiness.ENTRY_RECORD:
            value["non_authorization"].remove("camera_sentinel_or_media_access")
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


def test_ci_check_rejects_missing_blocked_entry_command(monkeypatch) -> None:
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
