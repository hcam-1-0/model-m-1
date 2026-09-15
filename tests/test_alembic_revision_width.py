from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text


def _config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_long_revision_is_reachable_after_version_marker_widening(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'revision-width.db').as_posix()}"
    config = _config(database_url)
    command.upgrade(config, "0014_rule_authoring_evaluation")
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == "0018_operations_security_scale"

    directory = ScriptDirectory.from_config(config)
    marker = directory.get_revision("0014b_alembic_version_width")
    alert_lifecycle = directory.get_revision("0015_alert_lifecycle_orchestration")
    assert marker is not None
    assert alert_lifecycle is not None
    assert alert_lifecycle.down_revision == marker.revision
