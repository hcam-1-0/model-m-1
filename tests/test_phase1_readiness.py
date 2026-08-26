from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout

from tools import phase1_readiness


def test_phase1_validation_timeout_accommodates_the_full_suite(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def run(command: list[str], **kwargs: object):
        observed.update(kwargs)
        return phase1_readiness.subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(phase1_readiness.subprocess, "run", run)

    _evidence, error = phase1_readiness._run([sys.executable, "-m", "pytest"])

    assert error is None
    assert observed["timeout"] == phase1_readiness.VALIDATION_COMMAND_TIMEOUT_SECONDS
    assert phase1_readiness.VALIDATION_COMMAND_TIMEOUT_SECONDS >= 600


def test_phase1_report_is_complete() -> None:
    report = phase1_readiness.build_readiness_report(run_validation=False)
    assert report.failures == 0
    assert report.manual_gates == 0
    assert report.status == "complete"


def test_phase1_contract_and_safety_checks_pass() -> None:
    assert phase1_readiness.check_required_files().status == phase1_readiness.PASS
    assert (
        phase1_readiness.check_api_and_security_contracts().status
        == phase1_readiness.PASS
    )
    assert (
        phase1_readiness.check_safety_documentation().status
        == phase1_readiness.PASS
    )
    assert (
        phase1_readiness.check_database_integrity_contracts().status
        == phase1_readiness.PASS
    )
    assert (
        phase1_readiness.check_operational_contracts().status
        == phase1_readiness.PASS
    )
    assert (
        phase1_readiness.check_deployment_resilience_contracts().status
        == phase1_readiness.PASS
    )
    assert (
        phase1_readiness.check_owner_review_packet().status
        == phase1_readiness.PASS
    )
    assert (
        phase1_readiness.check_build_quality_contracts().status
        == phase1_readiness.PASS
    )


def test_phase1_json_report_is_machine_readable() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = phase1_readiness.main(["--json"])
    assert exit_code == 0
    assert '"status": "complete"' in output.getvalue()


def test_phase1_strict_mode_passes_after_owner_acceptance() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = phase1_readiness.main(["--strict"])
    assert exit_code == 0
    assert "Manual gates: 0" in output.getvalue()
