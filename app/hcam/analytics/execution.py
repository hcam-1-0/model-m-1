from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from time import perf_counter

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from hcam.analytics.activation import (
    P3_2_GENERATOR_ID,
    P3_2_GENERATOR_VERSION,
    P3_2_MODEL_ID,
    P3_2_MODEL_VERSION,
    P3_2_PIPELINE_ID,
    P3_2_PIPELINE_VERSION,
    P3_2_POLICY_VERSION,
    P3_2_POSTPROCESSING_VERSION,
    P3_2_PREPROCESSING_VERSION,
    P3_2_TAXONOMY_VERSION,
    assess_generated_activation,
)
from hcam.analytics.contracts import (
    ObservationCreatedV1,
    ObservationPayloadV1,
    ObservationQuality,
    ObjectClassification,
    ProcessingLineage,
    RuntimeReference,
    SourceFrame,
    VersionedArtifact,
    canonical_contract_json,
)
from hcam.analytics.generated import (
    GeneratedFrameLeaseError,
    GeneratedFrameLeaseStore,
    generate_det_r0_frame,
)
from hcam.analytics.models import (
    AnalyticsAssignment,
    AnalyticsGeneratedRun,
    AnalyticsObservation,
)
from hcam.analytics.runtime import (
    AnalyticsRuntimeAdapter,
    RuntimeBatchRequestV2,
    RuntimeInputDescriptorV1,
    failed_runtime_result,
)
from hcam.analytics.schemas import (
    AnalyticsObservationListResponse,
    AnalyticsObservationResponse,
    GeneratedAnalyticsRunCreate,
    GeneratedAnalyticsRunResponse,
)
from hcam.analytics.service import (
    AnalyticsAssignmentConflictError,
    AnalyticsAssignmentNotFoundError,
    AnalyticsAssignmentService,
    AnalyticsAssignmentValidationError,
    _safe_reason,
)
from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import utc_now
from hcam.security.auth import Principal
from hcam.streams.models import StreamEventOutbox


_TERMINAL_FAILURE_CODES = frozenset(
    {
        "artifact_rejected",
        "invalid_input",
        "runtime_unconfigured",
        "unsupported_capability",
    }
)
_STANDARD_RETENTION = timedelta(hours=168)
_RESTRICTED_RETENTION = timedelta(hours=24)


def _stable_id(prefix: str, *parts: object) -> str:
    payload = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:32]}"


def generated_run_to_response(
    run: AnalyticsGeneratedRun,
    *,
    reused: bool = False,
) -> GeneratedAnalyticsRunResponse:
    return GeneratedAnalyticsRunResponse(
        run_id=run.run_id,
        assignment_id=run.assignment_id,
        assignment_version=run.assignment_version,
        source_sequence=run.source_sequence,
        source_observed_at=run.source_observed_at,
        generator_id=run.generator_id,
        generator_version=run.generator_version,
        input_sha256=run.input_sha256,
        status=run.status,
        failure_code=run.failure_code,
        candidate_count=run.candidate_count,
        duration_ms=run.duration_ms,
        retention_class=run.retention_class,
        started_at=run.started_at,
        completed_at=run.completed_at,
        reused=reused,
    )


def observation_to_response(
    observation: AnalyticsObservation,
) -> AnalyticsObservationResponse:
    return AnalyticsObservationResponse(
        observation_id=observation.observation_id,
        run_id=observation.run_id,
        assignment_id=observation.assignment_id,
        candidate_index=observation.candidate_index,
        observed_at=observation.observed_at,
        processed_at=observation.processed_at,
        source_sequence=observation.source_sequence,
        source_width=observation.source_width,
        source_height=observation.source_height,
        model_id=observation.model_id,
        model_version=observation.model_version,
        class_id=observation.class_id,
        confidence=observation.confidence,
        bbox_x=observation.bbox_x,
        bbox_y=observation.bbox_y,
        bbox_width=observation.bbox_width,
        bbox_height=observation.bbox_height,
        lineage=observation.lineage,
        retention_class=observation.retention_class,
        created_at=observation.created_at,
    )


class GeneratedAnalyticsExecutionService:
    def __init__(
        self,
        session: Session,
        *,
        runtime: AnalyticsRuntimeAdapter,
        leases: GeneratedFrameLeaseStore,
    ) -> None:
        self.session = session
        self.runtime = runtime
        self.leases = leases

    def execute(
        self,
        assignment_id: str,
        payload: GeneratedAnalyticsRunCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> GeneratedAnalyticsRunResponse:
        normalized_reason = _safe_reason(reason)
        frame = generate_det_r0_frame(payload.seed)
        with self.session.begin():
            assignment = self._authorized_assignment(assignment_id, principal)
            assessment = assess_generated_activation(
                assignment,
                runtime_configured=self.runtime.descriptor.configured,
            )
            if not assessment.eligible:
                raise AnalyticsAssignmentValidationError(
                    "Analytics assignment is outside the generated-only execution scope"
                )
            if (
                assignment.desired_state != "enabled"
                or assignment.lifecycle_state
                not in {
                    "running",
                    "degraded",
                }
            ):
                raise AnalyticsAssignmentConflictError(
                    "Analytics assignment must be active before generated execution"
                )
            assignment_version = assignment.version_id
            run_id = _stable_id(
                "run",
                assignment.assignment_id,
                assignment_version,
                payload.sequence,
                payload.observed_at.isoformat(),
                frame.sha256,
            )
            existing = self.session.get(AnalyticsGeneratedRun, run_id)
            if existing is not None:
                return generated_run_to_response(existing, reused=True)
            assignment_snapshot = {
                "department": assignment.department,
                "stream_id": assignment.stream_id,
                "camera_id": assignment.camera_id,
                "minimum_confidence": assignment.minimum_confidence,
                "configuration_digest": assignment.configuration_digest,
                "retention_class": assignment.retention_class,
            }

        input_id = _stable_id("input", run_id)
        lease_id = _stable_id("lease", run_id)
        request_runtime_id = _stable_id("run", run_id, "runtime")
        issued_at = datetime.now(UTC)
        descriptor = RuntimeInputDescriptorV1(
            input_id=input_id,
            lease_id=lease_id,
            stream_id=assignment_snapshot["stream_id"],
            camera_id=assignment_snapshot["camera_id"],
            source=SourceFrame(
                sequence=payload.sequence,
                width=frame.width,
                height=frame.height,
                timestamp_source="generated",
                timestamp_confidence=1,
            ),
            observed_at=payload.observed_at,
            issued_at=issued_at,
            expires_at=issued_at + timedelta(seconds=5),
            pixel_format="bgr8",
        )
        runtime_request = RuntimeBatchRequestV2(
            request_id=request_runtime_id,
            assignment_id=assignment_id,
            capability="object_detection",
            stream_id=assignment_snapshot["stream_id"],
            camera_id=assignment_snapshot["camera_id"],
            deadline_at=issued_at + timedelta(seconds=1),
            inputs=[descriptor],
            minimum_confidence=assignment_snapshot["minimum_confidence"],
        )
        started_at = utc_now()
        started_clock = perf_counter()
        try:
            self.leases.issue(descriptor, frame)
            result = self.runtime.infer(runtime_request)
        except GeneratedFrameLeaseError as exc:
            result = failed_runtime_result(runtime_request, exc.code)
        finally:
            self.leases.revoke(lease_id)
        completed_at = utc_now()
        duration_ms = min(
            60_000, max(0, round((perf_counter() - started_clock) * 1_000))
        )
        if len(result.candidates) > 300:
            result = failed_runtime_result(runtime_request, "resource_exhausted")

        try:
            with self.session.begin():
                assignment = self._authorized_assignment(assignment_id, principal)
                if (
                    assignment.version_id != assignment_version
                    or assignment.desired_state != "enabled"
                    or assignment.lifecycle_state not in {"running", "degraded"}
                ):
                    raise AnalyticsAssignmentConflictError(
                        "Analytics assignment changed during generated execution"
                    )
                existing = self.session.get(AnalyticsGeneratedRun, run_id)
                if existing is not None:
                    return generated_run_to_response(existing, reused=True)
                run = AnalyticsGeneratedRun(
                    run_id=run_id,
                    assignment_id=assignment_id,
                    assignment_version=assignment_version,
                    department=assignment_snapshot["department"],
                    stream_id=assignment_snapshot["stream_id"],
                    camera_id=assignment_snapshot["camera_id"],
                    source_sequence=payload.sequence,
                    source_observed_at=payload.observed_at,
                    generator_id=P3_2_GENERATOR_ID,
                    generator_version=P3_2_GENERATOR_VERSION,
                    seed=payload.seed,
                    input_sha256=frame.sha256.lower(),
                    status=result.status,
                    failure_code=result.failure_code,
                    candidate_count=len(result.candidates),
                    duration_ms=duration_ms,
                    retention_class=assignment_snapshot["retention_class"],
                    started_at=started_at,
                    completed_at=completed_at,
                )
                self.session.add(run)
                self.session.flush()
                self._persist_observations(
                    run,
                    result.candidates,
                    assignment_snapshot=assignment_snapshot,
                    processed_at=completed_at,
                )
                lifecycle_state = self._lifecycle_for_result(
                    result.status,
                    result.failure_code,
                )
                lifecycle_changed = AnalyticsAssignmentService(
                    self.session
                ).apply_runtime_state(
                    assignment,
                    lifecycle_state=lifecycle_state,
                    actor_id=principal.actor_id,
                    reason=normalized_reason,
                    occurred_at=completed_at,
                )
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="analytics.generated_run.execute",
                    target_type="analytics_generated_run",
                    target_id=run_id,
                    source="hcam.api",
                    reason=normalized_reason,
                    outcome="success" if result.status == "succeeded" else "failure",
                    context={
                        "candidate_count": len(result.candidates),
                        "execution_scope": "generated_only",
                        "failure_code": result.failure_code,
                        "lifecycle_changed": lifecycle_changed,
                        "status": result.status,
                    },
                    request_id=request_id,
                )
            return generated_run_to_response(run)
        except IntegrityError as exc:
            self.session.rollback()
            existing = self.session.get(AnalyticsGeneratedRun, run_id)
            if existing is not None and principal.can_access_department(
                existing.department
            ):
                return generated_run_to_response(existing, reused=True)
            raise AnalyticsAssignmentConflictError(
                "Generated analytics run conflicts with existing metadata"
            ) from exc

    def get_run(
        self,
        run_id: str,
        *,
        principal: Principal,
    ) -> GeneratedAnalyticsRunResponse:
        run = self.session.get(AnalyticsGeneratedRun, run_id)
        if run is None or not principal.can_access_department(run.department):
            raise AnalyticsAssignmentNotFoundError("Generated analytics run not found")
        return generated_run_to_response(run)

    def list_observations(
        self,
        run_id: str,
        *,
        principal: Principal,
        limit: int,
        offset: int,
    ) -> AnalyticsObservationListResponse:
        run = self.session.get(AnalyticsGeneratedRun, run_id)
        if run is None or not principal.can_access_department(run.department):
            raise AnalyticsAssignmentNotFoundError("Generated analytics run not found")
        query = select(AnalyticsObservation).where(
            AnalyticsObservation.run_id == run_id
        )
        total = int(
            self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
        rows = self.session.scalars(
            query.order_by(AnalyticsObservation.candidate_index)
            .limit(limit)
            .offset(offset)
        ).all()
        return AnalyticsObservationListResponse(
            items=[observation_to_response(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def _authorized_assignment(
        self,
        assignment_id: str,
        principal: Principal,
    ) -> AnalyticsAssignment:
        assignment = self.session.get(AnalyticsAssignment, assignment_id)
        if assignment is None or not principal.can_access_department(
            assignment.department
        ):
            raise AnalyticsAssignmentNotFoundError("Analytics assignment not found")
        return assignment

    def _persist_observations(
        self,
        run: AnalyticsGeneratedRun,
        candidates,
        *,
        assignment_snapshot: dict[str, object],
        processed_at: datetime,
    ) -> None:
        lineage = ProcessingLineage(
            code_version=P3_2_PIPELINE_VERSION,
            pipeline=VersionedArtifact(
                id=P3_2_PIPELINE_ID,
                version=P3_2_PIPELINE_VERSION,
            ),
            preprocessing_version=P3_2_PREPROCESSING_VERSION,
            postprocessing_version=P3_2_POSTPROCESSING_VERSION,
            taxonomy_version=P3_2_TAXONOMY_VERSION,
            policy_version=P3_2_POLICY_VERSION,
            runtime=RuntimeReference(
                name=self.runtime.descriptor.adapter_id,
                version=self.runtime.descriptor.adapter_version,
            ),
            configuration_digest=assignment_snapshot["configuration_digest"],
        )
        source = SourceFrame(
            sequence=run.source_sequence,
            width=416,
            height=416,
            timestamp_source="generated",
            timestamp_confidence=1,
        )
        model = VersionedArtifact(id=P3_2_MODEL_ID, version=P3_2_MODEL_VERSION)
        for index, candidate in enumerate(candidates):
            observation_id = _stable_id("obs", run.run_id, index)
            event_id = _stable_id("evt", observation_id, "created")
            payload = ObservationPayloadV1(
                observation_id=observation_id,
                stream_id=run.stream_id,
                camera_id=run.camera_id,
                observed_at=run.source_observed_at,
                processed_at=processed_at,
                source=source,
                lineage=lineage,
                model=model,
                **{
                    "class": ObjectClassification(
                        id=candidate.class_id,
                        confidence=candidate.confidence,
                    )
                },
                bbox=candidate.bbox,
                quality=ObservationQuality(),
                retention_class=run.retention_class,
            )
            event = ObservationCreatedV1(
                event_id=event_id,
                stream_id=run.stream_id,
                camera_id=run.camera_id,
                partition_key=run.stream_id,
                occurred_at=processed_at,
                payload=payload,
            )
            canonical_contract_json(event)
            self.session.add(
                AnalyticsObservation(
                    observation_id=observation_id,
                    event_id=event_id,
                    run_id=run.run_id,
                    assignment_id=run.assignment_id,
                    candidate_index=index,
                    department=run.department,
                    stream_id=run.stream_id,
                    camera_id=run.camera_id,
                    observed_at=run.source_observed_at,
                    processed_at=processed_at,
                    source_sequence=run.source_sequence,
                    source_width=416,
                    source_height=416,
                    model_id=P3_2_MODEL_ID,
                    model_version=P3_2_MODEL_VERSION,
                    class_id=candidate.class_id,
                    confidence=candidate.confidence,
                    bbox_x=candidate.bbox.x,
                    bbox_y=candidate.bbox.y,
                    bbox_width=candidate.bbox.width,
                    bbox_height=candidate.bbox.height,
                    lineage=lineage.model_dump(mode="json"),
                    retention_class=run.retention_class,
                    created_at=processed_at,
                )
            )
            self.session.add(
                StreamEventOutbox(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    schema_version=event.schema_version,
                    stream_id=event.stream_id,
                    camera_id=event.camera_id,
                    occurred_at=event.occurred_at,
                    payload=event.payload.model_dump(mode="json", by_alias=True),
                )
            )

    @staticmethod
    def _lifecycle_for_result(
        status: str,
        failure_code: str | None,
    ) -> str:
        if status == "succeeded":
            return "running"
        if failure_code in _TERMINAL_FAILURE_CODES:
            return "failed"
        return "degraded"


def purge_expired_generated_analytics(
    session: Session,
    *,
    now: datetime,
) -> int:
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("retention cutoff must be timezone-aware UTC")
    deleted = 0
    for retention_class, lifetime in (
        ("derived.analytics.standard", _STANDARD_RETENTION),
        ("derived.analytics.restricted", _RESTRICTED_RETENTION),
    ):
        expired_event_ids = (
            select(AnalyticsObservation.event_id)
            .join(
                AnalyticsGeneratedRun,
                AnalyticsGeneratedRun.run_id == AnalyticsObservation.run_id,
            )
            .where(
                AnalyticsGeneratedRun.retention_class == retention_class,
                AnalyticsGeneratedRun.completed_at < now - lifetime,
            )
        )
        session.execute(
            delete(StreamEventOutbox).where(
                StreamEventOutbox.event_id.in_(expired_event_ids)
            )
        )
        result = session.execute(
            delete(AnalyticsGeneratedRun).where(
                AnalyticsGeneratedRun.retention_class == retention_class,
                AnalyticsGeneratedRun.completed_at < now - lifetime,
            )
        )
        deleted += int(result.rowcount or 0)
    return deleted
