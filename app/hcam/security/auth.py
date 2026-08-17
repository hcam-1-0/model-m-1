from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Annotated, Protocol

from fastapi import Depends, HTTPException, Request, status

from hcam.settings import Settings


CAMERA_VIEWER = "camera.viewer"
CAMERA_EDITOR = "camera.editor"
PLATFORM_ADMIN = "platform.admin"
KNOWN_ROLES = frozenset({CAMERA_VIEWER, CAMERA_EDITOR, PLATFORM_ADMIN})
_ACTOR_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@-]{0,159}$")
_DEPARTMENT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,119}$")


@dataclass(frozen=True, slots=True)
class Principal:
    actor_id: str
    roles: frozenset[str]
    departments: frozenset[str]
    authentication_method: str

    @property
    def has_unrestricted_department_access(self) -> bool:
        return PLATFORM_ADMIN in self.roles or "*" in self.departments

    @property
    def allowed_departments(self) -> frozenset[str] | None:
        if self.has_unrestricted_department_access:
            return None
        return self.departments

    def can_access_department(self, department: str | None) -> bool:
        if self.has_unrestricted_department_access:
            return True
        return department is not None and department in self.departments


class Authenticator(Protocol):
    @property
    def ready(self) -> bool: ...

    def authenticate(self, request: Request) -> Principal: ...


class UnconfiguredAuthenticator:
    @property
    def ready(self) -> bool:
        return False

    def authenticate(self, _request: Request) -> Principal:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication provider is not configured",
        )


def _parse_csv_header(value: str | None) -> frozenset[str]:
    if value is None:
        return frozenset()
    return frozenset(item.strip() for item in value.split(",") if item.strip())


class DevHeaderAuthenticator:
    """Explicit local-only identity adapter. It must never run in production."""

    @property
    def ready(self) -> bool:
        return True

    def authenticate(self, request: Request) -> Principal:
        actor_id = request.headers.get("X-HCAM-Actor", "").strip()
        roles = _parse_csv_header(request.headers.get("X-HCAM-Roles"))
        departments = _parse_csv_header(request.headers.get("X-HCAM-Departments"))

        if not actor_id or _ACTOR_PATTERN.fullmatch(actor_id) is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Valid local development actor header required",
                headers={"WWW-Authenticate": "H-CAM-Dev"},
            )
        if not roles or not roles.issubset(KNOWN_ROLES):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Valid local development roles header required",
                headers={"WWW-Authenticate": "H-CAM-Dev"},
            )
        if "*" in departments and len(departments) != 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wildcard department cannot be combined with other departments",
            )
        if any(
            department != "*" and _DEPARTMENT_PATTERN.fullmatch(department) is None
            for department in departments
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid local development department scope",
            )

        return Principal(
            actor_id=actor_id,
            roles=roles,
            departments=departments,
            authentication_method="local-dev-headers",
        )


def build_authenticator(settings: Settings) -> Authenticator:
    if settings.dev_auth_enabled:
        if settings.environment.lower() not in {"development", "test"}:
            raise RuntimeError("Local development authentication is forbidden in production")
        return DevHeaderAuthenticator()
    return UnconfiguredAuthenticator()


def get_current_principal(request: Request) -> Principal:
    return request.app.state.authenticator.authenticate(request)


PrincipalDependency = Annotated[Principal, Depends(get_current_principal)]


class RoleGuard:
    def __init__(self, *allowed_roles: str) -> None:
        self.allowed_roles = frozenset(allowed_roles)

    def __call__(self, principal: PrincipalDependency) -> Principal:
        if principal.roles.isdisjoint(self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return principal
