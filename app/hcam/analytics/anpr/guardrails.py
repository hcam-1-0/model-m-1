from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Literal

from pydantic import BaseModel, ValidationError

from hcam.analytics.anpr.contracts import (
    MAX_ANPR_DOCUMENT_DEPTH,
    MAX_ANPR_DOCUMENT_NODES,
    MAX_ANPR_REQUEST_BYTES,
    EphemeralSyntheticTokenV1,
    GeneratedTokenRequestV1,
    SyntheticAnprExecutionPolicyV1,
)


AnprBoundaryCode = Literal[
    "arbitrary_bytes_prohibited",
    "document_too_deep",
    "document_too_large",
    "document_too_many_nodes",
    "invalid_generated_request",
    "invalid_synthetic_token",
    "non_json_input",
    "plate_text_persistence_prohibited",
    "production_forbidden",
    "prohibited_input_field",
    "prohibited_input_value",
    "runtime_disabled",
]

_PROHIBITED_INPUT_FIELDS = frozenset(
    {
        "bytes",
        "camera",
        "camera_id",
        "case",
        "case_id",
        "external_text",
        "file",
        "file_path",
        "frame",
        "frame_bytes",
        "government_record",
        "image",
        "image_bytes",
        "media",
        "owner",
        "owner_record",
        "path",
        "plate",
        "plate_number",
        "raw_text",
        "registration",
        "registration_mark",
        "source_url",
        "stream",
        "stream_id",
        "text",
        "token",
        "upload",
        "url",
        "vehicle",
        "vehicle_record",
        "watchlist",
        "watchlist_match",
    }
)
_PROHIBITED_PERSISTENCE_FIELDS = frozenset(
    {
        "alternatives",
        "graphemes",
        "nfc_value",
        "normalized_text",
        "normalized_display_candidate",
        "ocr_text",
        "plate_number",
        "plate_text",
        "raw_text",
        "raw_hypothesis_digest",
        "registration_mark",
        "token",
    }
)
_PROHIBITED_STRING_VALUE = re.compile(
    r"(?ix)(?:"
    r"\bdata:|"
    r"\b(?:file|https?|rtsp|rtsps)://|"
    r"\bbearer\s+|"
    r"-----BEGIN\s+(?:[A-Z]+\s+)?PRIVATE\s+KEY-----|"
    r"(?:^|[\\/])\.\.(?:[\\/]|$)|"
    r"^[A-Z]:[\\/]|"
    r"^\\\\"
    r")"
)


class AnprBoundaryViolation(ValueError):
    """Boundary failure that intentionally excludes the rejected value."""

    def __init__(self, code: AnprBoundaryCode) -> None:
        super().__init__(f"P3.5 ANPR boundary rejected input: {code}")
        self.code = code


def _normalized_key(value: str) -> str:
    snake_case = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value.strip())
    return re.sub(r"[^a-z0-9]+", "_", snake_case.lower()).strip("_")


def _inspect_document(
    value: object,
    *,
    depth: int,
    nodes: list[int],
    maximum_depth: int,
    maximum_nodes: int,
    prohibited_fields: frozenset[str],
    reject_source_values: bool,
    reject_ephemeral_token: bool = False,
) -> None:
    if depth > maximum_depth:
        raise AnprBoundaryViolation("document_too_deep")
    nodes[0] += 1
    if nodes[0] > maximum_nodes:
        raise AnprBoundaryViolation("document_too_many_nodes")
    if reject_ephemeral_token and isinstance(value, EphemeralSyntheticTokenV1):
        raise AnprBoundaryViolation("plate_text_persistence_prohibited")
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AnprBoundaryViolation("non_json_input")
            if _normalized_key(key) in prohibited_fields:
                code: AnprBoundaryCode = (
                    "plate_text_persistence_prohibited"
                    if reject_ephemeral_token
                    else "prohibited_input_field"
                )
                raise AnprBoundaryViolation(code)
            _inspect_document(
                item,
                depth=depth + 1,
                nodes=nodes,
                maximum_depth=maximum_depth,
                maximum_nodes=maximum_nodes,
                prohibited_fields=prohibited_fields,
                reject_source_values=reject_source_values,
                reject_ephemeral_token=reject_ephemeral_token,
            )
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _inspect_document(
                item,
                depth=depth + 1,
                nodes=nodes,
                maximum_depth=maximum_depth,
                maximum_nodes=maximum_nodes,
                prohibited_fields=prohibited_fields,
                reject_source_values=reject_source_values,
                reject_ephemeral_token=reject_ephemeral_token,
            )
        return
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise AnprBoundaryViolation("arbitrary_bytes_prohibited")
    if (
        reject_source_values
        and isinstance(value, str)
        and _PROHIBITED_STRING_VALUE.search(value)
    ):
        raise AnprBoundaryViolation("prohibited_input_value")
    if value is not None and not isinstance(value, (str, int, float, bool)):
        raise AnprBoundaryViolation("non_json_input")


def inspect_generated_request_input(value: object) -> None:
    _inspect_document(
        value,
        depth=0,
        nodes=[0],
        maximum_depth=MAX_ANPR_DOCUMENT_DEPTH,
        maximum_nodes=MAX_ANPR_DOCUMENT_NODES,
        prohibited_fields=_PROHIBITED_INPUT_FIELDS,
        reject_source_values=True,
    )


def _bounded_json_size(value: object, *, maximum_bytes: int) -> None:
    try:
        payload = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AnprBoundaryViolation("non_json_input") from exc
    if len(payload) > maximum_bytes:
        raise AnprBoundaryViolation("document_too_large")


def authorize_generated_request(
    document: Mapping[str, object],
    *,
    policy: SyntheticAnprExecutionPolicyV1,
) -> GeneratedTokenRequestV1:
    inspect_generated_request_input(document)
    _bounded_json_size(document, maximum_bytes=policy.maximum_request_bytes)
    if not policy.enabled:
        raise AnprBoundaryViolation("runtime_disabled")
    if policy.environment == "production":
        raise AnprBoundaryViolation("production_forbidden")
    try:
        parsed = GeneratedTokenRequestV1.model_validate(document)
    except ValidationError:
        parsed = None
    if parsed is None:
        raise AnprBoundaryViolation("invalid_generated_request")
    return parsed


def validate_ephemeral_synthetic_token(
    document: Mapping[str, object],
) -> EphemeralSyntheticTokenV1:
    _inspect_document(
        document,
        depth=0,
        nodes=[0],
        maximum_depth=MAX_ANPR_DOCUMENT_DEPTH,
        maximum_nodes=MAX_ANPR_DOCUMENT_NODES,
        prohibited_fields=frozenset(),
        reject_source_values=False,
    )
    _bounded_json_size(document, maximum_bytes=MAX_ANPR_REQUEST_BYTES)
    try:
        parsed = EphemeralSyntheticTokenV1.model_validate(document)
    except ValidationError:
        parsed = None
    if parsed is None:
        raise AnprBoundaryViolation("invalid_synthetic_token")
    return parsed


def canonical_anpr_evidence_json(
    value: BaseModel | Mapping[str, object],
    *,
    maximum_bytes: int = MAX_ANPR_REQUEST_BYTES,
    maximum_nodes: int = MAX_ANPR_DOCUMENT_NODES,
) -> str:
    if maximum_bytes < 1 or maximum_nodes < 1:
        raise ValueError("ANPR evidence limits must be positive")
    _inspect_document(
        value,
        depth=0,
        nodes=[0],
        maximum_depth=MAX_ANPR_DOCUMENT_DEPTH,
        maximum_nodes=maximum_nodes,
        prohibited_fields=_PROHIBITED_PERSISTENCE_FIELDS,
        reject_source_values=False,
        reject_ephemeral_token=True,
    )
    document = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    _bounded_json_size(document, maximum_bytes=maximum_bytes)
    return (
        json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )
