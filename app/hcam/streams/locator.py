from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


MAX_STREAM_REFERENCE_LENGTH = 4096


def sanitize_stream_reference(value: str | None) -> str | None:
    if not value:
        return None

    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > MAX_STREAM_REFERENCE_LENGTH
        or any(ord(character) < 32 or ord(character) == 127 for character in normalized)
    ):
        return None

    try:
        parsed = urlsplit(normalized)
    except ValueError:
        return None
    if not parsed.scheme and not parsed.netloc:
        return parsed.path or None

    if parsed.scheme.lower() not in {"http", "https", "rtsp", "rtsps"}:
        return None
    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None
    if hostname is None:
        return None

    host = hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if port is not None:
        host = f"{host}:{port}"
    return urlunsplit((parsed.scheme.lower(), host, parsed.path, "", ""))
