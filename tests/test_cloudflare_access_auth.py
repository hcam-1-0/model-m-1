from __future__ import annotations

import pytest

from hcam.security.auth import CloudflareAccessAuthenticator
from hcam.settings import Settings


def _settings() -> Settings:
    return Settings(
        cloudflare_access_enabled=True,
        cloudflare_access_team_domain="https://hcam.cloudflareaccess.com",
        cloudflare_access_audience="hcam-gis-audience",
        cloudflare_access_group_mapping={
            "hcam-viewers": {
                "roles": ("camera.viewer",),
                "departments": ("traffic",),
            },
            "hcam-admins": {
                "roles": ("platform.admin",),
                "departments": ("*",),
            },
        },
    )


def test_cloudflare_access_maps_verified_group_claims() -> None:
    authenticator = CloudflareAccessAuthenticator(
        _settings(),
        token_decoder=lambda _token: {
            "type": "app",
            "email": "viewer@example.com",
            "groups": ["hcam-viewers"],
        },
    )
    request = type("Request", (), {"headers": {"Cf-Access-Jwt-Assertion": "signed"}})()
    principal = authenticator.authenticate(request)  # type: ignore[arg-type]
    assert principal.actor_id == "viewer@example.com"
    assert principal.roles == frozenset({"camera.viewer"})
    assert principal.departments == frozenset({"traffic"})


def test_cloudflare_access_rejects_unmapped_groups() -> None:
    authenticator = CloudflareAccessAuthenticator(
        _settings(),
        token_decoder=lambda _token: {
            "type": "app",
            "email": "viewer@example.com",
            "groups": ["unmapped"],
        },
    )
    request = type("Request", (), {"headers": {"Cf-Access-Jwt-Assertion": "signed"}})()
    with pytest.raises(Exception) as raised:
        authenticator.authenticate(request)  # type: ignore[arg-type]
    assert getattr(raised.value, "status_code", None) == 403
