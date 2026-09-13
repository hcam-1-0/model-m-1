from datetime import UTC, datetime, timedelta

import pytest

from hcam.operations.platform.contracts import KillSwitchRevisionV1
from hcam.operations.platform.controls import capability_allowed, effective_switches, protect_mandatory_control


NOW = datetime(2026, 9, 5, tzinfo=UTC)


def _switch(state: str, revision: int = 1, *, mandatory: bool = False, expires=None) -> KillSwitchRevisionV1:
    return KillSwitchRevisionV1(
        switch_id="ref_" + "1" * 32,
        department="Generated Department",
        scope="department",
        scope_key="generated:department",
        state=state,
        mandatory_control=mandatory,
        revision=revision,
        actor_id="generated:owner",
        reason_code="control.generated",
        expires_at=expires,
        recorded_at=NOW,
    )


def test_deny_precedence_and_latest_revision() -> None:
    assert capability_allowed([_switch("allow")], now=NOW)
    assert not capability_allowed([_switch("allow"), _switch("deny", 2)], now=NOW)
    assert effective_switches([_switch("deny", expires=NOW - timedelta(seconds=1))], now=NOW) == []


def test_mandatory_control_cannot_be_bypassed() -> None:
    with pytest.raises(ValueError):
        protect_mandatory_control([_switch("allow", mandatory=True)], now=NOW)


def test_control_conflicts_and_empty_policy_fail_closed() -> None:
    assert capability_allowed([], now=NOW) is False
    protect_mandatory_control([_switch("deny", mandatory=True)], now=NOW)
    conflicting = _switch("allow").model_copy(update={"state": "deny"})
    with pytest.raises(ValueError):
        effective_switches([_switch("allow"), conflicting], now=NOW)
