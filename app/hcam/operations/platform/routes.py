from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from hcam.database import get_session
from hcam.operations.platform.service import PlatformService
from hcam.security.auth import (
    OPERATIONS_CAPACITY_READ,
    OPERATIONS_CONTROL_READ,
    OPERATIONS_PLATFORM_READ,
    OPERATIONS_RECOVERY_READ,
    OPERATIONS_SECURITY_READ,
    OPERATIONS_SUPPLY_CHAIN_READ,
    PLATFORM_ADMIN,
    Principal,
    RoleGuard,
)


router = APIRouter(prefix="/platform/operations", tags=["platform-operations"])
SessionDependency = Annotated[Session, Depends(get_session)]
PlatformReader = Annotated[
    Principal,
    Depends(
        RoleGuard(
            OPERATIONS_PLATFORM_READ,
            OPERATIONS_SECURITY_READ,
            OPERATIONS_RECOVERY_READ,
            OPERATIONS_CAPACITY_READ,
            OPERATIONS_SUPPLY_CHAIN_READ,
            OPERATIONS_CONTROL_READ,
            PLATFORM_ADMIN,
        )
    ),
]


def _service(request: Request, session: Session) -> PlatformService:
    return PlatformService(session, request.app.state.operations_platform_runtime)


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


def _disabled(exc: RuntimeError) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Platform operations view is disabled") from exc


def _forbidden(exc: PermissionError) -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for operations view") from exc


@router.get("/summary")
def summary(request: Request, response: Response, session: SessionDependency, principal: PlatformReader) -> dict[str, object]:
    try:
        result = _service(request, session).summary(principal=principal)
    except RuntimeError as exc:
        _disabled(exc)
    _no_store(response)
    return result


@router.get("/{view}")
def read_view(
    view: Literal["objectives", "budgets", "degradation", "controls", "recovery", "capacity", "supply-chain", "security"],
    request: Request,
    response: Response,
    session: SessionDependency,
    principal: PlatformReader,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> dict[str, Any]:
    try:
        items = _service(request, session).read(view, principal=principal, limit=limit)
    except RuntimeError as exc:
        _disabled(exc)
    except PermissionError as exc:
        _forbidden(exc)
    _no_store(response)
    return {"view": view, "items": items, "count": len(items), "generated_only": True}
