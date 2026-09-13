from __future__ import annotations

from datetime import datetime, timedelta

from hcam.operations.platform.contracts import CircuitStateV1


def record_failure(
    state: CircuitStateV1,
    *,
    now: datetime,
    threshold: int = 3,
) -> CircuitStateV1:
    if not 1 <= threshold <= 100:
        raise ValueError("circuit threshold is outside bounds")
    failures = state.consecutive_failures + 1
    opened = failures >= threshold
    return state.model_copy(
        update={
            "state": "open" if opened else "closed",
            "consecutive_failures": failures,
            "probe_remaining": 0,
            "opened_at": now if opened else state.opened_at,
            "updated_at": now,
        }
    )


def record_success(state: CircuitStateV1, *, now: datetime) -> CircuitStateV1:
    return state.model_copy(
        update={
            "state": "closed",
            "consecutive_failures": 0,
            "probe_remaining": 0,
            "opened_at": None,
            "updated_at": now,
        }
    )


def allow_half_open_probe(
    state: CircuitStateV1,
    *,
    now: datetime,
    reset_after_seconds: int = 60,
    maximum_probes: int = 1,
) -> CircuitStateV1:
    if state.state != "open" or state.opened_at is None:
        raise ValueError("only an open circuit can become half open")
    if now < state.opened_at + timedelta(seconds=reset_after_seconds):
        raise ValueError("circuit reset interval has not elapsed")
    if not 1 <= maximum_probes <= 16:
        raise ValueError("half-open probe bound is invalid")
    return state.model_copy(
        update={"state": "half_open", "probe_remaining": maximum_probes, "updated_at": now}
    )


def consume_probe(state: CircuitStateV1, *, now: datetime) -> CircuitStateV1:
    if state.state != "half_open" or state.probe_remaining < 1:
        raise ValueError("no half-open probe is available")
    return state.model_copy(update={"probe_remaining": state.probe_remaining - 1, "updated_at": now})
