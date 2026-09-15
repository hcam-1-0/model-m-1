from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from hcam.database import CURRENT_SCHEMA_REVISION, Database
from hcam.operations.platform.models import PlatformServiceObjectiveRecord


PLATFORM_TABLES = {
    "platform_service_objectives",
    "platform_error_budgets",
    "platform_degradation_states",
    "platform_circuit_states",
    "platform_kill_switch_revisions",
    "platform_recovery_results",
    "platform_capacity_results",
    "platform_supply_chain_inventories",
    "platform_security_evidence",
    "platform_operations_outbox",
}


def _config(database_url: str) -> Config:
    result = Config("alembic.ini")
    result.set_main_option("sqlalchemy.url", database_url)
    return result


def test_phase46_migration_round_trips_from_phase45(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'phase46.db').as_posix()}"
    alembic = _config(database_url)
    command.upgrade(alembic, "0017_investigation_evidence")
    before = Database(database_url, allow_unversioned_schema=True)
    try:
        assert PLATFORM_TABLES.isdisjoint(inspect(before.engine).get_table_names())
    finally:
        before.dispose()
    command.upgrade(alembic, "0018_operations_security_scale")
    current = Database(database_url)
    try:
        current.check_ready()
        command.check(alembic)
        assert CURRENT_SCHEMA_REVISION == "0018_operations_security_scale"
        assert PLATFORM_TABLES.issubset(inspect(current.engine).get_table_names())
        assert PlatformServiceObjectiveRecord.__tablename__ in PLATFORM_TABLES
    finally:
        current.dispose()
    command.downgrade(alembic, "0017_investigation_evidence")
    downgraded = Database(database_url, allow_unversioned_schema=True)
    try:
        assert PLATFORM_TABLES.isdisjoint(inspect(downgraded.engine).get_table_names())
    finally:
        downgraded.dispose()
    command.upgrade(alembic, "0018_operations_security_scale")


def test_phase46_registers_one_linear_head() -> None:
    directory = ScriptDirectory.from_config(_config("sqlite:///:memory:"))
    assert directory.get_heads() == ["0018_operations_security_scale"]
    revision = directory.get_revision("0018_operations_security_scale")
    assert revision is not None
    assert revision.down_revision == "0017_investigation_evidence"
