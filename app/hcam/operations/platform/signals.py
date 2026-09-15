from __future__ import annotations

from hcam.operations.platform.bounds import validate_generated_document
from hcam.operations.platform.contracts import SignalEnvelopeV1, SignalProjectionV1


LANE_SAFE_FIELDS = {
    "operational": frozenset({"component", "outcome", "queue_class", "state"}),
    "security": frozenset({"control", "outcome", "policy", "state"}),
    "audit": frozenset({"action", "outcome", "resource_type"}),
    "evidence": frozenset({"integrity_state", "reference_type", "state"}),
}


class SignalProjectionError(ValueError):
    pass


def project_signal(signal: SignalEnvelopeV1) -> SignalProjectionV1:
    allowed = LANE_SAFE_FIELDS[signal.lane]
    safe: dict[str, str | int | bool] = {}
    for key, value in signal.attributes.items():
        if key not in allowed:
            continue
        if isinstance(value, bool | int | str):
            safe[key] = value
    validate_generated_document(safe)
    return SignalProjectionV1(
        signal_id=signal.signal_id,
        lane=signal.lane,
        department=signal.department,
        event_type=signal.event_type,
        severity=signal.severity,
        occurred_at=signal.occurred_at,
        safe_facets=safe,
    )


def assert_lane_separation(signals: list[SignalEnvelopeV1]) -> None:
    seen: dict[str, str] = {}
    for signal in signals:
        previous = seen.setdefault(signal.signal_id, signal.lane)
        if previous != signal.lane:
            raise SignalProjectionError("a signal identifier cannot cross authoritative lanes")
