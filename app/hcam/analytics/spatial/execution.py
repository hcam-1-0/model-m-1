from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from time import perf_counter

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from hcam.analytics.models import (
    AnalyticsAssignment,
    AnalyticsEvent,
    AnalyticsGeometry,
    AnalyticsGeometryEvaluatorRun,
    AnalyticsGeometryRule,
    AnalyticsTrackRuleState,
)
from hcam.analytics.service import _safe_reason
from hcam.analytics.spatial.cel_policy import ConstrainedCelEnvironment
from hcam.analytics.spatial.contracts import GeometryRuleV1
from hcam.analytics.spatial.evaluator import (
    AnalyticPrimitiveEvent,
    BoundedEventBuffer,
    CompiledGeometryRule,
    EvaluatorBoundaryError,
    GeometryEventEvaluator,
)
from hcam.analytics.spatial.generated import build_generated_lifecycle_scenario
from hcam.analytics.spatial.geometry_engine import canonicalize_geometry
from hcam.analytics.spatial.schemas import (
    AnalyticEventListResponse,
    AnalyticEventResponse,
    GeneratedGeometryRunCreate,
    GeneratedGeometryRunResponse,
)
from hcam.analytics.spatial.service import (
    SpatialConflictError,
    SpatialNotFoundError,
    _geometry_definition,
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


def _configuration_digest(rows: list[AnalyticsGeometryRule]) -> str:
    payload = "\n".join(
        row.configuration_digest
        for row in sorted(rows, key=lambda item: item.rule_record_id)
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def run_response(
    row: AnalyticsGeometryEvaluatorRun,
    *,
    reused: bool = False,
) -> GeneratedGeometryRunResponse:
    return GeneratedGeometryRunResponse(
        run_id=row.run_id,
        assignment_id=row.assignment_id,
        execution_scope=row.execution_scope,
        scenario_id=row.scenario_id,
        seed=row.seed,
        input_sha256=row.input_sha256,
        configuration_digest=row.configuration_digest,
        status=row.status,
        close_reason=row.close_reason,
        input_count=row.input_count,
        event_count=row.event_count,
        duplicate_count=row.duplicate_count,
        late_count=row.late_count,
        maximum_buffer_depth=row.maximum_buffer_depth,
        maximum_candidate_count=row.maximum_candidate_count,
        maximum_state_count=row.maximum_state_count,
        duration_ms=row.duration_ms,
        retention_class=row.retention_class,
        started_at=row.started_at,
        completed_at=row.completed_at,
        reused=reused,
    )


def event_response(row: AnalyticsEvent) -> AnalyticEventResponse:
    return AnalyticEventResponse(
        event_id=row.event_id,
        event_kind=row.event_kind,
        occurred_at=row.occurred_at,
        department=row.department,
        assignment_id=row.assignment_id,
        stream_id=row.stream_id,
        camera_id=row.camera_id,
        epoch_id=row.epoch_id,
        track_id=row.track_id,
        lifecycle_id=row.lifecycle_id,
        source_sequence=row.source_sequence,
        payload=row.payload,
        retention_class=row.retention_class,
        alert_state=row.alert_state,
    )


class GeneratedGeometryExecutionService:
    def __init__(self, session: Session, *, runtime_configured: bool) -> None:
        self.session = session
        self.runtime_configured = runtime_configured
        self.cel = ConstrainedCelEnvironment()

    def execute(
        self,
        assignment_id: str,
        payload: GeneratedGeometryRunCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> GeneratedGeometryRunResponse:
        if not self.runtime_configured:
            raise SpatialConflictError("Generated geometry runtime is disabled")
        normalized_reason = _safe_reason(reason)
        if len(payload.rule_record_ids) != len(set(payload.rule_record_ids)):
            raise SpatialConflictError("Generated run rule identifiers must be unique")
        started_clock = perf_counter()
        with self.session.begin():
            assignment = self.session.get(AnalyticsAssignment, assignment_id)
            if (
                assignment is None
                or not principal.can_access_department(assignment.department)
            ):
                raise SpatialNotFoundError("Analytics assignment not found")
            if (
                assignment.desired_state != "enabled"
                or assignment.lifecycle_state != "running"
                or assignment.execution_scope != "generated_only"
            ):
                raise SpatialConflictError("Analytics assignment is not running")
            rows = [
                self.session.get(AnalyticsGeometryRule, record_id)
                for record_id in payload.rule_record_ids
            ]
            if any(row is None for row in rows):
                raise SpatialNotFoundError("Approved geometry rule not found")
            rules = [row for row in rows if row is not None]
            if any(
                row.status != "approved"
                or row.assignment_id != assignment_id
                or row.department != assignment.department
                or row.stream_id != assignment.stream_id
                or row.camera_id != assignment.camera_id
                for row in rules
            ):
                raise SpatialNotFoundError("Approved geometry rule not found")
            compiled = self._compile(rules)
            maximum_dwell = max(
                (
                    item.definition.dwell_threshold_ms or 0
                    for item in compiled
                ),
                default=2_000,
            )
            retention_class = (
                "derived.analytics.restricted"
                if any(
                    row.retention_class == "derived.analytics.restricted" for row in rules
                )
                else "derived.analytics.standard"
            )
            scenario = build_generated_lifecycle_scenario(
                payload.scenario_id,
                seed=payload.seed,
                observed_at=payload.observed_at,
                department=assignment.department,
                assignment_id=assignment.assignment_id,
                stream_id=assignment.stream_id,
                camera_id=assignment.camera_id,
                maximum_dwell_ms=max(2_000, maximum_dwell),
                retention_class=retention_class,
            )
            configuration_digest = _configuration_digest(rules)
            existing = self.session.scalar(
                select(AnalyticsGeometryEvaluatorRun).where(
                    AnalyticsGeometryEvaluatorRun.assignment_id == assignment_id,
                    AnalyticsGeometryEvaluatorRun.scenario_id == payload.scenario_id,
                    AnalyticsGeometryEvaluatorRun.seed == payload.seed,
                    AnalyticsGeometryEvaluatorRun.input_sha256 == scenario.digest,
                    AnalyticsGeometryEvaluatorRun.configuration_digest
                    == configuration_digest,
                )
            )
            if existing is not None:
                return run_response(existing, reused=True)
            evaluator = GeometryEventEvaluator(tuple(compiled), cel_environment=self.cel)
            buffer = BoundedEventBuffer()
            events: list[AnalyticPrimitiveEvent] = []
            duplicate_count = 0
            late_count = 0
            maximum_buffer_depth = 0
            maximum_state_count = 0
            close_reason = "completed"
            status = "succeeded"
            try:
                for item in scenario.inputs:
                    outcome = buffer.push(item)
                    if outcome == "duplicate":
                        duplicate_count += 1
                    elif outcome == "late":
                        late_count += 1
                    maximum_buffer_depth = max(maximum_buffer_depth, buffer.depth)
                    for ready in buffer.pop_ready():
                        events.extend(evaluator.evaluate(ready))
                        maximum_state_count = max(
                            maximum_state_count, evaluator.state_count
                        )
                for ready in buffer.drain():
                    events.extend(evaluator.evaluate(ready))
                    maximum_state_count = max(maximum_state_count, evaluator.state_count)
            except EvaluatorBoundaryError as exc:
                status = "failed"
                close_reason = exc.code
                events.clear()
            completed_at = utc_now()
            duration_ms = min(60_000, int((perf_counter() - started_clock) * 1_000))
            run_id = _stable_id(
                "grun",
                assignment_id,
                payload.scenario_id,
                payload.seed,
                scenario.digest,
                configuration_digest,
            )
            run = AnalyticsGeometryEvaluatorRun(
                run_id=run_id,
                assignment_id=assignment_id,
                department=assignment.department,
                stream_id=assignment.stream_id,
                camera_id=assignment.camera_id,
                epoch_id=scenario.inputs[0].epoch_id,
                execution_scope="generated_only",
                scenario_id=payload.scenario_id,
                seed=payload.seed,
                input_sha256=scenario.digest,
                configuration_digest=configuration_digest,
                status=status,
                close_reason=close_reason,
                input_count=len(scenario.inputs),
                event_count=len(events),
                duplicate_count=duplicate_count,
                late_count=late_count,
                maximum_buffer_depth=maximum_buffer_depth,
                maximum_candidate_count=len(compiled),
                maximum_state_count=maximum_state_count,
                duration_ms=duration_ms,
                retention_class=retention_class,
                started_at=payload.observed_at,
                completed_at=completed_at,
            )
            self.session.add(run)
            self.session.flush()
            rule_by_key = {
                (row.rule_id, row.rule_version): row for row in rules
            }
            geometry_by_id = {
                row.geometry_record_id: self.session.get(
                    AnalyticsGeometry, row.geometry_record_id
                )
                for row in rules
            }
            for event in events:
                rule_row = rule_by_key[(event.rule_id, event.rule_version)]
                self._persist_event(
                    run,
                    event,
                    rule_row=rule_row,
                    geometry_row=geometry_by_id[rule_row.geometry_record_id],
                )
            for snapshot in evaluator.state_snapshots():
                rule_row = rule_by_key[
                    (str(snapshot["rule_id"]), int(snapshot["rule_version"]))
                ]
                self.session.add(
                    AnalyticsTrackRuleState(
                        state_id=_stable_id(
                            "state",
                            run_id,
                            rule_row.rule_record_id,
                            snapshot["track_id"],
                        ),
                        evaluator_run_id=run_id,
                        rule_record_id=rule_row.rule_record_id,
                        department=run.department,
                        stream_id=run.stream_id,
                        epoch_id=run.epoch_id,
                        track_id=str(snapshot["track_id"]),
                        state=snapshot,
                        updated_at=completed_at,
                    )
                )
            AuditRepository(self.session).record(
                actor_id=principal.actor_id,
                action="analytics.geometry_run.execute",
                target_type="analytics_geometry_evaluator_run",
                target_id=run_id,
                source="hcam.api",
                reason=normalized_reason,
                outcome="success" if status == "succeeded" else "failure",
                context={
                    "event_count": len(events),
                    "scenario_id": payload.scenario_id,
                    "status": status,
                },
                request_id=request_id,
            )
        return run_response(run)

    def get_run(
        self, run_id: str, *, principal: Principal
    ) -> GeneratedGeometryRunResponse:
        row = self.session.get(AnalyticsGeometryEvaluatorRun, run_id)
        if row is None or not principal.can_access_department(row.department):
            raise SpatialNotFoundError("Geometry evaluator run not found")
        return run_response(row)

    def list_events(
        self,
        run_id: str,
        *,
        principal: Principal,
        limit: int,
        offset: int,
    ) -> AnalyticEventListResponse:
        run = self.session.get(AnalyticsGeometryEvaluatorRun, run_id)
        if run is None or not principal.can_access_department(run.department):
            raise SpatialNotFoundError("Geometry evaluator run not found")
        query = select(AnalyticsEvent).where(AnalyticsEvent.evaluator_run_id == run_id)
        total = int(self.session.scalar(select(func.count()).select_from(query.subquery())) or 0)
        rows = self.session.scalars(
            query.order_by(
                AnalyticsEvent.source_sequence,
                AnalyticsEvent.event_kind,
                AnalyticsEvent.event_id,
            )
            .limit(limit)
            .offset(offset)
        ).all()
        return AnalyticEventListResponse(
            items=[event_response(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def _compile(
        self, rows: list[AnalyticsGeometryRule]
    ) -> list[CompiledGeometryRule]:
        compiled: list[CompiledGeometryRule] = []
        for row in rows:
            geometry = self.session.get(AnalyticsGeometry, row.geometry_record_id)
            if geometry is None or geometry.status != "approved":
                raise SpatialNotFoundError("Approved geometry not found")
            definition = GeometryRuleV1.model_validate(row.configuration)
            canonical = canonicalize_geometry(_geometry_definition(geometry).shape)
            if canonical.digest != geometry.configuration_digest:
                raise SpatialConflictError("Geometry canonical digest drift detected")
            item = CompiledGeometryRule.build(
                definition,
                _geometry_definition(geometry),
                canonical,
                self.cel,
            )
            if item.checked_cel.digest != row.checked_cel_digest:
                raise SpatialConflictError("Checked CEL digest drift detected")
            compiled.append(item)
        return sorted(
            compiled,
            key=lambda item: (item.definition.rule_id, item.definition.version),
        )

    def _persist_event(
        self,
        run: AnalyticsGeometryEvaluatorRun,
        event: AnalyticPrimitiveEvent,
        *,
        rule_row: AnalyticsGeometryRule,
        geometry_row: AnalyticsGeometry | None,
    ) -> None:
        if geometry_row is None:
            raise SpatialConflictError("Geometry disappeared during event persistence")
        document = event.document()
        self.session.add(
            AnalyticsEvent(
                event_id=event.event_id,
                evaluator_run_id=run.run_id,
                rule_record_id=rule_row.rule_record_id,
                geometry_record_id=geometry_row.geometry_record_id,
                department=event.department,
                assignment_id=event.assignment_id,
                stream_id=event.stream_id,
                camera_id=event.camera_id,
                epoch_id=event.epoch_id,
                track_id=event.track_id,
                lifecycle_id=event.lifecycle_id,
                source_sequence=event.source_sequence,
                event_kind=event.event_kind,
                occurred_at=event.occurred_at,
                payload=document,
                retention_class=event.retention_class,
                alert_state="not_evaluated",
                created_at=utc_now(),
            )
        )
        self.session.add(
            StreamEventOutbox(
                event_id=event.event_id,
                event_type=event.event_kind,
                schema_version=1,
                stream_id=event.stream_id,
                camera_id=event.camera_id,
                occurred_at=event.occurred_at,
                payload=document,
            )
        )


def purge_expired_geometry_events(session: Session, *, now: datetime) -> int:
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("retention cutoff must be timezone-aware UTC")
    deleted = 0
    for retention_class, lifetime in (
        ("derived.analytics.standard", _STANDARD_RETENTION),
        ("derived.analytics.restricted", _RESTRICTED_RETENTION),
    ):
        expired_runs = select(AnalyticsGeometryEvaluatorRun.run_id).where(
            AnalyticsGeometryEvaluatorRun.retention_class == retention_class,
            AnalyticsGeometryEvaluatorRun.completed_at < now - lifetime,
        )
        expired_events = select(AnalyticsEvent.event_id).where(
            AnalyticsEvent.evaluator_run_id.in_(expired_runs)
        )
        session.execute(
            delete(StreamEventOutbox).where(StreamEventOutbox.event_id.in_(expired_events))
        )
        result = session.execute(
            delete(AnalyticsGeometryEvaluatorRun).where(
                AnalyticsGeometryEvaluatorRun.run_id.in_(expired_runs)
            )
        )
        deleted += int(result.rowcount or 0)
    return deleted
