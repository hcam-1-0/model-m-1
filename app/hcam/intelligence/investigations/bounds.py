from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Any


MAX_CONTRACT_BYTES = 64 * 1024
MAX_ENTRY_PAYLOAD_BYTES = 16 * 1024
MAX_STRING_BYTES = 4_096
MAX_PAGE_SIZE = 200
MAX_ENTRIES_PER_TIMELINE = 10_000
MAX_RELATIONSHIP_DEPTH = 32
MAX_CORRECTION_CHAIN_DEPTH = 64
MAX_PROVENANCE_NODES = 4_096
MAX_PROVENANCE_EDGES = 8_192
MAX_PROVENANCE_DEPTH = 32
MAX_PROVENANCE_FANOUT = 256
MAX_IMPACT_TARGETS = 5_000
MAX_EXPORT_REFERENCES = 10_000
MAX_JOB_ATTEMPTS = 3
JOB_LEASE_SECONDS = 90
MAX_REASON_BYTES = 2_000

FORBIDDEN_FIELD_PARTS = frozenset(
    {
        "api_key",
        "biometric",
        "credential",
        "dispatch",
        "enforcement",
        "face",
        "image_bytes",
        "media_bytes",
        "owner_detail",
        "password",
        "private_key",
        "raw_source",
        "secret",
        "source_bytes",
        "video_bytes",
        "watchlist",
    }
)
_URL = re.compile(r"(?i)(?:https?|file|rtsp|wss?)://")
_WINDOWS_PATH = re.compile(r"(?i)(?:^|\s)[a-z]:[\\/]")
_SECRET_MATERIAL = re.compile(r"(?i)(?:bearer\s+[a-z0-9._~+/=-]{16,}|-----BEGIN)")


class BoundsError(ValueError):
    pass


def bounded_reason(value: str) -> str:
    encoded = value.encode("utf-8")
    if value.strip() != value or not 8 <= len(encoded) <= MAX_REASON_BYTES:
        raise BoundsError("reason must be trimmed and 8 to 2000 UTF-8 bytes")
    return value


def bounded_page_size(value: int) -> int:
    if not 1 <= value <= MAX_PAGE_SIZE:
        raise BoundsError("page size must be between 1 and 200")
    return value


def _validate_string(value: str) -> None:
    if len(value.encode("utf-8")) > MAX_STRING_BYTES:
        raise BoundsError("document string exceeds the maximum size")
    if "\x00" in value:
        raise BoundsError("document strings cannot contain NUL")
    if _URL.search(value) or _WINDOWS_PATH.search(value) or _SECRET_MATERIAL.search(value):
        raise BoundsError("document contains a prohibited locator or secret-like value")


def validate_generated_document(value: Any, *, depth: int = 0) -> int:
    if depth > 16:
        raise BoundsError("document exceeds the maximum nesting depth")
    if value is None or isinstance(value, bool | int):
        return 1
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BoundsError("document numbers must be finite")
        return 1
    if isinstance(value, str):
        _validate_string(value)
        return 1
    if isinstance(value, Mapping):
        if len(value) > 128:
            raise BoundsError("document object has too many fields")
        count = 1
        for key, child in value.items():
            if not isinstance(key, str):
                raise BoundsError("document keys must be strings")
            normalized = key.casefold()
            if any(part in normalized for part in FORBIDDEN_FIELD_PARTS):
                raise BoundsError("document contains a prohibited field")
            _validate_string(key)
            count += validate_generated_document(child, depth=depth + 1)
            if count > 2_048:
                raise BoundsError("document contains too many items")
        return count
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        if len(value) > 2_048:
            raise BoundsError("document array has too many items")
        count = 1
        for child in value:
            count += validate_generated_document(child, depth=depth + 1)
            if count > 2_048:
                raise BoundsError("document contains too many items")
        return count
    raise BoundsError("document contains an unsupported value")
