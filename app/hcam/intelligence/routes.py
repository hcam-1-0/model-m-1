from __future__ import annotations

import re
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from hcam.database import get_session
from hcam.intelligence.contracts import AlertAggregateV1, CorrelationHypothesisV1
from hcam.intelligence.alerts.contracts import AlertAggregateV2
from hcam.intelligence.correlation.contracts import (
    CorrelationHypothesisV2,
    HypothesisRevisionV1,
)
from hcam.intelligence.repository import IntelligenceRepository
from hcam.intelligence.schemas import (
    AlertListResponse,
    CorrelationHypothesisListResponse,
    CorrelationGraphResponse,
    CorrelationProjectionResponse,
    CorrelationRevisionListResponse,
    CorrelationRunListResponse,
    CorrelationRunResponse,
    IntelligenceHealthResponse,
    IntelligenceRuleCreate,
    IntelligenceRuleListResponse,
    IntelligenceRuleResponse,
    IntelligenceRuleStatusPatch,
    InvestigationTimelineListResponse,
    InvestigationTimelineResponse,
    ReferenceProviderCreate,
    ReferenceProviderListResponse,
    ReferenceProviderResponse,
    P42CompilationResponse,
    P42CompilePreview,
    P42EvaluationListResponse,
    P42RuleCreate,
    P42RuleResponse,
    P42RuleVersionListResponse,
    P42ShadowComparisonListResponse,
)
from hcam.intelligence.service import (
    IntelligenceConflictError,
    IntelligenceControlService,
    IntelligenceDisabledError,
    IntelligenceNotFoundError,
    IntelligencePreconditionError,
    IntelligenceValidationError,
    provider_response,
    rule_response,
)
from hcam.intelligence.rules.contracts import (
    RuleEvaluationV1,
    RuleShadowComparisonV1,
)
from hcam.intelligence.rules.persistence import (
    RuleConflictError,
    RuleControlDisabledError,
    RuleControlError,
    RuleControlService,
    RuleNotFoundError,
    RulePreconditionError,
    compilation_response,
    p42_rule_response,
)
from hcam.observability import request_id_from_scope
from hcam.security.auth import (
    INTELLIGENCE_APPROVER,
    INTELLIGENCE_EDITOR,
    INTELLIGENCE_REVIEWER,
    INTELLIGENCE_VIEWER,
    PLATFORM_ADMIN,
    Principal,
    RoleGuard,
)


router = APIRouter(tags=["intelligence-control-plane"])
SessionDependency = Annotated[Session, Depends(get_session)]
ViewerPrincipal = Annotated[
    Principal,
    Depends(
        RoleGuard(
            INTELLIGENCE_VIEWER,
            INTELLIGENCE_EDITOR,
            INTELLIGENCE_REVIEWER,
            INTELLIGENCE_APPROVER,
            PLATFORM_ADMIN,
        )
    ),
]
EditorPrincipal = Annotated[
    Principal,
    Depends(RoleGuard(INTELLIGENCE_EDITOR, INTELLIGENCE_APPROVER, PLATFORM_ADMIN)),
]
ApproverPrincipal = Annotated[
    Principal, Depends(RoleGuard(INTELLIGENCE_APPROVER, PLATFORM_ADMIN))
]
ReasonHeader = Annotated[
    str,
    Header(alias="X-HCAM-Reason", min_length=8, max_length=1000, pattern=r".*\S.*"),
]
_ETAG_PATTERN = re.compile(r'^"([1-9][0-9]*)"$')


def _etag(version: int) -> str:
    return f'"{version}"'


def _expected_version(value: str | None) -> int:
    if value is None:
        raise HTTPException(428, "If-Match resource version is required")
    match = _ETAG_PATTERN.fullmatch(value.strip())
    if match is None:
        raise HTTPException(400, "If-Match must contain a resource version ETag")
    return int(match.group(1))


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def _raise_error(error: Exception) -> None:
    if isinstance(error, RuleNotFoundError):
        raise HTTPException(404, "Generated rule was not found") from error
    if isinstance(error, RulePreconditionError):
        raise HTTPException(
            412, "Generated rule resource version does not match"
        ) from error
    if isinstance(error, RuleConflictError):
        raise HTTPException(409, "Generated rule transition was rejected") from error
    if isinstance(error, RuleControlDisabledError):
        raise HTTPException(
            503, "P4.2 generated rule control plane is disabled"
        ) from error
    if isinstance(error, RuleControlError):
        raise HTTPException(422, "Generated rule request was rejected") from error
    if isinstance(error, IntelligenceNotFoundError):
        raise HTTPException(404, "Intelligence resource not found") from error
    if isinstance(error, IntelligencePreconditionError):
        raise HTTPException(
            412, "Intelligence resource version does not match"
        ) from error
    if isinstance(error, IntelligenceConflictError):
        raise HTTPException(
            409, "Intelligence state transition was rejected"
        ) from error
    if isinstance(error, IntelligenceDisabledError):
        raise HTTPException(503, "P4.0 generated control plane is disabled") from error
    if isinstance(error, (IntelligenceValidationError, ValueError)):
        raise HTTPException(422, "Intelligence request was rejected") from error
    raise error


def _service(request: Request, session: Session) -> IntelligenceControlService:
    return IntelligenceControlService(
        session,
        enabled=request.app.state.settings.intelligence_generated_control_plane_enabled,
    )


def _p42_service(request: Request, session: Session) -> RuleControlService:
    return RuleControlService(
        session,
        enabled=request.app.state.settings.intelligence_generated_rule_evaluation_enabled,
    )


@router.get("/intelligence-health", response_model=IntelligenceHealthResponse)
def intelligence_health(
    request: Request, response: Response
) -> IntelligenceHealthResponse:
    _no_store(response)
    return IntelligenceHealthResponse(
        control_plane_enabled=bool(
            request.app.state.settings.intelligence_generated_control_plane_enabled
        )
    )


@router.post(
    "/streams/{stream_id}/intelligence-rules",
    response_model=IntelligenceRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    stream_id: str,
    payload: IntelligenceRuleCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> IntelligenceRuleResponse:
    try:
        row = _service(request, session).create_rule(
            stream_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.version_id)
    response.headers["Location"] = f"/intelligence-rules/{row.rule_record_id}"
    _no_store(response)
    return rule_response(row)


@router.post(
    "/intelligence-rules/compile-preview",
    response_model=P42CompilationResponse,
)
def preview_p42_rule(
    payload: P42CompilePreview,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> P42CompilationResponse:
    if not principal.can_access_department(payload.document.department):
        raise HTTPException(404, "Generated rule scope was not found")
    try:
        compiled = _p42_service(request, session).preview(payload.document)
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    _no_store(response)
    return P42CompilationResponse.model_validate(
        compiled.compilation.model_dump(mode="json")
    )


@router.post(
    "/intelligence-rules",
    response_model=P42RuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_p42_rule(
    payload: P42RuleCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> P42RuleResponse:
    try:
        row = _p42_service(request, session).create(
            payload.document,
            payload.scope_stream_ids,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.version_id)
    response.headers["Location"] = f"/intelligence-rules/{row.rule_record_id}"
    _no_store(response)
    return P42RuleResponse.model_validate(p42_rule_response(row))


@router.get("/intelligence-rules", response_model=IntelligenceRuleListResponse)
def list_rules(
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    stream_id: Annotated[str | None, Query(max_length=64)] = None,
    rule_status: Annotated[str | None, Query(alias="status", max_length=16)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> IntelligenceRuleListResponse:
    rows, total = IntelligenceRepository(session).list_rules(
        principal,
        stream_id=stream_id,
        status=rule_status,
        limit=limit,
        offset=offset,
    )
    _no_store(response)
    return IntelligenceRuleListResponse(
        items=[rule_response(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/intelligence-rules/{record_id}",
    response_model=IntelligenceRuleResponse | P42RuleResponse,
)
def get_rule(
    record_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> IntelligenceRuleResponse | P42RuleResponse:
    row = IntelligenceRepository(session).get_rule(record_id, principal)
    if row is None:
        raise HTTPException(404, "Intelligence resource not found")
    response.headers["ETag"] = _etag(row.version_id)
    _no_store(response)
    return rule_response(row)


@router.get(
    "/intelligence-rules/{record_id}/versions",
    response_model=P42RuleVersionListResponse,
)
def list_p42_rule_versions(
    record_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> P42RuleVersionListResponse:
    try:
        rows = RuleControlService(session, enabled=True).list_versions(
            record_id, principal
        )
    except RuntimeError as exc:
        _raise_error(exc)
        raise
    _no_store(response)
    items = [P42RuleResponse.model_validate(p42_rule_response(row)) for row in rows]
    return P42RuleVersionListResponse(items=items, total=len(items))


@router.get(
    "/intelligence-rule-compilations/{compilation_id}",
    response_model=P42CompilationResponse,
)
def get_p42_compilation(
    compilation_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> P42CompilationResponse:
    row = RuleControlService(session, enabled=True).get_compilation(
        compilation_id, principal
    )
    if row is None:
        raise HTTPException(404, "Generated rule compilation was not found")
    _no_store(response)
    return P42CompilationResponse.model_validate(compilation_response(row))


def _transition_p42(
    record_id: str,
    target: str,
    request: Request,
    response: Response,
    session: Session,
    principal: Principal,
    reason: str,
    if_match: str | None,
) -> P42RuleResponse:
    try:
        row = _p42_service(request, session).transition(
            record_id,
            target,
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.version_id)
    _no_store(response)
    return P42RuleResponse.model_validate(p42_rule_response(row))


@router.post("/intelligence-rules/{record_id}/validate", response_model=P42RuleResponse)
def validate_p42_rule(
    record_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> P42RuleResponse:
    return _transition_p42(
        record_id, "validated", request, response, session, principal, reason, if_match
    )


@router.post("/intelligence-rules/{record_id}/approve", response_model=P42RuleResponse)
def approve_p42_rule(
    record_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ApproverPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> P42RuleResponse:
    return _transition_p42(
        record_id, "approved", request, response, session, principal, reason, if_match
    )


@router.post(
    "/intelligence-rules/{record_id}/mark-shadow-eligible",
    response_model=P42RuleResponse,
)
def shadow_p42_rule(
    record_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ApproverPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> P42RuleResponse:
    return _transition_p42(
        record_id, "shadow", request, response, session, principal, reason, if_match
    )


@router.post("/intelligence-rules/{record_id}/suspend", response_model=P42RuleResponse)
def suspend_p42_rule(
    record_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> P42RuleResponse:
    return _transition_p42(
        record_id, "suspended", request, response, session, principal, reason, if_match
    )


@router.post("/intelligence-rules/{record_id}/retire", response_model=P42RuleResponse)
def retire_p42_rule(
    record_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> P42RuleResponse:
    return _transition_p42(
        record_id, "retired", request, response, session, principal, reason, if_match
    )


@router.get(
    "/intelligence-rules/{record_id}/evaluations",
    response_model=P42EvaluationListResponse,
)
def list_p42_evaluations(
    record_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> P42EvaluationListResponse:
    try:
        rows, total = RuleControlService(session, enabled=True).list_evaluations(
            record_id, principal, limit=limit, offset=offset
        )
    except RuntimeError as exc:
        _raise_error(exc)
        raise
    _no_store(response)
    return P42EvaluationListResponse(
        items=[RuleEvaluationV1.model_validate(row.snapshot) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/intelligence-rules/{record_id}/shadow-comparisons",
    response_model=P42ShadowComparisonListResponse,
)
def list_p42_shadow_comparisons(
    record_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> P42ShadowComparisonListResponse:
    try:
        rows, total = RuleControlService(session, enabled=True).list_shadow_comparisons(
            record_id, principal, limit=limit, offset=offset
        )
    except RuntimeError as exc:
        _raise_error(exc)
        raise
    _no_store(response)
    return P42ShadowComparisonListResponse(
        items=[
            RuleShadowComparisonV1.model_validate(
                {
                    "comparison_id": row.comparison_id,
                    "department": row.department,
                    "candidate_compilation_id": row.candidate_compilation_id,
                    "baseline_compilation_id": row.baseline_compilation_id,
                    "candidate_matches": row.candidate_matches,
                    "baseline_matches": row.baseline_matches,
                    "disagreement_count": row.disagreement_count,
                    "comparison_digest": row.comparison_digest,
                    "generated_only": True,
                    "operational": False,
                }
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/intelligence-rules/{record_id}", response_model=IntelligenceRuleResponse
)
def update_rule(
    record_id: str,
    payload: IntelligenceRuleStatusPatch,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> IntelligenceRuleResponse:
    try:
        row = _service(request, session).update_rule_status(
            record_id,
            payload.status,
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.version_id)
    _no_store(response)
    return rule_response(row)


@router.post(
    "/reference-providers",
    response_model=ReferenceProviderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_provider(
    payload: ReferenceProviderCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> ReferenceProviderResponse:
    try:
        row = _service(request, session).create_provider(
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.version_id)
    response.headers["Location"] = f"/reference-providers/{row.provider_id}"
    _no_store(response)
    return provider_response(row)


@router.get("/reference-providers", response_model=ReferenceProviderListResponse)
def list_providers(
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReferenceProviderListResponse:
    rows, total = IntelligenceRepository(session).list_providers(
        principal, limit=limit, offset=offset
    )
    _no_store(response)
    return ReferenceProviderListResponse(
        items=[provider_response(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/reference-providers/{provider_id}", response_model=ReferenceProviderResponse
)
def get_provider(
    provider_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> ReferenceProviderResponse:
    row = IntelligenceRepository(session).get_provider(provider_id, principal)
    if row is None:
        raise HTTPException(404, "Intelligence resource not found")
    response.headers["ETag"] = _etag(row.version_id)
    _no_store(response)
    return provider_response(row)


@router.get("/correlation-hypotheses", response_model=CorrelationHypothesisListResponse)
def list_hypotheses(
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CorrelationHypothesisListResponse:
    rows, total = IntelligenceRepository(session).list_hypotheses(
        principal, limit=limit, offset=offset
    )
    _no_store(response)
    return CorrelationHypothesisListResponse(
        items=[
            (
                CorrelationHypothesisV2.model_validate(row.payload)
                if row.payload.get("contract_type")
                == "hcam.intelligence.correlation-hypothesis.v2"
                else CorrelationHypothesisV1.model_validate(row.payload)
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


def _run_response(row) -> CorrelationRunResponse:
    return CorrelationRunResponse(
        run_id=row.run_id,
        department=row.department,
        status=row.status,
        execution_scope=row.execution_scope,
        reason_code=row.reason_code,
        profile_id=row.profile_id,
        profile_version=row.profile_version,
        result_digest=row.result_digest,
        replay_binding=row.replay_binding,
        input_count=row.input_count,
        accepted_count=row.accepted_count,
        duplicate_count=row.duplicate_count,
        rejected_count=row.rejected_count,
        watermark_at=row.watermark_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/correlation-runs", response_model=CorrelationRunListResponse)
def list_correlation_runs(
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CorrelationRunListResponse:
    rows, total = IntelligenceRepository(session).list_runs(
        principal, limit=limit, offset=offset
    )
    _no_store(response)
    return CorrelationRunListResponse(
        items=[_run_response(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/correlation-runs/{run_id}", response_model=CorrelationRunResponse)
def get_correlation_run(
    run_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> CorrelationRunResponse:
    row = IntelligenceRepository(session).get_run(run_id, principal)
    if row is None:
        raise HTTPException(404, "Intelligence resource not found")
    _no_store(response)
    return _run_response(row)


def _p41_hypothesis(hypothesis_id: str, session: Session, principal: Principal):
    row = IntelligenceRepository(session).get_hypothesis(hypothesis_id, principal)
    if row is None or row.payload.get("contract_type") != (
        "hcam.intelligence.correlation-hypothesis.v2"
    ):
        raise HTTPException(404, "Intelligence resource not found")
    return CorrelationHypothesisV2.model_validate(row.payload)


@router.get(
    "/correlation-hypotheses/{hypothesis_id}/graph",
    response_model=CorrelationGraphResponse,
)
def get_correlation_graph(
    hypothesis_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> CorrelationGraphResponse:
    hypothesis = _p41_hypothesis(hypothesis_id, session, principal)
    _no_store(response)
    return CorrelationGraphResponse(
        hypothesis_id=hypothesis.hypothesis_id,
        graph=hypothesis.graph,
        graph_digest=hypothesis.graph_digest,
    )


@router.get(
    "/correlation-hypotheses/{hypothesis_id}/projection",
    response_model=CorrelationProjectionResponse,
)
def get_correlation_projection(
    hypothesis_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> CorrelationProjectionResponse:
    hypothesis = _p41_hypothesis(hypothesis_id, session, principal)
    _no_store(response)
    return CorrelationProjectionResponse(projection=hypothesis.flat_projection)


@router.get(
    "/correlation-hypotheses/{hypothesis_id}/revisions",
    response_model=CorrelationRevisionListResponse,
)
def list_correlation_revisions(
    hypothesis_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CorrelationRevisionListResponse:
    if IntelligenceRepository(session).get_hypothesis(hypothesis_id, principal) is None:
        raise HTTPException(404, "Intelligence resource not found")
    rows, total = IntelligenceRepository(session).list_hypothesis_revisions(
        hypothesis_id,
        principal,
        limit=limit,
        offset=offset,
    )
    _no_store(response)
    return CorrelationRevisionListResponse(
        items=[
            HypothesisRevisionV1(
                revision_id=row.revision_id,
                hypothesis_id=row.hypothesis_id,
                revision=row.revision,
                previous_state=row.previous_state,
                new_state=row.new_state,
                reason_code=row.reason_code,
                snapshot_digest=row.snapshot_digest,
                recorded_at=row.recorded_at,
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AlertListResponse:
    rows, total = IntelligenceRepository(session).list_alerts(
        principal, limit=limit, offset=offset
    )
    _no_store(response)
    return AlertListResponse(
        items=[
            (
                AlertAggregateV2.model_validate(row.payload)
                if row.payload.get("contract_type") == "hcam.intelligence.alert.v2"
                else AlertAggregateV1.model_validate(row.payload)
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/investigation-timelines", response_model=InvestigationTimelineListResponse
)
def list_timelines(
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> InvestigationTimelineListResponse:
    rows, total = IntelligenceRepository(session).list_timelines(
        principal, limit=limit, offset=offset
    )
    _no_store(response)
    return InvestigationTimelineListResponse(
        items=[
            InvestigationTimelineResponse(
                timeline_id=row.timeline_id,
                record_version=row.version_id,
                department=row.department,
                status=row.status,
                title_code=row.title_code,
                owner_id=row.owner_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
