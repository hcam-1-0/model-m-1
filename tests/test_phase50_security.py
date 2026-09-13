from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hcam.operator_application import (
    BrowserSecurityBoundaryV1,
    CapabilityCeilingV1,
    SafeProblemV1,
    assert_generated_payload,
    prohibited_paths,
    resolve_capability,
)


NOW = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)


def test_browser_boundary_is_same_origin_and_closes_every_direct_path() -> None:
    boundary = BrowserSecurityBoundaryV1()
    assert boundary.same_origin_bff_required is True
    assert boundary.direct_camera_access is False
    assert boundary.direct_database_access is False
    assert boundary.direct_broker_access is False
    assert boundary.direct_model_runtime_access is False
    assert boundary.direct_provider_access is False
    assert boundary.persistent_sensitive_browser_storage is False


def test_browser_boundary_cannot_be_opened() -> None:
    with pytest.raises(ValidationError):
        BrowserSecurityBoundaryV1(direct_provider_access=True)


def test_prohibited_paths_recurses_without_retaining_values() -> None:
    payload = {
        "generated_only": True,
        "safe": [{"stream_url": "redacted"}, {"nested": {"password": "redacted"}}],
    }
    assert prohibited_paths(payload) == (
        "$.safe[0].stream_url",
        "$.safe[1].nested.password",
    )
    with pytest.raises(ValueError, match="prohibited field"):
        assert_generated_payload(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {"generated_only": True, "summary": "GJ 01 AB 1234"},
        {"generated_only": True, "summary": "MH-12-X-98"},
    ],
)
def test_generated_payload_rejects_registration_like_text(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="issuable registration"):
        assert_generated_payload(payload)


def test_generated_payload_requires_explicit_marker() -> None:
    with pytest.raises(ValueError, match="generated_only"):
        assert_generated_payload({"summary": "synthetic"})
    assert_generated_payload({"generated_only": True, "summary": "syn_case_only"})


def test_server_denial_has_priority_over_local_capability() -> None:
    ceiling = CapabilityCeilingV1(
        policy_version="phase5.0.v1",
        allowed_actions=["view"],
        denied_actions=[],
    )
    decision = resolve_capability(
        action="view",
        server_allowed=False,
        ceiling=ceiling,
        resource_profile="control_room",
        observed_at=NOW,
    )
    assert decision.allowed is False
    assert decision.reason_code == "server_denied"
    assert decision.source == "server"


def test_resource_profile_may_reduce_but_never_expand_authority() -> None:
    ceiling = CapabilityCeilingV1(
        policy_version="phase5.0.v1",
        allowed_actions=["visualize_dense", "multi_monitor"],
        denied_actions=[],
    )
    low = resolve_capability(
        action="visualize_dense",
        server_allowed=True,
        ceiling=ceiling,
        resource_profile="low_resource",
        observed_at=NOW,
    )
    enhanced = resolve_capability(
        action="visualize_dense",
        server_allowed=True,
        ceiling=ceiling,
        resource_profile="enhanced",
        observed_at=NOW,
    )
    assert (low.allowed, low.reason_code) == (False, "resource_profile_unavailable")
    assert (enhanced.allowed, enhanced.reason_code) == (True, "allowed")


def test_safe_problem_has_bounded_sanitized_recovery_contract() -> None:
    problem = SafeProblemV1(
        reason_code="temporarily_unavailable",
        title_key="problem.temporarily_unavailable",
        recovery_action="retry",
        retry_after_seconds=30,
        trace_ref="trace_0123456789abcdef",
    )
    assert problem.raw_detail is None
    with pytest.raises(ValidationError, match="bounded retry delay"):
        SafeProblemV1(
            reason_code="temporarily_unavailable",
            title_key="problem.temporarily_unavailable",
            recovery_action="retry",
        )
    with pytest.raises(ValidationError, match="only valid for retry"):
        SafeProblemV1(
            reason_code="denied",
            title_key="problem.denied",
            recovery_action="request_access",
            retry_after_seconds=30,
        )
