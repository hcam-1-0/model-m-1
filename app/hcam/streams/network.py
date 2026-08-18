from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit


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
            addresses = {
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(normalized, None)
            }
        except (OSError, ValueError) as exc:
            raise StreamNetworkPolicyError(
                "stream host is not resolvable or explicitly allowed"
            ) from exc
        if not addresses or not all(address.is_loopback for address in addresses):
            raise StreamNetworkPolicyError(
                "stream host is outside the probe network allowlist"
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
