from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import false, select, text
from sqlalchemy.orm import Session

from hcam.camera_registry.models import Camera
from hcam.camera_registry.schemas import CameraGeoCollection
from hcam.database import get_session
from hcam.security.auth import (
    CAMERA_EDITOR,
    CAMERA_VIEWER,
    PLATFORM_ADMIN,
    Principal,
    RoleGuard,
)


router = APIRouter(prefix="/cameras/geo", tags=["camera-gis"])
SessionDependency = Annotated[Session, Depends(get_session)]
ViewerPrincipal = Annotated[
    Principal,
    Depends(RoleGuard(CAMERA_VIEWER, CAMERA_EDITOR, PLATFORM_ADMIN)),
]


def _scope_conditions(principal: Principal) -> list[object]:
    departments = principal.allowed_departments
    if departments is None:
        return []
    if not departments:
        return [false()]
    return [Camera.department.in_(departments)]


def _camera_feature(camera: Camera) -> dict[str, object]:
    # This is the browser-facing GIS boundary.  Do not add registry transport,
    # ownership, storage, or provider fields here: GIS selection is not a media
    # authorization decision.  A live handoff stays session-authorized by the
    # playback endpoint, so catalogue records are deliberately registry-only.
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": (float(camera.longitude), float(camera.latitude)),
        },
        "properties": {
            "camera_id": camera.camera_id,
            "display_name": camera.display_name,
            "department": camera.department,
            "camera_type": camera.camera_type,
            "health_status": camera.health_status,
            "approved_live": False,
            "stale": (camera.health_status or "").strip().lower() == "stale",
        },
        "id": camera.camera_id,
    }


def _bounded_cameras(
    session: Session,
    principal: Principal,
    *,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    limit: int,
    offset: int = 0,
) -> list[Camera]:
    if min_lon > max_lon or min_lat > max_lat:
        raise HTTPException(status_code=422, detail="Invalid geographic bounds")
    conditions: list[object] = [
        Camera.latitude.is_not(None),
        Camera.longitude.is_not(None),
        Camera.longitude >= min_lon,
        Camera.longitude <= max_lon,
        Camera.latitude >= min_lat,
        Camera.latitude <= max_lat,
        *_scope_conditions(principal),
    ]
    statement = (
        select(Camera)
        .where(*conditions)
        .order_by(Camera.camera_id)
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement).all())


@router.get("/bbox", response_model=CameraGeoCollection)
def cameras_in_bbox(
    session: SessionDependency,
    principal: ViewerPrincipal,
    min_lon: Annotated[float, Query(ge=-180, le=180)],
    min_lat: Annotated[float, Query(ge=-90, le=90)],
    max_lon: Annotated[float, Query(ge=-180, le=180)],
    max_lat: Annotated[float, Query(ge=-90, le=90)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    cameras = _bounded_cameras(
        session,
        principal,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        limit=limit,
        offset=offset,
    )
    return {"type": "FeatureCollection", "features": list(map(_camera_feature, cameras))}


def _distance_meters(
    lat_a: float,
    lon_a: float,
    lat_b: float,
    lon_b: float,
) -> float:
    radius = 6_371_008.8
    phi_a = math.radians(lat_a)
    phi_b = math.radians(lat_b)
    delta_phi = math.radians(lat_b - lat_a)
    delta_lambda = math.radians(lon_b - lon_a)
    haversine = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi_a) * math.cos(phi_b) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))


@router.get("/radius", response_model=CameraGeoCollection)
def cameras_in_radius(
    session: SessionDependency,
    principal: ViewerPrincipal,
    lon: Annotated[float, Query(ge=-180, le=180)],
    lat: Annotated[float, Query(ge=-90, le=90)],
    radius_m: Annotated[float, Query(gt=0, le=100_000)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
) -> dict[str, object]:
    latitude_delta = radius_m / 111_320
    longitude_scale = max(math.cos(math.radians(lat)), 0.01)
    longitude_delta = radius_m / (111_320 * longitude_scale)
    candidates = _bounded_cameras(
        session,
        principal,
        min_lon=max(-180, lon - longitude_delta),
        min_lat=max(-90, lat - latitude_delta),
        max_lon=min(180, lon + longitude_delta),
        max_lat=min(90, lat + latitude_delta),
        limit=5000,
    )
    ranked = sorted(
        (
            (_distance_meters(lat, lon, float(camera.latitude), float(camera.longitude)), camera)
            for camera in candidates
        ),
        key=lambda item: (item[0], item[1].camera_id),
    )
    cameras = [camera for distance, camera in ranked if distance <= radius_m][:limit]
    return {"type": "FeatureCollection", "features": list(map(_camera_feature, cameras))}


@router.get("/cluster", response_model=CameraGeoCollection)
def cameras_clustered(
    session: SessionDependency,
    principal: ViewerPrincipal,
    min_lon: Annotated[float, Query(ge=-180, le=180)],
    min_lat: Annotated[float, Query(ge=-90, le=90)],
    max_lon: Annotated[float, Query(ge=-180, le=180)],
    max_lat: Annotated[float, Query(ge=-90, le=90)],
    zoom: Annotated[int, Query(ge=0, le=20)],
    grid_size: Annotated[int, Query(ge=16, le=256)] = 64,
) -> dict[str, object]:
    cameras = _bounded_cameras(
        session,
        principal,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        limit=5000,
    )
    grid_degrees = 360 / (256 * (2**zoom)) * grid_size
    clusters: dict[tuple[int, int], list[Camera]] = {}
    for camera in cameras:
        key = (
            math.floor((float(camera.longitude) + 180) / grid_degrees),
            math.floor((float(camera.latitude) + 90) / grid_degrees),
        )
        clusters.setdefault(key, []).append(camera)

    features: list[dict[str, object]] = []
    for members in clusters.values():
        longitude = sum(float(camera.longitude) for camera in members) / len(members)
        latitude = sum(float(camera.latitude) for camera in members) / len(members)
        feature = _camera_feature(members[0])
        feature["geometry"] = {"type": "Point", "coordinates": (longitude, latitude)}
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}


@router.get("/tile/{z}/{x}/{y}.pbf")
def camera_vector_tile(
    z: int,
    x: int,
    y: int,
    request: Request,
    session: SessionDependency,
    principal: ViewerPrincipal,
) -> Response:
    if not 0 <= z <= 20 or x < 0 or y < 0 or x >= 2**z or y >= 2**z:
        raise HTTPException(status_code=422, detail="Invalid vector tile coordinate")
    if session.get_bind().dialect.name != "postgresql":
        raise HTTPException(status_code=503, detail="Vector tiles require PostgreSQL with PostGIS")

    settings = request.app.state.settings
    extent = settings.gis_tile_extent
    buffer = settings.gis_tile_buffer
    limit = settings.gis_max_features_per_tile
    scope_sql = ""
    parameters: dict[str, object] = {
        "z": z,
        "x": x,
        "y": y,
        "extent": extent,
        "buffer": buffer,
        "limit": limit,
    }
    departments = principal.allowed_departments
    if departments is not None:
        if not departments:
            return Response(content=b"", media_type="application/vnd.mapbox-vector-tile")
        scope_sql = "AND c.department = ANY(:departments)"
        parameters["departments"] = list(departments)

    statement = text(
        f"""
        WITH bounds AS (
            SELECT ST_TileEnvelope(:z, :x, :y) AS geom
        ), tile_rows AS (
            SELECT c.camera_id, c.display_name, c.department, c.camera_type,
                   c.health_status, false AS approved_live,
                   CASE WHEN c.health_status = 'stale' THEN true ELSE false END AS stale,
                   ST_AsMVTGeom(ST_Transform(c.geometry, 3857), bounds.geom,
                                :extent, :buffer, true) AS geom
            FROM cameras AS c, bounds
            WHERE c.geometry IS NOT NULL
              AND ST_Intersects(ST_Transform(c.geometry, 3857), bounds.geom)
              {scope_sql}
            ORDER BY c.camera_id
            LIMIT :limit
        )
        SELECT ST_AsMVT(tile_rows.*, 'cameras', :extent, 'geom') FROM tile_rows
        """
    )
    payload = session.execute(statement, parameters).scalar_one_or_none() or b""
    return Response(content=bytes(payload), media_type="application/vnd.mapbox-vector-tile")
