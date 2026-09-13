from __future__ import annotations

import json
from pathlib import Path

from tools.phase53.verify_p53 import (
    EXPECTED_CONTRACTS,
    EXPECTED_FIXTURES,
    canonical_sha,
    recursive_keys,
    verify,
)

ROOT = Path(__file__).resolve().parents[2]


def test_expected_phase53_contract_and_fixture_sets_are_complete() -> None:
    assert len(EXPECTED_CONTRACTS) == 8
    assert len(EXPECTED_FIXTURES) == 8


def test_recursive_key_projection_is_fail_closed() -> None:
    keys = recursive_keys(
        {"safe": [{"token": "not retained"}], "nested": {"state": "ready"}}
    )
    assert keys == {"safe", "token", "nested", "state"}


def test_canonical_hash_is_order_independent_for_objects() -> None:
    assert canonical_sha({"b": 2, "a": 1}) == canonical_sha({"a": 1, "b": 2})


def test_repository_phase53_verification_passes() -> None:
    result = verify(ROOT)
    assert result["status"] == "pass", json.dumps(result, indent=2)
    assert result["generated_cameras"] == 10
