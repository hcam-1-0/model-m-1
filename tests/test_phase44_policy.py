from __future__ import annotations

import pytest

from hcam.intelligence.integrations.manifests import ManifestError, ManifestRegistry
from hcam.intelligence.integrations.policy import PolicyDeniedError, compile_query_plan
from tests.test_phase44_contracts import intent, manifest


def test_manifest_registry_and_policy_compile_stable_closed_plan() -> None:
    provider = manifest()
    registry = ManifestRegistry()
    registry.register(provider)
    assert registry.get(provider.provider_version_id) == provider
    assert registry.list(department=provider.department) == [provider]
    plan = compile_query_plan(intent(provider), provider, control_enabled=True)
    assert plan.provider_version_id == provider.provider_version_id
    assert plan.generated_only is True
    assert plan.operational is False
    assert plan.semantic_key.startswith("sha256:")


def test_manifest_registry_and_policy_deny_duplicates_disabled_or_wrong_scope() -> None:
    provider = manifest()
    registry = ManifestRegistry()
    registry.register(provider)
    with pytest.raises(ManifestError):
        registry.register(provider)
    with pytest.raises(PolicyDeniedError):
        compile_query_plan(intent(provider), provider, control_enabled=False)
    other = intent(provider).model_copy(update={"department": "Generated-Department-2"})
    with pytest.raises(PolicyDeniedError):
        compile_query_plan(other, provider, control_enabled=True)
