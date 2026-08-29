from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.dialects import postgresql, sqlite

from hcam.camera_registry import gis_routes
from hcam.camera_registry.models import Camera, PortablePointGeometry


class _Scalars:
    def __init__(self, values: list[Any]) -> None:
        self._values = values

    def all(self) -> list[Any]:
        return self._values


class _Result:
    def __init__(
        self,
        *,
        scalar_values: list[Any] | None = None,
        rows: list[Any] | None = None,
    ) -> None:
        self._scalar_values = scalar_values or []
        self._rows = rows or []

    def scalars(self) -> _Scalars:
        return _Scalars(self._scalar_values)

    def all(self) -> list[Any]:
        return self._rows


class _Session:
    def __init__(self, result: _Result | Exception) -> None:
        self._result = result

    def execute(self, _statement: Any) -> _Result:
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _camera(*, latitude: float | None = 23.0225, longitude: float | None = 72.5714) -> Camera:
    return Camera(
        camera_id="synthetic:gis-001",
        source_id="synthetic",
        external_id="gis-001",
        display_name="Synthetic GIS Camera",
        latitude=latitude,
        longitude=longitude,
        department="Traffic",
        camera_type="fixed",
        health_status="healthy",
        operational_status="active",
        source_schema="hcam.camera_registry.seed.v1",
        provenance={"kind": "synthetic-test"},
    )


def test_bbox_and_radius_return_geojson_features() -> None:
    session = _Session(_Result(scalar_values=[_camera()]))

    bbox = gis_routes.cameras_in_bbox(
        min_lon=72.0,
        min_lat=22.0,
        max_lon=73.0,
        max_lat=24.0,
        limit=100,
        offset=0,
        session=session,  # type: ignore[arg-type]
    )
    radius = gis_routes.cameras_in_radius(
        lon=72.5714,
        lat=23.0225,
        radius_m=1_000,
        limit=100,
        offset=0,
        session=session,  # type: ignore[arg-type]
    )

    for collection in (bbox, radius):
        assert collection.type == "FeatureCollection"
        assert collection.features[0].id == "synthetic:gis-001"
        assert collection.features[0].geometry is not None
        assert collection.features[0].geometry.coordinates == [72.5714, 23.0225]


def test_cluster_converts_postgis_point_and_skips_empty_cells() -> None:
    cluster = SimpleNamespace(
        grid_point=from_shape(Point(72.5714, 23.0225), srid=4326),
        count=2,
        camera_ids=["synthetic:gis-001", "synthetic:gis-002"],
        names=["One", "Two"],
        departments=["Traffic", "Traffic"],
        types=["fixed", "fixed"],
        health_statuses=["healthy", "healthy"],
    )
    empty_cell = SimpleNamespace(grid_point=None)
    session = _Session(_Result(rows=[cluster, empty_cell]))

    collection = gis_routes.cameras_clustered(
        min_lon=72.0,
        min_lat=22.0,
        max_lon=73.0,
        max_lat=24.0,
        zoom=10,
        grid_size=64,
        session=session,  # type: ignore[arg-type]
    )

    assert len(collection.features) == 1
    assert collection.features[0].properties.count == 2  # type: ignore[attr-defined]


def test_vector_tile_handles_features_empty_results_and_errors(monkeypatch) -> None:
    feature_response = gis_routes.camera_vector_tile(
        10,
        718,
        420,
        session=_Session(_Result(scalar_values=[_camera()])),  # type: ignore[arg-type]
    )
    empty_response = gis_routes.camera_vector_tile(
        10,
        718,
        420,
        session=_Session(_Result()),  # type: ignore[arg-type]
    )
    fallback_response = gis_routes.camera_vector_tile(
        10,
        718,
        420,
        session=_Session(RuntimeError("synthetic database failure")),  # type: ignore[arg-type]
    )
    invalid_response = gis_routes.camera_vector_tile(
        21,
        0,
        0,
        session=_Session(_Result()),  # type: ignore[arg-type]
    )

    assert feature_response.status_code == 200
    assert feature_response.body
    assert empty_response.status_code == 200
    assert empty_response.body
    assert fallback_response.status_code == 200
    assert fallback_response.body
    assert invalid_response.status_code == 400

    geometry_camera = _camera(latitude=None, longitude=None)
    geometry_camera.geometry = from_shape(Point(72.5714, 23.0225), srid=4326)
    geometry_response = gis_routes.camera_vector_tile(
        10,
        718,
        420,
        session=_Session(_Result(scalar_values=[geometry_camera])),  # type: ignore[arg-type]
    )
    assert geometry_response.body

    invalid_geometry_camera = _camera(latitude=None, longitude=None)
    invalid_geometry_camera.geometry = "not-a-wkb-value"
    skipped_geometry_response = gis_routes.camera_vector_tile(
        10,
        718,
        420,
        session=_Session(_Result(scalar_values=[invalid_geometry_camera])),  # type: ignore[arg-type]
    )
    assert skipped_geometry_response.body

    monkeypatch.setattr(gis_routes, "encode", lambda *_args, **_kwargs: 1 / 0)
    double_failure = gis_routes.camera_vector_tile(
        10,
        718,
        420,
        session=_Session(RuntimeError("synthetic database failure")),  # type: ignore[arg-type]
    )
    assert double_failure.body == b""
    assert double_failure.media_type == "application/x-protobuf"


def test_geojson_uses_geometry_and_allows_missing_location() -> None:
    geometry_camera = _camera(latitude=None, longitude=None)
    geometry_camera.geometry = from_shape(Point(72.5, 23.0), srid=4326)
    feature = gis_routes._camera_to_geojson(geometry_camera)

    no_location = _camera(latitude=None, longitude=None)
    no_location_feature = gis_routes._camera_to_geojson(no_location)

    assert feature["geometry"] == {
        "type": "Point",
        "coordinates": (72.5, 23.0),
    }
    assert no_location_feature["geometry"] is None


def test_portable_geometry_and_coordinate_helpers() -> None:
    portable = PortablePointGeometry()
    assert portable.load_dialect_impl(sqlite.dialect()).python_type is str
    assert portable.load_dialect_impl(postgresql.dialect()).geometry_type == "POINT"

    coordinate_camera = _camera()
    assert coordinate_camera.lat == 23.0225
    assert coordinate_camera.lon == 72.5714
    coordinate_camera.sync_geometry_from_coords()
    assert coordinate_camera.geometry is not None

    geometry_camera = _camera(latitude=None, longitude=None)
    geometry_camera.geometry = from_shape(Point(72.5, 23.0), srid=4326)
    assert geometry_camera.lat is None
    assert geometry_camera.lon is None
    geometry_camera.sync_coords_from_geometry()
    assert geometry_camera.latitude == 23.0
    assert geometry_camera.longitude == 72.5

    empty_camera = _camera(latitude=None, longitude=None)
    empty_camera.sync_geometry_from_coords()
    empty_camera.sync_coords_from_geometry()
    assert empty_camera.geometry is None
