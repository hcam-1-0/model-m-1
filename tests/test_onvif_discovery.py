from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from hcam.camera_registry.models import utc_now
from hcam.main import create_app
from hcam.security.auth import PLATFORM_ADMIN, Principal
from hcam.settings import Settings
from hcam.streams.models import OnvifOperationRun
from hcam.streams.onvif_discovery import (
    OnvifDiscoveryDisabledError,
    OnvifDiscoveryEngine,
    OnvifDiscoveryRuntimeError,
    OnvifDiscoveryService,
    build_onvif_discovery_engine,
)


_MATCH = b"""<?xml version="1.0"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
 xmlns:a="http://www.w3.org/2005/08/addressing">
 <s:Body><d:ProbeMatches><d:ProbeMatch>
  <a:EndpointReference><a:Address>urn:uuid:camera-01</a:Address></a:EndpointReference>
  <d:Types>dn:NetworkVideoTransmitter tds:Device</d:Types>
  <d:Scopes>onvif://www.onvif.org/name/H-CAM onvif://www.onvif.org/location/Lab</d:Scopes>
  <d:XAddrs>http://10.20.30.40/onvif/device_service http://169.254.169.254/meta
   http://camera.local/onvif/device_service http://operator:secret@10.20.30.40/onvif</d:XAddrs>
 </d:ProbeMatch></d:ProbeMatches></s:Body>
</s:Envelope>"""


class _FakeSocket:
    def __init__(
        self,
        responses: list[bytes] | None = None,
        *,
        fail_on_send: bool = False,
    ) -> None:
        self.sent: list[tuple[bytes, tuple[str, int]]] = []
        self.bound = None
        self.closed = False
        self.responses = list(responses if responses is not None else [_MATCH])
        self.fail_on_send = fail_on_send

    def setsockopt(self, *_args) -> None:
        return None

    def settimeout(self, _timeout: float) -> None:
        return None

    def bind(self, address) -> None:
        self.bound = address

    def sendto(self, payload: bytes, address) -> None:
        if self.fail_on_send:
            raise OSError("synthetic discovery failure")
        self.sent.append((payload, address))

    def recvfrom(self, _maximum: int):
        if self.responses:
            return self.responses.pop(0), ("10.20.30.40", 3702)
        raise socket.timeout

    def close(self) -> None:
        self.closed = True


def test_ws_discovery_is_bounded_and_filters_unapproved_xaddrs() -> None:
    fake = _FakeSocket()
    engine = OnvifDiscoveryEngine(
        interface_address=ipaddress.IPv4Address("10.20.30.5"),
        allowed_networks=(ipaddress.ip_network("10.20.30.0/24"),),
        timeout_seconds=0.1,
        max_results=4,
        socket_factory=lambda *_args: fake,
    )

    result = engine.discover(operation_id="ovf_" + "a" * 32)

    assert result.result_count == 1
    assert result.matches[0].endpoint_reference == "urn:uuid:camera-01"
    assert result.matches[0].xaddrs == [
        "http://10.20.30.40/onvif/device_service"
    ]
    assert fake.bound == ("10.20.30.5", 0)
    assert fake.sent[0][1] == ("239.255.255.250", 3702)
    assert b"NetworkVideoTransmitter" in fake.sent[0][0]
    assert fake.closed is True


def test_ws_discovery_deduplicates_and_honors_result_limit() -> None:
    fake = _FakeSocket([_MATCH, _MATCH])
    engine = OnvifDiscoveryEngine(
        interface_address=ipaddress.IPv4Address("10.20.30.5"),
        allowed_networks=(ipaddress.ip_network("10.20.30.0/24"),),
        timeout_seconds=0.1,
        max_results=2,
        socket_factory=lambda *_args: fake,
    )
    assert engine.discover(operation_id="ovf_" + "b" * 32).result_count == 1

    limited = _FakeSocket([_MATCH])
    result = OnvifDiscoveryEngine(
        interface_address=ipaddress.IPv4Address("10.20.30.5"),
        allowed_networks=(ipaddress.ip_network("10.20.30.0/24"),),
        timeout_seconds=0.1,
        max_results=1,
        socket_factory=lambda *_args: limited,
    ).discover(operation_id="ovf_" + "c" * 32)
    assert result.result_count == 1


def test_ws_discovery_rejects_malformed_and_unsafe_matches() -> None:
    engine = OnvifDiscoveryEngine(
        interface_address=ipaddress.IPv4Address("10.20.30.5"),
        allowed_networks=(ipaddress.ip_network("10.20.30.0/24"),),
        timeout_seconds=0.1,
        max_results=2,
    )
    assert engine._parse(b"<not-closed") == []
    assert engine._parse(b"x" * (256 * 1024 + 1)) == []
    assert engine._parse(
        b"<Envelope><ProbeMatch><XAddrs>https://8.8.8.8/device</XAddrs>"
        b"</ProbeMatch></Envelope>"
    ) == []
    for unsafe in (
        "ftp://10.20.30.40/device",
        "http://[::1]/device",
        "http://10.20.30.40:invalid/device",
        "http://10.20.30.40/device?secret=x",
        "http://10.20.30.40/device#fragment",
    ):
        assert engine._approved_xaddr(unsafe) is False


def test_ws_discovery_normalizes_socket_failure() -> None:
    fake = _FakeSocket(fail_on_send=True)
    engine = OnvifDiscoveryEngine(
        interface_address=ipaddress.IPv4Address("10.20.30.5"),
        allowed_networks=(ipaddress.ip_network("10.20.30.0/24"),),
        timeout_seconds=0.1,
        max_results=1,
        socket_factory=lambda *_args: fake,
    )
    with pytest.raises(OnvifDiscoveryRuntimeError) as error:
        engine.discover(operation_id="ovf_" + "d" * 32)
    assert error.value.reason_code == "ws_discovery_network_error"
    assert fake.closed is True

    factory_failure = OnvifDiscoveryEngine(
        interface_address=ipaddress.IPv4Address("10.20.30.5"),
        allowed_networks=(ipaddress.ip_network("10.20.30.0/24"),),
        timeout_seconds=0.1,
        max_results=1,
        socket_factory=lambda *_args: (_ for _ in ()).throw(
            OSError("socket unavailable")
        ),
    )
    with pytest.raises(OnvifDiscoveryRuntimeError) as factory_error:
        factory_failure.discover(operation_id="ovf_" + "e" * 32)
    assert factory_error.value.reason_code == "ws_discovery_network_error"


def test_ws_discovery_requires_explicit_configuration() -> None:
    with pytest.raises(OnvifDiscoveryDisabledError):
        build_onvif_discovery_engine(Settings(environment="test"))


def test_ws_discovery_api_is_admin_only_and_disabled_by_default(
    imported_app,
    viewer_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    viewer = {
        **viewer_headers,
        "X-HCAM-Reason": "Unauthorized discovery role verification",
    }
    with TestClient(imported_app) as client:
        denied = client.post("/onvif/discovery-runs", headers=viewer)
        disabled = client.post("/onvif/discovery-runs", headers=admin_headers)
    assert denied.status_code == 403
    assert disabled.status_code == 409
    assert "not enabled" in disabled.text


def test_ws_discovery_service_records_success_and_failure(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'discovery.db').as_posix()}",
        create_schema=True,
        environment="test",
        onvif_discovery_enabled=True,
        onvif_discovery_interface="127.0.0.1",
        onvif_discovery_allowed_networks=(ipaddress.ip_network("127.0.0.0/8"),),
        onvif_discovery_timeout_seconds=0.1,
    )
    app = create_app(settings)
    app.state.database.create_schema()
    principal = Principal(
        actor_id="discovery-admin",
        roles=frozenset({PLATFORM_ADMIN}),
        departments=frozenset({"*"}),
        authentication_method="test",
    )
    loopback_match = _MATCH.replace(b"10.20.30.40", b"127.0.0.2")
    try:
        with app.state.database.session_factory() as session:
            success = OnvifDiscoveryService(
                session,
                settings,
                socket_factory=lambda *_args: _FakeSocket([loopback_match]),
            ).run(
                principal=principal,
                reason="Authorized isolated discovery success test",
                request_id="request-success",
            )
        with app.state.database.session_factory() as session:
            with pytest.raises(OnvifDiscoveryRuntimeError):
                OnvifDiscoveryService(
                    session,
                    settings,
                    socket_factory=lambda *_args: _FakeSocket(fail_on_send=True),
                ).run(
                    principal=principal,
                    reason="Authorized isolated discovery failure test",
                    request_id="request-failure",
                )
        with app.state.database.session_factory() as session:
            runs = session.scalars(
                select(OnvifOperationRun).order_by(OnvifOperationRun.requested_at)
            ).all()
    finally:
        app.state.database.dispose()
    assert success.result_count == 1
    assert [run.outcome for run in runs] == ["success", "failure"]
    assert runs[1].reason_code == "ws_discovery_network_error"


def test_ws_discovery_audit_failure_is_normalized() -> None:
    settings = Settings(
        environment="test",
        onvif_discovery_enabled=True,
        onvif_discovery_interface="127.0.0.1",
        onvif_discovery_allowed_networks=(ipaddress.ip_network("127.0.0.0/8"),),
    )
    session = MagicMock()
    session.begin.side_effect = SQLAlchemyError("database unavailable")
    service = OnvifDiscoveryService(
        session, settings, socket_factory=lambda *_args: _FakeSocket([])
    )
    principal = Principal(
        actor_id="discovery-admin",
        roles=frozenset({PLATFORM_ADMIN}),
        departments=frozenset({"*"}),
        authentication_method="test",
    )
    with pytest.raises(OnvifDiscoveryRuntimeError) as error:
        service._begin_record(
            "ovf_" + "f" * 32,
            principal,
            "Authorized discovery audit failure test",
            "request-audit",
            utc_now(),
        )
    assert error.value.reason_code == "ws_discovery_audit_unavailable"


@pytest.mark.parametrize(
    "settings",
    [
        {"environment": "production", "onvif_discovery_enabled": True},
        {
            "environment": "test",
            "onvif_discovery_enabled": True,
            "onvif_discovery_interface": "10.20.31.5",
            "onvif_discovery_allowed_networks": (
                ipaddress.ip_network("10.20.30.0/24"),
            ),
        },
    ],
)
def test_ws_discovery_settings_fail_closed(settings: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Settings(**settings)
