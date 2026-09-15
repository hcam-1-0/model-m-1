from __future__ import annotations

from typing import Protocol

from hcam.intelligence.integrations.contracts import (
    CompiledQueryPlanV1,
    GeneratedProviderPayload,
)


class ProviderError(RuntimeError):
    reason_code = "generated_provider_error"


class GeneratedProvider(Protocol):
    provider_version_id: str

    def execute(
        self,
        plan: CompiledQueryPlanV1,
        parameters: dict[str, str],
    ) -> GeneratedProviderPayload: ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, GeneratedProvider] = {}

    def register(self, provider: GeneratedProvider) -> None:
        if provider.provider_version_id in self._providers:
            raise ProviderError("generated provider is already registered")
        self._providers[provider.provider_version_id] = provider

    def get(self, provider_version_id: str) -> GeneratedProvider:
        try:
            return self._providers[provider_version_id]
        except KeyError as exc:
            raise ProviderError("generated provider is not registered") from exc
