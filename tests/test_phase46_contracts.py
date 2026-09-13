from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hcam.operations.platform.bounds import BoundsError, validate_generated_document
from hcam.operations.platform.contracts import CorrelationContextV1, SignalEnvelopeV1


NOW = datetime(2026, 9, 5, tzinfo=UTC)


def test_contracts_forbid_unknown_fields_and_operational_values() -> None:
    with pytest.raises(ValidationError):
        CorrelationContextV1(correlation_id="generated:one", unknown=True)
    with pytest.raises(ValidationError):
        SignalEnvelopeV1(
            signal_id="ref_" + "1" * 32,
            lane="operational",
            department="Generated Department",
            event_type="worker.completed",
            severity="info",
            occurred_at=NOW,
            attributes={"state": "succeeded"},
            correlation=CorrelationContextV1(correlation_id="generated:one"),
            operational=True,
        )


def test_generated_document_rejects_secrets_locators_and_nonfinite_values() -> None:
    for value in ({"password": "generated"}, {"item": "https://example.invalid"}, {"item": float("nan")}):
        with pytest.raises(BoundsError):
            validate_generated_document(value)


def test_generated_document_accepts_bounded_metadata() -> None:
    assert validate_generated_document({"state": "generated", "count": 3, "active": False}) == 4
