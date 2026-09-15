from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from hcam.security.auth import Principal


_SCOPE_SEPARATOR = "\x1f"
REFERENCE_INTEGRATION_TABLES = (
    "reference_provider_versions",
    "reference_catalogue_snapshots",
    "reference_catalogue_records",
    "reference_query_jobs",
    "reference_query_attempts",
    "reference_candidate_sets",
    "reference_review_handoffs",
    "reference_control_revisions",
    "reference_circuit_states",
    "reference_integration_outbox",
)
INVESTIGATION_TABLES = (
    "investigation_timelines_v2",
    "investigation_timeline_revisions",
    "investigation_timeline_entries_v2",
    "investigation_evidence_references",
    "investigation_integrity_assessments",
    "investigation_provenance_bundles",
    "investigation_corrections",
    "investigation_correction_impacts",
    "investigation_reviews",
    "investigation_relationships",
    "investigation_hold_overlays",
    "investigation_retention_evaluations",
    "investigation_deletion_receipts",
    "investigation_export_manifests",
    "investigation_impact_jobs",
    "investigation_command_receipts",
    "investigation_outbox",
)


def apply_department_scope(session: Session, principal: Principal) -> None:
    if session.get_bind().dialect.name != "postgresql":
        return
    unrestricted = principal.has_unrestricted_department_access
    departments = "" if unrestricted else _SCOPE_SEPARATOR.join(sorted(principal.departments))
    session.execute(
        text("SELECT set_config('hcam.is_platform_admin', :value, true)"),
        {"value": "true" if unrestricted else "false"},
    )
    session.execute(
        text("SELECT set_config('hcam.allowed_departments', :value, true)"),
        {"value": departments},
    )
