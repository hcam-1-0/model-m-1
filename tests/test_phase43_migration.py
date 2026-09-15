from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from hcam.database import CURRENT_SCHEMA_REVISION, Database


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
P43_ALERT_COLUMNS = {
    "semantic_key",
    "delivery_key",
    "source_evaluation_id",
    "source_evaluation_revision",
    "source_evaluation_digest",
    "incident_key",
    "domain",
    "certainty",
    "chronology_confidence",
    "assigned_to",
    "suppression_code",
    "merged_into",
    "policy_digest",
}
P44_TABLES = {
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
}


def _config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_phase43_migration_round_trip_and_metadata_parity(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'phase43-migration.db').as_posix()}"
    config = _config(database_url)
    command.upgrade(config, "0014_rule_authoring_evaluation")
    before = Database(database_url, allow_unversioned_schema=True)
    try:
        before_inspector = inspect(before.engine)
        assert P43_TABLES.isdisjoint(before_inspector.get_table_names())
        assert P43_ALERT_COLUMNS.isdisjoint(
            column["name"] for column in before_inspector.get_columns("alerts")
        )
    finally:
        before.dispose()

    command.upgrade(config, "0015_alert_lifecycle_orchestration")
    phase43 = Database(database_url, allow_unversioned_schema=True)
    try:
        inspector = inspect(phase43.engine)
        assert P43_TABLES.issubset(inspector.get_table_names())
        assert P44_TABLES.isdisjoint(inspector.get_table_names())
        assert P43_ALERT_COLUMNS.issubset(
            column["name"] for column in inspector.get_columns("alerts")
        )
        assert any(
            item["name"] == "uq_alert_semantic_key"
            for item in inspector.get_unique_constraints("alerts")
        )
        timer_checks = " ".join(
            str(item["sqltext"])
            for item in inspector.get_check_constraints("alert_timer_intents")
        )
        assert "attempt_count >= 0" in timer_checks
        assert "attempt_count <= 3" in timer_checks
        for table in P43_TABLES:
            columns = {item["name"] for item in inspector.get_columns(table)}
            assert "department" in columns
    finally:
        phase43.dispose()

    command.upgrade(config, "0018_operations_security_scale")
    database = Database(database_url)
    try:
        database.check_ready()
        command.check(config)
        assert CURRENT_SCHEMA_REVISION == "0018_operations_security_scale"
        assert P44_TABLES.issubset(inspect(database.engine).get_table_names())
    finally:
        database.dispose()

    command.downgrade(config, "0015_alert_lifecycle_orchestration")
    downgraded = Database(database_url, allow_unversioned_schema=True)
    try:
        downgraded_inspector = inspect(downgraded.engine)
        assert P43_TABLES.issubset(downgraded_inspector.get_table_names())
        assert P44_TABLES.isdisjoint(downgraded_inspector.get_table_names())
    finally:
        downgraded.dispose()

    command.upgrade(config, "head")
    final = Database(database_url)
    try:
        final.check_ready()
        command.check(config)
        assert P43_TABLES.issubset(inspect(final.engine).get_table_names())
    finally:
        final.dispose()


def test_phase43_migration_registers_one_linear_head() -> None:
    config = _config("sqlite:///:memory:")
    directory = ScriptDirectory.from_config(config)
    assert directory.get_heads() == ["0018_operations_security_scale"]
    revision = directory.get_revision("0018_operations_security_scale")
    assert revision is not None
    assert revision.down_revision == "0017_investigation_evidence"
