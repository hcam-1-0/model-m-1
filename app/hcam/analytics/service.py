from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from hcam.analytics.contracts import (
    AnalyticsAssignmentV1,
    AnalyticsContractSafetyError,
    DeploymentTargetV1,
    ModelDeploymentChangedV1,
    ModelDeploymentPayloadV1,
    VersionedArtifact,
    VersionedConfiguration,
    canonical_contract_json,
    inspect_contract_safety,
)
from hcam.analytics.models import AnalyticsAssignment, AnalyticsAssignmentRevision
from hcam.analytics.repository import assignment_to_contract
from hcam.analytics.schemas import AnalyticsAssignmentCreate, AnalyticsAssignmentPatch
from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera, utc_now
from hcam.security.auth import Principal
from hcam.streams.models import StreamEndpoint, StreamEventOutbox


class AnalyticsAssignmentNotFoundError(RuntimeError):
    pass


class AnalyticsAssignmentConflictError(RuntimeError):
    pass


class AnalyticsAssignmentPreconditionError(RuntimeError):
    pass


class AnalyticsAssignmentValidationError(RuntimeError):
    pass


def _model_documents(models: list[VersionedArtifact]) -> list[dict[str, str]]:
    return [model.model_dump(mode="json") for model in models]


def _geometry_documents(
    values: list[VersionedConfiguration],
) -> list[dict[str, object]]:
    return [value.model_dump(mode="json") for value in values]


def _target(assignment: AnalyticsAssignment) -> DeploymentTargetV1:
    return DeploymentTargetV1(
        pipeline=VersionedArtifact(
            id=assignment.pipeline_id,
            version=assignment.pipeline_version,
        ),
        models=[VersionedArtifact.model_validate(item) for item in assignment.models],
        configuration_digest=assignment.configuration_digest,
    )


def _safe_reason(reason: str) -> str:
    normalized = reason.strip()
    if not normalized or normalized != reason:
        raise AnalyticsAssignmentValidationError(
            "Reason must be non-blank without outer whitespace"
        )
    try:
        inspect_contract_safety({"change_reason": normalized})
    except AnalyticsContractSafetyError as exc:
        raise AnalyticsAssignmentValidationError(
            "Reason contains prohibited sensitive content"
        ) from exc
    return normalized


def _safe_audit_reason(reason: str) -> str:
    try:
        return _safe_reason(reason)
    except AnalyticsAssignmentValidationError:
        return "Rejected unsafe analytics assignment request"


class AnalyticsAssignmentService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        stream_id: str,
        payload: AnalyticsAssignmentCreate,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> AnalyticsAssignment:
        assignment_id = f"ana_{uuid4().hex}"
        try:
            normalized_reason = _safe_reason(reason)
            with self.session.begin():
                endpoint = self.session.get(StreamEndpoint, stream_id)
                if endpoint is None:
                    raise AnalyticsAssignmentNotFoundError("Stream not found")
                camera = self.session.get(Camera, endpoint.camera_id)
                if camera is None or not principal.can_access_department(
                    camera.department
                ):
                    raise AnalyticsAssignmentNotFoundError("Stream not found")
                now = utc_now()
                assignment = AnalyticsAssignment(
                    assignment_id=assignment_id,
                    department=camera.department,
                    stream_id=stream_id,
                    camera_id=endpoint.camera_id,
                    capability=payload.capability,
                    desired_state="paused",
                    lifecycle_state="blocked",
                    reason_code="owner_gates_pending",
                    pipeline_id=payload.pipeline.id,
                    pipeline_version=payload.pipeline.version,
                    models=_model_documents(payload.models),
                    taxonomy_version=payload.taxonomy_version,
                    policy_version=payload.policy_version,
                    configuration_digest=payload.configuration_digest,
                    minimum_confidence=payload.minimum_confidence,
                    sampling_fps=payload.sampling_fps,
                    maximum_queue_age_ms=payload.maximum_queue_age_ms,
                    geometry_refs=_geometry_documents(payload.geometry_refs),
                    retention_class=payload.retention_class,
                    last_actor_id=principal.actor_id,
                    last_change_reason=normalized_reason,
                    approval_record_id=payload.approval_record_id,
                    created_at=now,
                    updated_at=now,
                )
                self.session.add(assignment)
                self.session.flush()
                contract = self._validated_contract(assignment)
                self._record_revision(assignment, contract, now)
                self._queue_deployment_event(
                    assignment,
                    previous=None,
                    current=_target(assignment),
                    occurred_at=now,
                )
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="analytics.assignment.create",
                    target_type="analytics_assignment",
                    target_id=assignment_id,
                    source="hcam.api",
                    reason=normalized_reason,
                    outcome="success",
                    context={
                        "camera_id": assignment.camera_id,
                        "stream_id": stream_id,
                        "capability": assignment.capability,
                        "version": assignment.version_id,
                        "lifecycle_state": "blocked",
                    },
                    request_id=request_id,
                )
            return assignment
        except (
            AnalyticsAssignmentNotFoundError,
            AnalyticsAssignmentValidationError,
        ) as exc:
            self._record_failure(
                principal,
                "analytics.assignment.create",
                assignment_id,
                reason,
                exc,
                request_id,
            )
            raise
        except IntegrityError as exc:
            error = AnalyticsAssignmentConflictError(
                "Stream already has an assignment for this capability"
            )
            self._record_failure(
                principal,
                "analytics.assignment.create",
                assignment_id,
                reason,
                error,
                request_id,
            )
            raise error from exc

    def update(
        self,
        assignment_id: str,
        payload: AnalyticsAssignmentPatch,
        *,
        expected_version: int,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> AnalyticsAssignment:
        try:
            normalized_reason = _safe_reason(reason)
            with self.session.begin():
                assignment = self.session.get(AnalyticsAssignment, assignment_id)
                if assignment is None:
                    raise AnalyticsAssignmentNotFoundError("Assignment not found")
                endpoint = self.session.get(StreamEndpoint, assignment.stream_id)
                camera = self.session.get(Camera, assignment.camera_id)
                if (
                    endpoint is None
                    or endpoint.camera_id != assignment.camera_id
                    or camera is None
                    or camera.department != assignment.department
                    or not principal.can_access_department(camera.department)
                ):
                    raise AnalyticsAssignmentNotFoundError("Assignment not found")
                if assignment.version_id != expected_version:
                    raise AnalyticsAssignmentPreconditionError(
                        "Analytics assignment version does not match"
                    )

                changes = payload.model_dump(exclude_unset=True)
                material_changes = set(changes) - {"configuration_digest"}
                if material_changes and "configuration_digest" not in changes:
                    raise AnalyticsAssignmentValidationError(
                        "Configuration changes require a new configuration_digest"
                    )
                if (
                    "configuration_digest" in changes
                    and payload.configuration_digest == assignment.configuration_digest
                ):
                    raise AnalyticsAssignmentValidationError(
                        "configuration_digest must change for an assignment update"
                    )

                before = assignment_to_contract(assignment)
                previous_target = _target(assignment)
                self._apply_changes(assignment, payload, changes)
                assignment.last_actor_id = principal.actor_id
                assignment.last_change_reason = normalized_reason
                assignment.updated_at = utc_now()
                self.session.flush()
                contract = self._validated_contract(assignment)
                self._record_revision(assignment, contract, assignment.updated_at)
                self._queue_deployment_event(
                    assignment,
                    previous=previous_target,
                    current=_target(assignment),
                    occurred_at=assignment.updated_at,
                )
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="analytics.assignment.update",
                    target_type="analytics_assignment",
                    target_id=assignment_id,
                    source="hcam.api",
                    reason=normalized_reason,
                    outcome="success",
                    context={
                        "camera_id": assignment.camera_id,
                        "stream_id": assignment.stream_id,
                        "capability": assignment.capability,
                        "changed_fields": sorted(changes),
                        "previous_version": before.version,
                        "version": assignment.version_id,
                        "lifecycle_state": "blocked",
                    },
                    request_id=request_id,
                )
            return assignment
        except (
            AnalyticsAssignmentNotFoundError,
            AnalyticsAssignmentPreconditionError,
            AnalyticsAssignmentValidationError,
        ) as exc:
            self._record_failure(
                principal,
                "analytics.assignment.update",
                assignment_id,
                reason,
                exc,
                request_id,
            )
            raise
        except StaleDataError as exc:
            error = AnalyticsAssignmentPreconditionError(
                "Analytics assignment changed during the update"
            )
            self._record_failure(
                principal,
                "analytics.assignment.update",
                assignment_id,
                reason,
                error,
                request_id,
            )
            raise error from exc
        except IntegrityError as exc:
            error = AnalyticsAssignmentConflictError(
                "Analytics assignment update conflicts with existing data"
            )
            self._record_failure(
                principal,
                "analytics.assignment.update",
                assignment_id,
                reason,
                error,
                request_id,
            )
            raise error from exc

    @staticmethod
    def _apply_changes(
        assignment: AnalyticsAssignment,
        payload: AnalyticsAssignmentPatch,
        changes: dict[str, object],
    ) -> None:
        if "pipeline" in changes and payload.pipeline is not None:
            assignment.pipeline_id = payload.pipeline.id
            assignment.pipeline_version = payload.pipeline.version
        if "models" in changes and payload.models is not None:
            assignment.models = _model_documents(payload.models)
        for field in (
            "taxonomy_version",
            "policy_version",
            "configuration_digest",
            "minimum_confidence",
            "sampling_fps",
            "maximum_queue_age_ms",
            "retention_class",
            "approval_record_id",
        ):
            if field in changes:
                value = getattr(payload, field)
                if value is not None:
                    setattr(assignment, field, value)
        if "geometry_refs" in changes and payload.geometry_refs is not None:
            assignment.geometry_refs = _geometry_documents(payload.geometry_refs)

    @staticmethod
    def _validated_contract(assignment: AnalyticsAssignment) -> AnalyticsAssignmentV1:
        try:
            contract = assignment_to_contract(assignment)
            canonical_contract_json(contract)
        except ValueError as exc:
            raise AnalyticsAssignmentValidationError(
                "Analytics assignment violates the reviewed metadata contract"
            ) from exc
        return contract

    def _record_revision(
        self,
        assignment: AnalyticsAssignment,
        contract: AnalyticsAssignmentV1,
        recorded_at: datetime,
    ) -> None:
        self.session.add(
            AnalyticsAssignmentRevision(
                assignment_id=assignment.assignment_id,
                version=assignment.version_id,
                snapshot=contract.model_dump(mode="json"),
                actor_id=assignment.last_actor_id,
                reason=assignment.last_change_reason,
                recorded_at=recorded_at,
            )
        )

    def _queue_deployment_event(
        self,
        assignment: AnalyticsAssignment,
        *,
        previous: DeploymentTargetV1 | None,
        current: DeploymentTargetV1,
        occurred_at: datetime,
    ) -> None:
        event = ModelDeploymentChangedV1(
            event_id=f"evt_{uuid4().hex}",
            stream_id=assignment.stream_id,
            camera_id=assignment.camera_id,
            partition_key=assignment.stream_id,
            occurred_at=occurred_at,
            payload=ModelDeploymentPayloadV1(
                assignment_id=assignment.assignment_id,
                department=assignment.department,
                stream_id=assignment.stream_id,
                camera_id=assignment.camera_id,
                capability=assignment.capability,
                previous=previous,
                current=current,
                lifecycle_state="blocked",
                reason_code="owner_gates_pending",
                actor_id=assignment.last_actor_id,
                change_reason=assignment.last_change_reason,
                approval_record_id=assignment.approval_record_id,
                effective_at=occurred_at,
            ),
        )
        canonical_contract_json(event)
        self.session.add(
            StreamEventOutbox(
                event_id=event.event_id,
                event_type=event.event_type,
                schema_version=event.schema_version,
                stream_id=event.stream_id,
                camera_id=event.camera_id,
                occurred_at=event.occurred_at,
                payload=event.payload.model_dump(mode="json"),
            )
        )

    def _record_failure(
        self,
        principal: Principal,
        action: str,
        target_id: str,
        reason: str,
        error: Exception,
        request_id: str | None,
    ) -> None:
        try:
            with self.session.begin():
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action=action,
                    target_type="analytics_assignment",
                    target_id=target_id,
                    source="hcam.api",
                    reason=_safe_audit_reason(reason),
                    outcome="failure",
                    context={"error_type": type(error).__name__},
                    request_id=request_id,
                )
        except SQLAlchemyError:
            return
