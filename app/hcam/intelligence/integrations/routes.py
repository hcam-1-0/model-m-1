from __future__ import annotations

import re
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from hcam.database import get_session
from hcam.intelligence.integrations.contracts import (
    CandidateSetV1,
    ControlRevisionV1,
    ProviderManifestV2,
    QueryIntentV1,
    QueryJobV1,
)
from hcam.intelligence.integrations.service import (
    IntegrationControlError,
    IntegrationControlService,
    IntegrationDisabledError,
    IntegrationNotFoundError,
    IntegrationPreconditionError,
)
from hcam.security.auth import (
    PLATFORM_ADMIN,
    REFERENCE_CANDIDATE_READ,
    REFERENCE_CONTROL_MANAGE_GENERATED,
    REFERENCE_CONTROL_READ,
    REFERENCE_PROVIDER_CREATE_GENERATED,
    REFERENCE_PROVIDER_READ,
    REFERENCE_QUERY_CANCEL,
    REFERENCE_QUERY_READ,
    REFERENCE_QUERY_SUBMIT_GENERATED,
    Principal,
    RoleGuard,
)


router = APIRouter(tags=["generated-reference-integrations"])
SessionDependency = Annotated[Session, Depends(get_session)]
ProviderReader = Annotated[
    Principal, Depends(RoleGuard(REFERENCE_PROVIDER_READ, PLATFORM_ADMIN))
]
ProviderCreator = Annotated[
    Principal,
    Depends(RoleGuard(REFERENCE_PROVIDER_CREATE_GENERATED, PLATFORM_ADMIN)),
]
QuerySubmitter = Annotated[
    Principal,
    Depends(RoleGuard(REFERENCE_QUERY_SUBMIT_GENERATED, PLATFORM_ADMIN)),
]
QueryReader = Annotated[
    Principal, Depends(RoleGuard(REFERENCE_QUERY_READ, PLATFORM_ADMIN))
]
QueryCanceller = Annotated[
    Principal, Depends(RoleGuard(REFERENCE_QUERY_CANCEL, PLATFORM_ADMIN))
]
CandidateReader = Annotated[
    Principal, Depends(RoleGuard(REFERENCE_CANDIDATE_READ, PLATFORM_ADMIN))
]
ControlReader = Annotated[
    Principal, Depends(RoleGuard(REFERENCE_CONTROL_READ, PLATFORM_ADMIN))
]
ControlManager = Annotated[
    Principal,
    Depends(RoleGuard(REFERENCE_CONTROL_MANAGE_GENERATED, PLATFORM_ADMIN)),
]
ReasonHeader = Annotated[
    str,
    Header(alias="X-HCAM-Reason", min_length=8, max_length=2000, pattern=r".*\S.*"),
]
_ETAG = re.compile(r'^"([0-9]+)"$')


class ProviderListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ProviderManifestV2]
    total: int


class QuerySubmissionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job: QueryJobV1
    reused: bool


class ControlListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ControlRevisionV1]
    total: int


class ControlMutation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    department: Annotated[str, Field(min_length=1, max_length=120)]
    scope: Literal[
        "organization", "department", "provider", "operation", "purpose", "auth_profile"
    ]
    scope_key: Annotated[str, Field(min_length=1, max_length=128)]
    state: Literal["enabled_generated", "suspended", "revoked"]


def _service(request: Request, session: Session) -> IntegrationControlService:
    return IntegrationControlService(
        session,
        enabled=request.app.state.settings.intelligence_generated_reference_integrations_enabled,
        manual_queries_enabled=(
            request.app.state.settings.intelligence_generated_reference_manual_queries_enabled
        ),
        hypothesis_enrichment_enabled=(
            request.app.state.settings.intelligence_generated_reference_hypothesis_enrichment_enabled
        ),
    )


def _no_store(response: Response, version: int | None = None) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    if version is not None:
        response.headers["ETag"] = f'"{version}"'


def _expected_version(value: str | None) -> int:
    match = _ETAG.fullmatch(value.strip()) if value is not None else None
    if match is None:
        raise HTTPException(428 if value is None else 400, "valid If-Match version required")
    return int(match.group(1))


def _raise(error: IntegrationControlError) -> None:
    if isinstance(error, IntegrationDisabledError):
        raise HTTPException(503, "generated reference integrations are disabled") from error
    if isinstance(error, IntegrationNotFoundError):
        raise HTTPException(404, "reference resource was not found") from error
    if isinstance(error, IntegrationPreconditionError):
        raise HTTPException(412, "reference resource precondition failed") from error
    raise HTTPException(422, "generated reference integration request was rejected") from error


@router.get("/reference-integrations/health")
def integration_health(
    request: Request, response: Response, principal: ProviderReader
) -> dict[str, object]:
    _ = principal
    _no_store(response)
    return {
        "status": "ready",
        "generated_only": True,
        "operational": False,
        "network_allowed": False,
        "runtime_enabled": request.app.state.settings.intelligence_generated_reference_integrations_enabled,
        "manual_query_lane_enabled": request.app.state.settings.intelligence_generated_reference_manual_queries_enabled,
        "hypothesis_enrichment_lane_enabled": request.app.state.settings.intelligence_generated_reference_hypothesis_enrichment_enabled,
    }


@router.post(
    "/reference-integrations/providers",
    response_model=ProviderManifestV2,
    status_code=status.HTTP_201_CREATED,
)
def create_provider(
    manifest: ProviderManifestV2,
    reason: ReasonHeader,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ProviderCreator,
) -> ProviderManifestV2:
    _ = reason
    try:
        result = _service(request, session).register_manifest(manifest, principal=principal)
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response, 1)
    return result


@router.get("/reference-integrations/providers", response_model=ProviderListResponse)
def list_providers(
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ProviderReader,
) -> ProviderListResponse:
    try:
        items = _service(request, session).list_manifests(principal=principal)
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response)
    return ProviderListResponse(items=items, total=len(items))


@router.get(
    "/reference-integrations/providers/{provider_version_id}",
    response_model=ProviderManifestV2,
)
def get_provider(
    provider_version_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ProviderReader,
) -> ProviderManifestV2:
    try:
        result = _service(request, session).get_manifest(
            provider_version_id, principal=principal
        )
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response, result.version)
    return result


@router.post(
    "/reference-integrations/queries",
    response_model=QuerySubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_query(
    intent: QueryIntentV1,
    reason: ReasonHeader,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: QuerySubmitter,
) -> QuerySubmissionResponse:
    if intent.reason != reason:
        raise HTTPException(400, "query reason does not match X-HCAM-Reason")
    try:
        job, reused = _service(request, session).submit_query(intent, principal=principal)
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response, 1)
    response.headers["Location"] = f"/reference-integrations/queries/{job.job_id}"
    return QuerySubmissionResponse(job=job, reused=reused)


@router.get("/reference-integrations/queries/{job_id}", response_model=QueryJobV1)
def get_query(
    job_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: QueryReader,
) -> QueryJobV1:
    try:
        result = _service(request, session).get_job(job_id, principal=principal)
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.post("/reference-integrations/queries/{job_id}/cancel", response_model=QueryJobV1)
def cancel_query(
    job_id: str,
    reason: ReasonHeader,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: QueryCanceller,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> QueryJobV1:
    _ = reason
    try:
        result = _service(request, session).cancel_job(
            job_id,
            expected_version=_expected_version(if_match),
            principal=principal,
        )
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response, 2)
    return result


@router.get(
    "/reference-integrations/candidate-sets/{candidate_set_id}",
    response_model=CandidateSetV1,
)
def get_candidate_set(
    candidate_set_id: str,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: CandidateReader,
) -> CandidateSetV1:
    try:
        result = _service(request, session).get_candidate_set(
            candidate_set_id, principal=principal
        )
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response)
    return result


@router.get("/reference-integrations/controls", response_model=ControlListResponse)
def list_controls(
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ControlReader,
) -> ControlListResponse:
    try:
        items = _service(request, session).controls(principal=principal)
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response)
    return ControlListResponse(items=items, total=len(items))


@router.post("/reference-integrations/controls", response_model=ControlRevisionV1)
def mutate_control(
    mutation: ControlMutation,
    reason: ReasonHeader,
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: ControlManager,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> ControlRevisionV1:
    try:
        result = _service(request, session).apply_control(
            department=mutation.department,
            scope=mutation.scope,
            scope_key=mutation.scope_key,
            state=mutation.state,
            expected_version=_expected_version(if_match),
            reason=reason,
            principal=principal,
        )
    except IntegrationControlError as exc:
        _raise(exc)
    _no_store(response, result.version)
    return result
