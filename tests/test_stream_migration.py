from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import MetaData, Table, inspect, select
from sqlalchemy.exc import IntegrityError

from hcam.camera_registry.models import Camera
from hcam.database import Database
from hcam.streams.models import (
    OnvifControlLease,
    OnvifOperationRun,
    StreamCapabilityRefresh,
    StreamCapabilitySnapshot,
    StreamEndpoint,
    StreamHealthCurrent,
)


def _upgrade(database_url: str, revision: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, revision)


def _downgrade(database_url: str, revision: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.downgrade(config, revision)


def _legacy_camera() -> Camera:
    now = datetime.now(UTC)
    return Camera(
        camera_id="legacy:cctv-001",
        source_id="legacy",
        external_id="cctv-001",
        display_name="Legacy CCTV 001",
        department="Traffic",
        selected_url="https://media.test.local/live/cctv-001/index.m3u8",
        delivery_type="hls",
        codec="h264",
        container="hls",
        reachability="healthy",
        last_checked_at=now,
        source_schema="hcam.camera_registry.seed.v1",
        provenance={"kind": "synthetic-test"},
        imported_at=now,
        created_at=now,
        updated_at=now,
    )


def test_stream_migration_backfills_and_round_trips(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = f"sqlite:///{(tmp_path / 'stream-migration.db').as_posix()}"
    monkeypatch.setenv("HCAM_DATABASE_URL", database_url)
    _upgrade(database_url, "0003_camera_integrity")

    database = Database(database_url, allow_unversioned_schema=True)
    try:
        # Reflect the historical table instead of issuing an INSERT through
        # today's ORM model, which legitimately contains columns introduced by
        # later migrations (for example the 0008 GIS geometry column).
        legacy_cameras = Table(
            "cameras",
            MetaData(),
            autoload_with=database.engine,
        )
        legacy_camera = _legacy_camera()
        with database.session_factory.begin() as session:
            session.execute(
                legacy_cameras.insert().values(
                    camera_id=legacy_camera.camera_id,
                    version_id=1,
                    source_id=legacy_camera.source_id,
                    external_id=legacy_camera.external_id,
                    display_name=legacy_camera.display_name,
                    department=legacy_camera.department,
                    selected_url=legacy_camera.selected_url,
                    delivery_type=legacy_camera.delivery_type,
                    codec=legacy_camera.codec,
                    container=legacy_camera.container,
                    reachability=legacy_camera.reachability,
                    last_checked_at=legacy_camera.last_checked_at,
                    source_schema=legacy_camera.source_schema,
                    provenance=legacy_camera.provenance,
                    imported_at=legacy_camera.imported_at,
                    created_at=legacy_camera.created_at,
                    updated_at=legacy_camera.updated_at,
                )
            )

        _upgrade(database_url, "head")
        inspector = inspect(database.engine)
        table_names = set(inspector.get_table_names())
        stream_columns = {
            column["name"] for column in inspector.get_columns("stream_endpoints")
        }
        assert {
            "management_locator",
            "onvif_auth_mode",
            "capability_refresh_enabled",
            "capability_due_at",
            "onvif_control_enabled",
            "onvif_max_velocity",
            "onvif_max_move_seconds",
        }.issubset(stream_columns)
        assert {
            OnvifControlLease.__tablename__,
            OnvifOperationRun.__tablename__,
            StreamCapabilitySnapshot.__tablename__,
            StreamCapabilityRefresh.__tablename__,
        }.issubset(table_names)
        expected_stream_id = "str_" + hashlib.sha256(
            b"legacy:cctv-001"
        ).hexdigest()[:32]
        with database.session_factory() as session:
            endpoint = session.get(StreamEndpoint, expected_stream_id)
            health = session.get(StreamHealthCurrent, expected_stream_id)
            assert endpoint is not None
            assert endpoint.protocol == "hls"
            assert endpoint.is_primary is True
            assert endpoint.probe_due_at is not None
            assert endpoint.management_locator is None
            assert endpoint.onvif_auth_mode == "none"
            assert endpoint.capability_refresh_enabled is False
            assert endpoint.onvif_control_enabled is False
            assert endpoint.onvif_max_velocity == 0.5
            assert endpoint.onvif_max_move_seconds == 2.0
            assert health is not None
            assert health.state == "healthy"
            assert health.codec == "h264"

            operation_id = "ovf_" + "c" * 32
            session.add(
                OnvifOperationRun(
                    operation_id=operation_id,
                    stream_id=expected_stream_id,
                    actor_id="migration-test",
                    operation_type="capability_discover_sync",
                    outcome="pending",
                    reason_code=None,
                    parameters={"compatibility_endpoint": True},
                    audit_reason="Validate synchronous discovery lifecycle schema",
                    request_id="migration-request",
                    requested_at=datetime.now(UTC),
                    finished_at=None,
                    duration_ms=None,
                )
            )
            session.commit()
            operation = session.get(OnvifOperationRun, operation_id)
            assert operation is not None
            assert operation.operation_type == "capability_discover_sync"
            assert operation.outcome == "pending"

            session.add(
                StreamEndpoint(
                    stream_id="str_" + "f" * 32,
                    camera_id="legacy:cctv-001",
                    name="duplicate-primary",
                    adapter_kind="hls",
                    protocol="hls",
                    locator="https://media.test.local/other/index.m3u8",
                    is_primary=True,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

        _downgrade(database_url, "0003_camera_integrity")
        table_names = set(inspect(database.engine).get_table_names())
        assert "stream_endpoints" not in table_names
        assert "cameras" in table_names

        _upgrade(database_url, "head")
        with database.session_factory() as session:
            assert session.scalar(select(StreamEndpoint.stream_id)) == expected_stream_id
    finally:
        database.dispose()
