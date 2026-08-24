from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from hcam.analytics.contracts import (
    AnalyticsAssignmentV1,
    VersionedArtifact,
    VersionedConfiguration,
)
from hcam.analytics.models import AnalyticsAssignment, AnalyticsAssignmentRevision
from hcam.analytics.schemas import (
    AnalyticsAssignmentListResponse,
    AnalyticsAssignmentResponse,
    AnalyticsAssignmentRevisionListResponse,
    AnalyticsAssignmentRevisionResponse,
)
from hcam.camera_registry.models import Camera
from hcam.streams.models import StreamEndpoint


BLOCKING_REASONS = [
    "runtime_unconfigured",
    "taxonomy_unapproved",
    "retention_policy_unapproved",
]


@dataclass(frozen=True, slots=True)
class AnalyticsAssignmentFilters:
    stream_id: str | None = None
    camera_id: str | None = None
    capability: str | None = None
    desired_state: str | None = None
    lifecycle_state: str | None = None
    allowed_departments: frozenset[str] | None = None


def assignment_to_contract(assignment: AnalyticsAssignment) -> AnalyticsAssignmentV1:
    return AnalyticsAssignmentV1(
        assignment_id=assignment.assignment_id,
        department=assignment.department,
        stream_id=assignment.stream_id,
        camera_id=assignment.camera_id,
        capability=assignment.capability,
        desired_state=assignment.desired_state,
        version=assignment.version_id,
        pipeline=VersionedArtifact(
            id=assignment.pipeline_id,
            version=assignment.pipeline_version,
        ),
        models=[VersionedArtifact.model_validate(item) for item in assignment.models],
        taxonomy_version=assignment.taxonomy_version,
        policy_version=assignment.policy_version,
        configuration_digest=assignment.configuration_digest,
        minimum_confidence=assignment.minimum_confidence,
        sampling_fps=assignment.sampling_fps,
        maximum_queue_age_ms=assignment.maximum_queue_age_ms,
        geometry_refs=[
            VersionedConfiguration.model_validate(item)
            for item in assignment.geometry_refs
        ],
        retention_class=assignment.retention_class,
        actor_id=assignment.last_actor_id,
        reason=assignment.last_change_reason,
        approval_record_id=assignment.approval_record_id,
        updated_at=assignment.updated_at,
    )


def assignment_to_response(
    assignment: AnalyticsAssignment,
) -> AnalyticsAssignmentResponse:
    contract = assignment_to_contract(assignment)
    return AnalyticsAssignmentResponse(
        **contract.model_dump(),
        lifecycle_state="blocked",
        reason_code="owner_gates_pending",
        activation_eligible=False,
        blocking_reasons=BLOCKING_REASONS,
        created_at=assignment.created_at,
    )


class AnalyticsAssignmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _authorized_query(
        self,
        allowed_departments: frozenset[str] | None,
    ) -> Select[tuple[AnalyticsAssignment]]:
        query = (
            select(AnalyticsAssignment)
            .join(
                StreamEndpoint,
                StreamEndpoint.stream_id == AnalyticsAssignment.stream_id,
            )
            .join(Camera, Camera.camera_id == AnalyticsAssignment.camera_id)
            .where(StreamEndpoint.camera_id == AnalyticsAssignment.camera_id)
            .where(Camera.department == AnalyticsAssignment.department)
        )
        if allowed_departments is not None:
            if not allowed_departments:
                query = query.where(False)
            else:
                query = query.where(Camera.department.in_(allowed_departments))
        return query

    def get(
        self,
        assignment_id: str,
        *,
        allowed_departments: frozenset[str] | None,
    ) -> AnalyticsAssignment | None:
        return self.session.scalar(
            self._authorized_query(allowed_departments).where(
                AnalyticsAssignment.assignment_id == assignment_id
            )
        )

    def list(
        self,
        *,
        filters: AnalyticsAssignmentFilters,
        limit: int,
        offset: int,
    ) -> AnalyticsAssignmentListResponse:
        query = self._authorized_query(filters.allowed_departments)
        for field, value in (
            (AnalyticsAssignment.stream_id, filters.stream_id),
            (AnalyticsAssignment.camera_id, filters.camera_id),
            (AnalyticsAssignment.capability, filters.capability),
            (AnalyticsAssignment.desired_state, filters.desired_state),
            (AnalyticsAssignment.lifecycle_state, filters.lifecycle_state),
        ):
            if value is not None:
                query = query.where(field == value)
        total = int(
            self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
        rows = self.session.scalars(
            query.order_by(
                AnalyticsAssignment.updated_at.desc(),
                AnalyticsAssignment.assignment_id,
            )
            .limit(limit)
            .offset(offset)
        ).all()
        return AnalyticsAssignmentListResponse(
            items=[assignment_to_response(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def list_revisions(
        self,
        assignment: AnalyticsAssignment,
        *,
        limit: int,
        offset: int,
    ) -> AnalyticsAssignmentRevisionListResponse:
        query = select(AnalyticsAssignmentRevision).where(
            AnalyticsAssignmentRevision.assignment_id == assignment.assignment_id
        )
        total = int(
            self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
        rows = self.session.scalars(
            query.order_by(AnalyticsAssignmentRevision.version.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return AnalyticsAssignmentRevisionListResponse(
            items=[
                AnalyticsAssignmentRevisionResponse(
                    assignment_id=row.assignment_id,
                    version=row.version,
                    snapshot=AnalyticsAssignmentV1.model_validate(row.snapshot),
                    actor_id=row.actor_id,
                    reason=row.reason,
                    recorded_at=row.recorded_at,
                )
                for row in rows
            ],
            total=total,
            limit=limit,
            offset=offset,
        )
