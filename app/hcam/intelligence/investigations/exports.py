from __future__ import annotations

from datetime import datetime

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import (
    EvidenceReferenceV2,
    ExportManifestV1,
    ExportReferenceV1,
)


def build_reference_manifest(
    *,
    timeline_id: str,
    department: str,
    purpose_code: str,
    recipient_class: str,
    policy_ref: str,
    references: list[EvidenceReferenceV2],
    allowed_reference_ids: set[str],
    unresolved_reference_ids: set[str],
    prepared_by: str,
    prepared_at: datetime,
) -> ExportManifestV1:
    if any(
        reference.timeline_id != timeline_id or reference.department != department
        for reference in references
    ):
        raise ValueError("export references must share timeline and department")
    projected: list[ExportReferenceV1] = []
    for reference in sorted(references, key=lambda item: item.reference_id):
        if reference.reference_id in unresolved_reference_ids:
            inclusion = "unresolved"
            reason = "export.reference_unresolved"
        elif reference.reference_id not in allowed_reference_ids:
            inclusion = "denied"
            reason = "export.reference_denied"
        else:
            inclusion = "included"
            reason = "export.reference_included"
        projected.append(
            ExportReferenceV1(
                reference_id=reference.reference_id,
                version=reference.source_version,
                content_digest=reference.content_digest,
                inclusion=inclusion,
                reason_code=reason,
            )
        )
    states = {item.inclusion for item in projected}
    completeness = "complete" if states <= {"included"} else "partial"
    if projected and states <= {"denied", "unresolved"}:
        completeness = "blocked"
    material = {
        "timeline_id": timeline_id,
        "department": department,
        "purpose_code": purpose_code,
        "recipient_class": recipient_class,
        "policy_ref": policy_ref,
        "references": [item.model_dump(mode="json") for item in projected],
        "completeness": completeness,
    }
    manifest_digest = digest(material)
    return ExportManifestV1(
        manifest_id=stable_id("iexp", timeline_id, purpose_code, manifest_digest),
        timeline_id=timeline_id,
        department=department,
        purpose_code=purpose_code,
        recipient_class=recipient_class,
        policy_ref=policy_ref,
        references=projected,
        completeness=completeness,
        manifest_digest=manifest_digest,
        prepared_by=prepared_by,
        prepared_at=prepared_at,
    )
