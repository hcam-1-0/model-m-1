from __future__ import annotations

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

from hcam.camera_registry.models import utc_now
from hcam.streams.models import StreamEndpoint, StreamEventOutbox, StreamHealthCurrent


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
