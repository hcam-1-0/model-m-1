from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from hcam.database import CURRENT_SCHEMA_REVISION, Database
from hcam.intelligence.row_security import INVESTIGATION_TABLES


def _config(database_url: str) -> Config:
    result = Config("alembic.ini")
    result.set_main_option("sqlalchemy.url", database_url)
    return result


def test_phase45_migration_preserves_v1_and_round_trips(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'phase45-migration.db').as_posix()}"
    alembic = _config(database_url)
    command.upgrade(alembic, "0016_reference_integrations")
    before = Database(database_url, allow_unversioned_schema=True)
    try:
        tables = set(inspect(before.engine).get_table_names())
        assert "investigation_timelines" in tables
        assert set(INVESTIGATION_TABLES).isdisjoint(tables)
    finally:
        before.dispose()

    command.upgrade(alembic, "0017_investigation_evidence")
    phase45 = Database(database_url, allow_unversioned_schema=True)
    try:
        tables = set(inspect(phase45.engine).get_table_names())
        assert "investigation_timelines" in tables
        assert set(INVESTIGATION_TABLES).issubset(tables)
        assert "platform_service_objectives" not in tables
    finally:
        phase45.dispose()

    command.upgrade(alembic, "0018_operations_security_scale")
    current = Database(database_url)
    try:
        current.check_ready()
        command.check(alembic)
        assert CURRENT_SCHEMA_REVISION == "0018_operations_security_scale"
        assert "platform_service_objectives" in inspect(current.engine).get_table_names()
    finally:
        current.dispose()

    command.downgrade(alembic, "0017_investigation_evidence")
    downgraded = Database(database_url, allow_unversioned_schema=True)
    try:
        tables = set(inspect(downgraded.engine).get_table_names())
        assert "investigation_timelines" in tables
        assert set(INVESTIGATION_TABLES).issubset(tables)
        assert "platform_service_objectives" not in tables
    finally:
        downgraded.dispose()
    command.upgrade(alembic, "0018_operations_security_scale")


def test_phase45_registers_one_linear_head() -> None:
    directory = ScriptDirectory.from_config(_config("sqlite:///:memory:"))
    assert directory.get_heads() == ["0018_operations_security_scale"]
    revision = directory.get_revision("0018_operations_security_scale")
    assert revision is not None
    assert revision.down_revision == "0017_investigation_evidence"
