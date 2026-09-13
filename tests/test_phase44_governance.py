from __future__ import annotations

import pytest

from hcam.intelligence.integrations.governance import ControlRegistry, GovernanceError
from tests.test_phase44_contracts import NOW, intent, manifest


def test_hierarchical_controls_are_versioned_and_revocation_wins() -> None:
    provider = manifest()
    query = intent(provider)
    controls = ControlRegistry()
    assert controls.allows(provider, query) is True
    revision = controls.apply(
        department=provider.department,
        scope="provider",
        scope_key=provider.provider_version_id,
        state="revoked",
        expected_version=0,
        actor_id="generated-admin",
        reason="Generated provider revocation test",
        now=NOW,
    )
    assert revision.version == 1
    assert controls.allows(provider, query) is False
    assert controls.history(department=provider.department) == [revision]
    with pytest.raises(GovernanceError):
        controls.apply(
            department=provider.department,
            scope="provider",
            scope_key=provider.provider_version_id,
            state="enabled_generated",
            expected_version=0,
            actor_id="generated-admin",
            reason="Generated stale control update",
            now=NOW,
        )
