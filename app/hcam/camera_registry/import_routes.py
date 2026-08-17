from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from hcam.camera_registry.importer import (
    PayloadRegistryAdapter,
    RegistryImportError,
    RegistryImporter,
)
from hcam.camera_registry.schemas import RegistryImportResult, RegistrySeed
from hcam.security.auth import PLATFORM_ADMIN, Principal, RoleGuard


router = APIRouter(prefix="/camera-imports", tags=["camera-registry"])
AdminPrincipal = Annotated[Principal, Depends(RoleGuard(PLATFORM_ADMIN))]
ReasonHeader = Annotated[
    str,
    Header(
        alias="X-HCAM-Reason",
        min_length=8,
        max_length=500,
        pattern=r".*\S.*",
    ),
]
MAX_SYNCHRONOUS_CAMERAS = 1000


@router.post("", response_model=RegistryImportResult)
def import_camera_registry(
    seed: RegistrySeed,
    request: Request,
    principal: AdminPrincipal,
    reason: ReasonHeader,
) -> RegistryImportResult:
    if len(seed.cameras) > MAX_SYNCHRONOUS_CAMERAS:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Synchronous camera import is limited to 1000 records",
        )

    importer = RegistryImporter(request.app.state.database.session_factory)
    try:
        return importer.import_adapter(
            PayloadRegistryAdapter(seed),
            actor_id=principal.actor_id,
            reason=reason.strip(),
        )
    except RegistryImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Camera registry import conflicted with existing data",
        ) from exc
