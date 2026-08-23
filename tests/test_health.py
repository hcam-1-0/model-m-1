from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from hcam.main import create_app
from hcam.settings import Settings


def test_liveness_and_readiness(app: FastAPI) -> None:
    with TestClient(app) as client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")

    assert live.status_code == 200
    assert live.json() == {"status": "live"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


def test_readiness_fails_before_database_migration(tmp_path: Path) -> None:
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'unmigrated.db').as_posix()}",
            create_schema=False,
            environment="test",
        )
    )
    with TestClient(application) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not ready"}


def test_readiness_rejects_stale_migration_and_accepts_current_head(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("HCAM_DATABASE_URL", raising=False)
    database_url = f"sqlite:///{(tmp_path / 'stale.db').as_posix()}"
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "0001_camera_registry")

    stale_app = create_app(
        Settings(
            database_url=database_url,
            dev_auth_enabled=True,
            environment="test",
        )
    )
    with TestClient(stale_app) as client:
        stale = client.get("/health/ready")

    command.upgrade(config, "head")
    current_app = create_app(
        Settings(
            database_url=database_url,
            dev_auth_enabled=True,
            environment="test",
        )
    )
    with TestClient(current_app) as client:
        current = client.get("/health/ready")

    assert stale.status_code == 503
    assert stale.json() == {"detail": "Database is not ready"}
    assert current.status_code == 200
    assert current.json() == {"status": "ready"}


def test_readiness_rejects_missing_audit_columns(app: FastAPI) -> None:
    with app.state.database.engine.begin() as connection:
        connection.execute(text("ALTER TABLE audit_events DROP COLUMN reason"))

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not ready"}
