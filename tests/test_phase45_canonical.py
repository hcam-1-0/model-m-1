from __future__ import annotations

import math

import pytest

from hcam.intelligence.investigations.canonical import (
    CanonicalizationError,
    canonical_bytes,
    digest,
    stable_id,
)


def test_canonical_json_is_stable_ascii_and_sorted() -> None:
    assert canonical_bytes({"z": "generated", "a": 1}) == b'{"a":1,"z":"generated"}'
    assert digest({"a": 1, "z": "generated"}) == digest({"z": "generated", "a": 1})
    assert stable_id("inv", "generated", 1) == stable_id("inv", "generated", 1)


def test_canonical_json_rejects_invalid_and_oversized_values() -> None:
    with pytest.raises(CanonicalizationError, match="not canonical"):
        canonical_bytes({"value": math.nan})
    with pytest.raises(CanonicalizationError, match="size limit"):
        canonical_bytes({"value": "generated"}, maximum_bytes=4)
