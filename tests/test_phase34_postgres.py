from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from hcam.analytics.models import AnalyticsGeometry
from hcam.camera_registry.models import Camera
from hcam.database import Database
from hcam.main import create_app
from hcam.settings import Settings
from hcam.streams.models import StreamEndpoint


POSTGRES_TEST_URL = os.getenv("HCAM_POSTGRES_TEST_URL")
ROOT = Path(__file__).resolve().parents[1]
pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        not POSTGRES_TEST_URL,
        reason="HCAM_POSTGRES_TEST_URL is required for PostgreSQL integration",
    ),
]


def test_postgis_geometry_storage_is_valid_indexed_and_wkb_bound() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    camera_id = "synthetic:postgres-p34"
    stream_id = "str_0000000000000000000000000000b341"
    now = datetime.now(UTC)
    try:
        database.check_ready()
        with database.engine.connect() as connection:
            version = connection.scalar(text("SELECT postgis_lib_version()"))
            index_method = connection.scalar(
                text(
                    "SELECT am.amname FROM pg_class i "
                    "JOIN pg_am am ON am.oid = i.relam "
                    "WHERE i.relname = 'ix_analytics_geometry_spatial_gist'"
                )
            )
        assert str(version).startswith("3.6")
        assert index_method == "gist"

        with database.session_factory.begin() as session:
            existing = session.get(Camera, camera_id)
            if existing is not None:
                session.delete(existing)
                session.flush()
            session.add(
                Camera(
                    camera_id=camera_id,
                    source_id="postgres-p34-test",
                    external_id="camera-p34-01",
                    display_name="PostGIS P3.4 Test",
                    department="Engineering Lab",
                    source_schema="hcam.synthetic.test.v1",
                    provenance={"synthetic": True, "media_access": False},
                    imported_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
            session.add(
                StreamEndpoint(
                    stream_id=stream_id,
                    camera_id=camera_id,
                    name="p34-postgis",
                    adapter_kind="synthetic",
                    protocol="rtsp",
                    locator="rtsp://mediamtx:8554/hcam/postgres-p34",
                    transport="tcp",
                    is_primary=True,
                    enabled=True,
                    created_at=now,
                    updated_at=now,
                )
            )

        app = create_app(
            Settings(
                database_url=POSTGRES_TEST_URL,
                dev_auth_enabled=True,
                environment="test",
                access_log_enabled=False,
            )
        )
        with TestClient(app) as client:
            response = client.post(
                f"/streams/{stream_id}/analytics-geometries",
                json={
                    "geometry_id": "postgres-zone",
                    "version": 1,
                    "shape": {
                        "kind": "zone",
                        "vertices": [
                            {"x": 0.2, "y": 0.2},
                            {"x": 0.8, "y": 0.2},
                            {"x": 0.8, "y": 0.8},
                            {"x": 0.2, "y": 0.8},
                        ],
                    },
                    "intended_use": "Generated-only PostGIS validation",
                    "policy_version": "sha256:" + "a" * 64,
                },
                headers={
                    "X-HCAM-Actor": "postgres-p34-editor",
                    "X-HCAM-Roles": "camera.editor",
                    "X-HCAM-Departments": "Engineering Lab",
                    "X-HCAM-Reason": "Validate generated PostGIS geometry storage",
                },
            )
        assert response.status_code == 201, response.text
        record_id = response.json()["geometry_record_id"]
        with database.session_factory() as session:
            row = session.get(AnalyticsGeometry, record_id)
            valid, same_wkb, geometry_type, srid = session.execute(
                text(
                    "SELECT ST_IsValid(spatial_geometry), "
                    "ST_AsBinary(spatial_geometry) = canonical_wkb, "
                    "GeometryType(spatial_geometry), ST_SRID(spatial_geometry) "
                    "FROM analytics_geometries WHERE geometry_record_id = :record_id"
                ),
                {"record_id": record_id},
            ).one()
        assert row is not None and row.spatial_geometry == row.canonical_wkb
        assert (valid, same_wkb, geometry_type, srid) == (True, True, "POLYGON", 0)
    finally:
        with database.session_factory.begin() as session:
            camera = session.get(Camera, camera_id)
            if camera is not None:
                session.delete(camera)
        database.dispose()


def test_alembic_check_ignores_extensions_but_detects_unmanaged_tables() -> None:
    assert POSTGRES_TEST_URL is not None
    database = Database(POSTGRES_TEST_URL)
    environment = os.environ.copy()
    environment["HCAM_DATABASE_URL"] = POSTGRES_TEST_URL
    command = [sys.executable, "-m", "alembic", "check"]

    try:
        with database.engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS hcam_unmanaged_drift_probe"))
            connection.execute(
                text("CREATE TABLE hcam_unmanaged_drift_probe (id INTEGER PRIMARY KEY)")
            )

        drift = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        drift_output = drift.stdout + drift.stderr
        assert drift.returncode != 0
        assert "hcam_unmanaged_drift_probe" in drift_output
    finally:
        with database.engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS hcam_unmanaged_drift_probe"))
        database.dispose()

    clean = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert clean.returncode == 0, clean.stdout + clean.stderr
