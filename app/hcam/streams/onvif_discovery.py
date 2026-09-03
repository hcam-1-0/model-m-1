from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from urllib.parse import urlsplit
from uuid import uuid4
# Stdlib ElementTree is retained only for element types and ParseError.
from xml.etree import ElementTree  # nosec B405

from defusedxml import ElementTree as DefusedElementTree
from defusedxml.common import DefusedXmlException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import utc_now
from hcam.security.auth import Principal
from hcam.settings import Settings
from hcam.streams.models import OnvifOperationRun
from hcam.streams.schemas import OnvifDiscoveryMatchResponse, OnvifDiscoveryResponse


_DISCOVERY_ADDRESS = ("239.255.255.250", 3702)
_MAX_DATAGRAM_BYTES = 256 * 1024
_PROBE = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:a="http://www.w3.org/2005/08/addressing"
 xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
 xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
 <s:Header>
  <a:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>
  <a:MessageID>urn:uuid:{message_id}</a:MessageID>
  <a:ReplyTo><a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address></a:ReplyTo>
  <a:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>
 </s:Header>
 <s:Body><d:Probe><d:Types>dn:NetworkVideoTransmitter</d:Types></d:Probe></s:Body>
</s:Envelope>"""


class OnvifDiscoveryDisabledError(RuntimeError):
    pass


class OnvifDiscoveryRuntimeError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class OnvifDiscoveryEngine:
    interface_address: ipaddress.IPv4Address
    allowed_networks: tuple[ipaddress.IPv4Network, ...]
    timeout_seconds: float
    max_results: int
    socket_factory: Callable[..., socket.socket] = socket.socket

    def discover(self, *, operation_id: str) -> OnvifDiscoveryResponse:
        probe = _PROBE.format(message_id=uuid4()).encode("utf-8")
        matches: list[OnvifDiscoveryMatchResponse] = []
        seen: set[tuple[str | None, tuple[str, ...]]] = set()
        sock: socket.socket | None = None
        try:
            sock = self.socket_factory(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
            )
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_IF,
                socket.inet_aton(str(self.interface_address)),
            )
            sock.settimeout(self.timeout_seconds)
            sock.bind((str(self.interface_address), 0))
            sock.sendto(probe, _DISCOVERY_ADDRESS)
            deadline = monotonic() + self.timeout_seconds
            while len(matches) < self.max_results:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    break
                sock.settimeout(remaining)
                try:
                    document, _sender = sock.recvfrom(_MAX_DATAGRAM_BYTES)
                except (TimeoutError, socket.timeout):
                    break
                for match in self._parse(document):
                    key = (match.endpoint_reference, tuple(match.xaddrs))
                    if key in seen:
                        continue
                    seen.add(key)
                    matches.append(match)
                    if len(matches) >= self.max_results:
                        break
        except OSError as exc:
            raise OnvifDiscoveryRuntimeError("ws_discovery_network_error") from exc
        finally:
            if sock is not None:
                sock.close()
        return OnvifDiscoveryResponse(
            operation_id=operation_id,
            interface_address=str(self.interface_address),
            result_count=len(matches),
            matches=matches,
            observed_at=utc_now(),
        )

    def _parse(self, document: bytes) -> list[OnvifDiscoveryMatchResponse]:
        if len(document) > _MAX_DATAGRAM_BYTES:
            return []
        try:
            root = DefusedElementTree.fromstring(document)
        except (ElementTree.ParseError, DefusedXmlException):
            return []
        results: list[OnvifDiscoveryMatchResponse] = []
        for element in root.iter():
            if _local_name(element) != "ProbeMatch":
                continue
            xaddrs = []
            for value in _split_text(_first_text(element, "XAddrs"), 16, 4096):
                if self._approved_xaddr(value):
                    xaddrs.append(value)
            if not xaddrs:
                continue
            results.append(
                OnvifDiscoveryMatchResponse(
                    endpoint_reference=_bounded(_first_text(element, "Address"), 500),
                    types=_split_text(_first_text(element, "Types"), 16, 255),
                    scopes=_split_text(_first_text(element, "Scopes"), 32, 500),
                    xaddrs=xaddrs,
                )
            )
        return results

    def _approved_xaddr(self, value: str) -> bool:
        try:
            parsed = urlsplit(value)
            address = ipaddress.ip_address(parsed.hostname or "")
            _port = parsed.port
        except ValueError:
            return False
        return bool(
            parsed.scheme.lower() in {"http", "https"}
            and isinstance(address, ipaddress.IPv4Address)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
            and any(address in network for network in self.allowed_networks)
        )


def build_onvif_discovery_engine(
    settings: Settings,
    *,
    socket_factory: Callable[..., socket.socket] = socket.socket,
) -> OnvifDiscoveryEngine:
    if (
        not settings.onvif_discovery_enabled
        or settings.onvif_discovery_interface is None
        or not settings.onvif_discovery_allowed_networks
    ):
        raise OnvifDiscoveryDisabledError("ONVIF WS-Discovery is not enabled")
    return OnvifDiscoveryEngine(
        interface_address=ipaddress.IPv4Address(settings.onvif_discovery_interface),
        allowed_networks=settings.onvif_discovery_allowed_networks,
        timeout_seconds=settings.onvif_discovery_timeout_seconds,
        max_results=settings.onvif_discovery_max_results,
        socket_factory=socket_factory,
    )


class OnvifDiscoveryService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        *,
        socket_factory: Callable[..., socket.socket] = socket.socket,
    ) -> None:
        self.session = session
        self.engine = build_onvif_discovery_engine(
            settings, socket_factory=socket_factory
        )

    def run(
        self,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
    ) -> OnvifDiscoveryResponse:
        operation_id = f"ovf_{uuid4().hex}"
        requested_at = utc_now()
        started = monotonic()
        self._begin_record(
            operation_id,
            principal,
            reason,
            request_id,
            requested_at,
        )
        try:
            result = self.engine.discover(operation_id=operation_id)
        except OnvifDiscoveryRuntimeError as exc:
            self._complete_record(
                operation_id,
                principal,
                reason,
                request_id,
                requested_at,
                started,
                outcome="failure",
                reason_code=exc.reason_code,
                result_count=0,
            )
            raise
        self._complete_record(
            operation_id,
            principal,
            reason,
            request_id,
            requested_at,
            started,
            outcome="success",
            reason_code=None,
            result_count=result.result_count,
        )
        return result

    def _begin_record(
        self,
        operation_id: str,
        principal: Principal,
        reason: str,
        request_id: str | None,
        requested_at,
    ) -> None:
        try:
            with self.session.begin():
                self.session.add(
                    OnvifOperationRun(
                        operation_id=operation_id,
                        stream_id=None,
                        actor_id=principal.actor_id,
                        operation_type="ws_discovery",
                        outcome="pending",
                        reason_code=None,
                        parameters={},
                        audit_reason=reason.strip(),
                        request_id=request_id,
                        requested_at=requested_at,
                        finished_at=None,
                        duration_ms=None,
                    )
                )
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="platform.onvif.ws_discovery.requested",
                    target_type="onvif_discovery",
                    target_id=operation_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="pending",
                    context={},
                    request_id=request_id,
                )
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OnvifDiscoveryRuntimeError(
                "ws_discovery_audit_unavailable"
            ) from exc

    def _complete_record(
        self,
        operation_id: str,
        principal: Principal,
        reason: str,
        request_id: str | None,
        requested_at,
        started: float,
        *,
        outcome: str,
        reason_code: str | None,
        result_count: int,
    ) -> None:
        finished_at = utc_now()
        try:
            with self.session.begin():
                run = self.session.get(OnvifOperationRun, operation_id)
                if (
                    run is None
                    or run.actor_id != principal.actor_id
                    or run.operation_type != "ws_discovery"
                    or run.outcome != "pending"
                ):
                    raise OnvifDiscoveryRuntimeError(
                        "ws_discovery_audit_unavailable"
                    )
                run.outcome = outcome
                run.reason_code = reason_code
                run.parameters = {"result_count": result_count}
                run.finished_at = finished_at
                run.duration_ms = max(0.0, (monotonic() - started) * 1000)
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="platform.onvif.ws_discovery.completed",
                    target_type="onvif_discovery",
                    target_id=operation_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome=outcome,
                    context={
                        "reason_code": reason_code,
                        "result_count": result_count,
                    },
                    request_id=request_id,
                )
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise OnvifDiscoveryRuntimeError(
                "ws_discovery_audit_unavailable"
            ) from exc


def _local_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _first_text(element: ElementTree.Element, local_name: str) -> str | None:
    for candidate in element.iter():
        if _local_name(candidate) == local_name:
            value = (candidate.text or "").strip()
            return value or None
    return None


def _bounded(value: str | None, maximum: int) -> str | None:
    return value[:maximum] if value else None


def _split_text(value: str | None, maximum_items: int, maximum_length: int) -> list[str]:
    if value is None:
        return []
    return [item[:maximum_length] for item in value.split()[:maximum_items]]
