from __future__ import annotations

from dataclasses import dataclass

from hcam.intelligence.integrations.contracts import (
    CompiledQueryPlanV1,
    GeneratedProviderPayload,
)
from hcam.intelligence.integrations.providers import ProviderRegistry


@dataclass(frozen=True, slots=True)
class GeneratedTransportEnvelope:
    plan: CompiledQueryPlanV1
    parameters: dict[str, str]


class InProcessGeneratedTransport:
    network_allowed = False
    redirects_allowed = False
    environment_proxies_allowed = False

    def __init__(self, providers: ProviderRegistry) -> None:
        self._providers = providers

    def execute(self, envelope: GeneratedTransportEnvelope) -> GeneratedProviderPayload:
        provider = self._providers.get(envelope.plan.provider_version_id)
        return provider.execute(envelope.plan, dict(envelope.parameters))


class DisabledLoopbackTransport:
    def execute(self, _envelope: GeneratedTransportEnvelope) -> GeneratedProviderPayload:
        raise RuntimeError("loopback provider transport is disabled")
