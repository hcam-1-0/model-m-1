import pytest

from hcam.operations.platform.contracts import AuthorizationContextV1
from hcam.operations.platform.security import AuthorizationDenied, assert_pool_scope_reset, authorize, postgres_rls_predicate


def _context(department: str = "Generated Department") -> AuthorizationContextV1:
    return AuthorizationContextV1(
        actor_id="generated:operator",
        department=department,
        roles=frozenset({"operations:reader"}),
        purpose_code="generated.review",
        reason="generated review reason",
        expected_revision=1,
        idempotency_key="sha256:" + "1" * 64,
    )


def test_application_authorization_matches_department_scope() -> None:
    authorize(_context(), required_roles=frozenset({"operations:reader"}), permitted_departments=frozenset({"Generated Department"}))
    with pytest.raises(AuthorizationDenied):
        authorize(_context("Other Department"), required_roles=frozenset({"operations:reader"}), permitted_departments=frozenset({"Generated Department"}))


def test_rls_predicate_and_pool_reset_are_fail_closed() -> None:
    predicate = postgres_rls_predicate()
    assert "allowed_departments" in predicate and "is_platform_admin" in predicate
    with pytest.raises(AuthorizationDenied):
        assert_pool_scope_reset({"hcam.allowed_departments": "Generated Department"})
    assert_pool_scope_reset({"hcam.allowed_departments": ""})


def test_security_policy_denies_missing_role_or_purpose() -> None:
    context = _context()
    with pytest.raises(AuthorizationDenied):
        authorize(
            context,
            required_roles=frozenset({"operations:security"}),
            permitted_departments=None,
        )
    without_purpose = context.model_construct(**{**context.model_dump(), "purpose_code": ""})
    with pytest.raises(AuthorizationDenied):
        authorize(
            without_purpose,
            required_roles=frozenset({"operations:reader"}),
            permitted_departments=None,
        )
    assert_pool_scope_reset({"hcam.allowed_departments": "", "unrelated": "generated"})
