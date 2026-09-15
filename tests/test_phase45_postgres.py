from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from hcam.intelligence.row_security import INVESTIGATION_TABLES


@pytest.mark.postgres
def test_phase45_postgres_forced_rls() -> None:
    database_url = os.getenv("HCAM_POSTGRES_TEST_URL")
    if not database_url:
        pytest.skip("HCAM_POSTGRES_TEST_URL is not configured")
    alembic = Config("alembic.ini")
    alembic.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic, "head")
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity "
                    "FROM pg_class c WHERE c.relname = ANY(:tables)"
                ),
                {"tables": list(INVESTIGATION_TABLES)},
            ).all()
        assert len(rows) == len(INVESTIGATION_TABLES)
        assert all(row.relrowsecurity and row.relforcerowsecurity for row in rows)
    finally:
        engine.dispose()
