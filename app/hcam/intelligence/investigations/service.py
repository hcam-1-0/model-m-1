from __future__ import annotations

from datetime import datetime
from functools import wraps
from typing import Any, Callable, Literal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from hcam.intelligence.investigations.chronology import reconstruct
from hcam.intelligence.investigations.contracts import (
    CorrectionCommandV1,
    DeletionIntentV1,
    DeletionReceiptV1,
    EvidenceReferenceV2,
    ExportManifestV1,
    HoldOverlayV1,
    ImpactSetV1,
    IntegrityAssessmentV1,
    InvestigationTimelineV2,
    ProvenanceBundleV1,
    ReconstructionV1,
    RelationshipRevisionV1,
    RetentionEvaluationV1,
    RetentionPolicyReferenceV1,
    ReviewDecisionV1,
    TimelineCreateCommandV2,
    TimelineEntryV2,
)
from hcam.intelligence.investigations.corrections import build_impact_set
from hcam.intelligence.investigations.deletion import simulate_deletion
from hcam.intelligence.investigations.exports import build_reference_manifest
from hcam.intelligence.investigations.persistence import (
    InvestigationRepository,
    timeline_contract,
)
from hcam.intelligence.investigations.provenance import validate_graph
from hcam.intelligence.investigations.relationships import validate_merge_graph
from hcam.intelligence.investigations.retention import evaluate_retention
from hcam.intelligence.investigations.runtime import GeneratedInvestigationRuntime
from hcam.intelligence.row_security import apply_department_scope
from hcam.security.auth import Principal


class InvestigationError(RuntimeError):
    reason_code = "investigation.request_rejected"


class InvestigationDisabledError(InvestigationError):
    reason_code = "investigation.runtime_disabled"


class InvestigationNotFoundError(InvestigationError):
    reason_code = "investigation.resource_not_found"


class InvestigationPreconditionError(InvestigationError):
    reason_code = "investigation.precondition_failed"


def _translate_integrity_errors(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def guarded(self: InvestigationService, *args: Any, **kwargs: Any) -> Any:
        try:
            return method(self, *args, **kwargs)
        except IntegrityError as exc:
            self.session.rollback()
            raise InvestigationPreconditionError("investigation write conflicted") from exc

    return guarded


class InvestigationService:
    def __init__(self, session: Session, *, enabled: bool, environment: str) -> None:
        self.session = session
        self.runtime = GeneratedInvestigationRuntime(
            enabled=enabled,
            environment=environment,
        )
        self.repository = InvestigationRepository(session)

    def _authorize(self, principal: Principal, department: str | None = None) -> None:
        try:
            self.runtime.require_enabled()
        except RuntimeError as exc:
            raise InvestigationDisabledError(str(exc)) from exc
        apply_department_scope(self.session, principal)
        if department is not None and not principal.can_access_department(department):
            raise InvestigationNotFoundError("investigation resource was not found")

    @staticmethod
    def _actor(expected: str, principal: Principal) -> None:
        if expected != principal.actor_id:
            raise InvestigationError("attributed actor does not match authenticated actor")

    @_translate_integrity_errors
    def create_timeline(
        self, command: TimelineCreateCommandV2, *, principal: Principal
    ) -> tuple[InvestigationTimelineV2, bool]:
        self._authorize(principal, command.department)
        self._actor(command.actor_id, principal)
        try:
            result = self.repository.create_timeline(command)
            self.session.commit()
            return result
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    def timelines(self, *, principal: Principal) -> list[InvestigationTimelineV2]:
        self._authorize(principal)
        return self.repository.timelines(principal.allowed_departments)

    def timeline(self, timeline_id: str, *, principal: Principal) -> InvestigationTimelineV2:
        self._authorize(principal)
        row = self.repository.timeline(timeline_id)
        if row is None or not principal.can_access_department(row.department):
            raise InvestigationNotFoundError("timeline was not found")
        return timeline_contract(row)

    @_translate_integrity_errors
    def append_entry(
        self,
        entry: TimelineEntryV2,
        *,
        expected_revision: int,
        principal: Principal,
    ) -> tuple[InvestigationTimelineV2, bool]:
        self._authorize(principal, entry.department)
        self._actor(entry.actor_id, principal)
        try:
            result = self.repository.append_entry(
                entry,
                expected_revision=expected_revision,
            )
            self.session.commit()
            return result
        except KeyError as exc:
            self.session.rollback()
            raise InvestigationNotFoundError(str(exc)) from exc
        except ValueError as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    def reconstruct(
        self,
        timeline_id: str,
        *,
        through_revision: int,
        view: Literal["record_sequence", "event_time"],
        principal: Principal,
    ) -> ReconstructionV1:
        timeline = self.timeline(timeline_id, principal=principal)
        if through_revision > timeline.revision:
            raise InvestigationPreconditionError("requested revision is not available")
        entries = self.repository.entries(timeline_id)
        if not entries:
            raise InvestigationPreconditionError("timeline has no reconstructable entries")
        return reconstruct(entries, through_revision=through_revision, view=view)

    @_translate_integrity_errors
    def add_evidence(
        self, reference: EvidenceReferenceV2, *, principal: Principal
    ) -> tuple[EvidenceReferenceV2, bool]:
        self._authorize(principal, reference.department)
        self._actor(reference.registered_by, principal)
        try:
            result = self.repository.add_evidence(reference)
            self.session.commit()
            return result
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    def evidence(
        self, timeline_id: str, *, principal: Principal
    ) -> list[EvidenceReferenceV2]:
        self.timeline(timeline_id, principal=principal)
        return self.repository.evidence_for_timeline(timeline_id)

    @_translate_integrity_errors
    def add_integrity(
        self, assessment: IntegrityAssessmentV1, *, principal: Principal
    ) -> IntegrityAssessmentV1:
        self._authorize(principal, assessment.department)
        self._actor(assessment.assessed_by, principal)
        try:
            result = self.repository.add_integrity(assessment)
            self.session.commit()
            return result
        except ValueError as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    @_translate_integrity_errors
    def add_provenance(
        self,
        bundle: ProvenanceBundleV1,
        *,
        recorded_at: datetime,
        principal: Principal,
    ) -> ProvenanceBundleV1:
        self._authorize(principal, bundle.department)
        if validate_graph(bundle) != bundle.bundle_digest:
            raise InvestigationPreconditionError("provenance bundle digest does not match")
        try:
            result = self.repository.add_provenance(bundle, recorded_at=recorded_at)
            self.session.commit()
            return result
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    @_translate_integrity_errors
    def add_correction(
        self,
        correction: CorrectionCommandV1,
        *,
        dependencies: dict[str, list[tuple[str, str]]],
        principal: Principal,
    ) -> tuple[CorrectionCommandV1, ImpactSetV1, bool]:
        self._authorize(principal, correction.department)
        self._actor(correction.actor_id, principal)
        impacts = build_impact_set(
            correction,
            dependencies,
            recorded_at=correction.recorded_at,
        )
        try:
            saved, reused = self.repository.add_correction(correction, impacts.impacts)
            self.session.commit()
            return saved, impacts, reused
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    @_translate_integrity_errors
    def add_review(
        self, review: ReviewDecisionV1, *, principal: Principal
    ) -> ReviewDecisionV1:
        self._authorize(principal, review.department)
        self._actor(review.reviewer_id, principal)
        try:
            result, reused = self.repository.add_review(review)
            if reused:
                self.session.commit()
                return result
            timeline = self.repository.timeline(review.timeline_id)
            if timeline is None:
                raise KeyError("timeline was not found")
            self.repository.update_timeline_state(
                review.timeline_id,
                review.department,
                expected_revision=timeline.revision,
                actor_id=principal.actor_id,
                reason=review.reason,
                recorded_at=review.recorded_at,
                disposition=review.disposition,
            )
            self.session.commit()
            return result
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    @_translate_integrity_errors
    def add_relationship(
        self, relation: RelationshipRevisionV1, *, principal: Principal
    ) -> RelationshipRevisionV1:
        self._authorize(principal, relation.department)
        self._actor(relation.actor_id, principal)
        existing = self.repository.relationships(relation.department)
        validate_merge_graph([*existing, relation])
        try:
            result, _ = self.repository.add_relationship(relation)
            self.session.commit()
            return result
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    @_translate_integrity_errors
    def revise_lifecycle(
        self,
        timeline_id: str,
        *,
        department: str,
        lifecycle: Literal["closed", "reopened"],
        expected_revision: int,
        reason: str,
        recorded_at: datetime,
        principal: Principal,
    ) -> InvestigationTimelineV2:
        self._authorize(principal, department)
        current = self.timeline(timeline_id, principal=principal)
        if lifecycle == "reopened" and current.lifecycle != "closed":
            raise InvestigationPreconditionError("only closed timelines can be reopened")
        if lifecycle == "closed" and current.lifecycle == "closed":
            raise InvestigationPreconditionError("timeline is already closed")
        try:
            result = self.repository.update_timeline_state(
                timeline_id,
                department,
                expected_revision=expected_revision,
                actor_id=principal.actor_id,
                reason=reason,
                recorded_at=recorded_at,
                lifecycle=lifecycle,
            )
            self.session.commit()
            return result
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    @_translate_integrity_errors
    def add_hold(self, hold: HoldOverlayV1, *, principal: Principal) -> HoldOverlayV1:
        self._authorize(principal, hold.department)
        try:
            result = self.repository.add_hold(hold)
            self.session.commit()
            return result
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    @_translate_integrity_errors
    def evaluate_retention(
        self,
        *,
        timeline_id: str,
        department: str,
        policy: RetentionPolicyReferenceV1,
        policy_available: bool,
        evaluated_at: datetime,
        principal: Principal,
    ) -> RetentionEvaluationV1:
        self._authorize(principal, department)
        self.timeline(timeline_id, principal=principal)
        evaluation = evaluate_retention(
            timeline_id=timeline_id,
            department=department,
            policy=policy,
            holds=self.repository.holds(timeline_id),
            policy_available=policy_available,
            evaluated_at=evaluated_at,
        )
        try:
            self.repository.add_retention(evaluation)
            self.session.commit()
            return evaluation
        except (KeyError, ValueError) as exc:
            self.session.rollback()
            raise InvestigationPreconditionError(str(exc)) from exc

    @_translate_integrity_errors
    def simulate_deletion(
        self,
        intent: DeletionIntentV1,
        *,
        residuals: dict[str, list[str]],
        principal: Principal,
    ) -> list[DeletionReceiptV1]:
        self._authorize(principal, intent.department)
        self._actor(intent.requested_by, principal)
        evaluation = self.repository.retention(intent.policy_evaluation_id)
        if evaluation is None:
            raise InvestigationNotFoundError("retention evaluation was not found")
        receipts = simulate_deletion(
            intent,
            evaluation,
            residuals=residuals,
            recorded_at=intent.requested_at,
        )
        self.repository.add_deletion_receipts(receipts)
        self.session.commit()
        return receipts

    @_translate_integrity_errors
    def preview_export(
        self,
        *,
        timeline_id: str,
        department: str,
        purpose_code: str,
        recipient_class: str,
        policy_ref: str,
        allowed_reference_ids: set[str],
        unresolved_reference_ids: set[str],
        prepared_at: datetime,
        principal: Principal,
    ) -> ExportManifestV1:
        self._authorize(principal, department)
        timeline = self.timeline(timeline_id, principal=principal)
        if timeline.purpose_code != purpose_code:
            raise InvestigationPreconditionError("export purpose differs from timeline")
        references = self.repository.evidence_for_timeline(timeline_id)
        known = {item.reference_id for item in references}
        if not allowed_reference_ids <= known or not unresolved_reference_ids <= known:
            raise InvestigationPreconditionError("export selection contains unknown references")
        manifest = build_reference_manifest(
            timeline_id=timeline_id,
            department=department,
            purpose_code=purpose_code,
            recipient_class=recipient_class,
            policy_ref=policy_ref,
            references=references,
            allowed_reference_ids=allowed_reference_ids,
            unresolved_reference_ids=unresolved_reference_ids,
            prepared_by=principal.actor_id,
            prepared_at=prepared_at,
        )
        self.repository.add_export(manifest)
        self.session.commit()
        return manifest
