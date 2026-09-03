from __future__ import annotations

import hashlib
from dataclasses import asdict
from datetime import datetime, timedelta
from time import perf_counter

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from hcam.analytics.activation import (
    P3_3_CAPABILITY,
    P3_3_PIPELINE_ID,
    P3_3_PIPELINE_VERSION,
    P3_3_POLICY_VERSION,
    P3_3_TAXONOMY_VERSION,
    P3_3_TRACKER_ID,
    P3_3_TRACKER_VERSION,
    assess_generated_activation,
)
from hcam.analytics.contracts import (
    NormalizedBoundingBox,
    ProcessingLineage,
    RuntimeReference,
    TrackLifecyclePayloadV2,
    TrackLifecycleV2,
    VersionedArtifact,
    canonical_contract_json,
)
from hcam.analytics.models import (
    AnalyticsAssignment,
    AnalyticsTrackerEpoch,
    AnalyticsTrack,
    AnalyticsTrackLifecycle,
    AnalyticsTrackingRun,
)
from hcam.analytics.schemas import (
    GeneratedTrackingRunCreate,
    GeneratedTrackingRunResponse,
    TrackLifecycleListResponse,
    TrackLifecycleResponse,
    TrackListResponse,
    TrackResponse,
    TrackingEpochListResponse,
    TrackingEpochResponse,
)
from hcam.analytics.service import (
    AnalyticsAssignmentConflictError,
    AnalyticsAssignmentNotFoundError,
    AnalyticsAssignmentService,
    AnalyticsAssignmentValidationError,
    _safe_reason,
)
from hcam.analytics.tracking import (
    StreamLocalTracker,
    GeneratedTrackingLaneStore,
    TrackerConfiguration,
    build_generated_tracking_scenario,
    evaluate_tracking_sequence,
)
from hcam.analytics.tracking.generated_sequences import (
    GENERATOR_ID,
    GENERATOR_VERSION,
)
from hcam.analytics.tracking.types import (
    TrackTransition,
    TrackerFrameResult,
    TrackingResourceError,
)
from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import utc_now
from hcam.security.auth import Principal
from hcam.streams.models import StreamEventOutbox


_STANDARD_RETENTION = timedelta(hours=168)
_RESTRICTED_RETENTION = timedelta(hours=24)


def _stable_id(prefix: str, *parts: object) -> str:
    payload = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:32]}"


def _metrics_document(metric) -> dict[str, object]:
    return asdict(metric)


def _empty_metrics() -> dict[str, object]:
    return {
        "hota": 0.0,
        "detection_accuracy": 0.0,
        "association_accuracy": 0.0,
        "localization_accuracy": 1.0,
        "idf1": 0.0,
        "id_precision": 0.0,
        "id_recall": 0.0,
        "id_true_positives": 0,
        "id_false_positives": 0,
        "id_false_negatives": 0,
        "identity_switches": 0,
        "per_class": {},
    }


def tracking_run_to_response(
    run: AnalyticsTrackingRun,
    *,
    reused: bool = False,
) -> GeneratedTrackingRunResponse:
    return GeneratedTrackingRunResponse(
        run_id=run.run_id,
        assignment_id=run.assignment_id,
        assignment_version=run.assignment_version,
        scenario_id=run.scenario_id,
        seed=run.seed,
        input_sha256=run.input_sha256,
        generator_id=run.generator_id,
        generator_version=run.generator_version,
        tracker_id=run.tracker_id,
        tracker_version=run.tracker_version,
        pipeline_id=run.pipeline_id,
        pipeline_version=run.pipeline_version,
        configuration_digest=run.configuration_digest,
        status=run.status,
        failure_code=run.failure_code,
        frame_count=run.frame_count,
        transition_count=run.transition_count,
        duration_ms=run.duration_ms,
        metrics=run.metrics,
        retention_class=run.retention_class,
        started_at=run.started_at,
        completed_at=run.completed_at,
        reused=reused,
    )


def epoch_to_response(epoch: AnalyticsTrackerEpoch) -> TrackingEpochResponse:
    return TrackingEpochResponse(
        epoch_id=epoch.epoch_id,
        run_id=epoch.run_id,
        epoch_index=epoch.epoch_index,
        tracker_id=epoch.tracker_id,
        tracker_version=epoch.tracker_version,
        configuration_digest=epoch.configuration_digest,
        start_sequence=epoch.start_sequence,
        end_sequence=epoch.end_sequence,
        started_at=epoch.started_at,
        ended_at=epoch.ended_at,
        end_reason=epoch.end_reason,
    )


def track_to_response(track: AnalyticsTrack) -> TrackResponse:
    return TrackResponse(
        track_id=track.track_id,
        epoch_id=track.epoch_id,
        run_id=track.run_id,
        local_track_number=track.local_track_number,
        class_id=track.class_id,
        state=track.state,
        first_observed_at=track.first_observed_at,
        first_sequence=track.first_sequence,
        latest_observed_at=track.latest_observed_at,
        latest_sequence=track.latest_sequence,
        last_visible_at=track.last_visible_at,
        last_visible_sequence=track.last_visible_sequence,
        latest_observation_id=track.latest_observation_id,
        bbox_x=track.bbox_x,
        bbox_y=track.bbox_y,
        bbox_width=track.bbox_width,
        bbox_height=track.bbox_height,
        confidence=track.confidence,
        age_frames=track.age_frames,
        visible_frames=track.visible_frames,
        missed_frames=track.missed_frames,
        tracker_id=track.tracker_id,
        tracker_version=track.tracker_version,
        pipeline_id=track.pipeline_id,
        pipeline_version=track.pipeline_version,
        taxonomy_version=track.taxonomy_version,
        configuration_digest=track.configuration_digest,
        retention_class=track.retention_class,
        created_at=track.created_at,
        updated_at=track.updated_at,
    )


def lifecycle_to_response(
    lifecycle: AnalyticsTrackLifecycle,
) -> TrackLifecycleResponse:
    return TrackLifecycleResponse(
        lifecycle_id=lifecycle.lifecycle_id,
        event_id=lifecycle.event_id,
        run_id=lifecycle.run_id,
        transition_index=lifecycle.transition_index,
        state=lifecycle.state,
        reason=lifecycle.reason,
        payload=lifecycle.payload,
        retention_class=lifecycle.retention_class,
        created_at=lifecycle.created_at,
    )


class GeneratedTrackingExecutionService:
    def __init__(
        self,
        session: Session,
        *,
        runtime_configured: bool,
        lanes: GeneratedTrackingLaneStore,
    ) -> None:
        self.session = session
        self.runtime_configured = runtime_configured
        self.lanes = lanes

    def execute(
        self,
        assignment_id: str,
        payload: GeneratedTrackingRunCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> GeneratedTrackingRunResponse:
        normalized_reason = _safe_reason(reason)
        scenario = build_generated_tracking_scenario(
            payload.scenario_id,
            payload.seed,
            payload.observed_at,
        )
        configuration = TrackerConfiguration()
        with self.session.begin():
            assignment = self._authorized_assignment(assignment_id, principal)
            self._require_executable(assignment)
            assignment_version = assignment.version_id
            run_id = _stable_id(
                "trun",
                assignment.assignment_id,
                scenario.scenario_id,
                scenario.seed,
                scenario.digest,
                assignment.pipeline_version,
                assignment.policy_version,
                assignment.configuration_digest,
            )
            existing = self.session.get(AnalyticsTrackingRun, run_id)
            if existing is not None:
                return tracking_run_to_response(existing, reused=True)
            snapshot = {
                "assignment_id": assignment.assignment_id,
                "assignment_version": assignment.version_id,
                "department": assignment.department,
                "stream_id": assignment.stream_id,
                "camera_id": assignment.camera_id,
                "configuration_digest": assignment.configuration_digest,
                "retention_class": assignment.retention_class,
            }

        tracker = StreamLocalTracker(
            department=str(snapshot["department"]),
            assignment_id=assignment_id,
            camera_id=str(snapshot["camera_id"]),
            stream_id=str(snapshot["stream_id"]),
            configuration=configuration,
            execution_id=run_id,
        )
        started_at = utc_now()
        clock = perf_counter()
        frame_results: list[TrackerFrameResult] = []
        persistence_results: list[tuple[datetime, int, TrackerFrameResult]] = []
        failure_code: str | None = None
        try:
            with self.lanes.lease(str(snapshot["stream_id"])):
                for generated in scenario.frames:
                    result = tracker.update(generated.frame)
                    frame_results.append(result)
                    persistence_results.append(
                        (generated.frame.observed_at, generated.frame.sequence, result)
                    )
                if scenario.frames:
                    final_frame = scenario.frames[-1].frame
                    closure = tracker.close(
                        "explicit_reset",
                        final_frame.observed_at,
                        final_frame.sequence,
                    )
                    if closure is not None:
                        persistence_results.append(
                            (final_frame.observed_at, final_frame.sequence, closure)
                        )
            metrics = _metrics_document(
                evaluate_tracking_sequence(scenario, tuple(frame_results))
            )
            status = "succeeded"
        except TrackingResourceError:
            failure_code = "resource_exhausted"
            status = "failed"
            metrics = _empty_metrics()
            closure = tracker.close(
                "resource_exhausted",
                payload.observed_at,
                scenario.frames[0].frame.sequence if scenario.frames else 0,
            )
            if closure is not None:
                persistence_results.append(
                    (payload.observed_at, scenario.frames[0].frame.sequence, closure)
                )
        completed_at = utc_now()
        duration_ms = min(60_000, max(0, round((perf_counter() - clock) * 1_000)))
        transition_count = sum(
            len(result.transitions) for _, _, result in persistence_results
        )

        try:
            with self.session.begin():
                assignment = self._authorized_assignment(assignment_id, principal)
                self._require_executable(assignment)
                if assignment.version_id != assignment_version:
                    raise AnalyticsAssignmentConflictError(
                        "Analytics assignment changed during generated tracking"
                    )
                existing = self.session.get(AnalyticsTrackingRun, run_id)
                if existing is not None:
                    return tracking_run_to_response(existing, reused=True)
                run = AnalyticsTrackingRun(
                    run_id=run_id,
                    assignment_id=assignment_id,
                    assignment_version=assignment_version,
                    department=str(snapshot["department"]),
                    stream_id=str(snapshot["stream_id"]),
                    camera_id=str(snapshot["camera_id"]),
                    scenario_id=scenario.scenario_id,
                    seed=scenario.seed,
                    input_sha256=scenario.digest,
                    generator_id=GENERATOR_ID,
                    generator_version=GENERATOR_VERSION,
                    tracker_id=P3_3_TRACKER_ID,
                    tracker_version=P3_3_TRACKER_VERSION,
                    pipeline_id=P3_3_PIPELINE_ID,
                    pipeline_version=P3_3_PIPELINE_VERSION,
                    configuration_digest=configuration.digest,
                    status=status,
                    failure_code=failure_code,
                    frame_count=len(scenario.frames),
                    transition_count=transition_count,
                    duration_ms=duration_ms,
                    metrics=metrics,
                    retention_class=str(snapshot["retention_class"]),
                    started_at=started_at,
                    completed_at=completed_at,
                )
                self.session.add(run)
                self.session.flush()
                self._persist_results(run, persistence_results)
                lifecycle_changed = AnalyticsAssignmentService(
                    self.session
                ).apply_runtime_state(
                    assignment,
                    lifecycle_state="running" if status == "succeeded" else "degraded",
                    actor_id=principal.actor_id,
                    reason=normalized_reason,
                    occurred_at=completed_at,
                )
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="analytics.generated_tracking_run.execute",
                    target_type="analytics_tracking_run",
                    target_id=run_id,
                    source="hcam.api",
                    reason=normalized_reason,
                    outcome="success" if status == "succeeded" else "failure",
                    context={
                        "execution_scope": "generated_only",
                        "failure_code": failure_code,
                        "frame_count": len(scenario.frames),
                        "lifecycle_changed": lifecycle_changed,
                        "scenario_id": scenario.scenario_id,
                        "status": status,
                        "transition_count": transition_count,
                    },
                    request_id=request_id,
                )
            return tracking_run_to_response(run)
        except IntegrityError as exc:
            self.session.rollback()
            existing = self.session.get(AnalyticsTrackingRun, run_id)
            if existing is not None and principal.can_access_department(
                existing.department
            ):
                return tracking_run_to_response(existing, reused=True)
            raise AnalyticsAssignmentConflictError(
                "Generated tracking run conflicts with existing metadata"
            ) from exc

    def get_run(
        self,
        run_id: str,
        *,
        principal: Principal,
    ) -> GeneratedTrackingRunResponse:
        return tracking_run_to_response(self._authorized_run(run_id, principal))

    def list_epochs(
        self,
        run_id: str,
        *,
        principal: Principal,
        limit: int,
        offset: int,
    ) -> TrackingEpochListResponse:
        self._authorized_run(run_id, principal)
        query = select(AnalyticsTrackerEpoch).where(
            AnalyticsTrackerEpoch.run_id == run_id
        )
        total, rows = self._page(
            query.order_by(AnalyticsTrackerEpoch.epoch_index), limit, offset
        )
        return TrackingEpochListResponse(
            items=[epoch_to_response(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def list_tracks(
        self,
        run_id: str,
        *,
        principal: Principal,
        limit: int,
        offset: int,
    ) -> TrackListResponse:
        self._authorized_run(run_id, principal)
        query = select(AnalyticsTrack).where(AnalyticsTrack.run_id == run_id)
        total, rows = self._page(
            query.order_by(AnalyticsTrack.epoch_id, AnalyticsTrack.local_track_number),
            limit,
            offset,
        )
        return TrackListResponse(
            items=[track_to_response(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def list_lifecycle(
        self,
        run_id: str,
        *,
        principal: Principal,
        limit: int,
        offset: int,
    ) -> TrackLifecycleListResponse:
        self._authorized_run(run_id, principal)
        query = select(AnalyticsTrackLifecycle).where(
            AnalyticsTrackLifecycle.run_id == run_id
        )
        total, rows = self._page(
            query.order_by(AnalyticsTrackLifecycle.transition_index), limit, offset
        )
        return TrackLifecycleListResponse(
            items=[lifecycle_to_response(row) for row in rows],
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

    def _authorized_run(
        self,
        run_id: str,
        principal: Principal,
    ) -> AnalyticsTrackingRun:
        run = self.session.get(AnalyticsTrackingRun, run_id)
        if run is None or not principal.can_access_department(run.department):
            raise AnalyticsAssignmentNotFoundError("Generated tracking run not found")
        return run

    def _require_executable(self, assignment: AnalyticsAssignment) -> None:
        assessment = assess_generated_activation(
            assignment,
            runtime_configured=False,
            tracking_runtime_configured=self.runtime_configured,
        )
        if assignment.capability != P3_3_CAPABILITY or not assessment.eligible:
            raise AnalyticsAssignmentValidationError(
                "Analytics assignment is outside generated tracking scope"
            )
        if (
            assignment.desired_state != "enabled"
            or assignment.lifecycle_state not in {"running", "degraded"}
        ):
            raise AnalyticsAssignmentConflictError(
                "Analytics assignment must be active before generated tracking"
            )

    def _persist_results(
        self,
        run: AnalyticsTrackingRun,
        results: list[tuple[datetime, int, TrackerFrameResult]],
    ) -> None:
        epoch_indexes: dict[str, int] = {}
        transition_index = 0
        for observed_at, sequence, result in results:
            if result.epoch_started:
                epoch_indexes[result.epoch_id] = len(epoch_indexes) + 1
                self.session.add(
                    AnalyticsTrackerEpoch(
                        epoch_id=result.epoch_id,
                        run_id=run.run_id,
                        assignment_id=run.assignment_id,
                        department=run.department,
                        stream_id=run.stream_id,
                        camera_id=run.camera_id,
                        epoch_index=epoch_indexes[result.epoch_id],
                        tracker_id=run.tracker_id,
                        tracker_version=run.tracker_version,
                        configuration_digest=run.configuration_digest,
                        start_sequence=sequence,
                        started_at=observed_at,
                    )
                )
                self.session.flush()
            for transition in result.transitions:
                self._persist_transition(run, transition, transition_index)
                transition_index += 1
            for closure in result.closed_epochs:
                epoch = self.session.get(AnalyticsTrackerEpoch, closure.epoch_id)
                if epoch is None:
                    raise AnalyticsAssignmentValidationError(
                        "Tracker emitted an unknown epoch closure"
                    )
                epoch.end_sequence = closure.end_sequence
                epoch.ended_at = closure.ended_at
                epoch.end_reason = closure.reason

    def _persist_transition(
        self,
        run: AnalyticsTrackingRun,
        transition: TrackTransition,
        transition_index: int,
    ) -> None:
        existing = self.session.get(AnalyticsTrack, transition.track_id)
        x, y, width, height = transition.bbox
        if existing is None:
            if transition.state != "started":
                raise AnalyticsAssignmentValidationError(
                    "Tracker lifecycle must begin with a started transition"
                )
            existing = AnalyticsTrack(
                track_id=transition.track_id,
                epoch_id=transition.epoch_id,
                run_id=run.run_id,
                assignment_id=run.assignment_id,
                department=run.department,
                stream_id=run.stream_id,
                camera_id=run.camera_id,
                local_track_number=transition.local_track_number,
                class_id=transition.class_id,
                state=transition.state,
                first_observed_at=transition.first_observed_at,
                first_sequence=transition.first_sequence,
                latest_observed_at=transition.observed_at,
                latest_sequence=transition.source_sequence,
                last_visible_at=transition.last_visible_at,
                last_visible_sequence=transition.last_visible_sequence,
                latest_observation_id=transition.latest_observation_id,
                bbox_x=x,
                bbox_y=y,
                bbox_width=width,
                bbox_height=height,
                confidence=transition.confidence,
                age_frames=transition.age_frames,
                visible_frames=transition.visible_frames,
                missed_frames=transition.missed_frames,
                tracker_id=run.tracker_id,
                tracker_version=run.tracker_version,
                pipeline_id=run.pipeline_id,
                pipeline_version=run.pipeline_version,
                taxonomy_version=P3_3_TAXONOMY_VERSION,
                configuration_digest=run.configuration_digest,
                retention_class=run.retention_class,
                created_at=transition.observed_at,
                updated_at=transition.observed_at,
            )
            self.session.add(existing)
            self.session.flush()
        else:
            if existing.state == "ended":
                raise AnalyticsAssignmentValidationError(
                    "Ended tracker lifecycle cannot be resurrected"
                )
            existing.state = transition.state
            existing.latest_observed_at = transition.observed_at
            existing.latest_sequence = transition.source_sequence
            existing.last_visible_at = transition.last_visible_at
            existing.last_visible_sequence = transition.last_visible_sequence
            existing.latest_observation_id = transition.latest_observation_id
            existing.bbox_x = x
            existing.bbox_y = y
            existing.bbox_width = width
            existing.bbox_height = height
            existing.confidence = transition.confidence
            existing.age_frames = transition.age_frames
            existing.visible_frames = transition.visible_frames
            existing.missed_frames = transition.missed_frames
            existing.updated_at = transition.observed_at

        payload = self._lifecycle_payload(run, transition)
        lifecycle_id = _stable_id("lfc", run.run_id, transition_index)
        event_id = _stable_id("evt", lifecycle_id, "lifecycle-v2")
        event = TrackLifecycleV2(
            event_id=event_id,
            stream_id=run.stream_id,
            camera_id=run.camera_id,
            partition_key=run.stream_id,
            occurred_at=transition.observed_at,
            payload=payload,
        )
        canonical_contract_json(event)
        self.session.add(
            AnalyticsTrackLifecycle(
                lifecycle_id=lifecycle_id,
                event_id=event_id,
                run_id=run.run_id,
                epoch_id=transition.epoch_id,
                track_id=transition.track_id,
                assignment_id=run.assignment_id,
                department=run.department,
                stream_id=run.stream_id,
                camera_id=run.camera_id,
                transition_index=transition_index,
                state=transition.state,
                reason=transition.reason,
                occurred_at=transition.observed_at,
                source_sequence=transition.source_sequence,
                latest_observation_id=transition.latest_observation_id,
                payload=payload.model_dump(mode="json"),
                retention_class=run.retention_class,
                created_at=transition.observed_at,
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
    def _lifecycle_payload(
        run: AnalyticsTrackingRun,
        transition: TrackTransition,
    ) -> TrackLifecyclePayloadV2:
        x, y, width, height = transition.bbox
        lineage = ProcessingLineage(
            code_version=P3_3_PIPELINE_VERSION,
            pipeline=VersionedArtifact(
                id=P3_3_PIPELINE_ID,
                version=P3_3_PIPELINE_VERSION,
            ),
            preprocessing_version=GENERATOR_VERSION,
            postprocessing_version=P3_3_TRACKER_VERSION,
            taxonomy_version=P3_3_TAXONOMY_VERSION,
            policy_version=P3_3_POLICY_VERSION,
            runtime=RuntimeReference(
                name="hcam.stream-local-tracker",
                version=P3_3_TRACKER_ID,
            ),
            configuration_digest=run.configuration_digest,
        )
        return TrackLifecyclePayloadV2(
            track_id=transition.track_id,
            tracker_epoch=transition.epoch_id,
            stream_id=run.stream_id,
            camera_id=run.camera_id,
            state=transition.state,
            reason=transition.reason,
            first_observed_at=transition.first_observed_at,
            first_sequence=transition.first_sequence,
            observed_at=transition.observed_at,
            source_sequence=transition.source_sequence,
            last_visible_at=transition.last_visible_at,
            last_visible_sequence=transition.last_visible_sequence,
            latest_observation_id=transition.latest_observation_id,
            class_id=transition.class_id,
            bbox=NormalizedBoundingBox(
                x=x,
                y=y,
                width=width,
                height=height,
            ),
            confidence=transition.confidence,
            age_frames=transition.age_frames,
            visible_frames=transition.visible_frames,
            missed_frames=transition.missed_frames,
            tracker=VersionedArtifact(
                id=P3_3_TRACKER_ID,
                version=P3_3_TRACKER_VERSION,
            ),
            lineage=lineage,
            retention_class=run.retention_class,
        )

    def _page(self, query, limit: int, offset: int):
        total = int(
            self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        )
        rows = self.session.scalars(query.limit(limit).offset(offset)).all()
        return total, rows


def purge_expired_generated_tracking(
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
            select(AnalyticsTrackLifecycle.event_id)
            .join(
                AnalyticsTrackingRun,
                AnalyticsTrackingRun.run_id == AnalyticsTrackLifecycle.run_id,
            )
            .where(
                AnalyticsTrackingRun.retention_class == retention_class,
                AnalyticsTrackingRun.completed_at < now - lifetime,
            )
        )
        session.execute(
            delete(StreamEventOutbox).where(
                StreamEventOutbox.event_id.in_(expired_event_ids)
            )
        )
        result = session.execute(
            delete(AnalyticsTrackingRun).where(
                AnalyticsTrackingRun.retention_class == retention_class,
                AnalyticsTrackingRun.completed_at < now - lifetime,
            )
        )
        deleted += int(result.rowcount or 0)
    return deleted
