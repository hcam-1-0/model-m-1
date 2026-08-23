from __future__ import annotations

import ipaddress
import json
import ssl
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from hcam.streams import onvif
from hcam.streams.capabilities import (
    CapabilityDiscoveryEngine,
    CapabilityDiscoveryError,
    CapabilityEndpointConfig,
)
from hcam.streams.network import OnvifEgressRule, OnvifNetworkPolicy
from hcam.streams.onvif import (
    HttpxOnvifTransport,
    OnvifDeviceInformation,
    OnvifMediaCapabilities,
    OnvifMediaProfile,
    OnvifResolutionError,
)
from hcam.streams.onvif_simulator import handler_for
from hcam.streams.secrets import (
    CameraCredentials,
    FileCameraSecretProvider,
    UnconfiguredCameraSecretProvider,
)


def _write_private_ca_and_server_certificate(tmp_path: Path) -> tuple[Path, Path, Path]:
    now = datetime.now(UTC).replace(tzinfo=None)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "H-CAM Test CA")])
    ca_certificate = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=None,
                decipher_only=None,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_name = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "camera.private.test")]
    )
    server_certificate = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=None,
                decipher_only=None,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("camera.private.test")]),
            critical=False,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(server_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    ca_path = tmp_path / "camera-ca.pem"
    certificate_path = tmp_path / "camera.pem"
    key_path = tmp_path / "camera-key.pem"
    ca_path.write_bytes(ca_certificate.public_bytes(serialization.Encoding.PEM))
    certificate_path.write_bytes(
        server_certificate.public_bytes(serialization.Encoding.PEM)
    )
    key_path.write_bytes(
        server_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return ca_path, certificate_path, key_path


def test_transport_pins_approved_dns_and_validates_private_ca_sni(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response_body = b'<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" />'

    class Handler(BaseHTTPRequestHandler):
        observed_host: str | None = None

        def do_POST(self) -> None:
            type(self).observed_host = self.headers.get("Host")
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(200)
            self.send_header("Content-Type", "application/soap+xml")
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, *_args) -> None:
            return

    ca_path, certificate_path, key_path = _write_private_ca_and_server_certificate(
        tmp_path
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls_context.load_cert_chain(certificate_path, key_path)
    server.socket = tls_context.wrap_socket(server.socket, server_side=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    policy = OnvifNetworkPolicy(
        rules=(
            OnvifEgressRule(
                scheme="https",
                host="camera.private.test",
                port=port,
                approved_addresses=(ipaddress.ip_network("127.0.0.1/32"),),
            ),
        ),
        environment="test",
    )
    monkeypatch.setattr(
        OnvifNetworkPolicy,
        "_resolve",
        staticmethod(lambda _host, _port: (ipaddress.ip_address("127.0.0.1"),)),
    )
    service_url = f"https://camera.private.test:{port}/onvif/device_service"
    target = policy.authorize(service_url)
    try:
        root = HttpxOnvifTransport(
            timeout_seconds=2,
            ca_bundle=ca_path,
            network_policy=policy,
        ).request(
            service_url,
            b"<Envelope />",
            action="synthetic-action",
            credentials=None,
            auth_mode="none",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert target.request_url == f"https://127.0.0.1:{port}/onvif/device_service"
    assert target.host_header == f"camera.private.test:{port}"
    assert target.sni_hostname == b"camera.private.test"
    assert Handler.observed_host == f"camera.private.test:{port}"
    assert root.tag.endswith("Envelope")


def _engine(
    tmp_path: Path,
    port: int,
    *,
    password: str = "synthetic-password",
) -> CapabilityDiscoveryEngine:
    secret = tmp_path / "cameras" / "cam-01"
    secret.parent.mkdir(exist_ok=True)
    secret.write_text(
        json.dumps({"username": "operator", "password": password}),
        encoding="utf-8",
    )
    return CapabilityDiscoveryEngine(
        network_policy=OnvifNetworkPolicy(
            rules=(
                OnvifEgressRule(
                    scheme="http",
                    host="127.0.0.1",
                    port=port,
                    approved_addresses=(
                        ipaddress.ip_network("127.0.0.1/32"),
                    ),
                ),
            ),
            environment="test",
            lab_http_enabled=True,
        ),
        secret_provider=FileCameraSecretProvider(tmp_path),
        transport=HttpxOnvifTransport(timeout_seconds=2),
    )


def _endpoint(port: int, auth_mode: str) -> CapabilityEndpointConfig:
    return CapabilityEndpointConfig(
        stream_id="str_" + "a" * 32,
        camera_id="synthetic:camera-01",
        locator=f"http://127.0.0.1:{port}/onvif/media_service",
        protocol="http",
        management_locator=f"http://127.0.0.1:{port}/onvif/device_service",
        onvif_auth_mode=auth_mode,
        secret_ref="cameras/cam-01" if auth_mode != "none" else None,
    )


@pytest.mark.parametrize(
    "auth_mode",
    [
        "none",
        "wsse_password_digest",
        "http_digest",
        "wsse_and_http_digest",
    ],
)
def test_full_discovery_supports_all_explicit_authentication_modes(
    tmp_path: Path,
    auth_mode: str,
) -> None:
    credentials = (
        {"username": "operator", "password": "synthetic-password"}
        if auth_mode != "none"
        else {}
    )
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        handler_for(
            "rtsp://127.0.0.1:8554/synthetic-01",
            auth_mode=auth_mode,
            **credentials,
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        result = _engine(tmp_path, port).discover(_endpoint(port, auth_mode))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.source == "device_and_media"
    assert result.completeness == "complete"
    assert result.payload["device"]["manufacturer"] == "H-CAM Synthetic"
    assert result.payload["media"]["maximum_profiles"] == 8
    assert result.payload["warnings"] == []


def test_secret_rotation_is_used_without_restarting_provider(tmp_path: Path) -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        handler_for(
            "rtsp://127.0.0.1:8554/synthetic-01",
            auth_mode="http_digest",
            username="operator",
            password="correct-password",
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        engine = _engine(tmp_path, port, password="wrong-password")
        with pytest.raises(CapabilityDiscoveryError) as denied:
            engine.discover(_endpoint(port, "http_digest"))
        assert denied.value.reason_code == "unauthorized"
        (tmp_path / "cameras" / "cam-01").write_text(
            json.dumps(
                {"username": "operator", "password": "correct-password"}
            ),
            encoding="utf-8",
        )
        result = engine.discover(_endpoint(port, "http_digest"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result.completeness == "complete"


def test_wsse_fixture_rejects_replayed_username_token() -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        handler_for(
            "rtsp://127.0.0.1:8554/synthetic-01",
            auth_mode="wsse_password_digest",
            username="operator",
            password="synthetic-password",
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        payload = onvif._soap_envelope(
            onvif._GET_DEVICE_INFORMATION_BODY,
            credentials=CameraCredentials("operator", "synthetic-password"),
            auth_mode="wsse_password_digest",
        )
        transport = HttpxOnvifTransport(timeout_seconds=2)
        url = f"http://127.0.0.1:{port}/onvif/device_service"
        transport.request(
            url,
            payload,
            action=onvif._GET_DEVICE_INFORMATION_ACTION,
            credentials=None,
            auth_mode="none",
        )
        with pytest.raises(OnvifResolutionError) as replay:
            transport.request(
                url,
                payload,
                action=onvif._GET_DEVICE_INFORMATION_ACTION,
                credentials=None,
                auth_mode="none",
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert replay.value.reason_code == "unauthorized"


def test_hostile_advertised_media_url_is_not_contacted(tmp_path: Path) -> None:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        handler_for(
            "rtsp://127.0.0.1:8554/synthetic-01",
            advertised_media_url="http://169.254.169.254/latest/meta-data",
        ),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        result = _engine(tmp_path, port).discover(_endpoint(port, "none"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert result.completeness == "partial"
    assert "onvif_advertised_service_denied" in result.payload["warnings"]
    assert result.payload["media"] is not None


def test_discovery_fails_closed_for_missing_or_unavailable_credentials(
    tmp_path: Path,
) -> None:
    endpoint = _endpoint(8081, "http_digest")
    engine = CapabilityDiscoveryEngine(
        network_policy=OnvifNetworkPolicy(),
        secret_provider=UnconfiguredCameraSecretProvider(),
        transport=HttpxOnvifTransport(),
    )
    with pytest.raises(CapabilityDiscoveryError) as unavailable:
        engine.discover(endpoint)
    assert unavailable.value.reason_code == "camera_secret_provider_unconfigured"
    with pytest.raises(CapabilityDiscoveryError) as missing:
        engine.discover(replace(endpoint, secret_ref=None))
    assert missing.value.reason_code == "credentials_unavailable"


def test_discovery_records_partial_optional_sections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _engine(tmp_path, 8081)
    monkeypatch.setattr(
        "hcam.streams.capabilities.get_device_information",
        lambda *_args: OnvifDeviceInformation("H-CAM", "Test", None, None, None),
    )
    monkeypatch.setattr(
        "hcam.streams.capabilities.get_services",
        lambda *_args: (_ for _ in ()).throw(
            OnvifResolutionError("onvif_invalid_services")
        ),
    )
    monkeypatch.setattr(
        "hcam.streams.capabilities.get_device_clock_offset",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OnvifResolutionError("onvif_invalid_device_time")
        ),
    )
    monkeypatch.setattr(
        onvif.OnvifCapabilityDiscovery,
        "discover",
        lambda *_args, **_kwargs: OnvifMediaCapabilities(
            snapshot_uri=True,
            rotation=None,
            video_source_mode=None,
            osd=None,
            temporary_osd_text=None,
            exi_compression=None,
            maximum_profiles=1,
            profiles=(
                OnvifMediaProfile(
                    token="profile",
                    name=None,
                    fixed=None,
                    video_encoding=None,
                    width=None,
                    height=None,
                    frame_rate_limit=None,
                    audio_encoding=None,
                    ptz_configured=False,
                    analytics_configured=False,
                    metadata_configured=False,
                ),
            ),
        ),
    )
    result = engine.discover(_endpoint(8081, "none"))
    assert result.completeness == "partial"
    assert "onvif_invalid_services" in result.payload["warnings"]
    assert "onvif_invalid_device_time" in result.payload["warnings"]


def test_media_only_transport_failure_is_retryable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = _engine(tmp_path, 8081)
    monkeypatch.setattr(
        onvif.OnvifCapabilityDiscovery,
        "discover",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OnvifResolutionError("unreachable")
        ),
    )
    endpoint = _endpoint(8081, "none")
    media_only = CapabilityEndpointConfig(
        stream_id=endpoint.stream_id,
        camera_id=endpoint.camera_id,
        locator=endpoint.locator,
        protocol=endpoint.protocol,
        management_locator=None,
        onvif_auth_mode="none",
        secret_ref=None,
    )
    with pytest.raises(CapabilityDiscoveryError) as captured:
        engine.discover(media_only)
    assert captured.value.reason_code == "unreachable"
    assert captured.value.retryable is True


@pytest.mark.parametrize(
    ("status", "payload", "reason"),
    [
        (302, b"", "onvif_redirect_denied"),
        (500, b"", "onvif_http_error"),
        (200, b"x" * 64, "onvif_response_too_large"),
        (200, b"<broken", "onvif_invalid_response"),
    ],
)
def test_httpx_transport_normalizes_bounded_failures(
    status: int,
    payload: bytes,
    reason: str,
) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(status)
            if status == 302:
                self.send_header("Location", "/redirected")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/onvif/device_service"
        with pytest.raises(OnvifResolutionError) as captured:
            HttpxOnvifTransport(max_response_bytes=32).request(
                url,
                b"<Envelope />",
                action="synthetic-action",
                credentials=None,
                auth_mode="none",
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert captured.value.reason_code == reason
