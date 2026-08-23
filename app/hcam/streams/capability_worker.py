from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session, aliased

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import utc_now
from hcam.streams.capabilities import (
    CapabilityDiscoveryEngine,
    CapabilityDiscoveryError,
    CapabilityEndpointConfig,
    store_capability_snapshot,
)
from hcam.streams.models import (
    StreamCapabilityRefresh,
    StreamCapabilitySnapshot,
    StreamEndpoint,
)


_LOGGER = logging.getLogger("hcam.capability_worker")
_TERMINAL_RETRY_DELAYS = (timedelta(seconds=30), timedelta(minutes=2))
_CAPABILITY_HISTORY_RETENTION = timedelta(days=90)


class CapabilityWorkerLeaseError(RuntimeError):
    pass


class CapabilityWorkerRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _CapabilityClaimOutcome:
    processed: bool
    refresh_id: str | None = None
    endpoint: CapabilityEndpointConfig | None = None


def next_capability_due(now: datetime, stream_id: str) -> datetime:
    digest = hashlib.sha256(stream_id.encode("utf-8")).digest()
    fraction = int.from_bytes(digest[:8], "big") / ((1 << 64) - 1)
    jitter_seconds = (fraction * 2 - 1) * timedelta(hours=2).total_seconds()
    return now + timedelta(hours=24, seconds=jitter_seconds)


def _retry_delay(refresh_id: str, attempt_count: int) -> timedelta:
    base = _TERMINAL_RETRY_DELAYS[min(attempt_count - 1, 1)]
    digest = hashlib.sha256(f"{refresh_id}:{attempt_count}".encode("ascii")).digest()
    fraction = int.from_bytes(digest[:4], "big") / ((1 << 32) - 1)
    return timedelta(seconds=base.total_seconds() * (0.5 + fraction * 0.5))


def _prune_capability_history(
    session: Session,
    *,
    now: datetime,
    current_refresh_id: str,
) -> None:
    cutoff = now - _CAPABILITY_HISTORY_RETENTION
    session.execute(
        delete(StreamCapabilityRefresh)
        .where(
            StreamCapabilityRefresh.finished_at < cutoff,
            StreamCapabilityRefresh.refresh_id != current_refresh_id,
        )
        .execution_options(synchronize_session=False)
    )

    newer = aliased(StreamCapabilitySnapshot)
    has_newer_snapshot = (
        select(newer.snapshot_id)
        .where(
            newer.stream_id == StreamCapabilitySnapshot.stream_id,
            or_(
                newer.last_observed_at > StreamCapabilitySnapshot.last_observed_at,
                and_(
                    newer.last_observed_at == StreamCapabilitySnapshot.last_observed_at,
                    newer.created_at > StreamCapabilitySnapshot.created_at,
                ),
                and_(
                    newer.last_observed_at == StreamCapabilitySnapshot.last_observed_at,
                    newer.created_at == StreamCapabilitySnapshot.created_at,
                    newer.snapshot_id > StreamCapabilitySnapshot.snapshot_id,
                ),
            ),
        )
        .exists()
    )
    session.execute(
        delete(StreamCapabilitySnapshot)
        .where(
            StreamCapabilitySnapshot.last_observed_at < cutoff,
            has_newer_snapshot,
        )
        .execution_options(synchronize_session=False)
    )


def _terminalize_preflight_failure(
    session: Session,
    refresh: StreamCapabilityRefresh,
    *,
    endpoint: StreamEndpoint | None,
    reason_code: str,
    finished: datetime,
) -> None:
    refresh.status = "failed"
    refresh.reason_code = reason_code
    refresh.duration_ms = None
    refresh.result_completeness = None
    refresh.snapshot_id = None
    refresh.finished_at = finished
    refresh.lease_owner = None
    refresh.lease_until = None
    refresh.updated_at = finished
    context: dict[str, object] = {
        "stream_id": refresh.stream_id,
        "source": refresh.source,
        "reason_code": reason_code,
        "attempt_count": refresh.attempt_count,
    }
    if endpoint is not None:
        context["camera_id"] = endpoint.camera_id
    AuditRepository(session).record(
        actor_id=refresh.requested_by,
        action="stream.capability_refresh.fail",
        target_type="stream_capability_refresh",
        target_id=refresh.refresh_id,
        source="hcam.capability-worker",
        reason=refresh.audit_reason,
        outcome="failure",
        context=context,
        request_id=refresh.request_id,
    )
    _prune_capability_history(
        session,
        now=finished,
        current_refresh_id=refresh.refresh_id,
    )


class CapabilityRefreshWorker:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        engine: CapabilityDiscoveryEngine,
        *,
        worker_id: str,
        lease_duration: timedelta = timedelta(seconds=90),
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.session_factory = session_factory
        self.engine = engine
        self.worker_id = worker_id
        self.lease_duration = lease_duration
        self.clock = clock

    def _enqueue_scheduled(self) -> bool:
        now = self.clock()
        with self.session_factory() as session, session.begin():
            query = (
                select(StreamEndpoint)
                .where(
                    StreamEndpoint.enabled.is_(True),
                    StreamEndpoint.adapter_kind == "onvif",
                    StreamEndpoint.capability_refresh_enabled.is_(True),
                    or_(
                        StreamEndpoint.capability_due_at.is_(None),
                        StreamEndpoint.capability_due_at <= now,
                    ),
                )
                .order_by(
                    StreamEndpoint.capability_due_at,
                    StreamEndpoint.stream_id,
                )
                .limit(1)
            )
            if session.bind is not None and session.bind.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            endpoint = session.scalar(query)
            if endpoint is None:
                return False
            active = session.scalar(
                select(StreamCapabilityRefresh.refresh_id)
                .where(
                    StreamCapabilityRefresh.stream_id == endpoint.stream_id,
                    StreamCapabilityRefresh.status.in_(("queued", "running")),
                )
                .limit(1)
            )
            endpoint.capability_due_at = next_capability_due(now, endpoint.stream_id)
            endpoint.updated_at = now
            if active is not None:
                return False
            refresh = StreamCapabilityRefresh(
                refresh_id=f"cpr_{uuid4().hex}",
                stream_id=endpoint.stream_id,
                status="queued",
                source="scheduled",
                priority=0,
                requested_by=None,
                request_id=None,
                audit_reason="Scheduled ONVIF capability refresh",
                attempt_count=0,
                max_attempts=3,
                next_attempt_at=now,
                queued_at=now,
                created_at=now,
                updated_at=now,
            )
            session.add(refresh)
            AuditRepository(session).record(
                actor_id=None,
                action="stream.capability_refresh.queue",
                target_type="stream_capability_refresh",
                target_id=refresh.refresh_id,
                source="hcam.capability-worker",
                reason=refresh.audit_reason,
                outcome="success",
                context={
                    "stream_id": endpoint.stream_id,
                    "camera_id": endpoint.camera_id,
                    "source": "scheduled",
                },
            )
            return True

    def _claim(self) -> _CapabilityClaimOutcome:
        now = self.clock()
        with self.session_factory() as session, session.begin():
            query = (
                select(StreamCapabilityRefresh)
                .where(
                    or_(
                        and_(
                            StreamCapabilityRefresh.status == "queued",
                            StreamCapabilityRefresh.next_attempt_at <= now,
                        ),
                        and_(
                            StreamCapabilityRefresh.status == "running",
                            StreamCapabilityRefresh.lease_until.is_not(None),
                            StreamCapabilityRefresh.lease_until <= now,
                        ),
                    )
                )
                .order_by(
                    StreamCapabilityRefresh.priority.desc(),
                    StreamCapabilityRefresh.next_attempt_at,
                    StreamCapabilityRefresh.queued_at,
                )
                .limit(1)
            )
            if session.bind is not None and session.bind.dialect.name == "postgresql":
                query = query.with_for_update(skip_locked=True)
            refresh = session.scalar(query)
            if refresh is None:
                return _CapabilityClaimOutcome(processed=False)
            endpoint = session.get(StreamEndpoint, refresh.stream_id)
            if endpoint is None:
                _terminalize_preflight_failure(
                    session,
                    refresh,
                    endpoint=None,
                    reason_code="stream_not_found",
                    finished=now,
                )
                return _CapabilityClaimOutcome(processed=True)
            if not endpoint.enabled:
                _terminalize_preflight_failure(
                    session,
                    refresh,
                    endpoint=endpoint,
                    reason_code="stream_disabled",
                    finished=now,
                )
                return _CapabilityClaimOutcome(processed=True)
            recovered_expired_lease = refresh.status == "running"
            refresh.status = "running"
            refresh.attempt_count += 1
            refresh.started_at = refresh.started_at or now
            refresh.lease_owner = self.worker_id
            refresh.lease_until = now + self.lease_duration
            refresh.updated_at = now
            if recovered_expired_lease:
                AuditRepository(session).record(
                    actor_id=None,
                    action="stream.capability_refresh.lease_recovered",
                    target_type="stream_capability_refresh",
                    target_id=refresh.refresh_id,
                    source="hcam.capability-worker",
                    reason="Expired capability refresh worker lease recovered",
                    outcome="success",
                    context={
                        "stream_id": endpoint.stream_id,
                        "camera_id": endpoint.camera_id,
                        "source": refresh.source,
                        "attempt_count": refresh.attempt_count,
                    },
                    request_id=refresh.request_id,
                )
            return _CapabilityClaimOutcome(
                processed=True,
                refresh_id=refresh.refresh_id,
                endpoint=CapabilityEndpointConfig.from_endpoint(endpoint),
            )

    def _record_success(
        self,
        refresh_id: str,
        result,
    ) -> None:
        finished = self.clock()
        with self.session_factory() as session, session.begin():
            refresh = session.get(StreamCapabilityRefresh, refresh_id)
            if (
                refresh is None
                or refresh.status != "running"
                or refresh.lease_owner != self.worker_id
            ):
                raise CapabilityWorkerLeaseError("capability refresh lease was lost")
            endpoint = session.get(StreamEndpoint, refresh.stream_id)
            if endpoint is None:
                raise CapabilityWorkerLeaseError("capability stream was removed")
            snapshot, changed = store_capability_snapshot(
                session,
                endpoint,
                result,
                observed_at=finished,
            )
            refresh.status = "succeeded"
            refresh.reason_code = None
            refresh.duration_ms = result.duration_ms
            refresh.result_completeness = result.completeness
            refresh.snapshot_id = snapshot.snapshot_id
            refresh.finished_at = finished
            refresh.lease_owner = None
            refresh.lease_until = None
            refresh.updated_at = finished
            if endpoint.capability_refresh_enabled:
                endpoint.capability_due_at = next_capability_due(
                    finished, endpoint.stream_id
                )
            AuditRepository(session).record(
                actor_id=refresh.requested_by,
                action="stream.capability_refresh.complete",
                target_type="stream_capability_refresh",
                target_id=refresh.refresh_id,
                source="hcam.worker",
                reason=refresh.audit_reason,
                outcome="success",
                context={
                    "stream_id": endpoint.stream_id,
                    "camera_id": endpoint.camera_id,
                    "source": refresh.source,
                    "completeness": result.completeness,
                    "capabilities_changed": changed,
                    "attempt_count": refresh.attempt_count,
                },
                request_id=refresh.request_id,
            )
            _prune_capability_history(
                session,
                now=finished,
                current_refresh_id=refresh.refresh_id,
            )

    def _record_failure(
        self,
        refresh_id: str,
        error: CapabilityDiscoveryError,
        *,
        duration_ms: float,
    ) -> None:
        finished = self.clock()
        with self.session_factory() as session, session.begin():
            refresh = session.get(StreamCapabilityRefresh, refresh_id)
            if (
                refresh is None
                or refresh.status != "running"
                or refresh.lease_owner != self.worker_id
            ):
                raise CapabilityWorkerLeaseError("capability refresh lease was lost")
            endpoint = session.get(StreamEndpoint, refresh.stream_id)
            should_retry = (
                error.retryable and refresh.attempt_count < refresh.max_attempts
            )
            refresh.reason_code = error.reason_code
            refresh.duration_ms = duration_ms
            refresh.lease_owner = None
            refresh.lease_until = None
            refresh.updated_at = finished
            action = "stream.capability_refresh.retry"
            if should_retry:
                refresh.status = "queued"
                refresh.next_attempt_at = finished + _retry_delay(
                    refresh.refresh_id, refresh.attempt_count
                )
            else:
                refresh.status = "failed"
                refresh.finished_at = finished
                action = "stream.capability_refresh.fail"
                if endpoint is not None and endpoint.capability_refresh_enabled:
                    endpoint.capability_due_at = next_capability_due(
                        finished, endpoint.stream_id
                    )
            AuditRepository(session).record(
                actor_id=refresh.requested_by,
                action=action,
                target_type="stream_capability_refresh",
                target_id=refresh.refresh_id,
                source="hcam.worker",
                reason=refresh.audit_reason,
                outcome="failure" if not should_retry else "retry",
                context={
                    "stream_id": refresh.stream_id,
                    "source": refresh.source,
                    "reason_code": error.reason_code,
                    "attempt_count": refresh.attempt_count,
                    "will_retry": should_retry,
                },
                request_id=refresh.request_id,
            )
            if not should_retry:
                _prune_capability_history(
                    session,
                    now=finished,
                    current_refresh_id=refresh.refresh_id,
                )

    def run_once(self) -> bool:
        self._enqueue_scheduled()
        claim = self._claim()
        if not claim.processed:
            return False
        if claim.refresh_id is None or claim.endpoint is None:
            return True
        refresh_id = claim.refresh_id
        endpoint = claim.endpoint
        started = monotonic()
        try:
            result = self.engine.discover(endpoint)
        except CapabilityDiscoveryError as exc:
            self._record_failure(
                refresh_id,
                exc,
                duration_ms=max(0.0, (monotonic() - started) * 1000),
            )
            self._log("failure", exc.reason_code, endpoint.onvif_auth_mode)
            return True
        except Exception as exc:
            error = CapabilityDiscoveryError("capability_worker_error", retryable=True)
            self._record_failure(
                refresh_id,
                error,
                duration_ms=max(0.0, (monotonic() - started) * 1000),
            )
            raise CapabilityWorkerRuntimeError(
                "capability worker encountered an unexpected runtime failure"
            ) from exc
        self._record_success(refresh_id, result)
        self._log("success", None, endpoint.onvif_auth_mode)
        return True

    def run(
        self,
        *,
        poll_seconds: float = 2.0,
        heartbeat_file: Path | None = None,
    ) -> None:
        while True:
            processed = self.run_once()
            if heartbeat_file is not None:
                heartbeat_file.touch()
            if not processed:
                sleep(poll_seconds)

    def _log(self, outcome: str, reason_code: str | None, auth_mode: str) -> None:
        _LOGGER.info(
            json.dumps(
                {
                    "event": "stream.capability_refresh.completed",
                    "outcome": outcome,
                    "reason_code": reason_code,
                    "auth_mode": auth_mode,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
