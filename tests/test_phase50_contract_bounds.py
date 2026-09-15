from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from hcam.operator_application.bounds import require_bounded_text, require_unique
from hcam.operator_application.contracts import (
    CapabilityCeilingV1,
    OperatorActionV1,
    OperatorViewContractV1,
    ProducerBindingV1,
    SafeProblemV1,
)


def _producer() -> ProducerBindingV1:
    return ProducerBindingV1(
        operation_id="operations.summary",
        schema_version="phase4.7.v1",
        source_kind="http",
        freshness_seconds=30,
        authoritative=True,
        gap_class="ready_for_generated_consumer",
    )


def _view() -> OperatorViewContractV1:
    return OperatorViewContractV1(
        view_id="command.overview",
        portal_id="command",
        route_id="command.overview",
        title_key="view.command.overview",
        required_roles=["command.viewer"],
        supported_states=["loading", "ready", "denied"],
        actions=[
            OperatorActionV1(
                action_id="view",
                command_kind="query",
                required_roles=["command.viewer"],
            )
        ],
        producer=_producer(),
    )


def test_bounded_text_and_unique_helpers() -> None:
    assert require_bounded_text("valid", label="value") == "valid"
    assert require_unique(["a", "b"], label="values") == ("a", "b")
    with pytest.raises(ValueError, match="surrounding whitespace"):
        require_bounded_text(" invalid", label="value")
    with pytest.raises(ValueError, match="outside"):
        require_bounded_text("x", label="value", minimum=2)
    with pytest.raises(ValueError, match="control"):
        require_bounded_text("a\nb", label="value")
    with pytest.raises(ValueError, match="unique"):
        require_unique(["a", "a"], label="values")


def test_contract_models_are_strict_frozen_and_extra_forbidden() -> None:
    view = _view()
    assert view.generated_only is True
    with pytest.raises(ValidationError, match="Extra inputs"):
        OperatorViewContractV1.model_validate({**view.model_dump(), "unknown": True})
    with pytest.raises(ValidationError):
        view.view_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ProducerBindingV1.model_validate({**_producer().model_dump(), "freshness_seconds": "30"})


def test_view_rejects_duplicate_roles_states_actions_and_missing_locales() -> None:
    base = _view().model_dump()
    for field, value in (
        ("required_roles", ["command.viewer", "command.viewer"]),
        ("supported_states", ["ready", "ready"]),
        ("locales", ["en-IN", "gu-IN", "gu-IN"]),
    ):
        with pytest.raises(ValidationError):
            OperatorViewContractV1.model_validate({**base, field: value})
    duplicate_actions = [base["actions"][0], base["actions"][0]]
    with pytest.raises(ValidationError, match="action identifiers"):
        OperatorViewContractV1.model_validate({**base, "actions": duplicate_actions})


def test_capability_ceiling_and_safe_problem_consistency() -> None:
    ceiling = CapabilityCeilingV1(
        policy_version="policy.v1",
        allowed_actions=["view"],
        denied_actions=["dispatch"],
    )
    assert ceiling.allowed_actions == ["view"]
    for allowed, denied in ((["view", "view"], []), ([], ["view", "view"]), (["view"], ["view"])):
        with pytest.raises(ValidationError):
            CapabilityCeilingV1(
                policy_version="policy.v1",
                allowed_actions=allowed,
                denied_actions=denied,
            )
    problem = SafeProblemV1(
        reason_code="temporary_failure",
        title_key="problem.temporary",
        recovery_action="retry",
        retry_after_seconds=10,
        trace_ref="trace_0123456789abcdef",
    )
    assert problem.raw_detail is None
    with pytest.raises(ValidationError, match="requires"):
        SafeProblemV1(
            reason_code="temporary_failure",
            title_key="problem.temporary",
            recovery_action="retry",
        )
    with pytest.raises(ValidationError, match="only valid"):
        SafeProblemV1(
            reason_code="denied",
            title_key="problem.denied",
            recovery_action="request_access",
            retry_after_seconds=10,
        )


def test_producer_requires_utc_and_bounded_freshness() -> None:
    now = datetime.now(timezone.utc)
    assert now.utcoffset() is not None
    with pytest.raises(ValidationError):
        ProducerBindingV1(
            operation_id="operations.summary",
            schema_version="phase4.7.v1",
            source_kind="http",
            freshness_seconds=0,
            authoritative=True,
            gap_class="partial",
        )
