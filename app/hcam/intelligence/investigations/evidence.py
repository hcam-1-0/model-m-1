from __future__ import annotations

from datetime import datetime

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import EvidenceReferenceV2


class SourceResolutionDenied(RuntimeError):
    reason_code = "evidence.source_resolution_denied"


def register_reference(
    *,
    timeline_id: str,
    department: str,
    source_system_ref: str,
    source_object_ref: str,
    source_version: str,
    content_digest: str,
    canonicalization_profile: str,
    classification: str,
    registered_by: str,
    reason: str,
    registered_at: datetime,
) -> EvidenceReferenceV2:
    reference_id = stable_id(
        "iref",
        timeline_id,
        source_system_ref,
        source_object_ref,
        source_version,
        content_digest,
    )
    return EvidenceReferenceV2(
        reference_id=reference_id,
        timeline_id=timeline_id,
        department=department,
        source_system_ref=source_system_ref,
        source_object_ref=source_object_ref,
        source_version=source_version,
        content_digest=content_digest,
        canonicalization_profile=canonicalization_profile,
        classification=classification,
        registered_by=registered_by,
        reason=reason,
        registered_at=registered_at,
    )


def reference_identity(reference: EvidenceReferenceV2) -> str:
    return digest(
        {
            "source_system_ref": reference.source_system_ref,
            "source_object_ref": reference.source_object_ref,
            "source_version": reference.source_version,
            "content_digest": reference.content_digest,
            "canonicalization_profile": reference.canonicalization_profile,
        }
    )


def resolve_source(_reference: EvidenceReferenceV2) -> bytes:
    raise SourceResolutionDenied("source resolution is not implemented in generated P4.5")
