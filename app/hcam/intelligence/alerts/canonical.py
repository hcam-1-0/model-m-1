from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel

from hcam.intelligence.alerts.bounds import MAX_CONTRACT_BYTES


def canonical_bytes(value: BaseModel | dict[str, Any]) -> bytes:
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    encoded = json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    if len(encoded) > MAX_CONTRACT_BYTES:
        raise ValueError("canonical alert contract exceeds 64 KiB")
    return encoded


def digest(value: BaseModel | dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    material = "\x00".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(material).hexdigest()[:32]}"
