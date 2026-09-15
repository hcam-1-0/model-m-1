from __future__ import annotations

import pytest

from hcam.intelligence.integrations.bounds import BoundsError, bounded_page_size, bounded_reason
from hcam.intelligence.integrations.canonical import (
    CanonicalizationError,
    canonical_bytes,
    digest,
    stable_id,
)


def test_canonical_encoding_digest_and_identifier_are_stable() -> None:
    left = {"z": "gen_z", "a": [2, 1]}
    right = {"a": [2, 1], "z": "gen_z"}
    assert canonical_bytes(left) == canonical_bytes(right)
    assert digest(left) == digest(right)
    assert stable_id("prov", "a", 1) == stable_id("prov", "a", 1)
    assert stable_id("prov", "a", 1) != stable_id("prov", "a", 2)


@pytest.mark.parametrize("value", [{"value": float("nan")}, {"value": object()}])
def test_canonical_encoding_rejects_non_json_values(value: object) -> None:
    with pytest.raises(CanonicalizationError):
        canonical_bytes(value)  # type: ignore[arg-type]


def test_common_bounds_fail_closed() -> None:
    assert bounded_reason("Generated bounded reason") == "Generated bounded reason"
    assert bounded_page_size(200) == 200
    with pytest.raises(BoundsError):
        bounded_reason(" short ")
    with pytest.raises(BoundsError):
        bounded_page_size(201)
