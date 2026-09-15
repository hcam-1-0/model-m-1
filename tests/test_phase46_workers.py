from datetime import UTC, datetime, timedelta

import pytest

from hcam.operations.platform.circuits import allow_half_open_probe, consume_probe, record_failure, record_success
from hcam.operations.platform.contracts import CircuitStateV1, WorkerJobV1
from hcam.operations.platform.failures import failure
from hcam.operations.platform.workers import WorkerStateError, claim, complete, fail, heartbeat, recover_abandoned, retry_delay_seconds


NOW = datetime(2026, 9, 5, tzinfo=UTC)


def _job() -> WorkerJobV1:
    return WorkerJobV1(
        job_id="ref_" + "1" * 32,
        department="Generated Department",
        worker_class="telemetry",
        state="queued",
        attempt_count=0,
        idempotency_key="sha256:" + "2" * 64,
        payload_digest="sha256:" + "3" * 64,
        reason_code="worker.queued",
        updated_at=NOW,
    )


def test_worker_lease_heartbeat_and_completion() -> None:
    leased = claim(_job(), owner="generated:worker", now=NOW)
    renewed = heartbeat(leased, owner="generated:worker", now=NOW + timedelta(seconds=10))
    completed = complete(renewed, owner="generated:worker", now=NOW + timedelta(seconds=20))
    assert completed.state == "succeeded"
    assert completed.lease_owner is None


def test_worker_denies_late_commit_and_recovers_abandonment() -> None:
    leased = claim(_job(), owner="generated:worker", now=NOW)
    with pytest.raises(WorkerStateError):
        complete(leased, owner="generated:worker", now=NOW + timedelta(seconds=91))
    assert recover_abandoned(leased, now=NOW + timedelta(seconds=91)).state == "queued"


def test_worker_retry_is_bounded_and_deterministic() -> None:
    leased = claim(_job(), owner="generated:worker", now=NOW)
    retried = fail(leased, failure("dependency.timeout"), owner="generated:worker", now=NOW + timedelta(seconds=1))
    assert retried.state == "queued"
    assert retry_delay_seconds(retried.job_id, 1) == retry_delay_seconds(retried.job_id, 1)
    leased_again = claim(retried, owner="generated:worker", now=NOW + timedelta(seconds=2))
    denied = fail(leased_again, failure("authorization.denied"), owner="generated:worker", now=NOW + timedelta(seconds=3))
    assert denied.state == "failed"


def test_circuit_transitions_are_bounded() -> None:
    state = CircuitStateV1(dependency_class="generated:provider", state="closed", consecutive_failures=0, probe_remaining=0, updated_at=NOW)
    for offset in range(3):
        state = record_failure(state, now=NOW + timedelta(seconds=offset))
    assert state.state == "open"
    half_open = allow_half_open_probe(state, now=NOW + timedelta(seconds=70))
    assert half_open.state == "half_open"
    assert consume_probe(half_open, now=NOW + timedelta(seconds=70)).probe_remaining == 0
    assert record_success(half_open, now=NOW + timedelta(seconds=71)).state == "closed"


def test_worker_state_and_retry_bounds_fail_closed() -> None:
    with pytest.raises(WorkerStateError):
        claim(_job().model_copy(update={"state": "failed"}), owner="generated:worker", now=NOW)
    leased = claim(_job(), owner="generated:worker", now=NOW)
    with pytest.raises(WorkerStateError):
        heartbeat(leased, owner="generated:other", now=NOW)
    with pytest.raises(WorkerStateError):
        recover_abandoned(leased, now=NOW + timedelta(seconds=30))
    for attempt in (0, 4):
        with pytest.raises(ValueError):
            retry_delay_seconds(leased.job_id, attempt)


def test_worker_transient_failures_dead_letter_after_three_attempts() -> None:
    job = _job()
    for offset in range(3):
        leased = claim(job, owner="generated:worker", now=NOW + timedelta(seconds=offset * 2))
        job = fail(
            leased,
            failure("dependency.timeout"),
            owner="generated:worker",
            now=NOW + timedelta(seconds=offset * 2 + 1),
        )
    assert job.state == "dead_letter"
    abandoned = leased.model_copy(update={"attempt_count": 3})
    assert recover_abandoned(abandoned, now=NOW + timedelta(seconds=100)).state == "dead_letter"


def test_circuit_invalid_transitions_and_bounds_are_denied() -> None:
    closed = CircuitStateV1(
        dependency_class="generated:provider",
        state="closed",
        consecutive_failures=0,
        probe_remaining=0,
        updated_at=NOW,
    )
    for threshold in (0, 101):
        with pytest.raises(ValueError):
            record_failure(closed, now=NOW, threshold=threshold)
    with pytest.raises(ValueError):
        allow_half_open_probe(closed, now=NOW)
    opened = record_failure(closed, now=NOW, threshold=1)
    with pytest.raises(ValueError):
        allow_half_open_probe(opened, now=NOW + timedelta(seconds=30))
    with pytest.raises(ValueError):
        allow_half_open_probe(opened, now=NOW + timedelta(seconds=70), maximum_probes=0)
    with pytest.raises(ValueError):
        consume_probe(closed, now=NOW)
