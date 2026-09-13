from datetime import UTC, datetime

import pytest

from hcam.acceptance.adapters import AdapterBoundaryError, GeneratedApplicationBoundary
from hcam.acceptance.contracts import ScenarioStepV1
from hcam.acceptance.determinism import IdentifierProvider


NOW = datetime(2026, 1, 1, tzinfo=UTC)
IDS = IdentifierProvider("generated.p47", 1)


def _step(action: str, **data: object) -> ScenarioStepV1:
    return ScenarioStepV1.model_construct(
        step_id="p47.test.step",
        sequence=1,
        action=action,
        advance_ms=1,
        input_data=data,
        expected_outcome="denied",
        expected_reason="test.denied",
    )


def test_adapter_fails_closed_for_unallowlisted_action() -> None:
    adapter = GeneratedApplicationBoundary("S00")
    with pytest.raises(AdapterBoundaryError):
        adapter.execute(_step("unknown"), logical_at=NOW, identifiers=IDS)


def test_adapter_denies_missing_preconditions() -> None:
    adapter = GeneratedApplicationBoundary("S00")
    assert (
        adapter.execute(
            _step("duplicate_event"), logical_at=NOW, identifiers=IDS
        ).reason_code
        == "event.source_missing"
    )
    assert (
        adapter.execute(_step("correlate"), logical_at=NOW, identifiers=IDS).reason_code
        == "correlation.source_missing"
    )
    assert (
        adapter.execute(
            _step("propose_alert"), logical_at=NOW, identifiers=IDS
        ).reason_code
        == "alert.rule_not_matched"
    )
    assert (
        adapter.execute(
            _step("review_alert"), logical_at=NOW, identifiers=IDS
        ).reason_code
        == "review.alert_missing"
    )
    assert (
        adapter.execute(
            _step("open_investigation"), logical_at=NOW, identifiers=IDS
        ).reason_code
        == "investigation.alert_not_accepted"
    )
    assert (
        adapter.execute(
            _step("append_evidence_reference"), logical_at=NOW, identifiers=IDS
        ).reason_code
        == "evidence.investigation_missing"
    )
    assert (
        adapter.execute(
            _step("recover_worker"), logical_at=NOW, identifiers=IDS
        ).reason_code
        == "worker.not_degraded"
    )


def test_adapter_snapshot_records_only_generated_state() -> None:
    adapter = GeneratedApplicationBoundary("S08")
    adapter.execute(_step("degrade_worker"), logical_at=NOW, identifiers=IDS)
    adapter.execute(_step("recover_worker"), logical_at=NOW, identifiers=IDS)
    snapshot = adapter.snapshot()
    assert adapter.terminal_state() == "recovered"
    assert snapshot["generated_only"] is True
    assert snapshot["direct_persistence_attempts"] == snapshot["external_effects"] == 0
