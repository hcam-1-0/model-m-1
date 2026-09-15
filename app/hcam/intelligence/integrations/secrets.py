from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from hcam.intelligence.integrations.contracts import AuthProfileV1


class SecretProviderError(RuntimeError):
    reason_code = "secret_provider_unavailable"


@dataclass(frozen=True, slots=True)
class SecretLease:
    lease_id: str
    profile_id: str
    mode: str
    contains_secret: bool = False


class SecretProvider(Protocol):
    def resolve(self, profile: AuthProfileV1) -> SecretLease: ...


class UnconfiguredSecretProvider:
    def resolve(self, profile: AuthProfileV1) -> SecretLease:
        raise SecretProviderError("secret provider is not configured")


class NoneGeneratedSecretProvider:
    def resolve(self, profile: AuthProfileV1) -> SecretLease:
        if profile.mode != "none_generated" or not profile.enabled:
            raise SecretProviderError("authentication profile is not generated-only")
        return SecretLease(
            lease_id=f"lease:{profile.profile_id}",
            profile_id=profile.profile_id,
            mode=profile.mode,
        )


class DisabledDatabaseEnvelopeSecretProvider:
    def resolve(self, profile: AuthProfileV1) -> SecretLease:
        raise SecretProviderError("database envelope secret backend is disabled")
