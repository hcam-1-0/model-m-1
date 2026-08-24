from __future__ import annotations

import copy
import io
import json
import re
from contextlib import redirect_stdout
from types import SimpleNamespace

from tools import phase31_readiness


def test_current_p3_1_planning_is_authorized() -> None:
    report = phase31_readiness.build_readiness_report(run_validation=False)

    assert report.status == "authorized_for_implementation"
    assert report.scope == "phase3.p3_1.data_and_evaluation_foundation.planning"
    assert report.failures == 0
    assert report.manual_gates == 0
    assert re.fullmatch(r"[0-9A-F]{64}", report.package_digest)


def test_structured_planning_checks_pass() -> None:
    checks = (
        phase31_readiness.check_required_files(),
        phase31_readiness.check_authorization_record(),
        phase31_readiness.check_plan_completeness(),
        phase31_readiness.check_hardware_profile(),
        phase31_readiness.check_p3_0_dependency(),
        phase31_readiness.check_implementation_gates_pending(),
        phase31_readiness.check_package_digest(),
    )

    assert all(check.status == phase31_readiness.PASS for check in checks)
    assert all(
        check.status == phase31_readiness.PASS
        for check in phase31_readiness.check_planning_gates()
    )


def test_json_report_and_strict_exit_are_machine_readable() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = phase31_readiness.main(["--json", "--strict"])

    payload = json.loads(output.getvalue())
    assert exit_code == 0
    assert payload["status"] == "authorized_for_implementation"
    assert payload["failures"] == 0
    assert payload["manual_gates"] == 0


def test_authorization_rejects_source_tier_tampering(monkeypatch) -> None:
    original = phase31_readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == phase31_readiness.AUTHORIZATION_PATH:
            value["source_tiers"][2]["state"] = "authorized"
        return value

    monkeypatch.setattr(phase31_readiness, "_read_json", changed)
    result = phase31_readiness.check_authorization_record()

    assert result.status == phase31_readiness.FAIL
    assert "source_tiers" in result.detail


def test_authorization_rejects_evidence_waiver(monkeypatch) -> None:
    original = phase31_readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == phase31_readiness.AUTHORIZATION_PATH:
            value["later_review_policy"]["evidence_requirements_remain_mandatory"] = False
        return value

    monkeypatch.setattr(phase31_readiness, "_read_json", changed)
    result = phase31_readiness.check_authorization_record()

    assert result.status == phase31_readiness.FAIL
    assert "later_review_policy" in result.detail


def test_authorization_rejects_inference_expansion(monkeypatch) -> None:
    original = phase31_readiness._read_json

    def changed(relative_path: str):
        value = copy.deepcopy(original(relative_path))
        if relative_path == phase31_readiness.AUTHORIZATION_PATH:
            value["non_authorization"].remove(
                "training_finetuning_export_or_inference"
            )
        return value

    monkeypatch.setattr(phase31_readiness, "_read_json", changed)
    result = phase31_readiness.check_authorization_record()

    assert result.status == phase31_readiness.FAIL
    assert "non_authorization" in result.detail


def test_p3_0_dependency_must_remain_accepted(monkeypatch) -> None:
    report = SimpleNamespace(
        status="ready_for_owner_review",
        scope="phase3.p3_0.contracts_and_guardrails",
        failures=0,
        manual_gates=1,
    )
    monkeypatch.setattr(phase31_readiness, "_p3_0_report", lambda: report)

    result = phase31_readiness.check_p3_0_dependency()

    assert result.status == phase31_readiness.FAIL
    assert "zero failures and zero manual gates" in result.detail


def test_incomplete_planning_gate_requires_owner_authorization(monkeypatch) -> None:
    original = phase31_readiness._read

    def changed(relative_path: str) -> str:
        content = original(relative_path)
        if relative_path == phase31_readiness.READINESS_PATH:
            content = content.replace(
                "Status: `authorized_for_implementation`",
                "Status: `ready_for_owner_authorization`",
                1,
            )
            content = content.replace("- [x] `P31-G5`", "- [ ] `P31-G5`", 1)
            return content.replace(
                "Evidence: [P3.1 authorization](p3-1-authorization.md)",
                "Evidence: `pending`",
                1,
            )
        return content

    monkeypatch.setattr(phase31_readiness, "_read", changed)
    checks = phase31_readiness.check_planning_gates()

    assert checks[-1].status == phase31_readiness.MANUAL


def test_checked_planning_gate_rejects_remote_evidence(monkeypatch) -> None:
    original = phase31_readiness._read

    def changed(relative_path: str) -> str:
        content = original(relative_path)
        if relative_path == phase31_readiness.READINESS_PATH:
            return content.replace(
                "Evidence: [P3.1 plan](p3-1-plan.md)",
                "Evidence: [remote](https://example.invalid/plan)",
                1,
            )
        return content

    monkeypatch.setattr(phase31_readiness, "_read", changed)
    checks = phase31_readiness.check_planning_gates()

    assert checks[0].status == phase31_readiness.FAIL
    assert "safe local evidence link" in checks[0].detail


def test_planning_report_cannot_claim_implementation_completion(monkeypatch) -> None:
    original = phase31_readiness._read

    def changed(relative_path: str) -> str:
        content = original(relative_path)
        if relative_path == phase31_readiness.READINESS_PATH:
            return content.replace(
                "- [ ] P3.1 contracts and canonical fixtures implemented.",
                "- [x] P3.1 contracts and canonical fixtures implemented.",
                1,
            )
        return content

    monkeypatch.setattr(phase31_readiness, "_read", changed)
    result = phase31_readiness.check_implementation_gates_pending()

    assert result.status == phase31_readiness.FAIL
    assert "cannot claim implementation completion" in result.detail


def test_hardware_profile_rejects_machine_identifiers(monkeypatch) -> None:
    original = phase31_readiness._read

    def changed(relative_path: str) -> str:
        content = original(relative_path)
        if relative_path == phase31_readiness.HARDWARE_PATH:
            return content + "\nHost name: private-machine\n"
        return content

    monkeypatch.setattr(phase31_readiness, "_read", changed)
    result = phase31_readiness.check_hardware_profile()

    assert result.status == phase31_readiness.FAIL
    assert "machine identifier" in result.detail
