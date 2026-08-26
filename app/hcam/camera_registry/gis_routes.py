from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from geoalchemy2.shape import to_shape
from mapbox_vector_tile import encode
from shapely.geometry import mapping
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from hcam.camera_registry.models import Camera
from hcam.camera_registry.schemas import CameraGeoOut, CameraGeoCollection
from hcam.database import get_session

router = APIRouter(prefix="/geo", tags=["camera-gis"])


@router.get(
    "/bbox",
    response_model=CameraGeoCollection,
    summary="Query cameras within a bounding box",
)
def cameras_in_bbox(
    min_lon: float = Query(..., ge=-180, le=180, description="Minimum longitude"),
    min_lat: float = Query(..., ge=-90, le=90, description="Minimum latitude"),
    max_lon: float = Query(..., ge=-180, le=180, description="Maximum longitude"),
    max_lat: float = Query(..., ge=-90, le=90, description="Maximum latitude"),
    limit: int = Query(1000, ge=1, le=5000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: Session = Depends(get_session),
) -> CameraGeoCollection:
    """Return cameras within a rectangular bounds as GeoJSON FeatureCollection."""
    bbox = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)

    stmt = (
        select(Camera)
        .where(Camera.geometry is not None)
        .where(func.ST_Intersects(Camera.geometry, bbox))
        .limit(limit)
        .offset(offset)
    )

    result = session.execute(stmt)
    cameras = result.scalars().all()

    features = [_camera_to_geojson(cam) for cam in cameras]

    return CameraGeoCollection(type="FeatureCollection", features=features)


@router.get(
    "/radius",
    response_model=CameraGeoCollection,
    summary="Query cameras within a radius of a point",
)
def cameras_in_radius(
    lon: float = Query(..., ge=-180, le=180, description="Center longitude"),
    lat: float = Query(..., ge=-90, le=90, description="Center latitude"),
    radius_m: float = Query(..., gt=0, le=100000, description="Radius in meters"),
    limit: int = Query(1000, ge=1, le=5000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: Session = Depends(get_session),
) -> CameraGeoCollection:
    """Return cameras within radius_m meters of (lon, lat)."""
    center = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    # Use geography for accurate meter-based distance
    center_geog = func.Geography(center)

    stmt = (
        select(Camera)
        .where(Camera.geometry is not None)
        .where(
            func.ST_DWithin(
                func.Geography(Camera.geometry),
                center_geog,
                radius_m,
            )
        )
        .limit(limit)
        .offset(offset)
    )

    result = session.execute(stmt)
    cameras = result.scalars().all()

    features = [_camera_to_geojson(cam) for cam in cameras]

    return CameraGeoCollection(type="FeatureCollection", features=features)


@router.get(
    "/cluster",
    response_model=CameraGeoCollection,
    summary="Get clustered camera points for map visualization",
)
def cameras_clustered(
    min_lon: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lon: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    zoom: int = Query(..., ge=0, le=20, description="Map zoom level"),
    grid_size: int = Query(64, ge=16, le=256, description="Grid cell size in pixels"),
    session: Session = Depends(get_session),
) -> CameraGeoCollection:
    """Return clustered camera points using ST_SnapToGrid for efficient map rendering."""
    bbox = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)

    # Calculate grid size in degrees based on zoom and viewport
    # At zoom 0, world width ~360 deg, tile size 256px
    # grid_size_deg = (max_lon - min_lon) * (grid_size / viewport_width_px)
    # Simplified: use fixed degree grid based on zoom
    deg_per_px = 360 / (256 * (2 ** zoom))
    grid_deg = deg_per_px * grid_size

    # Snap points to grid and count per cell
    grid_expr = func.ST_SnapToGrid(Camera.geometry, grid_deg, grid_deg)

    stmt = (
        select(
            grid_expr.label("grid_point"),
            func.count(Camera.camera_id).label("count"),
            func.array_agg(Camera.camera_id).label("camera_ids"),
            func.array_agg(Camera.display_name).label("names"),
            func.array_agg(Camera.department).label("departments"),
            func.array_agg(Camera.camera_type).label("types"),
            func.array_agg(Camera.health_status).label("health_statuses"),
        )
        .where(Camera.geometry is not None)
        .where(func.ST_Intersects(Camera.geometry, bbox))
        .group_by(grid_expr)
    )

    result = session.execute(stmt)
    clusters = result.all()

    features = []
    for cluster in clusters:
        grid_point = cluster.grid_point
        if grid_point is not None:
            point_shape = to_shape(grid_point)
            properties = {
                "cluster": True,
                "count": cluster.count,
                "camera_ids": cluster.camera_ids,
                "names": cluster.names,
                "departments": cluster.departments,
                "types": cluster.types,
                "health_statuses": cluster.health_statuses,
            }
            features.append({
                "type": "Feature",
                "geometry": mapping(point_shape),
                "properties": properties,
            })

    return CameraGeoCollection(type="FeatureCollection", features=features)


@router.get(
    "/tile/{z}/{x}/{y}.pbf",
    summary="Vector tile (MVT) for camera points",
)
def camera_vector_tile(
    z: int,
    x: int,
    y: int,
    session: Session = Depends(get_session),
) -> Response:
    """Return Mapbox Vector Tile (MVT) for camera points at tile z/x/y."""
    if z < 0 or z > 20:
        return Response(content=b"", status_code=400, media_type="application/x-protobuf")

    import math

    def tile_to_bbox(z: int, x: int, y: int) -> tuple[float, float, float, float]:
        n = 2 ** z
        min_lon = x / n * 360.0 - 180.0
        max_lon = (x + 1) / n * 360.0 - 180.0
        min_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        max_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
        return (min_lon, min_lat, max_lon, max_lat)

    try:
        min_lon, min_lat, max_lon, max_lat = tile_to_bbox(z, x, y)
        bbox = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)

        # Fetch raw points in bbox — Python-side tile encoding (avoids ST_AsMVTGeom frag issues)
        stmt = (
            select(Camera)
            .where(Camera.geometry is not None)
            .where(func.ST_Intersects(Camera.geometry, bbox))
        )
        result = session.execute(stmt)
        cameras = result.scalars().all()

        # Convert lon/lat to tile pixel coords (0-4096)
        lon_range = max_lon - min_lon or 1
        lat_range = max_lat - min_lat or 1
        features = []
        for cam in cameras:
            lon = cam.longitude
            lat = cam.latitude
            if lon is None or lat is None:
                if cam.geometry is not None:
                    try:
                        pt = to_shape(cam.geometry)
                        lon, lat = pt.x, pt.y
                    except Exception:
                        continue
                else:
                    continue
            # Flip Y (tile origin top-left)
            x_px = int((lon - min_lon) / lon_range * 4096)
            y_px = int((max_lat - lat) / lat_range * 4096)
            x_px = max(0, min(4096, x_px))
            y_px = max(0, min(4096, y_px))
            features.append({
                "geometry": {"type": "Point", "coordinates": [x_px, y_px]},
                "properties": {
                    "camera_id": cam.camera_id,
                    "display_name": cam.display_name,
                    "department": cam.department or "",
                    "camera_type": cam.camera_type or "",
                    "health_status": cam.health_status or "",
                    "operational_status": cam.operational_status or "",
                },
                "id": cam.camera_id,
            })

        # Empty tile must still be valid MVT
        if not features:
            mvt_data = encode({"cameras": {"name": "cameras", "features": []}})
        else:
            mvt_data = encode({"cameras": {"name": "cameras", "features": features}})

        return Response(
            content=mvt_data,
            media_type="application/vnd.mapbox-vector-tile",
        )
    except Exception:
        # Never 500 — return empty tile on error (map lib handles it)
        try:
            mvt_data = encode({"cameras": {"name": "cameras", "features": []}})
            return Response(content=mvt_data, media_type="application/vnd.mapbox-vector-tile")
        except Exception:
            return Response(content=b"", media_type="application/x-protobuf")


def _camera_to_geojson(camera: Camera) -> dict[str, Any]:
    """Convert Camera model to GeoJSON Feature."""
    geometry = None
    if camera.geometry is not None:
        geom_shape = to_shape(camera.geometry)
        geometry = mapping(geom_shape)
    elif camera.latitude is not None and camera.longitude is not None:
        geometry = {
            "type": "Point",
            "coordinates": [camera.longitude, camera.latitude],
        }

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "camera_id": camera.camera_id,
            "display_name": camera.display_name,
            "location_label": camera.location_label,
            "department": camera.department,
            "ownership": camera.ownership,
            "camera_type": camera.camera_type,
            "connectivity_status": camera.connectivity_status,
            "storage_status": camera.storage_status,
            "health_status": camera.health_status,
            "maintenance_status": camera.maintenance_status,
            "operational_status": camera.operational_status,
            "timezone_name": camera.timezone_name,
        },
        "id": camera.camera_id,
    }