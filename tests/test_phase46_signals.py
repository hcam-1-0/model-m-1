from datetime import UTC, datetime

import pytest

from hcam.operations.platform.contracts import CorrelationContextV1, SignalEnvelopeV1
from hcam.operations.platform.signals import SignalProjectionError, assert_lane_separation, project_signal


def _signal(lane: str = "operational") -> SignalEnvelopeV1:
    return SignalEnvelopeV1(
        signal_id="ref_" + "1" * 32,
        lane=lane,
        department="Generated Department",
        event_type="worker.completed",
        severity="info",
        occurred_at=datetime(2026, 9, 5, tzinfo=UTC),
        attributes={"state": "succeeded", "internal_detail": "omitted"},
        correlation=CorrelationContextV1(correlation_id="generated:one"),
    )


def test_signal_projection_is_sanitized_and_lane_authoritative() -> None:
    projected = project_signal(_signal())
    assert projected.safe_facets == {"state": "succeeded"}
    assert projected.source_policy_authoritative is True


def test_signal_identity_cannot_cross_lanes() -> None:
    with pytest.raises(SignalProjectionError):
        assert_lane_separation([_signal("operational"), _signal("security")])
