from __future__ import annotations

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from hcam.camera_registry.models import Camera
from hcam.database import CURRENT_SCHEMA_REVISION


def test_camera_gis_bbox_radius_and_cluster_are_scoped(
    imported_app: FastAPI,
    viewer_headers: dict[str, str],
) -> None:
    traffic_headers = {**viewer_headers, "X-HCAM-Departments": "traffic"}
    blocked_headers = {**viewer_headers, "X-HCAM-Departments": "other"}
    with TestClient(imported_app) as client:
        bbox = client.get(
            "/cameras/geo/bbox",
            params={
                "min_lon": 72.0,
                "min_lat": 22.0,
                "max_lon": 73.0,
                "max_lat": 24.0,
            },
            headers=traffic_headers,
        )
        radius = client.get(
            "/cameras/geo/radius",
            params={"lon": 72.5714, "lat": 23.0225, "radius_m": 1000},
            headers=traffic_headers,
        )
        cluster = client.get(
            "/cameras/geo/cluster",
            params={
                "min_lon": 72.0,
                "min_lat": 22.0,
                "max_lon": 73.0,
                "max_lat": 24.0,
                "zoom": 12,
            },
            headers=traffic_headers,
        )
        blocked = client.get(
            "/cameras/geo/bbox",
            params={
                "min_lon": 72.0,
                "min_lat": 22.0,
                "max_lon": 73.0,
                "max_lat": 24.0,
            },
            headers=blocked_headers,
        )

    for response in (bbox, radius, cluster):
        assert response.status_code == 200
        assert response.json()["features"][0]["id"] == "synthetic:cctv-001"
    assert blocked.status_code == 200
    assert blocked.json()["features"] == []


def test_camera_gis_features_are_display_safe_and_registry_only(
    imported_app: FastAPI,
    viewer_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        response = client.get(
            "/cameras/geo/bbox",
            params={
                "min_lon": 72.0,
                "min_lat": 22.0,
                "max_lon": 73.0,
                "max_lat": 24.0,
            },
            headers=viewer_headers,
        )

    assert response.status_code == 200
    properties = response.json()["features"][0]["properties"]
    assert set(properties) == {
        "camera_id",
        "display_name",
        "department",
        "camera_type",
        "health_status",
        "approved_live",
        "stale",
    }
    assert properties["approved_live"] is False
    for forbidden in (
        "ownership",
        "storage_status",
        "stream_path",
        "hls_path",
        "selected_url",
        "timezone_name",
    ):
        assert forbidden not in properties


def test_camera_gis_rejects_invalid_bounds_and_requires_postgis_for_tiles(
    imported_app: FastAPI,
    viewer_headers: dict[str, str],
) -> None:
    with TestClient(imported_app) as client:
        invalid = client.get(
            "/cameras/geo/bbox",
            params={
                "min_lon": 73,
                "min_lat": 24,
                "max_lon": 72,
                "max_lat": 22,
            },
            headers=viewer_headers,
        )
        tile = client.get(
            "/cameras/geo/tile/10/726/437.pbf",
            headers=viewer_headers,
        )

    assert invalid.status_code == 422
    assert tile.status_code == 503


def test_camera_gis_schema_has_one_merged_head(app: FastAPI) -> None:
    config = Config("alembic.ini")
    heads = ScriptDirectory.from_config(config).get_heads()
    assert heads == [CURRENT_SCHEMA_REVISION]
    assert CURRENT_SCHEMA_REVISION == "0012_merge_camera_gis"
    columns = {
        column["name"]
        for column in inspect(app.state.database.engine).get_columns("cameras")
    }
    assert "geometry" in columns
    assert "ix_cameras_geometry" in {index.name for index in Camera.__table__.indexes}
