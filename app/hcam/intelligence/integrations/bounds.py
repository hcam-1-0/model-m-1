from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


MAX_CONTRACT_BYTES = 64 * 1024
MAX_MANIFEST_OPERATIONS = 64
MAX_REQUEST_FIELDS = 64
MAX_RESPONSE_FIELDS = 128
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_RESPONSE_DEPTH = 16
MAX_RESPONSE_ITEMS = 2_048
MAX_STRING_BYTES = 4_096
MAX_PAGE_SIZE = 200
MAX_PAGES_PER_JOB = 20
MAX_JOB_ATTEMPTS = 3
JOB_LEASE_SECONDS = 90
MAX_CANDIDATES = 25
MAX_SIGNALS_PER_CANDIDATE = 64
MAX_REASON_BYTES = 2_000

FORBIDDEN_FIELD_PARTS = frozenset(
    {
        "api_key",
        "biometric",
        "credential",
        "dispatch",
        "enforcement",
        "face",
        "image",
        "locator",
        "media",
        "owner",
        "password",
        "private_key",
        "raw_response",
        "secret",
        "video",
        "watchlist",
    }
)


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


def validate_safe_document(value: Any, *, depth: int = 0) -> int:
    if depth > MAX_RESPONSE_DEPTH:
        raise BoundsError("document exceeds the maximum nesting depth")
    if value is None or isinstance(value, bool | int | float):
        return 1
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_STRING_BYTES:
            raise BoundsError("document string exceeds the maximum size")
        return 1
    if isinstance(value, Mapping):
        if len(value) > MAX_RESPONSE_FIELDS:
            raise BoundsError("document object has too many fields")
        count = 1
        for key, child in value.items():
            if not isinstance(key, str):
                raise BoundsError("document keys must be strings")
            normalized = key.casefold()
            if any(part in normalized for part in FORBIDDEN_FIELD_PARTS):
                raise BoundsError("document contains a prohibited field")
            count += validate_safe_document(child, depth=depth + 1)
            if count > MAX_RESPONSE_ITEMS:
                raise BoundsError("document contains too many items")
        return count
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        if len(value) > MAX_RESPONSE_ITEMS:
            raise BoundsError("document array contains too many items")
        count = 1
        for child in value:
            count += validate_safe_document(child, depth=depth + 1)
            if count > MAX_RESPONSE_ITEMS:
                raise BoundsError("document contains too many items")
        return count
    raise BoundsError("document contains an unsupported value")
