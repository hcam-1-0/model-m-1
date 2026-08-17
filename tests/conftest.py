from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI

from hcam.camera_registry.importer import RegistryImporter
from hcam.main import create_app
from hcam.settings import Settings


@pytest.fixture
def seed_file() -> Path:
    return Path(__file__).parent / "fixtures" / "camera-registry-seed.json"


@pytest.fixture
def app(tmp_path: Path) -> Iterator[FastAPI]:
    database_path = tmp_path / "hcam-test.db"
    application = create_app(
        Settings(
            database_url=f"sqlite:///{database_path.as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
        )
    )
    application.state.database.create_schema()
    yield application
    application.state.database.dispose()


@pytest.fixture
def importer(app: FastAPI) -> RegistryImporter:
    return RegistryImporter(app.state.database.session_factory)


@pytest.fixture
def imported_app(app: FastAPI, seed_file: Path) -> FastAPI:
    RegistryImporter(app.state.database.session_factory).import_file(seed_file)
    return app


@pytest.fixture
def viewer_headers() -> dict[str, str]:
    return {
        "X-HCAM-Actor": "test-viewer",
        "X-HCAM-Roles": "camera.viewer",
        "X-HCAM-Departments": "*",
    }


@pytest.fixture
def editor_headers() -> dict[str, str]:
    return {
        "X-HCAM-Actor": "test-editor",
        "X-HCAM-Roles": "camera.editor",
        "X-HCAM-Departments": "*",
        "X-HCAM-Reason": "Authorized registry test update",
    }


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {
        "X-HCAM-Actor": "test-admin",
        "X-HCAM-Roles": "platform.admin",
        "X-HCAM-Departments": "*",
        "X-HCAM-Reason": "Authorized registry test import",
    }
