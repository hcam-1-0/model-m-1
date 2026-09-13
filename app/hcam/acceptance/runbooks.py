from __future__ import annotations

from hcam.acceptance.canonical import stable_id
from hcam.acceptance.contracts import (
    OperationsRunbookV1,
    ProductionPrerequisiteOutlineV1,
    ProductionPrerequisiteV1,
    RunbookStepV1,
)


def build_generated_runbook() -> OperationsRunbookV1:
    actions = (
        (
            "verify_authorization",
            "runbook.authorization_verified",
            "runbook.authorization_invalid",
            False,
        ),
        (
            "verify_sources",
            "runbook.sources_verified",
            "runbook.source_mismatch",
            False,
        ),
        ("lint_fixtures", "runbook.fixtures_linted", "runbook.fixture_invalid", False),
        (
            "execute_first_replay",
            "runbook.first_replay_complete",
            "runbook.replay_failed",
            True,
        ),
        (
            "reset_generated_state",
            "runbook.state_reset",
            "runbook.cleanup_failed",
            False,
        ),
        (
            "execute_second_replay",
            "runbook.second_replay_complete",
            "runbook.replay_failed",
            True,
        ),
        (
            "compare_semantics",
            "runbook.replays_equal",
            "runbook.replays_diverged",
            False,
        ),
        ("validate_handoff", "runbook.handoff_valid", "runbook.handoff_invalid", False),
        (
            "seal_evidence",
            "runbook.evidence_sealed",
            "runbook.evidence_incomplete",
            False,
        ),
        (
            "verify_zero_retention",
            "runbook.zero_retention_verified",
            "runbook.retention_detected",
            False,
        ),
    )
    return OperationsRunbookV1(
        runbook_id=stable_id("p47", "runbook", "generated-acceptance"),
        preconditions=(
            "owner_start_authorization_exact",
            "generated_only_inputs",
            "network_disabled",
            "production_environment_denied",
        ),
        steps=tuple(
            RunbookStepV1(
                order=index,
                action=action,
                expected_reason=expected,
                failure_reason=failure,
                resumable=resumable,
            )
            for index, (action, expected, failure, resumable) in enumerate(
                actions, start=1
            )
        ),
    )


def build_production_prerequisites() -> ProductionPrerequisiteOutlineV1:
    categories = {
        "authorization": ("approved_role_matrix", "department_isolation_evidence"),
        "data_governance": ("approved_data_classes", "retention_and_hold_policy"),
        "operations": ("owned_runbook", "incident_response_drill"),
        "reliability": ("accepted_slo", "recovery_validation"),
        "security": ("threat_review", "supply_chain_review"),
        "integrations": ("provider_authorization", "destination_and_secret_controls"),
        "accessibility": (
            "manual_accessibility_review",
            "assistive_technology_validation",
        ),
        "deployment": ("approved_topology", "rollback_validation"),
    }
    return ProductionPrerequisiteOutlineV1(
        prerequisites=tuple(
            ProductionPrerequisiteV1(
                prerequisite_id=stable_id("p47", "prerequisite", category),
                category=category,
                required_evidence=evidence,
            )
            for category, evidence in categories.items()
        )
    )


def validate_non_operational(
    runbook: OperationsRunbookV1,
    outline: ProductionPrerequisiteOutlineV1,
) -> None:
    if runbook.production_use or not runbook.zero_retention_required:
        raise ValueError(
            "the P4.7 runbook must remain non-operational and zero-retention"
        )
    if outline.operationally_validated or outline.executable:
        raise ValueError("production prerequisites must remain non-effective")
    if any(
        item.status != "not_operationally_validated" for item in outline.prerequisites
    ):
        raise ValueError("every production prerequisite must remain unvalidated")
    if any(
        item.environment_specific_content_present or item.executable
        for item in outline.prerequisites
    ):
        raise ValueError(
            "production prerequisite content cannot be executable or environment specific"
        )
