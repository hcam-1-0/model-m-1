from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FIXTURE_NAMES = (
    "generated-telemetry-registry-v1.json",
    "generated-trace-context-v1.json",
    "generated-signal-separation-v1.json",
    "generated-unified-search-v1.json",
    "generated-failure-taxonomy-v1.json",
    "generated-service-objectives-v1.json",
    "generated-worker-conformance-v1.json",
    "generated-control-hierarchy-v1.json",
    "generated-security-isolation-v1.json",
    "generated-supply-chain-v1.json",
    "generated-recovery-drills-v1.json",
    "generated-capacity-runs-v1.json",
    "generated-placement-plans-v1.json",
    "generated-abuse-v1.json",
)
SCENARIOS_PER_FIXTURE = 80


def _hex(category: str, index: int, length: int) -> str:
    return hashlib.sha256(f"phase46:{category}:{index}".encode("ascii")).hexdigest()[:length]


def _scenario(category: str, index: int) -> dict[str, Any]:
    common: dict[str, Any] = {
        "scenario_id": f"p46.{category}.{index:04d}",
        "department": f"Generated Department {index % 4}",
        "generated_only": True,
        "operational": False,
    }
    if category == "telemetry-registry":
        common.update(metric=f"hcam_generated_metric_{index % 16}", labels={"outcome": ("accepted", "denied", "failed", "unknown")[index % 4]})
    elif category == "trace-context":
        common.update(traceparent=f"00-{_hex(category, index, 32)}-{_hex(category + '.parent', index, 16)}-{index % 2:02x}", grants_authority=False)
    elif category == "signal-separation":
        common.update(lane=("operational", "security", "audit", "evidence")[index % 4], raw_retained=False)
    elif category == "unified-search":
        common.update(enabled=False, authoritative=False, raw_records_retained=False)
    elif category == "failure-taxonomy":
        common.update(code=("authorization.denied", "policy.denied", "dependency.timeout", "state.unknown")[index % 4], retry=("never", "never", "bounded", "never")[index % 4])
    elif category == "service-objectives":
        common.update(target_state=("unset", "provisional", "approved", "approved")[index % 4], good=index % 11, bad=index % 3, unknown=index % 2)
    elif category == "worker-conformance":
        common.update(state=("queued", "leased", "succeeded", "failed", "dead_letter")[index % 5], attempt_count=index % 4, lease_seconds=90)
    elif category == "control-hierarchy":
        common.update(scope=("platform", "department", "service", "lane")[index % 4], state=("deny", "allow")[index % 2], deny_precedence=True)
    elif category == "security-isolation":
        common.update(subject_department=f"Generated Department {index % 4}", target_department=f"Generated Department {(index + 1) % 4}", outcome="denied")
    elif category == "supply-chain":
        common.update(vulnerability_state=("not_observed", "unknown", "stale", "failed", "verified")[index % 5], scanners_executed=False)
    elif category == "recovery-drills":
        common.update(outcome=("complete", "partial", "failed", "unknown")[index % 4], external_action_executed=False, targets="unset")
    elif category == "capacity-runs":
        common.update(scale=("C1", "C10", "C50")[index % 3], mode=("latency", "balanced", "throughput")[index % 3], hardware_tested=False, limitations=["capacity.generated_simulation_only"])
    elif category == "placement-plans":
        common.update(profile_class=("developer_laptop", "owned_gpu_lab", "server_node", "kubernetes_node_class")[index % 4], executable=False, reason=("placed", "optional_lane_bypassed", "mandatory_capability_missing", "capacity_exhausted")[index % 4])
    elif category == "abuse":
        common.update(vector=("unknown_field", "oversized_value", "cross_scope", "malformed_trace", "retry_integrity")[index % 5], expected="rejected")
    return common


def render_fixture(filename: str) -> bytes:
    category = filename.removeprefix("generated-").removesuffix("-v1.json")
    payload = {
        "schema_version": f"hcam.phase4.p4_6.fixture.{category}.v1",
        "category": category,
        "scenario_count": SCENARIOS_PER_FIXTURE,
        "scenarios": [_scenario(category, index) for index in range(SCENARIOS_PER_FIXTURE)],
    }
    return (json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def generate(output_root: Path, *, check: bool = False) -> dict[str, str]:
    output_root = output_root.resolve()
    digests: dict[str, str] = {}
    for filename in FIXTURE_NAMES:
        payload = render_fixture(filename)
        path = output_root / filename
        if check:
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"generated fixture differs: {filename}")
        else:
            output_root.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        digests[filename] = hashlib.sha256(payload).hexdigest().upper()
    return digests


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic Phase 4.6 fixtures")
    parser.add_argument("--output-root", type=Path, default=Path("contracts/phase-4/p4-6/fixtures"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    digests = generate(args.output_root, check=args.check)
    print(json.dumps({"files": digests, "scenario_count": len(FIXTURE_NAMES) * SCENARIOS_PER_FIXTURE}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
