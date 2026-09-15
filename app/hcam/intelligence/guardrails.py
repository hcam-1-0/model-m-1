from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from hcam.intelligence.canonical import MAX_CONTRACT_BYTES, canonical_json_bytes
from hcam.intelligence.contracts import AuthorityClass


MAX_DOCUMENT_DEPTH = 16
MAX_DOCUMENT_NODES = 8192

PROHIBITED_FIELD_NAMES = frozenset(
    {
        "aadhaar",
        "address",
        "biometric",
        "biometric_template",
        "caste",
        "certificate",
        "command",
        "credential",
        "email",
        "expression",
        "face_embedding",
        "face_template",
        "full_name",
        "guilt",
        "host",
        "intent",
        "javascript",
        "owner_details",
        "owner_name",
        "password",
        "phone",
        "port",
        "private_key",
        "python",
        "raw_provider_record",
        "raw_response",
        "religion",
        "script",
        "secret",
        "shell",
        "sql",
        "token",
        "url",
        "uri",
        "vehicle_owner",
        "watchlist_identity",
    }
)

PROHIBITED_LOCATOR_PREFIXES = (
    "file://",
    "ftp://",
    "http://",
    "https://",
    "rtmp://",
    "rtsp://",
    "s3://",
)


class IntelligenceGuardrailError(ValueError):
    pass


def _walk(value: Any, *, depth: int, budget: list[int]) -> None:
    if depth > MAX_DOCUMENT_DEPTH:
        raise IntelligenceGuardrailError("contract nesting limit exceeded")
    budget[0] += 1
    if budget[0] > MAX_DOCUMENT_NODES:
        raise IntelligenceGuardrailError("contract node limit exceeded")
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in PROHIBITED_FIELD_NAMES:
                raise IntelligenceGuardrailError("contract contains a prohibited field")
            _walk(child, depth=depth + 1, budget=budget)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _walk(child, depth=depth + 1, budget=budget)
    elif isinstance(value, str) and value.strip().lower().startswith(
        PROHIBITED_LOCATOR_PREFIXES
    ):
        raise IntelligenceGuardrailError("contract contains a prohibited locator")


def validate_intelligence_document(
    value: BaseModel | Mapping[str, Any] | Sequence[Any],
    *,
    maximum_bytes: int = MAX_CONTRACT_BYTES,
) -> bytes:
    document = value.model_dump(mode="json", by_alias=True) if isinstance(value, BaseModel) else value
    _walk(document, depth=0, budget=[0])
    return canonical_json_bytes(document, maximum_bytes=maximum_bytes)


def require_authority_boundary(
    authority_class: AuthorityClass,
    *,
    generated_only: bool,
    operational: bool,
) -> None:
    if operational:
        raise IntelligenceGuardrailError("P4.0 operational authority is disabled")
    if authority_class == "future_autonomous_action":
        raise IntelligenceGuardrailError("future autonomous action is disabled")
    if authority_class == "bounded_system_health" and not generated_only:
        raise IntelligenceGuardrailError(
            "bounded system-health automation requires generated-only scope"
        )
