from __future__ import annotations

from datetime import timedelta
from hmac import compare_digest

from fastapi import APIRouter, HTTPException, Request, Response, status
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from hcam.audit.models import AuditEvent
from hcam.camera_registry.models import utc_now
from hcam.streams.models import (
    OnvifControlLease,
    OnvifOperationRun,
    StreamCapabilityRefresh,
    StreamCapabilitySnapshot,
    StreamEndpoint,
    StreamEventOutbox,
    StreamHealthCurrent,
)


router = APIRouter(prefix="/internal", tags=["internal"])


class RequestMetrics:
    """Application-local metrics with bounded, metadata-only labels."""

    def __init__(self, *, service_name: str, version: str) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "hcam_http_requests_total",
            "Completed H-CAM HTTP requests.",
            ("method", "route", "status_class"),
            registry=self.registry,
        )
        self.duration = Histogram(
            "hcam_http_request_duration_seconds",
            "H-CAM HTTP request duration in seconds.",
            ("method", "route"),
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5),
            registry=self.registry,
        )
        self.info = Gauge(
            "hcam_service_info",
            "Static H-CAM service build information.",
            ("service", "version"),
            registry=self.registry,
        )
        self.info.labels(service=service_name, version=version).set(1)
        self.stream_health = Gauge(
            "hcam_stream_health_state_total",
            "Current number of streams in each bounded health state.",
            ("state",),
            registry=self.registry,
        )
        self.stream_probe_due = Gauge(
            "hcam_stream_probe_due_total",
            "Current number of enabled streams due for a metadata probe.",
            registry=self.registry,
        )
        self.stream_outbox_pending = Gauge(
            "hcam_stream_outbox_unpublished_total",
            "Current number of unpublished stream state events.",
            registry=self.registry,
        )
        self.capability_jobs = Gauge(
            "hcam_capability_refresh_jobs_retained_total",
            "Retained capability refresh jobs by bounded state and configuration.",
            ("status", "source", "auth_mode"),
            registry=self.registry,
        )
        self.capability_queue = Gauge(
            "hcam_capability_refresh_queue_depth",
            "Capability refresh jobs waiting or running.",
            ("status",),
            registry=self.registry,
        )
        self.capability_duration = Gauge(
            "hcam_capability_refresh_duration_milliseconds",
            "Average retained capability refresh duration by outcome.",
            ("status",),
            registry=self.registry,
        )
        self.capability_retries = Gauge(
            "hcam_capability_refresh_retries_retained_total",
            "Retained capability refresh retry attempts by authentication mode.",
            ("auth_mode",),
            registry=self.registry,
        )
        self.capability_stale = Gauge(
            "hcam_capability_snapshot_stale_total",
            "Streams whose latest capability snapshot is older than 36 hours.",
            registry=self.registry,
        )
        self.capability_expired_leases = Gauge(
            "hcam_capability_refresh_expired_leases_total",
            "Running capability refresh jobs whose worker lease has expired.",
            registry=self.registry,
        )
        self.capability_lease_recoveries = Gauge(
            "hcam_capability_refresh_lease_recoveries_recent_total",
            "Capability refresh leases recovered during the last 15 minutes.",
            registry=self.registry,
        )
        self.capability_failures = Gauge(
            "hcam_capability_refresh_failures_retained_total",
            "Retained bounded capability failures by category.",
            ("category",),
            registry=self.registry,
        )
        self.onvif_operations = Gauge(
            "hcam_onvif_operations_retained_total",
            "Retained ONVIF operations by bounded type and outcome.",
            ("operation", "outcome"),
            registry=self.registry,
        )
        self.onvif_control_leases = Gauge(
            "hcam_onvif_control_leases_active_total",
            "Current unexpired ONVIF PTZ control leases.",
            registry=self.registry,
        )
        self.onvif_recent_failures = Gauge(
            "hcam_onvif_operation_failures_recent_total",
            "ONVIF operation failures observed during the last 15 minutes.",
            ("operation",),
            registry=self.registry,
        )

    def observe(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        status_class = f"{status_code // 100}xx"
        self.requests.labels(
            method=method,
            route=route,
            status_class=status_class,
        ).inc()
        self.duration.labels(method=method, route=route).observe(duration_seconds)

    def refresh_stream_metrics(self, session: Session) -> None:
        counts = dict(
            session.execute(
                select(StreamHealthCurrent.state, func.count()).group_by(
                    StreamHealthCurrent.state
                )
            ).all()
        )
        for state in (
            "unknown",
            "healthy",
            "degraded",
            "offline",
            "unauthorized",
            "misconfigured",
            "unsupported",
        ):
            self.stream_health.labels(state=state).set(counts.get(state, 0))
        now = utc_now()
        due = session.scalar(
            select(func.count())
            .select_from(StreamEndpoint)
            .where(
                StreamEndpoint.enabled.is_(True),
                or_(
                    StreamEndpoint.probe_due_at.is_(None),
                    StreamEndpoint.probe_due_at <= now,
                ),
            )
        )
        pending = session.scalar(
            select(func.count())
            .select_from(StreamEventOutbox)
            .where(StreamEventOutbox.published_at.is_(None))
        )
        self.stream_probe_due.set(int(due or 0))
        self.stream_outbox_pending.set(int(pending or 0))
        self._refresh_capability_metrics(session, now)
        self._refresh_onvif_operation_metrics(session, now)

    def _refresh_onvif_operation_metrics(self, session: Session, now) -> None:
        operation_types = (
            "imaging_inspect",
            "event_pull",
            "ptz_stop",
            "ptz_continuous",
            "ptz_relative",
            "ptz_absolute",
            "ptz_goto_preset",
            "ws_discovery",
            "capability_discover_sync",
        )
        outcomes = ("pending", "success", "failure")
        counts = {
            (operation, outcome): count
            for operation, outcome, count in session.execute(
                select(
                    OnvifOperationRun.operation_type,
                    OnvifOperationRun.outcome,
                    func.count(),
                ).group_by(
                    OnvifOperationRun.operation_type,
                    OnvifOperationRun.outcome,
                )
            ).all()
        }
        for operation in operation_types:
            for outcome in outcomes:
                self.onvif_operations.labels(
                    operation=operation, outcome=outcome
                ).set(counts.get((operation, outcome), 0))
        recent_failures = dict(
            session.execute(
                select(OnvifOperationRun.operation_type, func.count())
                .where(
                    OnvifOperationRun.outcome == "failure",
                    OnvifOperationRun.requested_at >= now - timedelta(minutes=15),
                )
                .group_by(OnvifOperationRun.operation_type)
            ).all()
        )
        for operation in operation_types:
            self.onvif_recent_failures.labels(operation=operation).set(
                recent_failures.get(operation, 0)
            )
        active_leases = session.scalar(
            select(func.count())
            .select_from(OnvifControlLease)
            .where(OnvifControlLease.expires_at > now)
        )
        self.onvif_control_leases.set(int(active_leases or 0))

    def _refresh_capability_metrics(self, session: Session, now) -> None:
        statuses = ("queued", "running", "succeeded", "failed")
        sources = ("manual", "scheduled")
        auth_modes = (
            "none",
            "wsse_password_digest",
            "http_digest",
            "wsse_and_http_digest",
        )
        rows = session.execute(
            select(
                StreamCapabilityRefresh.status,
                StreamCapabilityRefresh.source,
                StreamEndpoint.onvif_auth_mode,
                func.count(),
            )
            .join(
                StreamEndpoint,
                StreamEndpoint.stream_id == StreamCapabilityRefresh.stream_id,
            )
            .group_by(
                StreamCapabilityRefresh.status,
                StreamCapabilityRefresh.source,
                StreamEndpoint.onvif_auth_mode,
            )
        ).all()
        counts = {(status, source, auth): count for status, source, auth, count in rows}
        for status_value in statuses:
            queue_count = 0
            if status_value in {"queued", "running"}:
                queue_count = sum(
                    counts.get((status_value, source, auth), 0)
                    for source in sources
                    for auth in auth_modes
                )
            self.capability_queue.labels(status=status_value).set(queue_count)
            for source in sources:
                for auth_mode in auth_modes:
                    self.capability_jobs.labels(
                        status=status_value,
                        source=source,
                        auth_mode=auth_mode,
                    ).set(counts.get((status_value, source, auth_mode), 0))

        durations = dict(
            session.execute(
                select(
                    StreamCapabilityRefresh.status,
                    func.avg(StreamCapabilityRefresh.duration_ms),
                )
                .where(StreamCapabilityRefresh.duration_ms.is_not(None))
                .group_by(StreamCapabilityRefresh.status)
            ).all()
        )
        for status_value in statuses:
            self.capability_duration.labels(status=status_value).set(
                float(durations.get(status_value) or 0)
            )

        retry_counts = {auth_mode: 0 for auth_mode in auth_modes}
        for auth_mode, attempts in session.execute(
            select(
                StreamEndpoint.onvif_auth_mode,
                StreamCapabilityRefresh.attempt_count,
            ).join(
                StreamEndpoint,
                StreamEndpoint.stream_id == StreamCapabilityRefresh.stream_id,
            )
        ):
            retry_counts[auth_mode] += max(0, attempts - 1)
        for auth_mode, count in retry_counts.items():
            self.capability_retries.labels(auth_mode=auth_mode).set(count)

        latest = (
            select(
                StreamCapabilitySnapshot.stream_id,
                func.max(StreamCapabilitySnapshot.last_observed_at).label("observed_at"),
            )
            .group_by(StreamCapabilitySnapshot.stream_id)
            .subquery()
        )
        stale = session.scalar(
            select(func.count())
            .select_from(latest)
            .where(latest.c.observed_at < now - timedelta(hours=36))
        )
        self.capability_stale.set(int(stale or 0))
        expired_leases = session.scalar(
            select(func.count())
            .select_from(StreamCapabilityRefresh)
            .where(
                StreamCapabilityRefresh.status == "running",
                StreamCapabilityRefresh.lease_until.is_not(None),
                StreamCapabilityRefresh.lease_until <= now,
            )
        )
        self.capability_expired_leases.set(int(expired_leases or 0))
        lease_recoveries = session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.action == "stream.capability_refresh.lease_recovered",
                AuditEvent.outcome == "success",
                AuditEvent.occurred_at >= now - timedelta(minutes=15),
            )
        )
        self.capability_lease_recoveries.set(int(lease_recoveries or 0))
        reason_counts = dict(
            session.execute(
                select(StreamCapabilityRefresh.reason_code, func.count())
                .where(
                    StreamCapabilityRefresh.status == "failed",
                    StreamCapabilityRefresh.reason_code.is_not(None),
                )
                .group_by(StreamCapabilityRefresh.reason_code)
            ).all()
        )
        secret_reasons = {
            "camera_secret_provider_unconfigured",
            "camera_secret_invalid_reference",
            "camera_secret_invalid_file",
            "camera_secret_unavailable",
            "camera_secret_invalid_payload",
            "credentials_unavailable",
        }
        categories = {
            "authentication": reason_counts.get("unauthorized", 0),
            "secret_provider": sum(
                reason_counts.get(reason, 0) for reason in secret_reasons
            ),
            "network_policy": reason_counts.get("network_policy_denied", 0),
            "transport": sum(
                reason_counts.get(reason, 0)
                for reason in ("unreachable", "onvif_http_error")
            ),
            "other": 0,
        }
        categories["other"] = max(
            0,
            sum(reason_counts.values()) - sum(categories.values()),
        )
        for category, count in categories.items():
            self.capability_failures.labels(category=category).set(count)


def _bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    scheme, separator, credential = authorization.partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not credential:
        return None
    return credential


@router.get("/metrics", include_in_schema=False)
def prometheus_metrics(request: Request) -> Response:
    settings = request.app.state.settings
    if not settings.metrics_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    supplied = _bearer_token(request)
    expected = settings.metrics_token
    if supplied is None or expected is None or not compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Metrics authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    with request.app.state.database.session_factory() as session:
        request.app.state.request_metrics.refresh_stream_metrics(session)
    return Response(
        generate_latest(request.app.state.request_metrics.registry),
        media_type=CONTENT_TYPE_LATEST,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )
