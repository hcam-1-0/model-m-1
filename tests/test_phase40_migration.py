from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from hcam.database import CURRENT_SCHEMA_REVISION, Database


P4_TABLES = {
    "intelligence_rules",
    "correlation_runs",
    "correlation_hypotheses",
    "hypothesis_evidence_refs",
    "reference_providers",
    "reference_queries",
    "alerts",
    "alert_revisions",
    "investigation_timelines",
    "timeline_entries",
}
P4_1_TABLES = {
    "correlation_event_receipts",
    "correlation_partition_checkpoints",
    "correlation_window_events",
    "correlation_lane_results",
    "correlation_hypothesis_revisions",
}
P4_2_TABLES = {
    "intelligence_rule_compilations",
    "intelligence_rule_scope_members",
    "intelligence_rule_schedules",
    "intelligence_rule_lifecycle_events",
    "intelligence_rule_state_checkpoints",
    "intelligence_rule_evaluation_revisions",
    "intelligence_rule_shadow_comparisons",
}
P4_3_TABLES = {
    "alert_command_receipts",
    "alert_lifecycle_events",
    "alert_review_quorum_policies",
    "alert_review_decisions",
    "alert_assignment_events",
    "alert_suppression_events",
    "alert_merge_relations",
    "alert_budget_policies",
    "alert_budget_counters",
    "alert_timer_intents",
    "alert_workflow_executions",
}


def _config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_phase40_migration_upgrade_drift_downgrade_cycle(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'phase40.db').as_posix()}"
    config = _config(database_url)
    command.upgrade(config, "0012_intelligence_control_plane")
    phase40 = Database(database_url)
    phase40_inspector = inspect(phase40.engine)
    assert P4_TABLES.issubset(phase40_inspector.get_table_names())
    assert P4_1_TABLES.isdisjoint(phase40_inspector.get_table_names())
    assert P4_2_TABLES.isdisjoint(phase40_inspector.get_table_names())
    assert P4_3_TABLES.isdisjoint(phase40_inspector.get_table_names())
    phase40.dispose()

    command.upgrade(config, "0013_correlation_foundation")
    phase41 = Database(database_url, allow_unversioned_schema=True)
    phase41_tables = inspect(phase41.engine).get_table_names()
    assert P4_TABLES.issubset(phase41_tables)
    assert P4_1_TABLES.issubset(phase41_tables)
    assert P4_2_TABLES.isdisjoint(phase41_tables)
    assert P4_3_TABLES.isdisjoint(phase41_tables)
    phase41.dispose()

    command.upgrade(config, "0014_rule_authoring_evaluation")
    database = Database(database_url)
    try:
        phase42_tables = set(inspect(database.engine).get_table_names())
        assert P4_2_TABLES.issubset(phase42_tables)
        assert P4_3_TABLES.isdisjoint(phase42_tables)
        command.upgrade(config, "0018_operations_security_scale")
        database.check_ready()
        assert CURRENT_SCHEMA_REVISION == "0018_operations_security_scale"
        inspector = inspect(database.engine)
        assert P4_TABLES.issubset(inspector.get_table_names())
        assert P4_1_TABLES.issubset(inspector.get_table_names())
        assert P4_2_TABLES.issubset(inspector.get_table_names())
        assert P4_3_TABLES.issubset(inspector.get_table_names())
        assert {
            "rule_id",
            "authority_class",
            "operational",
            "generated_only",
            "configuration_digest",
        }.issubset(
            column["name"] for column in inspector.get_columns("intelligence_rules")
        )
        assert {
            "enabled",
            "transport_state",
            "credential_state",
            "provider_kind",
        }.issubset(
            column["name"] for column in inspector.get_columns("reference_providers")
        )
        command.check(config)
        database.dispose()
        command.downgrade(config, "0012_intelligence_control_plane")
        downgraded = Database(database_url)
        downgraded_tables = inspect(downgraded.engine).get_table_names()
        assert P4_TABLES.issubset(downgraded_tables)
        assert P4_1_TABLES.isdisjoint(downgraded_tables)
        assert P4_2_TABLES.isdisjoint(downgraded_tables)
        assert P4_3_TABLES.isdisjoint(downgraded_tables)
        downgraded.dispose()
        command.upgrade(config, "0013_correlation_foundation")
        phase41_again = Database(database_url, allow_unversioned_schema=True)
        phase41_again_tables = inspect(phase41_again.engine).get_table_names()
        assert P4_1_TABLES.issubset(phase41_again_tables)
        assert P4_2_TABLES.isdisjoint(phase41_again_tables)
        assert P4_3_TABLES.isdisjoint(phase41_again_tables)
        phase41_again.dispose()
        command.upgrade(config, "0014_rule_authoring_evaluation")
        phase42_again = set(inspect(phase41_again.engine).get_table_names())
        assert P4_2_TABLES.issubset(phase42_again)
        assert P4_3_TABLES.isdisjoint(phase42_again)
        command.upgrade(config, "0018_operations_security_scale")
        command.check(config)
        final = Database(database_url)
        final.check_ready()
        assert P4_1_TABLES.issubset(inspect(final.engine).get_table_names())
        assert P4_2_TABLES.issubset(inspect(final.engine).get_table_names())
        assert P4_3_TABLES.issubset(inspect(final.engine).get_table_names())
        final.dispose()
    finally:
        database.dispose()


def test_phase40_models_expose_expected_constraints_and_indexes() -> None:
    from hcam.intelligence.models import IntelligenceRule, ReferenceProvider

    rule_names = {item.name for item in IntelligenceRule.__table__.constraints}
    provider_names = {item.name for item in ReferenceProvider.__table__.constraints}
    assert "ck_intelligence_rule_nonoperational" in rule_names
    assert "ck_intelligence_rule_generated" in rule_names
    assert "ck_reference_provider_disabled" in provider_names
    assert "ck_reference_provider_credentials" in provider_names
    assert {index.name for index in IntelligenceRule.__table__.indexes} == {
        "ix_intelligence_rule_scope"
    }
