"""Checked, offline snapshot helper for the Sentinel catalogue v1 contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from hcam.labs.sentinel.models import ExactNetworkPolicy, NetworkRule, normalize_catalog_document


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "sentinel_contract_v1"


def _policy() -> ExactNetworkPolicy:
    return ExactNetworkPolicy(
        (
            NetworkRule("https", "catalog.invalid", 443, "/api/ingest"),
            NetworkRule("rtsp", "contract-media.invalid", 8554, "/hcam/"),
            NetworkRule("http", "contract-media.invalid", 8889, "/hcam/"),
            NetworkRule("http", "contract-media.invalid", 8888, "/hcam/"),
        )
    )


def snapshot_digest() -> str:
    document = json.loads((FIXTURES / "catalogues.json").read_text(encoding="utf-8"))["valid"]
    catalog = normalize_catalog_document(
        document, origin="https://catalog.invalid/api/ingest", network_policy=_policy()
    )
    return hashlib.sha256(catalog.canonical_json.encode("ascii")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "update"))
    parser.add_argument("--acknowledge", action="store_true", help="required to update a reviewed contract snapshot")
    args = parser.parse_args()
    expected_path = FIXTURES / "snapshot.sha256"
    digest = snapshot_digest()
    if args.action == "update":
        if not args.acknowledge:
            parser.error("refusing snapshot update without --acknowledge")
        expected_path.write_text(digest + "\n", encoding="ascii")
        return 0
    if expected_path.read_text(encoding="ascii").strip() != digest:
        raise SystemExit("snapshot drift; use update --acknowledge after review")
    print("sentinel contract v1 snapshot: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
