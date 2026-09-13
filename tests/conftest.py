from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from hcam.camera_registry.importer import RegistryImporter
from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import (
    TemporalAssertionV1,
    TimelineCreateCommandV2,
    TimelineEntryV2,
)
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


@pytest.fixture
def p45_app(tmp_path: Path) -> Iterator[FastAPI]:
    database_path = tmp_path / "hcam-p45-test.db"
    application = create_app(
        Settings(
            database_url=f"sqlite:///{database_path.as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            intelligence_generated_investigations_enabled=True,
        )
    )
    application.state.database.create_schema()
    yield application
    application.state.database.dispose()


@pytest.fixture
def p45_headers() -> dict[str, str]:
    return {
        "X-HCAM-Actor": "generated.p45.operator",
        "X-HCAM-Roles": "platform.admin",
        "X-HCAM-Departments": "*",
        "X-HCAM-Reason": "Generated P4.5 authorized test reason",
    }


@pytest.fixture
def p45_context() -> dict[str, Any]:
    now = datetime(2026, 9, 5, 10, 0, tzinfo=UTC)
    actor = "generated.p45.operator"
    department = "Generated-Department-0"
    reason = "Generated P4.5 authorized test reason"
    timeline_id = stable_id("inv", "p45-test-timeline")
    command = TimelineCreateCommandV2(
        timeline_id=timeline_id,
        department=department,
        title="generated.p45.timeline",
        purpose_code="generated.investigation",
        actor_id=actor,
        reason=reason,
        delivery_id="generated.p45.timeline.create",
        requested_at=now,
    )

    def entry(index: int = 1, *, family: str = "event") -> TimelineEntryV2:
        recorded_at = now + timedelta(seconds=index * 3)
        return TimelineEntryV2(
            entry_id=stable_id("ient", timeline_id, index, family),
            timeline_id=timeline_id,
            department=department,
            family=family,
            subject_ref=stable_id("ref", "subject", index),
            sequence=index,
            aggregate_revision=index + 1,
            temporal=TemporalAssertionV1(
                occurred_at=now + timedelta(seconds=index),
                observed_at=now + timedelta(seconds=index),
                received_at=now + timedelta(seconds=index * 2),
                recorded_at=recorded_at,
                occurrence_precision="second",
                clock_trust="trusted",
            ),
            payload={"generated_value": f"event-{index}"},
            actor_id=actor,
            reason=reason,
            semantic_key=digest({"semantic": index, "family": family}),
            delivery_key=digest({"delivery": index, "family": family}),
            content_digest=digest({"content": index, "family": family}),
        )

    return {
        "now": now,
        "actor": actor,
        "department": department,
        "reason": reason,
        "timeline_id": timeline_id,
        "command": command,
        "entry": entry,
    }
