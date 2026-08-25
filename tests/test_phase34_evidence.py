from __future__ import annotations

from tools.phase34_c10_evidence import EXPECTED_EVENTS, build_report, validate


def test_phase34_c10_evidence_is_complete_and_deterministic() -> None:
    first = build_report()
    second = build_report()
    assert first == second
    assert validate(first) == []
    assert first["logic_agreement"] == 1.0
    assert first["replay_stable"] is True
    assert len(first["scenario_reports"]) == len(EXPECTED_EVENTS)


def test_phase34_c10_validation_rejects_tampering() -> None:
    report = build_report()
    report["execution_scope"] = "camera"
    assert "execution_scope" in validate(report)
    assert "content_digest" in validate(report)
