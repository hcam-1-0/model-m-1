from __future__ import annotations

from hcam.operations.platform.contracts import AuthorizationContextV1


class AuthorizationDenied(RuntimeError):
    pass


def authorize(
    context: AuthorizationContextV1,
    *,
    required_roles: frozenset[str],
    permitted_departments: frozenset[str] | None,
) -> None:
    if context.roles.isdisjoint(required_roles):
        raise AuthorizationDenied("authorization.denied")
    if permitted_departments is not None and context.department not in permitted_departments:
        raise AuthorizationDenied("authorization.denied")
    if not context.purpose_code or not context.reason:
        raise AuthorizationDenied("policy.denied")


def postgres_rls_predicate() -> str:
    return (
        "current_setting('hcam.is_platform_admin', true) = 'true' OR "
        "department = ANY(string_to_array("
        "current_setting('hcam.allowed_departments', true), E'\\x1f'))"
    )


def assert_pool_scope_reset(settings: dict[str, str]) -> None:
    residual = {key for key, value in settings.items() if key.startswith("hcam.") and value}
    if residual:
        raise AuthorizationDenied("policy.denied")
