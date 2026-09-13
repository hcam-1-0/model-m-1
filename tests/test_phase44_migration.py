from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from hcam.database import CURRENT_SCHEMA_REVISION, Database
from hcam.intelligence.row_security import (
    INVESTIGATION_TABLES,
    REFERENCE_INTEGRATION_TABLES,
)


def config(database_url: str) -> Config:
    result = Config("alembic.ini")
    result.set_main_option("sqlalchemy.url", database_url)
    return result


def test_phase44_migration_round_trip_and_metadata_parity(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'phase44-migration.db').as_posix()}"
    alembic = config(database_url)
    command.upgrade(alembic, "0015_alert_lifecycle_orchestration")
    before = Database(database_url, allow_unversioned_schema=True)
    try:
        assert set(REFERENCE_INTEGRATION_TABLES).isdisjoint(
            inspect(before.engine).get_table_names()
        )
    finally:
        before.dispose()

    command.upgrade(alembic, "0016_reference_integrations")
    current = Database(database_url, allow_unversioned_schema=True)
    try:
        inspector = inspect(current.engine)
        assert set(REFERENCE_INTEGRATION_TABLES).issubset(inspector.get_table_names())
        assert set(INVESTIGATION_TABLES).isdisjoint(inspector.get_table_names())
        assert {"semantic_key", "delivery_key", "lease_until"}.issubset(
            item["name"] for item in inspector.get_columns("reference_query_jobs")
        )
    finally:
        current.dispose()

    command.upgrade(alembic, "0018_operations_security_scale")
    head = Database(database_url)
    try:
        head.check_ready()
        command.check(alembic)
        assert CURRENT_SCHEMA_REVISION == "0018_operations_security_scale"
        assert set(INVESTIGATION_TABLES).issubset(
            inspect(head.engine).get_table_names()
        )
    finally:
        head.dispose()

    command.downgrade(alembic, "0016_reference_integrations")
    downgraded = Database(database_url, allow_unversioned_schema=True)
    try:
        tables = inspect(downgraded.engine).get_table_names()
        assert set(REFERENCE_INTEGRATION_TABLES).issubset(tables)
        assert set(INVESTIGATION_TABLES).isdisjoint(tables)
    finally:
        downgraded.dispose()
    command.upgrade(alembic, "head")


def test_phase44_migration_registers_one_linear_head() -> None:
    directory = ScriptDirectory.from_config(config("sqlite:///:memory:"))
    assert directory.get_heads() == ["0018_operations_security_scale"]
    revision = directory.get_revision("0018_operations_security_scale")
    assert revision is not None
    assert revision.down_revision == "0017_investigation_evidence"
