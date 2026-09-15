import hashlib

import pytest

from hcam.acceptance.canonical import (
    CanonicalizationError,
    canonical_bytes,
    digest,
    file_sha256,
    stable_id,
)
from hcam.acceptance.fixtures import build_manifest


def test_canonical_json_is_order_independent_and_handles_nested_models() -> None:
    assert canonical_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert digest({"manifest": build_manifest()}).startswith("sha256:")


def test_canonical_json_rejects_invalid_and_oversized_values() -> None:
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"invalid": object()})
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"large": "x" * 50}, maximum_bytes=10)


def test_stable_and_file_digests_are_exact() -> None:
    assert stable_id("p47", "one") == stable_id("p47", "one")
    assert stable_id("p47", "one") != stable_id("p47", "two")
    assert file_sha256(b"generated") == hashlib.sha256(b"generated").hexdigest().upper()
