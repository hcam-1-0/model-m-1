from __future__ import annotations

from dataclasses import asdict
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from hcam.database import get_session
from hcam.intelligence.alerts.contracts import (
    AlertAggregateV2,
    AlertLifecycleCommandV1,
    AlertLifecycleEventV2,
    AlertReviewDecisionV1,
    ReviewQuorumPolicyV1,
)
from hcam.intelligence.alerts.persistence import (
    AlertControlError,
    AlertPersistence,
    AlertPreconditionError,
)
from hcam.intelligence.alerts.service import problem_for
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


router = APIRouter(tags=["generated-alert-lifecycle"])
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
ReviewerPrincipal = Annotated[
    Principal,
    Depends(RoleGuard(INTELLIGENCE_REVIEWER, INTELLIGENCE_APPROVER, PLATFORM_ADMIN)),
]
ReasonHeader = Annotated[
    str,
    Header(alias="X-HCAM-Reason", min_length=8, max_length=2000, pattern=r".*\S.*"),
]
IfMatchHeader = Annotated[
    str,
    Header(alias="If-Match", pattern=r'^"[1-9][0-9]*"$'),
]


class AlertV2ListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[AlertAggregateV2]
    total: int
    limit: int
    offset: int


class LifecycleListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[AlertLifecycleEventV2]
    total: int
    limit: int
    offset: int


class ReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alert: AlertAggregateV2
    quorum_outcome: str


def _store(response: Response, version: int | None = None) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    if version is not None:
        response.headers["ETag"] = f'"{version}"'


def _service(request: Request, session: Session) -> AlertPersistence:
    return AlertPersistence(
        session,
        enabled=request.app.state.settings.intelligence_generated_alert_lifecycle_enabled,
        high_impact_quorum=(
            request.app.state.settings.intelligence_generated_high_impact_quorum
        ),
    )


def _raise(error: AlertControlError) -> NoReturn:
    problem = problem_for(error)
    raise _ProblemException(problem.status, asdict(problem))


class _ProblemException(Exception):
    def __init__(self, status_code: int, content: dict[str, object]) -> None:
        self.status_code = status_code
        self.content = content


async def problem_exception_handler(_request: Request, exc: _ProblemException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.content,
        media_type="application/problem+json",
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@router.get("/generated-alerts", response_model=AlertV2ListResponse)
def list_generated_alerts(
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AlertV2ListResponse:
    try:
        rows, total = _service(request, session).list(
            principal, limit=limit, offset=offset
        )
    except AlertControlError as exc:
        _raise(exc)
    _store(response)
    return AlertV2ListResponse(items=list(rows), total=total, limit=limit, offset=offset)


@router.get("/generated-alerts/{alert_id}", response_model=AlertAggregateV2)
def get_generated_alert(
    alert_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> AlertAggregateV2:
    try:
        alert = _service(request, session).get(alert_id, principal)
    except AlertControlError as exc:
        _raise(exc)
    _store(response, alert.version)
    return alert


@router.post("/generated-alerts/{alert_id}/lifecycle", response_model=AlertAggregateV2)
def transition_generated_alert(
    alert_id: str,
    command: AlertLifecycleCommandV1,
    reason: ReasonHeader,
    if_match: IfMatchHeader,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
) -> AlertAggregateV2:
    if command.reason != reason:
        raise _ProblemException(
            400,
            {
                "type": "urn:hcam:problem:reason_mismatch",
                "title": "Command reason does not match X-HCAM-Reason",
                "status": 400,
                "reason_code": "reason_mismatch",
            },
        )
    if int(if_match[1:-1]) != command.expected_version:
        _raise(AlertPreconditionError("If-Match does not match command version"))
    try:
        alert = _service(request, session).transition(
            alert_id,
            command,
            principal=principal,
            request_id=request_id_from_scope(request.scope),
        )
    except AlertControlError as exc:
        _raise(exc)
    _store(response, alert.version)
    return alert


@router.post("/generated-alerts/{alert_id}/reviews", response_model=ReviewResponse)
def review_generated_alert(
    alert_id: str,
    decision: AlertReviewDecisionV1,
    reason: ReasonHeader,
    if_match: IfMatchHeader,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ReviewerPrincipal,
) -> ReviewResponse:
    if decision.reason != reason:
        raise _ProblemException(
            400,
            {
                "type": "urn:hcam:problem:reason_mismatch",
                "title": "Review reason does not match X-HCAM-Reason",
                "status": 400,
                "reason_code": "reason_mismatch",
            },
        )
    try:
        alert, outcome = _service(request, session).review(
            alert_id,
            decision,
            expected_version=int(if_match[1:-1]),
            principal=principal,
            request_id=request_id_from_scope(request.scope),
        )
    except AlertControlError as exc:
        _raise(exc)
    _store(response, alert.version)
    return ReviewResponse(alert=alert, quorum_outcome=outcome)


@router.get(
    "/generated-alerts/{alert_id}/review-policy",
    response_model=ReviewQuorumPolicyV1,
)
def get_generated_alert_review_policy(
    alert_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> ReviewQuorumPolicyV1:
    try:
        policy = _service(request, session).get_review_policy(alert_id, principal)
    except AlertControlError as exc:
        _raise(exc)
    _store(response)
    return policy


@router.get(
    "/generated-alerts/{alert_id}/lifecycle",
    response_model=LifecycleListResponse,
)
def list_generated_alert_lifecycle(
    alert_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LifecycleListResponse:
    try:
        rows, total = _service(request, session).list_lifecycle(
            alert_id, principal, limit=limit, offset=offset
        )
    except AlertControlError as exc:
        _raise(exc)
    _store(response)
    return LifecycleListResponse(items=rows, total=total, limit=limit, offset=offset)
