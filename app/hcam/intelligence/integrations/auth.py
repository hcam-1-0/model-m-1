from __future__ import annotations

from dataclasses import dataclass

from hcam.intelligence.integrations.contracts import AuthProfileV1
from hcam.intelligence.integrations.secrets import SecretLease, SecretProvider


class AuthenticationPolicyError(RuntimeError):
    reason_code = "authentication_policy_denied"


@dataclass(frozen=True, slots=True)
class AuthProfileExtensionDescriptor:
    extension_id: str
    version: int
    artifact_digest: str
    signed: bool
    allowlisted: bool
    enabled: bool = False

    def validate_for_p4_4(self) -> None:
        if self.enabled:
            raise AuthenticationPolicyError("authentication extensions are disabled")
        if not self.signed or not self.allowlisted:
            raise AuthenticationPolicyError("authentication extension is not trusted")


class AuthenticationResolver:
    def __init__(self, provider: SecretProvider) -> None:
        self._provider = provider

    def resolve(self, profile: AuthProfileV1) -> SecretLease:
        if profile.mode != "none_generated":
            raise AuthenticationPolicyError("non-generated authentication is disabled")
        lease = self._provider.resolve(profile)
        if lease.contains_secret:
            raise AuthenticationPolicyError("generated authentication cannot contain secrets")
        return lease
