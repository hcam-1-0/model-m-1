from __future__ import annotations

import ipaddress
import json
import socket
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


class StreamNetworkPolicyError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class StreamNetworkPolicy:
    """Deny network probes unless the destination is loopback or explicitly allowed."""

    allowed_hosts: frozenset[str] = frozenset()

    def validate(self, locator: str) -> None:
        host = urlsplit(locator).hostname
        if host is None:
            raise StreamNetworkPolicyError("stream locator has no host")
        normalized = host.rstrip(".").lower()
        if normalized in self.allowed_hosts:
            return
        try:
            address = ipaddress.ip_address(normalized)
        except ValueError:
            address = None
        if address is not None:
            if address.is_loopback:
                return
            raise StreamNetworkPolicyError(
                "stream host is outside the probe network allowlist"
            )
        raise StreamNetworkPolicyError(
            "stream hostname must be explicitly allowlisted"
        )


def parse_allowed_hosts(value: str | None) -> frozenset[str]:
    if value is None:
        return frozenset()
    hosts = frozenset(
        item.strip().rstrip(".").lower() for item in value.split(",") if item.strip()
    )
    if "*" in hosts:
        raise ValueError("HCAM_STREAM_PROBE_ALLOWED_HOSTS cannot contain a wildcard")
    return hosts


def parse_private_ipv4_networks(
    value: str | None,
) -> tuple[ipaddress.IPv4Network, ...]:
    if value is None or not value.strip():
        return ()
    parts = [item.strip() for item in value.split(",") if item.strip()]
    if not 1 <= len(parts) <= 32:
        raise ValueError(
            "HCAM_ONVIF_DISCOVERY_ALLOWED_NETWORKS requires 1 to 32 CIDRs"
        )
    try:
        networks = tuple(ipaddress.ip_network(item, strict=True) for item in parts)
    except ValueError as exc:
        raise ValueError(
            "HCAM_ONVIF_DISCOVERY_ALLOWED_NETWORKS contains an invalid CIDR"
        ) from exc
    if any(
        not isinstance(network, ipaddress.IPv4Network)
        or network.is_multicast
        or network.is_link_local
        or network.is_unspecified
        or (not network.is_private and not network.is_loopback)
        for network in networks
    ):
        raise ValueError(
            "ONVIF discovery networks must be private or loopback IPv4 CIDRs"
        )
    return networks


@dataclass(frozen=True, slots=True)
class OnvifEgressRule:
    scheme: str
    host: str
    port: int
    approved_addresses: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]


@dataclass(frozen=True, slots=True)
class AuthorizedOnvifTarget:
    request_url: str
    host_header: str
    sni_hostname: bytes | None
    address: ipaddress.IPv4Address | ipaddress.IPv6Address


def load_onvif_egress_rules(path: str | None) -> tuple[OnvifEgressRule, ...]:
    if path is None:
        return ()
    rule_path = Path(path).expanduser()
    try:
        if not rule_path.is_file() or rule_path.stat().st_size > 64 * 1024:
            raise ValueError(
                "HCAM_ONVIF_EGRESS_RULES_FILE must identify a small regular file"
            )
        payload = json.loads(rule_path.read_text(encoding="utf-8"))
    except ValueError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("HCAM_ONVIF_EGRESS_RULES_FILE is invalid") from exc
    if not isinstance(payload, dict) or set(payload) != {"version", "rules"}:
        raise ValueError("ONVIF egress rules must contain version and rules")
    if payload["version"] != 1 or not isinstance(payload["rules"], list):
        raise ValueError("ONVIF egress rules version must be 1")
    if len(payload["rules"]) > 1024:
        raise ValueError("ONVIF egress rules cannot contain more than 1024 entries")
    rules: list[OnvifEgressRule] = []
    for item in payload["rules"]:
        if not isinstance(item, dict) or set(item) != {
            "scheme",
            "host",
            "port",
            "approved_addresses",
        }:
            raise ValueError("each ONVIF egress rule has an invalid shape")
        scheme = item["scheme"]
        host = item["host"]
        port = item["port"]
        addresses = item["approved_addresses"]
        if scheme not in {"http", "https"}:
            raise ValueError("ONVIF egress rule scheme must be HTTP or HTTPS")
        if (
            not isinstance(host, str)
            or not host.strip()
            or host == "*"
            or host != host.strip().rstrip(".").lower()
        ):
            raise ValueError("ONVIF egress rule host must be exact and normalized")
        try:
            host_bytes = host.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("ONVIF egress rule host must use an ASCII A-label") from exc
        if b"%" in host_bytes or any(byte <= 32 or byte == 127 for byte in host_bytes):
            raise ValueError("ONVIF egress rule host is unsafe")
        if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
            raise ValueError("ONVIF egress rule port is invalid")
        if not isinstance(addresses, list) or not 1 <= len(addresses) <= 32:
            raise ValueError("ONVIF egress rule needs approved address ranges")
        try:
            networks = tuple(ipaddress.ip_network(value, strict=True) for value in addresses)
        except (TypeError, ValueError) as exc:
            raise ValueError("ONVIF approved address range is invalid") from exc
        rules.append(
            OnvifEgressRule(
                scheme=scheme,
                host=host,
                port=port,
                approved_addresses=networks,
            )
        )
    return tuple(rules)


@dataclass(frozen=True, slots=True)
class OnvifNetworkPolicy:
    rules: tuple[OnvifEgressRule, ...] = ()
    environment: str = "development"
    lab_http_enabled: bool = False

    def validate(self, locator: str) -> None:
        self.authorize(locator)

    def authorize(self, locator: str) -> AuthorizedOnvifTarget:
        if len(locator) > 2048 or any(
            ord(character) <= 32 or ord(character) == 127 for character in locator
        ):
            raise StreamNetworkPolicyError("ONVIF locator is not a safe HTTP(S) URL")
        parsed = urlsplit(locator)
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or parsed.hostname is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise StreamNetworkPolicyError("ONVIF locator is not a safe HTTP(S) URL")
        scheme = parsed.scheme.lower()
        host = parsed.hostname.rstrip(".").lower()
        try:
            host_bytes = host.encode("ascii")
        except UnicodeEncodeError as exc:
            raise StreamNetworkPolicyError(
                "ONVIF locator host must use an ASCII A-label"
            ) from exc
        if b"%" in host_bytes:
            raise StreamNetworkPolicyError("ONVIF locator host cannot contain a zone identifier")
        try:
            port = parsed.port or (443 if scheme == "https" else 80)
        except ValueError as exc:
            raise StreamNetworkPolicyError("ONVIF locator port is invalid") from exc
        if scheme == "http" and (
            self.environment == "production" or not self.lab_http_enabled
        ):
            raise StreamNetworkPolicyError("ONVIF HTTP is restricted to the private lab")
        rule = next(
            (
                candidate
                for candidate in self.rules
                if candidate.scheme == scheme
                and candidate.host == host
                and candidate.port == port
            ),
            None,
        )
        if rule is None:
            raise StreamNetworkPolicyError(
                "ONVIF destination is outside the exact egress rules"
            )
        addresses = self._resolve(host, port)
        for address in addresses:
            if not _allowed_camera_address(address, environment=self.environment):
                raise StreamNetworkPolicyError("ONVIF destination address is unsafe")
            if not any(address in network for network in rule.approved_addresses):
                raise StreamNetworkPolicyError(
                    "ONVIF destination address is outside the approved ranges"
                )
        address = addresses[0]
        pinned_host = f"[{address}]" if address.version == 6 else str(address)
        original_host = (
            f"[{host}]" if address.version == 6 and host == str(address) else host
        )
        default_port = 443 if scheme == "https" else 80
        host_header = original_host if port == default_port else f"{original_host}:{port}"
        request_url = urlunsplit(
            (scheme, f"{pinned_host}:{port}", parsed.path or "/", "", "")
        )
        return AuthorizedOnvifTarget(
            request_url=request_url,
            host_header=host_header,
            sni_hostname=host_bytes if scheme == "https" else None,
            address=address,
        )

    @staticmethod
    def _resolve(
        host: str, port: int
    ) -> tuple[ipaddress.IPv4Address | ipaddress.IPv6Address, ...]:
        try:
            return (ipaddress.ip_address(host),)
        except ValueError:
            pass
        try:
            addresses = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(
                    host,
                    port,
                    type=socket.SOCK_STREAM,
                    proto=socket.IPPROTO_TCP,
                )
            }
        except (OSError, ValueError) as exc:
            raise StreamNetworkPolicyError("ONVIF destination cannot be resolved") from exc
        if not addresses:
            raise StreamNetworkPolicyError("ONVIF destination cannot be resolved")
        return tuple(sorted(addresses, key=str))


def _allowed_camera_address(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
    *,
    environment: str,
) -> bool:
    if address.is_loopback:
        return environment in {"development", "test"}
    return not (
        address.is_global
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or address.is_reserved
    )
