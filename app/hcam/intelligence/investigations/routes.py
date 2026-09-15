from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from hcam.database import get_session
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
from hcam.intelligence.investigations.service import (
    InvestigationDisabledError,
    InvestigationError,
    InvestigationNotFoundError,
    InvestigationPreconditionError,
    InvestigationService,
)
from hcam.security.auth import (
    INVESTIGATION_CORRECTION_CREATE_GENERATED,
    INVESTIGATION_EVIDENCE_ASSESS_GENERATED,
    INVESTIGATION_EVIDENCE_READ,
    INVESTIGATION_EVIDENCE_REFERENCE_CREATE_GENERATED,
    INVESTIGATION_EXPORT_PREVIEW_GENERATED,
    INVESTIGATION_READ,
    INVESTIGATION_RELATIONSHIP_MANAGE_GENERATED,
    INVESTIGATION_RETENTION_EVALUATE_GENERATED,
    INVESTIGATION_REVIEW_CREATE_GENERATED,
    INVESTIGATION_WRITE_GENERATED,
    PLATFORM_ADMIN,
    Principal,
    RoleGuard,
)


router = APIRouter(prefix="/investigations", tags=["generated-investigations"])
SessionDependency = Annotated[Session, Depends(get_session)]
Reader = Annotated[Principal, Depends(RoleGuard(INVESTIGATION_READ, PLATFORM_ADMIN))]
Writer = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_WRITE_GENERATED, PLATFORM_ADMIN)),
]
EvidenceReader = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_EVIDENCE_READ, PLATFORM_ADMIN)),
]
EvidenceWriter = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_EVIDENCE_REFERENCE_CREATE_GENERATED, PLATFORM_ADMIN)),
]
IntegrityAssessor = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_EVIDENCE_ASSESS_GENERATED, PLATFORM_ADMIN)),
]
Corrector = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_CORRECTION_CREATE_GENERATED, PLATFORM_ADMIN)),
]
Reviewer = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_REVIEW_CREATE_GENERATED, PLATFORM_ADMIN)),
]
RelationshipManager = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_RELATIONSHIP_MANAGE_GENERATED, PLATFORM_ADMIN)),
]
RetentionEvaluator = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_RETENTION_EVALUATE_GENERATED, PLATFORM_ADMIN)),
]
ExportPreparer = Annotated[
    Principal,
    Depends(RoleGuard(INVESTIGATION_EXPORT_PREVIEW_GENERATED, PLATFORM_ADMIN)),
]
ReasonHeader = Annotated[
    str,
    Header(alias="X-HCAM-Reason", min_length=8, max_length=2000, pattern=r".*\S.*"),
]
_ETAG = re.compile(r'^"([0-9]+)"$')


class TimelineListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[InvestigationTimelineV2]
    total: int


class TimelineMutationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timeline: InvestigationTimelineV2
    reused: bool


class EvidenceListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[EvidenceReferenceV2]
    total: int


class ProvenanceSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bundle: ProvenanceBundleV1
    recorded_at: datetime


class CorrectionSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    command: CorrectionCommandV1
    dependencies: dict[str, list[tuple[str, str]]] = Field(default_factory=dict, max_length=5000)


class CorrectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    correction: CorrectionCommandV1
    impact_set: ImpactSetV1
    reused: bool


class LifecycleMutation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    department: Annotated[str, Field(min_length=1, max_length=120)]
    lifecycle: Literal["closed", "reopened"]
    recorded_at: datetime


class RetentionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    department: Annotated[str, Field(min_length=1, max_length=120)]
    policy: RetentionPolicyReferenceV1
    policy_available: bool
    evaluated_at: datetime


class DeletionSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: DeletionIntentV1
    residuals: dict[str, list[str]] = Field(default_factory=dict, max_length=5000)


class DeletionSimulationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    receipts: list[DeletionReceiptV1]
    universal_deletion_proven: Literal[False] = False
    external_action_executed: Literal[False] = False


class ExportPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    department: Annotated[str, Field(min_length=1, max_length=120)]
    purpose_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{0,95}$")]
    recipient_class: Literal["generated.reviewer", "generated.records"]
    policy_ref: Annotated[str, Field(pattern=r"^ref_[0-9a-f]{32}$")]
    allowed_reference_ids: set[str] = Field(default_factory=set, max_length=10_000)
    unresolved_reference_ids: set[str] = Field(default_factory=set, max_length=10_000)
    prepared_at: datetime


def _service(request: Request, session: Session) -> InvestigationService:
    return InvestigationService(
        session,
        enabled=request.app.state.settings.intelligence_generated_investigations_enabled,
        environment=request.app.state.settings.environment,
    )


def _no_store(response: Response, version: int | None = None) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    if version is not None:
        response.headers["ETag"] = f'"{version}"'


def _expected_revision(value: str | None) -> int:
    match = _ETAG.fullmatch(value.strip()) if value is not None else None
    if match is None:
        raise HTTPException(428 if value is None else 400, "valid If-Match version required")
    return int(match.group(1))


def _raise(error: InvestigationError) -> None:
    if isinstance(error, InvestigationDisabledError):
        raise HTTPException(503, "generated investigation runtime is disabled") from error
    if isinstance(error, InvestigationNotFoundError):
        raise HTTPException(404, "investigation resource was not found") from error
    if isinstance(error, InvestigationPreconditionError):
        raise HTTPException(412, "investigation precondition failed") from error
    raise HTTPException(422, "generated investigation request was rejected") from error


@router.get("/health")
def health(request: Request, response: Response, principal: Reader) -> dict[str, object]:
    _ = principal
    _no_store(response)
    enabled = request.app.state.settings.intelligence_generated_investigations_enabled
    return {
        "status": "ready" if enabled else "disabled",
        "generated_only": True,
        "operational": False,
        "runtime_enabled": enabled,
        "source_resolution": False,
        "external_actions": False,
    }


@router.post("/timelines", response_model=TimelineMutationResponse, status_code=status.HTTP_201_CREATED)
def create_timeline(command: TimelineCreateCommandV2, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: Writer) -> TimelineMutationResponse:
    if command.reason != reason:
        raise HTTPException(422, "reason header and command reason must match")
    try:
        timeline, reused = _service(request, session).create_timeline(command, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response, timeline.revision)
    return TimelineMutationResponse(timeline=timeline, reused=reused)


@router.get("/timelines", response_model=TimelineListResponse)
def list_timelines(request: Request, response: Response, session: SessionDependency, principal: Reader) -> TimelineListResponse:
    try:
        items = _service(request, session).timelines(principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return TimelineListResponse(items=items, total=len(items))


@router.get("/timelines/{timeline_id}", response_model=InvestigationTimelineV2)
def get_timeline(timeline_id: str, request: Request, response: Response, session: SessionDependency, principal: Reader) -> InvestigationTimelineV2:
    try:
        result = _service(request, session).timeline(timeline_id, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response, result.revision)
    return result


@router.post("/timelines/{timeline_id}/entries", response_model=TimelineMutationResponse)
def append_entry(timeline_id: str, entry: TimelineEntryV2, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: Writer, if_match: Annotated[str | None, Header(alias="If-Match")] = None) -> TimelineMutationResponse:
    if entry.timeline_id != timeline_id or entry.reason != reason:
        raise HTTPException(422, "path, body, and reason header must agree")
    try:
        timeline, reused = _service(request, session).append_entry(entry, expected_revision=_expected_revision(if_match), principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response, timeline.revision)
    return TimelineMutationResponse(timeline=timeline, reused=reused)


@router.get("/timelines/{timeline_id}/reconstruction", response_model=ReconstructionV1)
def get_reconstruction(timeline_id: str, request: Request, response: Response, session: SessionDependency, principal: Reader, through_revision: Annotated[int, Query(ge=1)], view: Literal["record_sequence", "event_time"] = "record_sequence") -> ReconstructionV1:
    try:
        result = _service(request, session).reconstruct(timeline_id, through_revision=through_revision, view=view, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.post("/timelines/{timeline_id}/lifecycle", response_model=InvestigationTimelineV2)
def revise_lifecycle(timeline_id: str, mutation: LifecycleMutation, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: Writer, if_match: Annotated[str | None, Header(alias="If-Match")] = None) -> InvestigationTimelineV2:
    try:
        result = _service(request, session).revise_lifecycle(timeline_id, department=mutation.department, lifecycle=mutation.lifecycle, expected_revision=_expected_revision(if_match), reason=reason, recorded_at=mutation.recorded_at, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response, result.revision)
    return result


@router.post("/timelines/{timeline_id}/evidence", response_model=EvidenceReferenceV2, status_code=status.HTTP_201_CREATED)
def create_evidence(timeline_id: str, reference: EvidenceReferenceV2, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: EvidenceWriter) -> EvidenceReferenceV2:
    if reference.timeline_id != timeline_id or reference.reason != reason:
        raise HTTPException(422, "path, body, and reason header must agree")
    try:
        result, _reused = _service(request, session).add_evidence(reference, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.get("/timelines/{timeline_id}/evidence", response_model=EvidenceListResponse)
def list_evidence(timeline_id: str, request: Request, response: Response, session: SessionDependency, principal: EvidenceReader) -> EvidenceListResponse:
    try:
        items = _service(request, session).evidence(timeline_id, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return EvidenceListResponse(items=items, total=len(items))


@router.post("/timelines/{timeline_id}/integrity", response_model=IntegrityAssessmentV1, status_code=status.HTTP_201_CREATED)
def create_integrity(timeline_id: str, assessment: IntegrityAssessmentV1, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: IntegrityAssessor) -> IntegrityAssessmentV1:
    _ = reason
    if assessment.timeline_id != timeline_id:
        raise HTTPException(422, "timeline path and body must agree")
    try:
        result = _service(request, session).add_integrity(assessment, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.post("/timelines/{timeline_id}/provenance", response_model=ProvenanceBundleV1, status_code=status.HTTP_201_CREATED)
def create_provenance(timeline_id: str, submission: ProvenanceSubmission, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: EvidenceWriter) -> ProvenanceBundleV1:
    _ = reason
    if submission.bundle.timeline_id != timeline_id:
        raise HTTPException(422, "timeline path and body must agree")
    try:
        result = _service(request, session).add_provenance(submission.bundle, recorded_at=submission.recorded_at, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.post("/timelines/{timeline_id}/corrections", response_model=CorrectionResponse, status_code=status.HTTP_201_CREATED)
def create_correction(timeline_id: str, submission: CorrectionSubmission, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: Corrector) -> CorrectionResponse:
    if submission.command.timeline_id != timeline_id or submission.command.reason != reason:
        raise HTTPException(422, "path, body, and reason header must agree")
    try:
        correction, impact_set, reused = _service(request, session).add_correction(submission.command, dependencies=submission.dependencies, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return CorrectionResponse(correction=correction, impact_set=impact_set, reused=reused)


@router.post("/timelines/{timeline_id}/reviews", response_model=ReviewDecisionV1, status_code=status.HTTP_201_CREATED)
def create_review(timeline_id: str, review: ReviewDecisionV1, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: Reviewer) -> ReviewDecisionV1:
    if review.timeline_id != timeline_id or review.reason != reason:
        raise HTTPException(422, "path, body, and reason header must agree")
    try:
        result = _service(request, session).add_review(review, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.post("/relationships", response_model=RelationshipRevisionV1, status_code=status.HTTP_201_CREATED)
def create_relationship(relation: RelationshipRevisionV1, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: RelationshipManager) -> RelationshipRevisionV1:
    if relation.reason != reason:
        raise HTTPException(422, "reason header and body reason must agree")
    try:
        result = _service(request, session).add_relationship(relation, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.post("/timelines/{timeline_id}/holds", response_model=HoldOverlayV1, status_code=status.HTTP_201_CREATED)
def create_generated_hold(timeline_id: str, hold: HoldOverlayV1, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: RetentionEvaluator) -> HoldOverlayV1:
    _ = reason
    if hold.timeline_id != timeline_id:
        raise HTTPException(422, "timeline path and body must agree")
    try:
        result = _service(request, session).add_hold(hold, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.post("/timelines/{timeline_id}/retention-evaluations", response_model=RetentionEvaluationV1, status_code=status.HTTP_201_CREATED)
def create_retention_evaluation(timeline_id: str, body: RetentionRequest, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: RetentionEvaluator) -> RetentionEvaluationV1:
    _ = reason
    try:
        result = _service(request, session).evaluate_retention(timeline_id=timeline_id, department=body.department, policy=body.policy, policy_available=body.policy_available, evaluated_at=body.evaluated_at, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.post("/timelines/{timeline_id}/deletion-simulations", response_model=DeletionSimulationResponse)
def create_deletion_simulation(timeline_id: str, body: DeletionSimulationRequest, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: RetentionEvaluator) -> DeletionSimulationResponse:
    if body.intent.timeline_id != timeline_id or body.intent.reason != reason:
        raise HTTPException(422, "path, body, and reason header must agree")
    try:
        receipts = _service(request, session).simulate_deletion(body.intent, residuals=body.residuals, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return DeletionSimulationResponse(receipts=receipts)


@router.post("/timelines/{timeline_id}/export-previews", response_model=ExportManifestV1)
def create_export_preview(timeline_id: str, body: ExportPreviewRequest, reason: ReasonHeader, request: Request, response: Response, session: SessionDependency, principal: ExportPreparer) -> ExportManifestV1:
    _ = reason
    try:
        result = _service(request, session).preview_export(timeline_id=timeline_id, department=body.department, purpose_code=body.purpose_code, recipient_class=body.recipient_class, policy_ref=body.policy_ref, allowed_reference_ids=body.allowed_reference_ids, unresolved_reference_ids=body.unresolved_reference_ids, prepared_at=body.prepared_at, principal=principal)
    except InvestigationError as exc:
        _raise(exc)
    _no_store(response)
    return result
