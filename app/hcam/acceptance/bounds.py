from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


MAX_CONTRACT_BYTES = 65_536
MAX_STRING_BYTES = 4_096
MAX_DOCUMENT_DEPTH = 16
MAX_DOCUMENT_ITEMS = 10_000
MAX_SCENARIOS = 64
MAX_STEPS_PER_SCENARIO = 256
MAX_RECORDS_PER_SCENARIO = 10_000
MAX_BYTES_PER_SCENARIO = 16_777_216
MAX_EVIDENCE_COMPONENTS = 4_096
MAX_EVIDENCE_EDGES = 16_384
MAX_CLAIMS = 512
MAX_LIMITATIONS = 512
MAX_HANDOFF_OPERATIONS = 1_024
MAX_UI_STATES = 4_096
MAX_COMPATIBILITY_ENTRIES = 2_048
REQUIRED_SCENARIO_IDS = tuple(f"S{index:02d}" for index in range(9))
REQUIRED_REPLAYS = 2

PROHIBITED_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "biometric",
        "camera_url",
        "credential",
        "face_embedding",
        "government_id",
        "media_bytes",
        "password",
        "private_key",
        "secret",
        "stream_url",
    }
)
PROHIBITED_VALUE_PATTERNS = (
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"rtsp://", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
)


class GeneratedBoundaryError(ValueError):
    """Raised when generated-only data crosses a P4.7 boundary."""


def bounded_text(
    value: str, *, minimum: int = 1, maximum: int = MAX_STRING_BYTES
) -> str:
    if value != value.strip():
        raise GeneratedBoundaryError("text must not have surrounding whitespace")
    length = len(value.encode("utf-8"))
    if length < minimum or length > maximum:
        raise GeneratedBoundaryError("text is outside the byte limit")
    if any(pattern.search(value) for pattern in PROHIBITED_VALUE_PATTERNS):
        raise GeneratedBoundaryError("text contains prohibited generated-only material")
    return value


def validate_generated_document(value: Any, *, depth: int = 0) -> Any:
    if depth > MAX_DOCUMENT_DEPTH:
        raise GeneratedBoundaryError("generated document exceeds the depth limit")
    if value is None or type(value) in {bool, int, float}:
        return value
    if isinstance(value, str):
        return bounded_text(value, minimum=0)
    if isinstance(value, Mapping):
        if len(value) > MAX_DOCUMENT_ITEMS:
            raise GeneratedBoundaryError("generated mapping exceeds the item limit")
        for key, item in value.items():
            if not isinstance(key, str):
                raise GeneratedBoundaryError("generated mapping keys must be strings")
            normalized = key.strip().lower()
            if normalized in PROHIBITED_KEYS:
                raise GeneratedBoundaryError(
                    "generated document contains a prohibited key"
                )
            bounded_text(key, maximum=128)
            validate_generated_document(item, depth=depth + 1)
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > MAX_DOCUMENT_ITEMS:
            raise GeneratedBoundaryError("generated sequence exceeds the item limit")
        for item in value:
            validate_generated_document(item, depth=depth + 1)
        return value
    raise GeneratedBoundaryError("generated document contains an unsupported value")
