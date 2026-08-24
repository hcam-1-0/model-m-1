from __future__ import annotations

import copy
import io
import json
from contextlib import redirect_stdout

from tools import phase31_implementation_readiness as readiness


def test_current_implementation_is_accepted() -> None:
    report = readiness.build_readiness_report(run_validation=False)

    assert report.status == "accepted"
    assert report.scope == "phase3.p3_1.data_and_evaluation_foundation.implementation"
    assert report.failures == 0
    assert report.manual_gates == 0
    assert len(report.package_digest) == 64
    statuses = {check.name: check.status for check in report.checks}
    assert statuses["clean_source_baseline"] == readiness.PASS
    assert statuses["owner_acceptance"] == readiness.PASS
    assert all(status == readiness.PASS for status in statuses.values())


def test_json_report_is_machine_readable_and_strict_accepts_closed_gate() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = readiness.main(["--json", "--strict"])

    payload = json.loads(output.getvalue())
    assert exit_code == 0
    assert payload["status"] == "accepted"
    assert payload["failures"] == 0
    assert payload["manual_gates"] == 0


def test_structured_technical_checks_pass() -> None:
    checks = (
        readiness.check_required_files(),
        readiness.check_snapshot_drift(),
        readiness.check_evidence_index(),
        readiness.check_generated_source_evidence(),
        readiness.check_quality_and_leakage_reports(),
        readiness.check_metric_goldens(),
        readiness.check_candidate_dossier(),
        readiness.check_run_safety(),
        readiness.check_ci_integration(),
        readiness.check_owner_acceptance(),
        readiness.check_package_digest(),
    )

    assert all(check.status == readiness.PASS for check in checks)


def test_evidence_index_rejects_overclaim_and_digest_tampering(monkeypatch) -> None:
    original = readiness._read_json

    def changed(path):
        document = copy.deepcopy(original(path))
        if path.name == "evidence-index.json":
            document["assertions"]["candidate_eligible_count"] = 1
        return document

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_evidence_index()

    assert result.status == readiness.FAIL
    assert "candidate_eligible_count" in result.evidence
    assert "index_digest" in result.evidence


def test_generated_source_check_rejects_external_reference(monkeypatch) -> None:
    original = readiness._read_json

    def changed(path):
        document = copy.deepcopy(original(path))
        if path.name == "detection-v1.json":
            document["external_inputs"] = ["https://example.invalid/source"]
        return document

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_generated_source_evidence()

    assert result.status == readiness.FAIL
    assert "detection-v1.json" in result.evidence
    assert "detection-v1.json-external-reference" in result.evidence


def test_quality_check_rejects_report_tampering(monkeypatch) -> None:
    original = readiness._read_json

    def changed(path):
        document = copy.deepcopy(original(path))
        if path.name == "split-validation-report-v1.json":
            document["item_count"] += 1
        return document

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_quality_and_leakage_reports()

    assert result.status == readiness.FAIL
    assert "digest does not match" in result.detail


def test_metric_check_rejects_promoted_unapproved_gate(monkeypatch) -> None:
    original = readiness._read_json

    def changed(path):
        document = copy.deepcopy(original(path))
        if path.name == "metric-report-v1.json":
            document["hard_gates"][0]["outcome"] = "pass"
        return document

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_metric_goldens()

    assert result.status == readiness.FAIL
    assert "invalid" in result.detail


def test_candidate_check_rejects_manifest_tampering(monkeypatch) -> None:
    original = readiness._read_json

    def changed(path):
        document = copy.deepcopy(original(path))
        if path.name == "candidate-det-r0.json":
            document["known_limits"].append("Tampered")
        return document

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_candidate_dossier()

    assert result.status == readiness.FAIL
    assert "invalid" in result.detail


def test_run_check_rejects_manifest_tampering(monkeypatch) -> None:
    original = readiness._read_json

    def changed(path):
        document = copy.deepcopy(original(path))
        if path.name == "evaluation-run-v1.json":
            document["operator_id"] = "tampered-operator"
        return document

    monkeypatch.setattr(readiness, "_read_json", changed)
    result = readiness.check_run_safety()

    assert result.status == readiness.FAIL
    assert "invalid" in result.detail


def test_clean_source_and_owner_gates_pass_with_exact_records() -> None:
    assert readiness.check_clean_source_baseline().status == readiness.PASS
    assert readiness.check_owner_acceptance().status == readiness.PASS


def test_owner_acceptance_rejects_record_tampering(monkeypatch) -> None:
    original = readiness._read_json

    def changed(path):
        document = copy.deepcopy(original(path))
        if path == readiness.ACCEPTANCE_PATH:
            document["evidence_package_digest"] = "0" * 64
        return document

    monkeypatch.setattr(readiness, "_read_json", changed)

    assert readiness.check_owner_acceptance().status == readiness.FAIL


def test_owner_acceptance_rejects_altered_package_requirement(monkeypatch) -> None:
    original = readiness._read_json

    def changed(path):
        document = copy.deepcopy(original(path))
        if path.name == "evidence-index.json":
            document["owner_acceptance"]["required_record"] = "different-record"
        return document

    monkeypatch.setattr(readiness, "_read_json", changed)

    assert readiness.check_owner_acceptance().status == readiness.FAIL


def test_ci_check_rejects_missing_command(monkeypatch) -> None:
    workflow = readiness.ROOT / ".github" / "workflows" / "python-ci.yml"
    original = workflow.read_text

    def changed(*args, **kwargs):
        return original(*args, **kwargs).replace(
            "python tools/phase31_contracts.py check",
            "missing-p3-1-command",
        )

    monkeypatch.setattr(type(workflow), "read_text", lambda self, **kwargs: changed(**kwargs))
    result = readiness.check_ci_integration()

    assert result.status == readiness.FAIL


def test_validation_command_result_reports_failure(monkeypatch) -> None:
    monkeypatch.setattr(readiness, "_run", lambda command: (" ".join(command), "failed"))

    result = readiness.run_validation_commands()

    assert result.status == readiness.FAIL
    assert len(result.evidence) == 4


def test_build_report_status_precedence(monkeypatch) -> None:
    passing = readiness.CheckResult("pass", readiness.PASS, "ok", [])
    failing = readiness.CheckResult("fail", readiness.FAIL, "bad", [])
    manual = readiness.CheckResult("manual", readiness.MANUAL, "owner", [])

    functions = [
        "check_required_files",
        "check_snapshot_drift",
        "check_evidence_index",
        "check_generated_source_evidence",
        "check_quality_and_leakage_reports",
        "check_metric_goldens",
        "check_candidate_dossier",
        "check_run_safety",
        "check_ci_integration",
        "check_clean_source_baseline",
        "check_owner_acceptance",
        "check_package_digest",
    ]
    for name in functions:
        monkeypatch.setattr(readiness, name, lambda: passing)
    monkeypatch.setattr(readiness, "check_owner_acceptance", lambda: failing)
    assert readiness.build_readiness_report().status == "not_ready"

    monkeypatch.setattr(readiness, "check_owner_acceptance", lambda: manual)
    assert readiness.build_readiness_report().status == (
        "technical_evidence_ready_with_manual_gates"
    )

    monkeypatch.setattr(readiness, "check_owner_acceptance", lambda: passing)
    assert readiness.build_readiness_report().status == "accepted"
