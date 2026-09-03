from __future__ import annotations

import re
from dataclasses import dataclass
from collections.abc import Callable, Mapping
from typing import Annotated, Protocol

import jwt

from fastapi import Depends, HTTPException, Request, status

from hcam.settings import Settings


CAMERA_VIEWER = "camera.viewer"
CAMERA_EDITOR = "camera.editor"
CAMERA_CONTROLLER = "camera.controller"
PLATFORM_ADMIN = "platform.admin"
KNOWN_ROLES = frozenset(
    {CAMERA_VIEWER, CAMERA_EDITOR, CAMERA_CONTROLLER, PLATFORM_ADMIN}
)
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


class CloudflareAccessAuthenticator:
    """Validate a Cloudflare Access assertion and derive a scoped principal.

    Group membership is accepted only after the JWT signature, issuer,
    audience and expiry have been verified against Cloudflare's rotating JWKS.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        token_decoder: Callable[[str], Mapping[str, object]] | None = None,
    ) -> None:
        self._team_domain = settings.cloudflare_access_team_domain
        self._audience = settings.cloudflare_access_audience
        self._mapping = settings.cloudflare_access_group_mapping
        self._token_decoder = token_decoder
        if self._team_domain is None or self._audience is None:
            raise RuntimeError("Cloudflare Access authentication is not configured")
        self._jwks = jwt.PyJWKClient(f"{self._team_domain}/cdn-cgi/access/certs")

    @property
    def ready(self) -> bool:
        return True

    def _decode(self, token: str) -> Mapping[str, object]:
        if self._token_decoder is not None:
            return self._token_decoder(token)
        signing_key = self._jwks.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self._audience,
            issuer=self._team_domain,
            options={"require": ["exp", "iss", "aud", "sub", "type"]},
        )

    def authenticate(self, request: Request) -> Principal:
        token = request.headers.get("Cf-Access-Jwt-Assertion", "").strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cloudflare Access assertion required",
            )
        try:
            claims = self._decode(token)
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Cloudflare Access assertion",
            ) from exc
        if claims.get("type") != "app":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access token type")
        actor_id = str(claims.get("email") or claims.get("sub") or "").strip()
        if _ACTOR_PATTERN.fullmatch(actor_id) is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access identity")
        raw_groups = claims.get("groups", ())
        if isinstance(raw_groups, str):
            groups = (raw_groups,)
        elif isinstance(raw_groups, list) and all(isinstance(group, str) for group in raw_groups):
            groups = tuple(raw_groups)
        else:
            groups = ()
        roles: set[str] = set()
        departments: set[str] = set()
        for group in groups:
            grant = self._mapping.get(group)
            if grant is None:
                continue
            roles.update(grant["roles"])
            departments.update(grant["departments"])
        if not roles or not roles.issubset(KNOWN_ROLES):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No H-CAM role grant")
        if "*" in departments and PLATFORM_ADMIN not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unscoped access requires platform admin")
        if any(
            department != "*" and _DEPARTMENT_PATTERN.fullmatch(department) is None
            for department in departments
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid department grant")
        return Principal(
            actor_id=actor_id,
            roles=frozenset(roles),
            departments=frozenset(departments),
            authentication_method="cloudflare-access",
        )


def build_authenticator(settings: Settings) -> Authenticator:
    if settings.cloudflare_access_enabled:
        return CloudflareAccessAuthenticator(settings)
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
