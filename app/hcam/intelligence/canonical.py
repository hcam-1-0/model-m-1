from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel


MAX_CONTRACT_BYTES = 64 * 1024


class CanonicalizationError(ValueError):
    pass


def _document(value: BaseModel | Mapping[str, Any] | Sequence[Any]) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True)
    return value


def canonical_json_bytes(
    value: BaseModel | Mapping[str, Any] | Sequence[Any],
    *,
    maximum_bytes: int = MAX_CONTRACT_BYTES,
) -> bytes:
    try:
        encoded = json.dumps(
            _document(value),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError("contract is not canonical JSON") from exc
    if len(encoded) > maximum_bytes:
        raise CanonicalizationError("contract exceeds the canonical size limit")
    return encoded


def canonical_json(
    value: BaseModel | Mapping[str, Any] | Sequence[Any],
    *,
    maximum_bytes: int = MAX_CONTRACT_BYTES,
) -> str:
    return canonical_json_bytes(value, maximum_bytes=maximum_bytes).decode("ascii")


def canonical_sha256(
    value: BaseModel | Mapping[str, Any] | Sequence[Any],
    *,
    maximum_bytes: int = MAX_CONTRACT_BYTES,
) -> str:
    encoded = canonical_json_bytes(value, maximum_bytes=maximum_bytes)
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
