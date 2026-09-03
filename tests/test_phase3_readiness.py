from __future__ import annotations

import copy
import hashlib
import io
import json
import re
from contextlib import redirect_stdout

from tools import phase3_readiness


def test_current_p3_0_report_is_accepted() -> None:
    report = phase3_readiness.build_readiness_report(run_validation=False)

    assert report.status == "accepted"
    assert report.scope == "phase3.p3_0.contracts_and_guardrails"
    assert report.failures == 0
    assert report.manual_gates == 0
    assert re.fullmatch(r"[0-9A-F]{64}", report.documentation_digest)


def test_structured_contract_and_safety_checks_pass() -> None:
    checks = (
        phase3_readiness.check_required_files(),
        phase3_readiness.check_contract_snapshots(),
        phase3_readiness.check_fail_closed_boundaries(),
        phase3_readiness.check_privacy_and_safety(),
        phase3_readiness.check_observability(),
        phase3_readiness.check_documentation_digest(),
        phase3_readiness.check_owner_decision_record(),
        phase3_readiness.check_future_boundaries(),
    )

    assert all(check.status == phase3_readiness.PASS for check in checks)


def test_json_report_and_strict_accepted_exit_are_machine_readable() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = phase3_readiness.main(["--json"])

    payload = json.loads(output.getvalue())
    assert exit_code == 0
    assert payload["status"] == "accepted"
    assert payload["manual_gates"] == 0
    assert phase3_readiness.main(["--strict"]) == 0


def test_contract_check_fails_when_database_guard_changes(monkeypatch) -> None:
    original = phase3_readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == "contracts/phase-3/database.json":
            table = next(
                item
                for item in value["tables"]
                if item["name"] == "analytics_assignments"
            )
            guard = next(
                item
                for item in table["check_constraints"]
                if item["name"] == "ck_analytics_assignment_p3_lifecycle_state"
            )
            guard["sql"] = "lifecycle_state = 'active'"
        return value

    monkeypatch.setattr(phase3_readiness, "_read_json", changed)
    result = phase3_readiness.check_contract_snapshots()

    assert result.status == phase3_readiness.FAIL
    assert "ck_analytics_assignment_p3_lifecycle_state" in result.detail


def test_owner_decision_check_rejects_policy_tampering(monkeypatch) -> None:
    original = phase3_readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == "contracts/phase-3/p3-0-owner-decisions.json":
            value["metadata_policy"]["data_classes"][0]["access_roles"].append(
                "camera.exporter"
            )
        return value

    monkeypatch.setattr(phase3_readiness, "_read_json", changed)
    result = phase3_readiness.check_owner_decision_record()

    assert result.status == phase3_readiness.FAIL
    assert "derived.analytics.standard" in result.detail


def test_owner_decision_check_rejects_duplicate_gate_records(monkeypatch) -> None:
    original = phase3_readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == "contracts/phase-3/p3-0-owner-decisions.json":
            value["approvals"].append(
                {"gate_id": "P3-G1", "status": "owner_approved"}
            )
        return value

    monkeypatch.setattr(phase3_readiness, "_read_json", changed)
    result = phase3_readiness.check_owner_decision_record()

    assert result.status == phase3_readiness.FAIL
    assert "duplicates" in result.detail


def test_owner_acceptance_self_review_policy_is_tamper_evident(monkeypatch) -> None:
    original = phase3_readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == "contracts/phase-3/p3-0-owner-decisions.json":
            value["owner_p3_0_acceptance"]["review_policy"] = "independent_only"
        return value

    monkeypatch.setattr(phase3_readiness, "_read_json", changed)
    result = phase3_readiness.check_owner_decision_record()

    assert result.status == phase3_readiness.FAIL
    assert "self-review policy changed" in result.detail


def test_later_gate_review_policy_is_tamper_evident(monkeypatch) -> None:
    original = phase3_readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == "contracts/phase-3/p3-0-owner-decisions.json":
            value["later_gate_review_policy"]["evidence_requirements_remain_mandatory"] = False
        return value

    monkeypatch.setattr(phase3_readiness, "_read_json", changed)
    result = phase3_readiness.check_owner_decision_record()

    assert result.status == phase3_readiness.FAIL
    assert "later-gate separate-review policy changed" in result.detail


def test_checked_owner_gate_rejects_pending_evidence(monkeypatch) -> None:
    original = phase3_readiness._read

    def changed(relative_path: str) -> str:
        content = original(relative_path)
        if relative_path == "docs/phase-3/readiness-report.md":
            return content.replace(
                "Evidence: [P3-G1 owner decision](p3-0-owner-decisions.md#p3-g1)",
                "Evidence: `pending`",
                1,
            )
        return content

    monkeypatch.setattr(phase3_readiness, "_read", changed)
    gates = phase3_readiness.check_owner_gates()

    assert gates[0].status == phase3_readiness.FAIL
    assert "safe repository evidence link" in gates[0].detail


def test_owner_gates_cannot_be_completed_out_of_order(monkeypatch) -> None:
    original = phase3_readiness._read

    def changed(relative_path: str) -> str:
        content = original(relative_path)
        if relative_path == "docs/phase-3/readiness-report.md":
            content = content.replace("- [x] `P3-G1`", "- [ ] `P3-G1`", 1)
            return content.replace(
                "Evidence: [P3-G1 owner decision](p3-0-owner-decisions.md#p3-g1)",
                "Evidence: `pending`",
                1,
            )
        return content

    monkeypatch.setattr(phase3_readiness, "_read", changed)
    gates = phase3_readiness.check_owner_gates()

    assert gates[1].status == phase3_readiness.FAIL
    assert gates[1].detail == "Owner gates must be completed in order."


def test_validation_evidence_uses_portable_python_name() -> None:
    command = [phase3_readiness.sys.executable, "-m", "compileall"]

    assert phase3_readiness._display_command(command) == "python -m compileall"


def test_documentation_digest_is_sorted_and_deterministic(tmp_path, monkeypatch) -> None:
    (tmp_path / "b.md").write_text("second\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("first\n", encoding="utf-8")
    monkeypatch.setattr(phase3_readiness, "PHASE3", tmp_path)

    digest, manifest = phase3_readiness.documentation_digest()
    expected_manifest = [
        f"a.md:{hashlib.sha256((tmp_path / 'a.md').read_bytes()).hexdigest().upper()}\n",
        f"b.md:{hashlib.sha256((tmp_path / 'b.md').read_bytes()).hexdigest().upper()}\n",
    ]
    expected = hashlib.sha256("".join(expected_manifest).encode()).hexdigest().upper()

    assert manifest == expected_manifest
    assert digest == expected
