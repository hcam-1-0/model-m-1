from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from hcam.intelligence.rules.bounds import MAX_AUTHORING_BYTES


class RuleCanonicalizationError(ValueError):
    """Raised when rule JSON is ambiguous, non-finite, or oversized."""


def strict_json_loads(
    payload: str | bytes, *, maximum_bytes: int = MAX_AUTHORING_BYTES
) -> Any:
    encoded = payload.encode("utf-8") if isinstance(payload, str) else payload
    if len(encoded) > maximum_bytes:
        raise RuleCanonicalizationError("rule document exceeds the size limit")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise RuleCanonicalizationError(
                    "rule document contains a duplicate key"
                )
            result[key] = value
        return result

    try:
        return json.loads(
            encoded, object_pairs_hook=pairs, parse_constant=_reject_constant
        )
    except RuleCanonicalizationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuleCanonicalizationError(
            "rule document is not strict UTF-8 JSON"
        ) from exc


def _reject_constant(_value: str) -> None:
    raise RuleCanonicalizationError("rule document contains a non-finite number")


def canonical_rule_bytes(
    value: BaseModel | Mapping[str, Any] | Sequence[Any],
    *,
    maximum_bytes: int = MAX_AUTHORING_BYTES,
) -> bytes:
    document = (
        value.model_dump(mode="json", by_alias=True)
        if isinstance(value, BaseModel)
        else value
    )
    try:
        result = json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RuleCanonicalizationError("rule document is not canonical JSON") from exc
    if len(result) > maximum_bytes:
        raise RuleCanonicalizationError("rule document exceeds the size limit")
    return result


def rule_sha256(value: BaseModel | Mapping[str, Any] | Sequence[Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_rule_bytes(value)).hexdigest()
