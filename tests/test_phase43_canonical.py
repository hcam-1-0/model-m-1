from __future__ import annotations

import pytest

from hcam.intelligence.alerts.canonical import canonical_bytes, digest, stable_id


def test_canonical_alert_material_is_order_independent_and_ascii() -> None:
    left = {"b": 2, "a": [True, "value"]}
    right = {"a": [True, "value"], "b": 2}
    assert canonical_bytes(left) == canonical_bytes(right) == b'{"a":[true,"value"],"b":2}'
    assert digest(left) == digest(right)
    assert stable_id("alt", "a", 1) == stable_id("alt", "a", 1)


def test_canonical_alert_material_is_bounded() -> None:
    with pytest.raises(ValueError, match="64 KiB"):
        canonical_bytes({"payload": "x" * (64 * 1024)})
