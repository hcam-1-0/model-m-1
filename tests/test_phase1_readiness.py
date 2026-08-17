from __future__ import annotations

import io
from contextlib import redirect_stdout

from tools import phase1_readiness


def test_phase1_report_is_ready_for_owner_review() -> None:
    report = phase1_readiness.build_readiness_report(run_validation=False)
    assert report.failures == 0
    assert report.manual_gates == 1
    assert report.status == "ready_for_owner_review"


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
        phase1_readiness.check_owner_review_packet().status
        == phase1_readiness.PASS
    )


def test_phase1_json_report_is_machine_readable() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = phase1_readiness.main(["--json"])
    assert exit_code == 0
    assert '"status": "ready_for_owner_review"' in output.getvalue()


def test_phase1_strict_mode_preserves_owner_gate() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = phase1_readiness.main(["--strict"])
    assert exit_code == 2
    assert "Manual gates: 1" in output.getvalue()
