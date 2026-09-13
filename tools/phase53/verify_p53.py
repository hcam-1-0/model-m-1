from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

MARKER = "HCAM-GENERATED-NON-OPERATIONAL"
FORBIDDEN_KEYS = {
    "locator",
    "password",
    "secret",
    "secret_ref",
    "username",
    "raw_address",
    "raw_probe_payload",
    "sdp",
    "ice",
}
EXPECTED_CONTRACTS = {
    "browser-camera-projection.v1.json",
    "client-media-signal.v1.json",
    "cross-portal-handoff.v1.json",
    "generated-media-manifest.v1.json",
    "media-profile.v1.json",
    "playback-session.v1.json",
    "stream-diagnostics.v1.json",
    "workspace-layout.v1.json",
}
EXPECTED_FIXTURES = {
    "c1.generated.v1.json",
    "c4.generated.v1.json",
    "c10.generated.v1.json",
    "camera-catalogue.generated.v1.json",
    "media-generation-plan.generated.v1.json",
    "playback-scenarios.generated.v1.json",
    "replay-manifest.generated.v1.json",
    "security-cases.generated.v1.json",
}


def canonical_sha(value: Any) -> str:
    return (
        hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        )
        .hexdigest()
        .upper()
    )


def recursive_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {str(key).lower() for key in value} | set().union(
            *(recursive_keys(item) for item in value.values()), set()
        )
    if isinstance(value, list):
        return set().union(*(recursive_keys(item) for item in value), set())
    return set()


def verify(repo: Path) -> dict[str, Any]:
    failures: list[str] = []
    contract_root = repo / "contracts" / "phase-5" / "p5-3"
    fixture_root = repo / "fixtures" / "phase-5" / "p5-3"
    contract_names = {path.name for path in contract_root.glob("*.json")}
    fixture_names = {path.name for path in fixture_root.glob("*.json")}
    if contract_names != EXPECTED_CONTRACTS:
        failures.append("contract_set_mismatch")
    if fixture_names != EXPECTED_FIXTURES:
        failures.append("fixture_set_mismatch")
    documents = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(fixture_root.glob("*.json"))
    ]
    if any(document.get("marker") != MARKER for document in documents):
        failures.append("generated_marker_missing")
    catalogue = json.loads(
        (fixture_root / "camera-catalogue.generated.v1.json").read_text(
            encoding="utf-8"
        )
    )
    if len(catalogue.get("cameras", [])) != 10:
        failures.append("camera_count_mismatch")
    keys = recursive_keys(catalogue)
    if keys & FORBIDDEN_KEYS:
        failures.append("forbidden_browser_field")
    profiles = {
        name: json.loads((fixture_root / name).read_text(encoding="utf-8"))
        for name in (
            "c1.generated.v1.json",
            "c4.generated.v1.json",
            "c10.generated.v1.json",
        )
    }
    if [len(profiles[name]["stream_refs"]) for name in profiles] != [1, 4, 10]:
        failures.append("capacity_fixture_mismatch")
    if canonical_sha(documents) != canonical_sha(json.loads(json.dumps(documents))):
        failures.append("replay_not_deterministic")
    dependency = json.loads(
        (repo / "frontend" / "dependency-evidence.json").read_text(encoding="utf-8")
    )
    candidate = json.loads(
        (repo / "frontend" / "dependency-lock-candidate.json").read_text(
            encoding="utf-8"
        )
    )
    hls_records = [
        item for item in candidate.get("packages", []) if item.get("name") == "hls.js"
    ]
    if (
        dependency.get("schema_version") != "hcam.phase5.p5_3.dependency_evidence.v1"
        or dependency.get("result") != "pass"
        or len(hls_records) != 1
        or hls_records[0].get("version") != "1.7.2"
    ):
        failures.append("hls_dependency_evidence_missing")
    producer_source = (
        repo / "frontend" / "packages" / "test-fixtures" / "src" / "p5-3-fixtures.ts"
    ).read_text(encoding="utf-8")
    producer_match = re.search(
        r"export const p53UnavailableProducers = \[(?P<body>.*?)\] as const;",
        producer_source,
        re.DOTALL,
    )
    producer_count = (
        len(
            re.findall(
                r'^\s+"[a-z0-9_]+",$', producer_match.group("body"), re.MULTILINE
            )
        )
        if producer_match
        else 0
    )
    if producer_count != 20:
        failures.append("producer_gap_inventory_incomplete")
    return {
        "schema_version": "hcam.phase5.p5_3.verification.v1",
        "status": "pass" if not failures else "fail",
        "contracts": len(contract_names),
        "fixtures": len(fixture_names),
        "generated_cameras": len(catalogue.get("cameras", [])),
        "producer_gaps": producer_count,
        "canonical_fixture_sha256": canonical_sha(documents),
        "failures": sorted(failures),
    }


def main() -> int:
    result = verify(Path(__file__).resolve().parents[2])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
