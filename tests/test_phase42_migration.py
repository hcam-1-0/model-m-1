from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from hcam.database import CURRENT_SCHEMA_REVISION, Database


P42_TABLES = {
    "intelligence_rule_compilations",
    "intelligence_rule_scope_members",
    "intelligence_rule_schedules",
    "intelligence_rule_lifecycle_events",
    "intelligence_rule_state_checkpoints",
    "intelligence_rule_evaluation_revisions",
    "intelligence_rule_shadow_comparisons",
}
P42_RULE_COLUMNS = {
    "authoring_digest",
    "semantic_digest",
    "compilation_id",
    "schedule_digest",
}
P43_TABLES = {
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


def test_phase42_migration_round_trip_and_metadata_parity(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'phase42-migration.db').as_posix()}"
    config = _config(database_url)
    command.upgrade(config, "0014_rule_authoring_evaluation")
    database = Database(database_url)
    try:
        inspector = inspect(database.engine)
        assert P43_TABLES.isdisjoint(inspector.get_table_names())
        assert CURRENT_SCHEMA_REVISION == "0018_operations_security_scale"
        assert P42_TABLES.issubset(inspector.get_table_names())
        assert P42_RULE_COLUMNS.issubset(
            column["name"] for column in inspector.get_columns("intelligence_rules")
        )
        assert {
            "rule_key",
            "rule_version",
            "canonical_ast",
            "cel_compilations",
            "diagnostic_map",
            "static_cost",
            "operational",
            "generated_only",
        }.issubset(
            column["name"]
            for column in inspector.get_columns("intelligence_rule_compilations")
        )
        unique_sets = {
            tuple(item["column_names"])
            for item in inspector.get_unique_constraints("intelligence_rules")
        }
        assert ("department", "rule_key", "rule_version") in unique_sets
        assert ("rule_id",) not in unique_sets
        lifecycle_checks = " ".join(
            str(item["sqltext"])
            for item in inspector.get_check_constraints(
                "intelligence_rule_lifecycle_events"
            )
        )
        assert "'active'" not in lifecycle_checks
        assert "operational = false" in lifecycle_checks
        evaluation_columns = {
            column["name"]
            for column in inspector.get_columns(
                "intelligence_rule_evaluation_revisions"
            )
        }
        assert not evaluation_columns.intersection(
            {"frame", "image", "media", "locator", "url", "bytes"}
        )

        command.upgrade(config, "0018_operations_security_scale")
        database.check_ready()
        command.check(config)
        assert P43_TABLES.issubset(inspect(database.engine).get_table_names())

        database.dispose()
        command.downgrade(config, "0014_rule_authoring_evaluation")
        downgraded = Database(database_url)
        try:
            downgraded_inspector = inspect(downgraded.engine)
            assert P42_TABLES.issubset(downgraded_inspector.get_table_names())
            assert P43_TABLES.isdisjoint(downgraded_inspector.get_table_names())
        finally:
            downgraded.dispose()

        command.upgrade(config, "head")
        final = Database(database_url)
        try:
            final.check_ready()
            assert P42_TABLES.issubset(inspect(final.engine).get_table_names())
            command.check(config)
        finally:
            final.dispose()
    finally:
        database.dispose()
