from __future__ import annotations

import ipaddress
import io
import json
import socket
from pathlib import Path

import pytest

from hcam.settings import Settings
from hcam.streams.network import (
    OnvifEgressRule,
    OnvifNetworkPolicy,
    StreamNetworkPolicyError,
    load_onvif_egress_rules,
    parse_private_ipv4_networks,
)
from hcam.streams.secrets import (
    CameraSecretError,
    FileCameraSecretProvider,
    UnconfiguredCameraSecretProvider,
    build_camera_secret_provider,
)


def test_file_camera_secret_provider_rotates_and_redacts(tmp_path: Path) -> None:
    secret = tmp_path / "cameras" / "cam-01"
    secret.parent.mkdir()
    secret.write_text(
        json.dumps({"username": "operator", "password": "first-secret"}),
        encoding="utf-8",
    )
    provider = FileCameraSecretProvider(tmp_path)

    first = provider.get("cameras/cam-01")
    secret.write_text(
        json.dumps({"username": "operator", "password": "rotated-secret"}),
        encoding="utf-8",
    )
    second = provider.get("cameras/cam-01")

    assert first.password == "first-secret"
    assert second.password == "rotated-secret"
    assert "first-secret" not in repr(first)
    assert "operator" not in repr(first)
    assert "rotated-secret" not in repr(provider)


@pytest.mark.parametrize(
    ("reference", "payload", "reason"),
    [
        ("../outside", None, "camera_secret_invalid_reference"),
        ("missing", None, "camera_secret_unavailable"),
        ("bad-json", b"not-json", "camera_secret_invalid_payload"),
        (
            "extra",
            json.dumps(
                {"username": "operator", "password": "secret", "token": "x"}
            ).encode(),
            "camera_secret_invalid_payload",
        ),
        ("oversized", b"x" * (16 * 1024 + 1), "camera_secret_invalid_file"),
    ],
)
def test_file_camera_secret_provider_fails_closed(
    tmp_path: Path,
    reference: str,
    payload: bytes | None,
    reason: str,
) -> None:
    if payload is not None:
        (tmp_path / reference).write_bytes(payload)
    provider = FileCameraSecretProvider(tmp_path)
    with pytest.raises(CameraSecretError) as captured:
        provider.get(reference)
    assert captured.value.reason_code == reason


def test_file_camera_secret_provider_bounds_a_file_that_grows_after_stat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = tmp_path / "camera.json"
    secret.write_text(
        json.dumps({"username": "operator", "password": "secret"}),
        encoding="utf-8",
    )
    original_open = Path.open

    def raced_open(path: Path, *args, **kwargs):
        if path == secret.resolve():
            return io.BytesIO(b"x" * (16 * 1024 + 1))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", raced_open)
    with pytest.raises(CameraSecretError) as captured:
        FileCameraSecretProvider(tmp_path).get("camera.json")
    assert captured.value.reason_code == "camera_secret_invalid_file"


def test_unconfigured_secret_provider_is_explicit() -> None:
    with pytest.raises(CameraSecretError, match="camera_secret_provider_unconfigured"):
        UnconfiguredCameraSecretProvider().get("camera/ref")
    assert isinstance(
        build_camera_secret_provider("unconfigured", None),
        UnconfiguredCameraSecretProvider,
    )
    with pytest.raises(ValueError, match="incomplete"):
        build_camera_secret_provider("file", None)


def test_onvif_egress_rules_are_exact_and_private(tmp_path: Path) -> None:
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(
        json.dumps(
            {
                "version": 1,
                "rules": [
                    {
                        "scheme": "https",
                        "host": "10.20.30.40",
                        "port": 443,
                        "approved_addresses": ["10.20.30.40/32"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rules = load_onvif_egress_rules(str(rules_file))
    policy = OnvifNetworkPolicy(rules=rules, environment="production")

    policy.validate("https://10.20.30.40/onvif/device_service")
    for unsafe in (
        "http://10.20.30.40/onvif/device_service",
        "https://10.20.30.41/onvif/device_service",
        "https://operator:secret@10.20.30.40/onvif/device_service",
        "https://10.20.30.40/onvif/device_service?next=public",
    ):
        with pytest.raises(StreamNetworkPolicyError):
            policy.validate(unsafe)


def test_onvif_http_requires_nonproduction_lab_opt_in() -> None:
    rule = OnvifEgressRule(
        scheme="http",
        host="127.0.0.1",
        port=8081,
        approved_addresses=(ipaddress.ip_network("127.0.0.1/32"),),
    )
    with pytest.raises(StreamNetworkPolicyError, match="private lab"):
        OnvifNetworkPolicy(
            rules=(rule,), environment="test", lab_http_enabled=False
        ).validate("http://127.0.0.1:8081/onvif/device_service")
    OnvifNetworkPolicy(
        rules=(rule,), environment="test", lab_http_enabled=True
    ).validate("http://127.0.0.1:8081/onvif/device_service")


@pytest.mark.parametrize(
    "locator",
    [
        "https://camera.private.test/" + ("a" * 2050),
        "https://camera.private.test/onvif/\nservice",
        "https://camera.private.test/onvif/ service",
        "https://camera.private.test/onvif/\x7fservice",
        "https://camara-\N{LATIN SMALL LETTER N WITH TILDE}.private.test/onvif/device_service",
        "https://[fe80::1%25ethernet]/onvif/device_service",
    ],
)
def test_onvif_policy_rejects_ambiguous_or_unsafe_urls(locator: str) -> None:
    with pytest.raises(StreamNetworkPolicyError):
        OnvifNetworkPolicy(environment="production").authorize(locator)


def test_onvif_discovery_network_parser_is_strict() -> None:
    assert parse_private_ipv4_networks(None) == ()
    assert parse_private_ipv4_networks("  ") == ()
    assert parse_private_ipv4_networks("10.20.0.0/16,127.0.0.0/8") == (
        ipaddress.ip_network("10.20.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
    )
    with pytest.raises(ValueError, match="1 to 32"):
        parse_private_ipv4_networks(",".join(["10.0.0.0/8"] * 33))
    with pytest.raises(ValueError, match="invalid CIDR"):
        parse_private_ipv4_networks("10.0.0.1/24")
    for unsafe in ("8.8.8.0/24", "224.0.0.0/4", "169.254.0.0/16", "::1/128"):
        with pytest.raises(ValueError, match="private or loopback"):
            parse_private_ipv4_networks(unsafe)


def test_onvif_control_and_discovery_settings_fail_closed() -> None:
    with pytest.raises(ValueError, match="control is forbidden"):
        Settings(environment="production", onvif_control_enabled=True)
    with pytest.raises(ValueError, match="WS-Discovery is forbidden"):
        Settings(environment="production", onvif_discovery_enabled=True)
    with pytest.raises(ValueError, match="INTERFACE is required"):
        Settings(environment="test", onvif_discovery_enabled=True)
    with pytest.raises(ValueError, match="ALLOWED_NETWORKS is required"):
        Settings(
            environment="test",
            onvif_discovery_enabled=True,
            onvif_discovery_interface="127.0.0.1",
        )
    with pytest.raises(ValueError, match="IPv4 address"):
        Settings(environment="test", onvif_discovery_interface="camera.local")
    with pytest.raises(ValueError, match="IPv4 address"):
        Settings(environment="test", onvif_discovery_interface="::1")
    with pytest.raises(ValueError, match="private address"):
        Settings(environment="test", onvif_discovery_interface="8.8.8.8")
    with pytest.raises(ValueError, match="approved network"):
        Settings(
            environment="test",
            onvif_discovery_interface="10.20.31.5",
            onvif_discovery_allowed_networks=(ipaddress.ip_network("10.20.30.0/24"),),
        )
    with pytest.raises(ValueError, match="between 0.1 and 5"):
        Settings(environment="test", onvif_discovery_timeout_seconds=6)
    with pytest.raises(ValueError, match="between 1 and 64"):
        Settings(environment="test", onvif_discovery_max_results=65)


def test_settings_load_discovery_environment_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HCAM_ENVIRONMENT", "test")
    monkeypatch.setenv("HCAM_ONVIF_CONTROL_ENABLED", "true")
    monkeypatch.setenv("HCAM_ONVIF_DISCOVERY_ENABLED", "true")
    monkeypatch.setenv("HCAM_ONVIF_DISCOVERY_INTERFACE", "127.0.0.1")
    monkeypatch.setenv("HCAM_ONVIF_DISCOVERY_ALLOWED_NETWORKS", "127.0.0.0/8")
    monkeypatch.setenv("HCAM_ONVIF_DISCOVERY_TIMEOUT_SECONDS", "0.5")
    monkeypatch.setenv("HCAM_ONVIF_DISCOVERY_MAX_RESULTS", "8")
    settings = Settings.from_environment()
    assert settings.onvif_control_enabled is True
    assert settings.onvif_discovery_enabled is True
    assert settings.onvif_discovery_interface == "127.0.0.1"
    assert settings.onvif_discovery_allowed_networks == (
        ipaddress.ip_network("127.0.0.0/8"),
    )
    assert settings.onvif_discovery_timeout_seconds == 0.5
    assert settings.onvif_discovery_max_results == 8


def test_settings_reject_production_file_secrets_and_http_rules(tmp_path: Path) -> None:
    rule = OnvifEgressRule(
        scheme="http",
        host="10.0.0.8",
        port=80,
        approved_addresses=(ipaddress.ip_network("10.0.0.8/32"),),
    )
    with pytest.raises(ValueError, match="file camera secret provider"):
        Settings(
            environment="production",
            camera_secret_provider="file",
            camera_secret_root=tmp_path,
        )
    with pytest.raises(ValueError, match="must use HTTPS"):
        Settings(environment="production", onvif_egress_rules=(rule,))


def test_settings_validate_camera_secret_and_ca_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must be unconfigured or file"):
        Settings(camera_secret_provider="vault")
    with pytest.raises(ValueError, match="required"):
        Settings(camera_secret_provider="file")
    with pytest.raises(ValueError, match="requires"):
        Settings(camera_secret_root=tmp_path)
    with pytest.raises(ValueError, match="forbidden in production"):
        Settings(environment="production", onvif_lab_http_enabled=True)
    with pytest.raises(ValueError, match="regular file"):
        Settings(onvif_ca_bundle=tmp_path / "missing-ca.pem")
    ca_bundle = tmp_path / "camera-ca.pem"
    ca_bundle.write_text("synthetic-ca", encoding="ascii")
    configured = Settings(
        environment="test",
        camera_secret_provider="file",
        camera_secret_root=tmp_path,
        onvif_ca_bundle=ca_bundle,
    )
    assert configured.camera_secret_root == tmp_path.resolve()
    assert configured.onvif_ca_bundle == ca_bundle.resolve()


def test_settings_load_onvif_environment_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(
        json.dumps(
            {
                "version": 1,
                "rules": [
                    {
                        "scheme": "http",
                        "host": "127.0.0.1",
                        "port": 8081,
                        "approved_addresses": ["127.0.0.1/32"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HCAM_ENVIRONMENT", "test")
    monkeypatch.setenv("HCAM_ONVIF_EGRESS_RULES_FILE", str(rules_file))
    monkeypatch.setenv("HCAM_ONVIF_LAB_HTTP_ENABLED", "true")
    monkeypatch.setenv("HCAM_CAMERA_SECRET_PROVIDER", "file")
    monkeypatch.setenv("HCAM_CAMERA_SECRET_ROOT", str(tmp_path))
    settings = Settings.from_environment()
    assert settings.onvif_lab_http_enabled is True
    assert settings.camera_secret_provider == "file"
    assert settings.onvif_egress_rules[0].port == 8081


def test_onvif_hostname_resolution_must_remain_private_and_approved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rule = OnvifEgressRule(
        scheme="https",
        host="camera.private.test",
        port=8443,
        approved_addresses=(ipaddress.ip_network("10.10.0.0/16"),),
    )
    policy = OnvifNetworkPolicy(rules=(rule,), environment="production")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.10.1.5", 8443))
        ],
    )
    policy.validate("https://camera.private.test:8443/onvif/device_service")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 8443))
        ],
    )
    with pytest.raises(StreamNetworkPolicyError, match="unsafe"):
        policy.validate("https://camera.private.test:8443/onvif/device_service")
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.20.1.5", 8443))
        ],
    )
    with pytest.raises(StreamNetworkPolicyError, match="approved"):
        policy.validate("https://camera.private.test:8443/onvif/device_service")


def test_onvif_hostname_resolution_failure_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rule = OnvifEgressRule(
        scheme="https",
        host="camera.private.test",
        port=443,
        approved_addresses=(ipaddress.ip_network("10.0.0.0/8"),),
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("DNS unavailable")),
    )
    with pytest.raises(StreamNetworkPolicyError, match="resolved"):
        OnvifNetworkPolicy(rules=(rule,), environment="production").validate(
            "https://camera.private.test/onvif/device_service"
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"version": 2, "rules": []},
        {"version": 1, "rules": [{"scheme": "https"}]},
        {
            "version": 1,
            "rules": [
                {
                    "scheme": "https",
                    "host": "*",
                    "port": 443,
                    "approved_addresses": ["10.0.0.0/8"],
                }
            ],
        },
        {
            "version": 1,
            "rules": [
                {
                    "scheme": "https",
                    "host": "camara-\N{LATIN SMALL LETTER N WITH TILDE}.private.test",
                    "port": 443,
                    "approved_addresses": ["10.0.0.0/8"],
                }
            ],
        },
        {
            "version": 1,
            "rules": [
                {
                    "scheme": "https",
                    "host": "fe80::1%ethernet",
                    "port": 443,
                    "approved_addresses": ["fe80::1/128"],
                }
            ],
        },
    ],
)
def test_onvif_egress_rule_parser_rejects_unsafe_shapes(
    tmp_path: Path, payload: dict[str, object]
) -> None:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        load_onvif_egress_rules(str(path))
