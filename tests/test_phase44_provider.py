from __future__ import annotations

import pytest

from hcam.intelligence.integrations.generated_provider import StaticGeneratedProvider
from hcam.intelligence.integrations.policy import compile_query_plan
from hcam.intelligence.integrations.providers import ProviderError, ProviderRegistry
from hcam.intelligence.integrations.transport import GeneratedTransportEnvelope, InProcessGeneratedTransport
from tests.test_phase44_contracts import intent, manifest


def test_static_generated_provider_filters_and_projects_without_network() -> None:
    provider_manifest = manifest()
    provider = StaticGeneratedProvider(
        provider_manifest.provider_version_id,
        [
            {
                "record_key": "gen_record_001",
                "category": "gen_category_a",
                "region": "gen_region_west",
                "unused": "gen_not_projected",
            }
        ],
    )
    registry = ProviderRegistry()
    registry.register(provider)
    plan = compile_query_plan(intent(provider_manifest), provider_manifest, control_enabled=True)
    payload = InProcessGeneratedTransport(registry).execute(
        GeneratedTransportEnvelope(plan=plan, parameters=intent(provider_manifest).parameters)
    )
    assert payload.records == [
        {
            "record_key": "gen_record_001",
            "category": "gen_category_a",
            "region": "gen_region_west",
        }
    ]


def test_provider_registry_rejects_duplicate_and_missing_entries() -> None:
    provider_manifest = manifest()
    provider = StaticGeneratedProvider(provider_manifest.provider_version_id, [])
    registry = ProviderRegistry()
    registry.register(provider)
    with pytest.raises(ProviderError):
        registry.register(provider)
    with pytest.raises(ProviderError):
        ProviderRegistry().get(provider_manifest.provider_version_id)
