#!/usr/bin/env python3
"""Generate and verify reviewed P3.5 W1 ANPR contract snapshots."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path

from hcam.analytics.anpr import (
    SyntheticAnprExecutionPolicyV1,
    anpr_contract_bundle,
    build_sealed_split_manifest,
    synthetic_corpus_plan_fixture,
)
from hcam.analytics.anpr.contracts import generated_request_fixture
from hcam.analytics.anpr.guardrails import canonical_anpr_evidence_json


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "phase-3" / "p3-5-anpr-contracts.json"
FIXTURE_PATH = (
    ROOT / "contracts" / "phase-3" / "fixtures" / "p3-5-generated-request-v1.json"
)
SPLIT_MANIFEST_PATH = (
    ROOT / "contracts" / "phase-3" / "fixtures" / "p3-5-sealed-splits-v1.json"
)
_MAX_DIFF_LINES = 240
_MAX_MANIFEST_BYTES = 8 * 1024 * 1024
_MAX_MANIFEST_NODES = 200_000


def _render_bundle() -> str:
    return json.dumps(
        anpr_contract_bundle(),
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
    ) + "\n"


def render_contracts() -> dict[Path, str]:
    manifest = build_sealed_split_manifest(
        synthetic_corpus_plan_fixture(),
        policy=SyntheticAnprExecutionPolicyV1(enabled=True, environment="test"),
    )
    return {
        CONTRACT_PATH: _render_bundle(),
        FIXTURE_PATH: canonical_anpr_evidence_json(generated_request_fixture()),
        SPLIT_MANIFEST_PATH: canonical_anpr_evidence_json(
            manifest,
            maximum_bytes=_MAX_MANIFEST_BYTES,
            maximum_nodes=_MAX_MANIFEST_NODES,
        ),
    }


def check_contracts() -> int:
    failures = 0
    for path, actual in render_contracts().items():
        try:
            expected = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[fail] {path.relative_to(ROOT)}: {exc}")
            failures += 1
            continue
        if expected != actual:
            print(f"[fail] {path.relative_to(ROOT)} drifted")
            diff = list(
                difflib.unified_diff(
                    expected.splitlines(),
                    actual.splitlines(),
                    fromfile=f"tracked/{path.name}",
                    tofile=f"current/{path.name}",
                    lineterm="",
                )
            )
            for line in diff[:_MAX_DIFF_LINES]:
                print(line)
            if len(diff) > _MAX_DIFF_LINES:
                print(f"... {len(diff) - _MAX_DIFF_LINES} diff lines omitted")
            failures += 1
            continue
        print(f"[pass] {path.relative_to(ROOT)}")
    return 1 if failures else 0


def write_contracts(*, acknowledged: bool) -> int:
    if not acknowledged:
        print("Refusing to rewrite P3.5 contracts without reviewed-change acknowledgment")
        return 2
    for path, document in render_contracts().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document, encoding="utf-8", newline="\n")
        print(f"[write] {path.relative_to(ROOT)}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check")
    write = subparsers.add_parser("write")
    write.add_argument("--acknowledge-reviewed-change", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "check":
        return check_contracts()
    return write_contracts(acknowledged=args.acknowledge_reviewed_change)


if __name__ == "__main__":
    raise SystemExit(main())
