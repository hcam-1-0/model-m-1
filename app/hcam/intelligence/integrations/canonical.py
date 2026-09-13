from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from hcam.intelligence.integrations.bounds import MAX_CONTRACT_BYTES


class CanonicalizationError(ValueError):
    pass


def canonical_bytes(
    value: BaseModel | Mapping[str, Any] | Sequence[Any],
    *,
    maximum_bytes: int = MAX_CONTRACT_BYTES,
) -> bytes:
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    try:
        encoded = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError("value is not canonical JSON") from exc
    if len(encoded) > maximum_bytes:
        raise CanonicalizationError("canonical value exceeds the size limit")
    return encoded


def digest(
    value: BaseModel | Mapping[str, Any] | Sequence[Any],
    *,
    maximum_bytes: int = MAX_CONTRACT_BYTES,
) -> str:
    return "sha256:" + hashlib.sha256(
        canonical_bytes(value, maximum_bytes=maximum_bytes)
    ).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    material = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(material).hexdigest()[:32]}"
