from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from hcam.analytics.activation import (
    P3_2_GENERATOR_VERSION,
    P3_2_PIPELINE_VERSION,
    P3_2_POLICY_VERSION,
    assess_generated_activation,
)
from hcam.analytics.models import AnalyticsAssignment


ROOT = Path(__file__).parents[1]


def _canonical_digest(relative_path: str) -> str:
    document = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    canonical = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def test_p3_2_activation_versions_are_bound_to_owner_records() -> None:
    assert P3_2_POLICY_VERSION == _canonical_digest(
        "contracts/phase-3/p3-2-start-authorization.json"
    )
    assert P3_2_PIPELINE_VERSION == _canonical_digest(
        "contracts/phase-3/p3-2-runtime-approval.json"
    )
    assert P3_2_GENERATOR_VERSION == _canonical_digest(
        "contracts/phase-3/p3-2-dataset-approval.json"
    )


def test_p3_2_activation_expires_closed() -> None:
    assignment = AnalyticsAssignment(
        assignment_id="ana_" + "1" * 32,
        department="Engineering Lab",
        stream_id="str_" + "2" * 32,
        camera_id="synthetic:cctv-001",
        capability="object_detection",
        pipeline_id="unapproved",
        pipeline_version="sha256:" + "1" * 64,
        models=[],
        taxonomy_version="hcam.objects.tier_a.v1",
        policy_version="sha256:" + "2" * 64,
        configuration_digest="sha256:" + "3" * 64,
        minimum_confidence=0.25,
        sampling_fps=1,
        maximum_queue_age_ms=1_000,
        geometry_refs=[],
        retention_class="derived.analytics.standard",
        last_actor_id="test",
        last_change_reason="Validate authorization expiry",
        approval_record_id="D-P3.2-START",
    )

    assessment = assess_generated_activation(
        assignment,
        runtime_configured=True,
        now=datetime(2026, 9, 25, tzinfo=UTC),
    )

    assert assessment.eligible is False
    assert "authorization_expired" in assessment.blocking_reasons
