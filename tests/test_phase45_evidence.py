from __future__ import annotations

import pytest

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.evidence import (
    SourceResolutionDenied,
    reference_identity,
    register_reference,
    resolve_source,
)


def test_reference_registration_is_opaque_and_resolution_is_denied(p45_context: dict) -> None:
    reference = register_reference(
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        source_system_ref=stable_id("ref", "system"),
        source_object_ref=stable_id("ref", "object"),
        source_version="generated.v1",
        content_digest=digest({"generated": "evidence"}),
        canonicalization_profile="generated.json.v1",
        classification="generated.restricted",
        registered_by=p45_context["actor"],
        reason=p45_context["reason"],
        registered_at=p45_context["now"],
    )
    assert reference.source_payload_retained is False
    assert reference.locator_retained is False
    assert reference_identity(reference).startswith("sha256:")
    with pytest.raises(SourceResolutionDenied):
        resolve_source(reference)
