from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from hcam.database import Database


def test_alembic_accepts_percent_encoded_database_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_path = tmp_path / "percent%20encoded-migration.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)
    monkeypatch.delenv("HCAM_DATABASE_URL_FILE", raising=False)

    command.upgrade(Config("alembic.ini"), "head")

    database = Database(database_url)
    try:
        database.check_ready()
    finally:
        database.dispose()
