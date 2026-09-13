from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MARKER = "HCAM-GENERATED-NON-OPERATIONAL"
SEED = "HCAM-P5.4-R0-2026-09-09"
GROUPS = (
    ("semantic_truth_and_forbidden_claims", 128),
    ("queue_detail_and_degraded_states", 96),
    ("relationship_spatial_rule_and_table_parity", 128),
    ("candidate_uncertainty_and_proposed_alerts", 128),
    ("review_quorum_concurrency_idempotency_and_receipts", 160),
    ("correction_event_profile_and_teardown", 96),
    ("accessibility_localization_security_and_hostile_inputs", 96),
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest().upper()


def generated_case(group: str, index: int) -> dict[str, Any]:
    digest = hashlib.sha256(f"{SEED}:{group}:{index}".encode()).hexdigest().upper()
    return {
        "case_ref": f"SYN-P54-{digest[:16]}",
        "group": group,
        "ordinal": index,
        "input_class": ("valid", "boundary", "hostile", "degraded")[index % 4],
        "expected": ("accept", "deny", "abstain", "refetch")[index % 4],
        "generated": True,
        "marker": MARKER,
    }


def queue_item(index: int, queue: str) -> dict[str, Any]:
    priorities = ("urgent_review", "elevated_review", "standard_review", "unknown")
    return {
        "ref": f"SYN-{queue.upper().replace('_', '-')}-{index:04d}",
        "queue": queue,
        "priority": priorities[index % 4],
        "state": "correction_pending" if index % 11 == 0 else "awaiting_review",
        "revision": index + 1,
        "identity_established": False,
        "operational_authority": False,
        "generated": True,
    }


def scale_fixture(scale: int) -> dict[str, Any]:
    graph_limits = {1: (12, 24), 10: (50, 100), 50: (100, 200)}[scale]
    return {
        "schema_version": "hcam.phase5.p5_4.scale_fixture.v1",
        "marker": MARKER,
        "profile": f"C{scale}",
        "queue_items": [queue_item(index, "mandatory_review") for index in range(scale)],
        "relationship_limits": {"nodes": graph_limits[0], "edges": graph_limits[1]},
        "rendering_only_profile_change": True,
        "authority_change": False,
    }


def build_documents() -> dict[str, dict[str, Any]]:
    cases = [generated_case(group, index) for group, count in GROUPS for index in range(count)]
    review_cases = [case for case in cases if case["group"] == GROUPS[4][0]]
    security_cases = [case for case in cases if case["group"] == GROUPS[6][0]]
    visual_cases = [
        {
            "viewport": viewport,
            "profile": profile,
            "expected": "stable_non_overlapping",
            "marker": MARKER,
        }
        for viewport in ("360x800", "390x844", "768x1024", "1280x720", "1440x900", "1920x1080")
        for profile in (
            "low_resource",
            "enhanced_workstation",
            "control_room",
            "owned_gpu_lab",
            "future_server",
        )
    ]
    documents: dict[str, dict[str, Any]] = {
        "c1.generated.v1.json": scale_fixture(1),
        "c10.generated.v1.json": scale_fixture(10),
        "c50.generated.v1.json": scale_fixture(50),
        "intelligence-cases.generated.v1.json": {
            "schema_version": "hcam.phase5.p5_4.contract_cases.v1",
            "marker": MARKER,
            "seed": SEED,
            "exact_case_count": len(cases),
            "groups": [{"name": name, "count": count} for name, count in GROUPS],
            "cases": cases,
        },
        "review-cases.generated.v1.json": {
            "schema_version": "hcam.phase5.p5_4.review_cases.v1",
            "marker": MARKER,
            "case_refs": [case["case_ref"] for case in review_cases],
            "server_authoritative": True,
            "automatic_retry": False,
            "external_side_effects": False,
        },
        "security-cases.generated.v1.json": {
            "schema_version": "hcam.phase5.p5_4.security_cases.v1",
            "marker": MARKER,
            "case_refs": [case["case_ref"] for case in security_cases],
            "threat_refs": [f"P5.4-T{index:02d}" for index in range(1, 41)],
            "real_data": False,
        },
        "visual-cases.generated.v1.json": {
            "schema_version": "hcam.phase5.p5_4.visual_cases.v1",
            "marker": MARKER,
            "cases": visual_cases,
        },
    }
    documents["replay-manifest.generated.v1.json"] = {
        "schema_version": "hcam.phase5.p5_4.replay_manifest.v1",
        "marker": MARKER,
        "seed": SEED,
        "inputs": {name: canonical_sha(value) for name, value in sorted(documents.items())},
        "clean_replays_required": 2,
    }
    return documents


def write_documents(root: Path) -> dict[str, str]:
    destination = root / "fixtures" / "phase-5" / "p5-4"
    destination.mkdir(parents=True, exist_ok=True)
    documents = build_documents()
    for name, value in documents.items():
        (destination / name).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return {name: canonical_sha(value) for name, value in sorted(documents.items())}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    hashes = write_documents(root)
    print(json.dumps({"status": "pass", "fixtures": len(hashes), "hashes": hashes}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
