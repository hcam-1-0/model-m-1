#!/usr/bin/env python3
"""Generate and verify deterministic Phase 3 analytics contracts."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path

from hcam.analytics.contracts import (
    analytics_contract_bundle,
    canonical_contract_json,
)
from hcam.analytics.fixtures import golden_contract_fixtures


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "contracts" / "phase-3"
SCHEMA_SNAPSHOT = CONTRACT_ROOT / "analytics-contracts.json"
FIXTURE_ROOT = CONTRACT_ROOT / "fixtures"
_MAX_DIFF_LINES = 240


def serialized_document(document: object) -> str:
    if isinstance(document, dict):
        return json.dumps(
            document,
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        ) + "\n"
    return canonical_contract_json(document)


def render_contracts() -> dict[Path, str]:
    rendered = {SCHEMA_SNAPSHOT: serialized_document(analytics_contract_bundle())}
    for name, fixture in golden_contract_fixtures().items():
        rendered[FIXTURE_ROOT / name] = serialized_document(fixture)
    return rendered


def contract_digest(document: str) -> str:
    return hashlib.sha256(document.encode("utf-8")).hexdigest()


def contract_diff(path: Path, expected: str, actual: str) -> list[str]:
    lines = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile=f"tracked/{path.name}",
            tofile=f"current/{path.name}",
            lineterm="",
        )
    )
    if len(lines) > _MAX_DIFF_LINES:
        omitted = len(lines) - _MAX_DIFF_LINES
        return [*lines[:_MAX_DIFF_LINES], f"... {omitted} diff lines omitted"]
    return lines


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
            for line in contract_diff(path, expected, actual):
                print(line)
            failures += 1
            continue
        print(
            f"[pass] {path.relative_to(ROOT)} "
            f"sha256={contract_digest(actual)}"
        )
    return 1 if failures else 0


def write_contracts(*, acknowledged: bool) -> int:
    if not acknowledged:
        print(
            "Refusing to rewrite analytics contracts without "
            "--acknowledge-reviewed-change"
        )
        return 2
    for path, document in render_contracts().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(document, encoding="utf-8", newline="\n")
        print(
            f"[write] {path.relative_to(ROOT)} "
            f"sha256={contract_digest(document)}"
        )
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify reviewed H-CAM Phase 3 analytics contracts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="Fail when tracked contracts drift")
    write = subparsers.add_parser(
        "write", help="Rewrite snapshots after explicit contract review"
    )
    write.add_argument("--acknowledge-reviewed-change", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "check":
        return check_contracts()
    return write_contracts(acknowledged=args.acknowledge_reviewed_change)


if __name__ == "__main__":
    raise SystemExit(main())
