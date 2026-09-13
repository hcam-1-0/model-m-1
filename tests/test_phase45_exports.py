from __future__ import annotations

import pytest

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.evidence import register_reference
from hcam.intelligence.investigations.exports import build_reference_manifest


def _reference(p45_context: dict, key: str):
    return register_reference(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        source_system_ref=stable_id("ref", "system"),
        source_object_ref=stable_id("ref", key),
        source_version="generated.v1",
        content_digest=digest({"evidence": key}),
        canonicalization_profile="generated.json.v1",
        classification="generated.restricted",
        registered_by=p45_context["actor"],
        reason=p45_context["reason"],
        registered_at=p45_context["now"],
    )


def test_export_is_reference_only_and_exposes_incomplete_closure(p45_context: dict) -> None:
    included = _reference(p45_context, "included")
    denied = _reference(p45_context, "denied")
    manifest = build_reference_manifest(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        purpose_code="generated.investigation",
        recipient_class="generated.reviewer",
        policy_ref=stable_id("ref", "export-policy"),
        references=[denied, included],
        allowed_reference_ids={included.reference_id},
        unresolved_reference_ids=set(),
        prepared_by=p45_context["actor"],
        prepared_at=p45_context["now"],
    )
    assert manifest.completeness == "partial"
    assert manifest.source_payload_included is False
    assert manifest.signature_profile == "disabled"
    assert manifest.delivery_state == "not_authorized"
    blocked = build_reference_manifest(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        purpose_code="generated.investigation",
        recipient_class="generated.records",
        policy_ref=stable_id("ref", "export-policy-blocked"),
        references=[included],
        allowed_reference_ids=set(),
        unresolved_reference_ids={included.reference_id},
        prepared_by=p45_context["actor"],
        prepared_at=p45_context["now"],
    )
    assert blocked.completeness == "blocked"
    with pytest.raises(ValueError, match="share timeline"):
        build_reference_manifest(
            timeline_id=p45_context["timeline_id"],
            department="Generated-Department-Other",
            purpose_code="generated.investigation",
            recipient_class="generated.records",
            policy_ref=stable_id("ref", "export-policy-other"),
            references=[included],
            allowed_reference_ids=set(),
            unresolved_reference_ids=set(),
            prepared_by=p45_context["actor"],
            prepared_at=p45_context["now"],
        )
