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

from hcam.analytics.repository import (
    AnalyticsAssignmentFilters,
    AnalyticsAssignmentRepository,
    assignment_to_response,
)
from hcam.analytics.execution import GeneratedAnalyticsExecutionService
from hcam.analytics.schemas import (
    AnalyticsObservationListResponse,
    AnalyticsAssignmentCreate,
    AnalyticsAssignmentListResponse,
    AnalyticsAssignmentPatch,
    AnalyticsAssignmentResponse,
    AnalyticsAssignmentRevisionListResponse,
    GeneratedAnalyticsRunCreate,
    GeneratedAnalyticsRunResponse,
)
from hcam.analytics.service import (
    AnalyticsAssignmentConflictError,
    AnalyticsAssignmentNotFoundError,
    AnalyticsAssignmentPreconditionError,
    AnalyticsAssignmentService,
    AnalyticsAssignmentValidationError,
)
from hcam.database import get_session
from hcam.observability import request_id_from_scope
from hcam.security.auth import (
    CAMERA_EDITOR,
    CAMERA_VIEWER,
    PLATFORM_ADMIN,
    Principal,
    RoleGuard,
)


router = APIRouter(tags=["analytics-control-plane"])
SessionDependency = Annotated[Session, Depends(get_session)]
ViewerPrincipal = Annotated[
    Principal,
    Depends(RoleGuard(CAMERA_VIEWER, CAMERA_EDITOR, PLATFORM_ADMIN)),
]
EditorPrincipal = Annotated[
    Principal,
    Depends(RoleGuard(CAMERA_EDITOR, PLATFORM_ADMIN)),
]
ReasonHeader = Annotated[
    str,
    Header(alias="X-HCAM-Reason", min_length=8, max_length=500, pattern=r".*\S.*"),
]
_ETAG_PATTERN = re.compile(r'^"([1-9][0-9]*)"$')


def _etag(version: int) -> str:
    return f'"{version}"'


def _expected_version(if_match: str | None) -> int:
    if if_match is None:
        raise HTTPException(428, "If-Match analytics assignment version is required")
    match = _ETAG_PATTERN.fullmatch(if_match.strip())
    if match is None:
        raise HTTPException(
            400,
            "If-Match must contain an analytics assignment version ETag",
        )
    return int(match.group(1))


def _raise_service_error(error: RuntimeError) -> None:
    if isinstance(error, AnalyticsAssignmentNotFoundError):
        raise HTTPException(404, "Analytics assignment or stream not found") from error
    if isinstance(error, AnalyticsAssignmentPreconditionError):
        raise HTTPException(412, str(error)) from error
    if isinstance(error, AnalyticsAssignmentConflictError):
        raise HTTPException(409, str(error)) from error
    if isinstance(error, AnalyticsAssignmentValidationError):
        raise HTTPException(422, str(error)) from error
    raise error


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def _runtime_configured(request: Request) -> bool:
    return bool(request.app.state.analytics_runtime.descriptor.configured)


@router.get(
    "/analytics-assignments",
    response_model=AnalyticsAssignmentListResponse,
)
def list_analytics_assignments(
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    stream_id: Annotated[str | None, Query(max_length=64)] = None,
    camera_id: Annotated[str | None, Query(max_length=160)] = None,
    capability: Annotated[str | None, Query(max_length=128)] = None,
    desired_state: Annotated[str | None, Query(max_length=16)] = None,
    lifecycle_state: Annotated[str | None, Query(max_length=16)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnalyticsAssignmentListResponse:
    _no_store(response)
    return AnalyticsAssignmentRepository(session).list(
        filters=AnalyticsAssignmentFilters(
            stream_id=stream_id,
            camera_id=camera_id,
            capability=capability,
            desired_state=desired_state,
            lifecycle_state=lifecycle_state,
            allowed_departments=principal.allowed_departments,
        ),
        limit=limit,
        offset=offset,
        runtime_configured=_runtime_configured(request),
    )


@router.post(
    "/streams/{stream_id}/analytics-assignments",
    response_model=AnalyticsAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_analytics_assignment(
    stream_id: str,
    payload: AnalyticsAssignmentCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> AnalyticsAssignmentResponse:
    try:
        assignment = AnalyticsAssignmentService(session).create(
            stream_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["ETag"] = _etag(assignment.version_id)
    response.headers["Location"] = f"/analytics-assignments/{assignment.assignment_id}"
    _no_store(response)
    return assignment_to_response(
        assignment,
        runtime_configured=_runtime_configured(request),
    )


@router.get(
    "/analytics-assignments/{assignment_id}",
    response_model=AnalyticsAssignmentResponse,
)
def get_analytics_assignment(
    assignment_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> AnalyticsAssignmentResponse:
    assignment = AnalyticsAssignmentRepository(session).get(
        assignment_id,
        allowed_departments=principal.allowed_departments,
    )
    if assignment is None:
        raise HTTPException(404, "Analytics assignment not found")
    response.headers["ETag"] = _etag(assignment.version_id)
    _no_store(response)
    return assignment_to_response(
        assignment,
        runtime_configured=_runtime_configured(request),
    )


@router.patch(
    "/analytics-assignments/{assignment_id}",
    response_model=AnalyticsAssignmentResponse,
)
def update_analytics_assignment(
    assignment_id: str,
    payload: AnalyticsAssignmentPatch,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> AnalyticsAssignmentResponse:
    try:
        assignment = AnalyticsAssignmentService(session).update(
            assignment_id,
            payload,
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["ETag"] = _etag(assignment.version_id)
    _no_store(response)
    return assignment_to_response(
        assignment,
        runtime_configured=_runtime_configured(request),
    )


@router.post(
    "/analytics-assignments/{assignment_id}/activate",
    response_model=AnalyticsAssignmentResponse,
)
def activate_analytics_assignment(
    assignment_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> AnalyticsAssignmentResponse:
    try:
        assignment = AnalyticsAssignmentService(session).transition(
            assignment_id,
            activate=True,
            runtime_configured=_runtime_configured(request),
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["ETag"] = _etag(assignment.version_id)
    _no_store(response)
    return assignment_to_response(
        assignment,
        runtime_configured=_runtime_configured(request),
    )


@router.post(
    "/analytics-assignments/{assignment_id}/pause",
    response_model=AnalyticsAssignmentResponse,
)
def pause_analytics_assignment(
    assignment_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> AnalyticsAssignmentResponse:
    try:
        assignment = AnalyticsAssignmentService(session).transition(
            assignment_id,
            activate=False,
            runtime_configured=_runtime_configured(request),
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["ETag"] = _etag(assignment.version_id)
    _no_store(response)
    return assignment_to_response(
        assignment,
        runtime_configured=_runtime_configured(request),
    )


@router.get(
    "/analytics-assignments/{assignment_id}/revisions",
    response_model=AnalyticsAssignmentRevisionListResponse,
)
def list_analytics_assignment_revisions(
    assignment_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnalyticsAssignmentRevisionListResponse:
    repository = AnalyticsAssignmentRepository(session)
    assignment = repository.get(
        assignment_id,
        allowed_departments=principal.allowed_departments,
    )
    if assignment is None:
        raise HTTPException(404, "Analytics assignment not found")
    _no_store(response)
    return repository.list_revisions(
        assignment,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/analytics-assignments/{assignment_id}/generated-runs",
    response_model=GeneratedAnalyticsRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_generated_analytics_run(
    assignment_id: str,
    payload: GeneratedAnalyticsRunCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> GeneratedAnalyticsRunResponse:
    service = GeneratedAnalyticsExecutionService(
        session,
        runtime=request.app.state.analytics_runtime,
        leases=request.app.state.analytics_frame_leases,
    )
    try:
        result = service.execute(
            assignment_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    response.headers["Location"] = f"/analytics-generated-runs/{result.run_id}"
    request.app.state.request_metrics.analytics_generated_leases.set(
        request.app.state.analytics_frame_leases.active_leases
    )
    _no_store(response)
    return result


@router.get(
    "/analytics-generated-runs/{run_id}",
    response_model=GeneratedAnalyticsRunResponse,
)
def get_generated_analytics_run(
    run_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> GeneratedAnalyticsRunResponse:
    service = GeneratedAnalyticsExecutionService(
        session,
        runtime=request.app.state.analytics_runtime,
        leases=request.app.state.analytics_frame_leases,
    )
    try:
        result = service.get_run(run_id, principal=principal)
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    _no_store(response)
    return result


@router.get(
    "/analytics-generated-runs/{run_id}/observations",
    response_model=AnalyticsObservationListResponse,
)
def list_generated_analytics_observations(
    run_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=300)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnalyticsObservationListResponse:
    service = GeneratedAnalyticsExecutionService(
        session,
        runtime=request.app.state.analytics_runtime,
        leases=request.app.state.analytics_frame_leases,
    )
    try:
        result = service.list_observations(
            run_id,
            principal=principal,
            limit=limit,
            offset=offset,
        )
    except RuntimeError as exc:
        _raise_service_error(exc)
        raise
    _no_store(response)
    return result
