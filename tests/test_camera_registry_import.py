from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from hcam.audit.models import AuditEvent
from hcam.camera_registry.importer import RegistryImportError, RegistryImporter
from hcam.camera_registry.models import Camera


def test_import_is_successful_idempotent_and_audited(
    importer: RegistryImporter, app, seed_file: Path
) -> None:
    first = importer.import_file(seed_file)
    second = importer.import_file(seed_file)

    assert first.created == 2
    assert first.updated == 0
    assert first.unchanged == 0
    assert second.created == 0
    assert second.updated == 0
    assert second.unchanged == 2

    with app.state.database.session_factory() as session:
        cameras = session.scalars(select(Camera).order_by(Camera.camera_id)).all()
        events = session.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at)).all()

    assert len(cameras) == 2
    assert len(events) == 2
    assert all(event.outcome == "success" for event in events)
    assert cameras[0].selected_url == "https://camera.example.invalid/streams/1"
    assert cameras[0].stream_path == "/streams/1"


def test_changed_seed_updates_only_changed_camera(
    importer: RegistryImporter, seed_file: Path, tmp_path: Path
) -> None:
    importer.import_file(seed_file)
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    payload["cameras"][0]["display_name"] = "Updated Synthetic Camera"
    changed_seed = tmp_path / "changed-seed.json"
    changed_seed.write_text(json.dumps(payload), encoding="utf-8")

    result = importer.import_file(changed_seed)

    assert result.created == 0
    assert result.updated == 1
    assert result.unchanged == 1


def test_source_identity_collision_rolls_back_and_is_audited(
    importer: RegistryImporter, app, seed_file: Path, tmp_path: Path
) -> None:
    importer.import_file(seed_file)
    payload = json.loads(seed_file.read_text(encoding="utf-8"))
    payload["cameras"] = [
        {
            **payload["cameras"][0],
            "camera_id": "synthetic:replacement",
            "display_name": "Conflicting Camera",
        }
    ]
    collision_seed = tmp_path / "collision-seed.json"
    collision_seed.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RegistryImportError):
        importer.import_file(collision_seed)

    with app.state.database.session_factory() as session:
        cameras = session.scalars(select(Camera)).all()
        events = session.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at)).all()

    assert len(cameras) == 2
    assert all(camera.camera_id != "synthetic:replacement" for camera in cameras)
    assert events[-1].outcome == "failure"


@pytest.mark.parametrize("kind", ["missing", "invalid"])
def test_import_failure_is_clear_and_audited(
    kind: str,
    importer: RegistryImporter,
    app,
    tmp_path: Path,
) -> None:
    seed_path = tmp_path / "bad-seed.json"
    if kind == "invalid":
        seed_path.write_text('{"schema": "wrong"}', encoding="utf-8")

    with pytest.raises(RegistryImportError):
        importer.import_file(seed_path)

    with app.state.database.session_factory() as session:
        event = session.scalars(select(AuditEvent)).one()

    assert event.outcome == "failure"
    assert event.context["file"] == "bad-seed.json"
    assert "error_type" in event.context
    assert "secret" not in json.dumps(event.context).lower()
