from __future__ import annotations

import json
from pathlib import Path

from tools.phase54.generate_fixtures import GROUPS, build_documents, canonical_sha
from tools.phase54.verify_p54 import EXPECTED_CONTRACTS, EXPECTED_FIXTURES, recursive_keys, verify

ROOT = Path(__file__).resolve().parents[2]


def test_phase54_contract_fixture_and_case_counts_are_exact() -> None:
    assert len(EXPECTED_CONTRACTS) == 14
    assert len(EXPECTED_FIXTURES) == 8
    assert sum(count for _, count in GROUPS) == 832


def test_phase54_generation_is_deterministic() -> None:
    first = build_documents()
    second = build_documents()
    assert canonical_sha(first) == canonical_sha(second)


def test_phase54_recursive_key_scan_is_fail_closed() -> None:
    assert recursive_keys({"safe": [{"secret": "discarded"}]}) == {"safe", "secret"}


def test_repository_phase54_verification_passes() -> None:
    result = verify(ROOT)
    assert result["status"] == "pass", json.dumps(result, indent=2)
    assert result["generated_cases"] == 832
    assert (ROOT / "contracts/phase-5/p5-5-start-acceptance.json").is_file()
