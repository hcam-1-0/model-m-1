from __future__ import annotations

from hcam.acceptance.canonical import stable_id
from hcam.acceptance.contracts import CompatibilityEntryV1, CompatibilityMatrixV1


def build_compatibility_matrix(evidence_ref: str) -> CompatibilityMatrixV1:
    entries = tuple(
        CompatibilityEntryV1(
            entry_id=f"phase5.compatibility.{index}",
            contract=contract,
            from_version="1.0.0",
            to_version="1.0.0",
            change_class=change_class,
            supported_consumers=("phase5.consumer.v1",),
            migration_required=change_class
            in {"breaking_schema", "breaking_semantic", "security_boundary"},
            evidence_ref=evidence_ref,
            security_review_required=change_class == "security_boundary",
        )
        for index, (contract, change_class) in enumerate(
            (
                ("hcam.handoff.http-operation.v1", "compatible_behavior"),
                ("hcam.handoff.event-workflow.v1", "optional_additive"),
                ("hcam.handoff.ui-accessibility.v1", "new_capability"),
                ("hcam.handoff.compatibility.v1", "documentation"),
            ),
            start=1,
        )
    )
    return CompatibilityMatrixV1(entries=entries)


def classify_change(
    *, required_field_added: bool, authorization_changed: bool, semantics_changed: bool
) -> str:
    if authorization_changed:
        return "security_boundary"
    if semantics_changed:
        return "breaking_semantic"
    if required_field_added:
        return "breaking_schema"
    return "optional_additive"


def validate_compatibility(matrix: CompatibilityMatrixV1) -> None:
    identifiers = {item.entry_id for item in matrix.entries}
    if len(identifiers) != len(matrix.entries):
        raise ValueError("compatibility entries must be unique")
    for entry in matrix.entries:
        expected_migration = entry.change_class in {
            "breaking_schema",
            "breaking_semantic",
            "security_boundary",
        }
        if entry.migration_required != expected_migration:
            raise ValueError("breaking changes require explicit migration")
        if (
            entry.change_class == "security_boundary"
            and not entry.security_review_required
        ):
            raise ValueError("security-boundary changes require review")


def compatibility_evidence_ref() -> str:
    return stable_id("p47", "evidence", "contracts/phase-4/p4-7/scenario-results.json")
