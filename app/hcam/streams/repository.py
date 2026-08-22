from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from hcam.camera_registry.models import Camera
from hcam.streams.models import StreamEndpoint, StreamHealthCurrent, StreamProbeRun
from hcam.streams.schemas import (
    StreamEndpointListResponse,
    StreamEndpointResponse,
    StreamHealthResponse,
    StreamProbeListResponse,
    StreamProbeResponse,
)


@dataclass(frozen=True, slots=True)
class StreamFilters:
    camera_id: str | None = None
    protocol: str | None = None
    state: str | None = None
    enabled: bool | None = None
    allowed_departments: frozenset[str] | None = None


def stream_to_response(
    endpoint: StreamEndpoint, health: StreamHealthCurrent
) -> StreamEndpointResponse:
    return StreamEndpointResponse(
        stream_id=endpoint.stream_id,
        camera_id=endpoint.camera_id,
        version=endpoint.version_id,
        name=endpoint.name,
        adapter_kind=endpoint.adapter_kind,
        protocol=endpoint.protocol,
        locator=endpoint.locator,
        secret_configured=endpoint.secret_ref is not None,
        management_locator=endpoint.management_locator,
        onvif_auth_mode=endpoint.onvif_auth_mode,
        capability_refresh_enabled=endpoint.capability_refresh_enabled,
        capability_due_at=endpoint.capability_due_at,
        onvif_control_enabled=endpoint.onvif_control_enabled,
        onvif_max_velocity=endpoint.onvif_max_velocity,
        onvif_max_move_seconds=endpoint.onvif_max_move_seconds,
        transport=endpoint.transport,
        is_primary=endpoint.is_primary,
        enabled=endpoint.enabled,
        health=StreamHealthResponse(
            state=health.state,
            reason_code=health.reason_code,
            observed_at=health.observed_at,
            consecutive_successes=health.consecutive_successes,
            consecutive_failures=health.consecutive_failures,
            probe_latency_ms=health.probe_latency_ms,
            codec=health.codec,
            container=health.container,
            width=health.width,
            height=health.height,
            frame_rate=health.frame_rate,
            last_success_at=health.last_success_at,
            last_failure_at=health.last_failure_at,
        ),
        created_at=endpoint.created_at,
        updated_at=endpoint.updated_at,
    )


def probe_to_response(probe: StreamProbeRun) -> StreamProbeResponse:
    return StreamProbeResponse(
        probe_id=probe.probe_id,
        stream_id=probe.stream_id,
        worker_id=probe.worker_id,
        started_at=probe.started_at,
        finished_at=probe.finished_at,
        outcome=probe.outcome,
        reason_code=probe.reason_code,
        latency_ms=probe.latency_ms,
        media=probe.media,
    )


class StreamRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _authorized_query(
        self, allowed_departments: frozenset[str] | None
    ) -> Select[tuple[StreamEndpoint, StreamHealthCurrent]]:
        query = (
            select(StreamEndpoint, StreamHealthCurrent)
            .join(Camera, Camera.camera_id == StreamEndpoint.camera_id)
            .join(
                StreamHealthCurrent,
                StreamHealthCurrent.stream_id == StreamEndpoint.stream_id,
            )
        )
        if allowed_departments is not None:
            if not allowed_departments:
                query = query.where(False)
            else:
                query = query.where(Camera.department.in_(allowed_departments))
        return query

    def get(
        self,
        stream_id: str,
        *,
        allowed_departments: frozenset[str] | None,
    ) -> tuple[StreamEndpoint, StreamHealthCurrent] | None:
        query = self._authorized_query(allowed_departments).where(
            StreamEndpoint.stream_id == stream_id
        )
        return self.session.execute(query).one_or_none()

    def list(
        self,
        *,
        filters: StreamFilters,
        limit: int,
        offset: int,
    ) -> StreamEndpointListResponse:
        query = self._authorized_query(filters.allowed_departments)
        if filters.camera_id is not None:
            query = query.where(StreamEndpoint.camera_id == filters.camera_id)
        if filters.protocol is not None:
            query = query.where(StreamEndpoint.protocol == filters.protocol)
        if filters.state is not None:
            query = query.where(StreamHealthCurrent.state == filters.state)
        if filters.enabled is not None:
            query = query.where(StreamEndpoint.enabled == filters.enabled)

        count_query = select(func.count()).select_from(query.subquery())
        total = int(self.session.scalar(count_query) or 0)
        rows = self.session.execute(
            query.order_by(StreamEndpoint.camera_id, StreamEndpoint.name)
            .limit(limit)
            .offset(offset)
        ).all()
        return StreamEndpointListResponse(
            items=[stream_to_response(endpoint, health) for endpoint, health in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def list_probes(
        self,
        stream_id: str,
        *,
        limit: int,
        offset: int,
    ) -> StreamProbeListResponse:
        query = select(StreamProbeRun).where(StreamProbeRun.stream_id == stream_id)
        total = int(
            self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
        probes = self.session.scalars(
            query.order_by(StreamProbeRun.started_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return StreamProbeListResponse(
            items=[probe_to_response(probe) for probe in probes],
            total=total,
            limit=limit,
            offset=offset,
        )
