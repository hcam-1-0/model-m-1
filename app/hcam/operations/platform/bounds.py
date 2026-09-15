from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Any


MAX_CONTRACT_BYTES = 65_536
MAX_STRING_BYTES = 4_096
MAX_DOCUMENT_ITEMS = 2_048
MAX_DOCUMENT_DEPTH = 16
MAX_SAFE_FAILURE_PARAMETERS = 16
MAX_METRIC_DEFINITIONS = 2_048
MAX_LABELS_PER_METRIC = 8
MAX_CLOSED_VALUES_PER_LABEL = 64
MAX_GENERATED_SERIES = 32_768
MAX_TRACE_STATE_BYTES = 512
MAX_LOG_EVENT_BYTES = 16_384
MAX_OBJECTIVES = 256
MAX_BURN_WINDOWS = 8
MAX_WORKER_CLASSES = 64
MAX_JOB_PAYLOAD_BYTES = 65_536
MAX_JOB_ATTEMPTS = 3
WORKER_LEASE_SECONDS = 90
MAX_CIRCUIT_CLASSES = 64
MAX_CONTROL_DEPTH = 8
MAX_RECOVERY_ASSETS = 256
MAX_RECOVERY_DEPENDENCIES = 1_024
MAX_SUPPLY_CHAIN_COMPONENTS = 10_000
MAX_CAPABILITY_PROFILES = 64
MAX_CAPACITY_STEPS = 100_000
MAX_PLACEMENT_NODES = 256
MAX_PLACEMENT_SERVICES = 256
MAX_UNIFIED_SEARCH_ITEMS = 10_000

FORBIDDEN_FIELD_PARTS = frozenset(
    {
        "authorization",
        "biometric",
        "credential",
        "dispatch",
        "enforcement",
        "evidence_payload",
        "face",
        "image_bytes",
        "owner_detail",
        "password",
        "private_key",
        "raw_audit",
        "raw_evidence",
        "raw_signal",
        "secret",
        "token",
        "video_bytes",
        "watchlist",
    }
)
_LOCATOR = re.compile(r"(?i)(?:https?|file|ftp|rtsp|wss?)://|(?:^|\s)[a-z]:[\\/]")
_SECRET_MATERIAL = re.compile(r"(?i)(?:bearer\s+[a-z0-9._~+/=-]{16,}|-----BEGIN)")


class BoundsError(ValueError):
    pass


def bounded_text(value: str, *, minimum: int = 1, maximum: int = MAX_STRING_BYTES) -> str:
    encoded = value.encode("utf-8")
    if value.strip() != value or not minimum <= len(encoded) <= maximum:
        raise BoundsError("text is outside its UTF-8 bounds")
    if "\x00" in value or _LOCATOR.search(value) or _SECRET_MATERIAL.search(value):
        raise BoundsError("text contains prohibited material")
    return value


def validate_generated_document(value: Any, *, depth: int = 0) -> int:
    if depth > MAX_DOCUMENT_DEPTH:
        raise BoundsError("document exceeds maximum nesting depth")
    if value is None or isinstance(value, bool | int):
        return 1
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BoundsError("document numbers must be finite")
        return 1
    if isinstance(value, str):
        bounded_text(value)
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
            bounded_text(key)
            count += validate_generated_document(child, depth=depth + 1)
            if count > MAX_DOCUMENT_ITEMS:
                raise BoundsError("document contains too many items")
        return count
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        if len(value) > MAX_DOCUMENT_ITEMS:
            raise BoundsError("document array has too many items")
        count = 1
        for child in value:
            count += validate_generated_document(child, depth=depth + 1)
            if count > MAX_DOCUMENT_ITEMS:
                raise BoundsError("document contains too many items")
        return count
    raise BoundsError("document contains an unsupported value")
