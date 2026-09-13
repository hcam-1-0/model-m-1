from __future__ import annotations

import pytest

from hcam.intelligence.integrations.auth import (
    AuthProfileExtensionDescriptor,
    AuthenticationPolicyError,
    AuthenticationResolver,
)
from hcam.intelligence.integrations.contracts import AuthProfileV1
from hcam.intelligence.integrations.secrets import (
    DisabledDatabaseEnvelopeSecretProvider,
    NoneGeneratedSecretProvider,
    SecretProviderError,
    UnconfiguredSecretProvider,
)


def test_generated_auth_resolves_without_secret_material() -> None:
    profile = AuthProfileV1(
        profile_id="generated.auth.none.v1", mode="none_generated", enabled=True
    )
    lease = AuthenticationResolver(NoneGeneratedSecretProvider()).resolve(profile)
    assert lease.contains_secret is False
    assert lease.profile_id == profile.profile_id


def test_non_generated_auth_and_unconfigured_backends_fail_closed() -> None:
    profile = AuthProfileV1(
        profile_id="generated.auth.disabled.v1",
        mode="database_envelope_disabled",
        secret_ref="secret_ref_" + "1" * 32,
    )
    with pytest.raises(AuthenticationPolicyError):
        AuthenticationResolver(NoneGeneratedSecretProvider()).resolve(profile)
    with pytest.raises(SecretProviderError):
        UnconfiguredSecretProvider().resolve(profile)
    with pytest.raises(SecretProviderError):
        DisabledDatabaseEnvelopeSecretProvider().resolve(profile)


def test_auth_extension_requires_trust_and_stays_disabled() -> None:
    trusted = AuthProfileExtensionDescriptor(
        extension_id="generated.extension.v1",
        version=1,
        artifact_digest="sha256:" + "1" * 64,
        signed=True,
        allowlisted=True,
    )
    trusted.validate_for_p4_4()
    with pytest.raises(AuthenticationPolicyError):
        AuthProfileExtensionDescriptor(
            extension_id="generated.extension.v1",
            version=1,
            artifact_digest="sha256:" + "1" * 64,
            signed=True,
            allowlisted=True,
            enabled=True,
        ).validate_for_p4_4()
