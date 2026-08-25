from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from hcam.analytics.service import AnalyticsAssignmentValidationError
from hcam.analytics.spatial.schemas import (
    AnalyticEventListResponse,
    GeneratedGeometryRunCreate,
    GeneratedGeometryRunResponse,
    GeometryApproval,
    GeometryCreate,
    GeometryListResponse,
    GeometryResponse,
    GeometryRuleApproval,
    GeometryRuleCreate,
    GeometryRuleListResponse,
    GeometryRuleResponse,
    RuleCompilePreview,
)
from hcam.analytics.spatial.execution import GeneratedGeometryExecutionService
from hcam.analytics.spatial.service import (
    SpatialConflictError,
    SpatialControlService,
    SpatialNotFoundError,
    SpatialPreconditionError,
    SpatialValidationError,
    geometry_response,
    rule_response,
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


router = APIRouter(tags=["analytics-geometry-control-plane"])
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
        raise HTTPException(428, "If-Match resource version is required")
    match = _ETAG_PATTERN.fullmatch(if_match.strip())
    if match is None:
        raise HTTPException(400, "If-Match must contain a resource version ETag")
    return int(match.group(1))


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def _raise_error(error: Exception) -> None:
    if isinstance(error, SpatialNotFoundError):
        raise HTTPException(404, "Analytics geometry resource not found") from error
    if isinstance(error, SpatialPreconditionError):
        raise HTTPException(412, str(error)) from error
    if isinstance(error, SpatialConflictError):
        raise HTTPException(409, str(error)) from error
    if isinstance(
        error,
        (SpatialValidationError, AnalyticsAssignmentValidationError, ValueError),
    ):
        raise HTTPException(422, "Analytics geometry request was rejected") from error
    raise error


@router.post(
    "/streams/{stream_id}/analytics-geometries",
    response_model=GeometryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_geometry(
    stream_id: str,
    payload: GeometryCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> GeometryResponse:
    try:
        row = SpatialControlService(session).create_geometry(
            stream_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.record_version)
    response.headers["Location"] = f"/analytics-geometries/{row.geometry_record_id}"
    _no_store(response)
    return geometry_response(row)


@router.get("/analytics-geometries", response_model=GeometryListResponse)
def list_geometries(
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    stream_id: Annotated[str | None, Query(max_length=64)] = None,
    geometry_status: Annotated[str | None, Query(alias="status", max_length=16)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> GeometryListResponse:
    _no_store(response)
    return SpatialControlService(session).list_geometries(
        principal=principal,
        stream_id=stream_id,
        status=geometry_status,
        limit=limit,
        offset=offset,
    )


@router.get("/analytics-geometries/{record_id}", response_model=GeometryResponse)
def get_geometry(
    record_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> GeometryResponse:
    try:
        row = SpatialControlService(session).get_geometry(record_id, principal)
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.record_version)
    _no_store(response)
    return geometry_response(row)


@router.post(
    "/analytics-geometries/{record_id}/approve",
    response_model=GeometryResponse,
)
def approve_geometry(
    record_id: str,
    payload: GeometryApproval,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> GeometryResponse:
    try:
        row = SpatialControlService(session).approve_geometry(
            record_id,
            payload.approval_record_id,
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.record_version)
    _no_store(response)
    return geometry_response(row)


@router.post(
    "/analytics-geometries/{record_id}/rule-compile-previews",
    response_model=RuleCompilePreview,
)
def preview_rule(
    record_id: str,
    payload: GeometryRuleCreate,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
) -> RuleCompilePreview:
    try:
        _, _, preview, _ = SpatialControlService(session).compile_rule(
            record_id,
            payload,
            principal=principal,
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    _no_store(response)
    return preview


@router.post(
    "/analytics-geometries/{record_id}/rules",
    response_model=GeometryRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    record_id: str,
    payload: GeometryRuleCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> GeometryRuleResponse:
    try:
        row = SpatialControlService(session).create_rule(
            record_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.record_version)
    response.headers["Location"] = f"/analytics-geometry-rules/{row.rule_record_id}"
    _no_store(response)
    return rule_response(row)


@router.get("/analytics-geometry-rules", response_model=GeometryRuleListResponse)
def list_rules(
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    assignment_id: Annotated[str | None, Query(max_length=64)] = None,
    rule_status: Annotated[str | None, Query(alias="status", max_length=16)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> GeometryRuleListResponse:
    _no_store(response)
    return SpatialControlService(session).list_rules(
        principal=principal,
        assignment_id=assignment_id,
        status=rule_status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/analytics-geometry-rules/{record_id}", response_model=GeometryRuleResponse
)
def get_rule(
    record_id: str,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> GeometryRuleResponse:
    try:
        row = SpatialControlService(session).get_rule(record_id, principal)
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.record_version)
    _no_store(response)
    return rule_response(row)


@router.post(
    "/analytics-geometry-rules/{record_id}/approve",
    response_model=GeometryRuleResponse,
)
def approve_rule(
    record_id: str,
    payload: GeometryRuleApproval,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> GeometryRuleResponse:
    try:
        row = SpatialControlService(session).approve_rule(
            record_id,
            payload.approval_record_id,
            expected_version=_expected_version(if_match),
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["ETag"] = _etag(row.record_version)
    _no_store(response)
    return rule_response(row)


@router.post(
    "/analytics-assignments/{assignment_id}/generated-geometry-runs",
    response_model=GeneratedGeometryRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def execute_generated_geometry_run(
    assignment_id: str,
    payload: GeneratedGeometryRunCreate,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: EditorPrincipal,
    reason: ReasonHeader,
) -> GeneratedGeometryRunResponse:
    service = GeneratedGeometryExecutionService(
        session,
        runtime_configured=request.app.state.settings.analytics_generated_geometry_enabled,
    )
    try:
        result = service.execute(
            assignment_id,
            payload,
            principal=principal,
            reason=reason,
            request_id=request_id_from_scope(request.scope),
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    response.headers["Location"] = f"/analytics-geometry-runs/{result.run_id}"
    _no_store(response)
    return result


@router.get(
    "/analytics-geometry-runs/{run_id}",
    response_model=GeneratedGeometryRunResponse,
)
def get_generated_geometry_run(
    run_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> GeneratedGeometryRunResponse:
    service = GeneratedGeometryExecutionService(
        session,
        runtime_configured=request.app.state.settings.analytics_generated_geometry_enabled,
    )
    try:
        result = service.get_run(run_id, principal=principal)
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    _no_store(response)
    return result


@router.get(
    "/analytics-geometry-runs/{run_id}/events",
    response_model=AnalyticEventListResponse,
)
def list_generated_geometry_events(
    run_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ViewerPrincipal,
    limit: Annotated[int, Query(ge=1, le=1_000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnalyticEventListResponse:
    service = GeneratedGeometryExecutionService(
        session,
        runtime_configured=request.app.state.settings.analytics_generated_geometry_enabled,
    )
    try:
        result = service.list_events(
            run_id,
            principal=principal,
            limit=limit,
            offset=offset,
        )
    except (RuntimeError, ValueError) as exc:
        _raise_error(exc)
        raise
    _no_store(response)
    return result
