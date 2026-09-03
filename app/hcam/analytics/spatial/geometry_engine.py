from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN

import shapely
from shapely import LineString, Polygon, box, normalize, set_precision, to_wkb
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient
from shapely.validation import explain_validity

from hcam.analytics.geometry import GeometryShapeV1, LineGeometryV1, ZoneGeometryV1


GRID_SIZE = 1e-9
_UNIT_SQUARE = box(0.0, 0.0, 1.0, 1.0)


class GeometryEngineError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CanonicalGeometry:
    kind: str
    geometry: BaseGeometry
    canonical_json: str
    canonical_wkb: bytes
    digest: str
    wkb_sha256: str
    shapely_version: str
    geos_version: str


def _decimal_text(value: float) -> str:
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise GeometryEngineError("geometry coordinate must be finite and normalized")
    quantized = Decimal(str(value)).quantize(
        Decimal("0.000000001"), rounding=ROUND_HALF_EVEN
    )
    rendered = format(quantized.normalize(), "f")
    return "0" if rendered in {"-0", "-0.0"} else rendered


def _rotate_ring(coordinates: list[tuple[float, float]]) -> list[tuple[float, float]]:
    start = min(range(len(coordinates)), key=lambda index: coordinates[index])
    return coordinates[start:] + coordinates[:start]


def _shape_geometry(shape: GeometryShapeV1) -> tuple[BaseGeometry, dict[str, object]]:
    if isinstance(shape, LineGeometryV1):
        coordinates = [(shape.start.x, shape.start.y), (shape.end.x, shape.end.y)]
        geometry = LineString(coordinates)
        document: dict[str, object] = {
            "crossing_direction": shape.crossing_direction,
            "kind": "line",
            "points": [[_decimal_text(x), _decimal_text(y)] for x, y in coordinates],
        }
        return geometry, document

    if not isinstance(shape, ZoneGeometryV1):
        raise GeometryEngineError("unsupported geometry shape")
    polygon = Polygon([(point.x, point.y) for point in shape.vertices])
    if not polygon.is_valid:
        raise GeometryEngineError("invalid polygon: " + explain_validity(polygon))
    polygon = orient(polygon, sign=1.0)
    coordinates = _rotate_ring(list(polygon.exterior.coords)[:-1])
    polygon = Polygon(coordinates)
    document = {
        "boundary_policy": shape.boundary_policy,
        "kind": "zone",
        "vertices": [[_decimal_text(x), _decimal_text(y)] for x, y in coordinates],
    }
    return polygon, document


def canonicalize_geometry(shape: GeometryShapeV1) -> CanonicalGeometry:
    geometry, document = _shape_geometry(shape)
    if geometry.is_empty or not geometry.is_valid:
        raise GeometryEngineError("geometry is empty or invalid")
    reduced = set_precision(geometry, grid_size=GRID_SIZE, mode="valid_output")
    if reduced.is_empty or reduced.geom_type != geometry.geom_type:
        raise GeometryEngineError("precision reduction changed geometry type")
    if not reduced.equals(geometry):
        raise GeometryEngineError("geometry does not conform to the precision grid")
    canonical = normalize(reduced) if isinstance(shape, ZoneGeometryV1) else reduced
    canonical_json = json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    if len(canonical_json.encode("utf-8")) > 16_384:
        raise GeometryEngineError("canonical geometry exceeds 16 KiB")
    wkb = to_wkb(canonical, output_dimension=2, byte_order=1, include_srid=False)
    digest_input = canonical_json.encode("utf-8") + b"\x00" + wkb
    return CanonicalGeometry(
        kind=shape.kind,
        geometry=canonical,
        canonical_json=canonical_json,
        canonical_wkb=wkb,
        digest="sha256:" + hashlib.sha256(digest_input).hexdigest(),
        wkb_sha256=hashlib.sha256(wkb).hexdigest(),
        shapely_version=shapely.__version__,
        geos_version=shapely.geos_version_string,
    )


def zone_regions(
    polygon: BaseGeometry,
    hysteresis: float,
) -> tuple[BaseGeometry, BaseGeometry]:
    if polygon.geom_type != "Polygon":
        raise GeometryEngineError("zone predicates require a polygon")
    inner = polygon.buffer(-hysteresis) if hysteresis else polygon
    outer = polygon.buffer(hysteresis) if hysteresis else polygon
    if inner.is_empty or inner.geom_type != "Polygon":
        raise GeometryEngineError("zone hysteresis collapses the inner region")
    if not _UNIT_SQUARE.covers(outer):
        raise GeometryEngineError("zone hysteresis leaves normalized image space")
    return inner, outer


def signed_line_distance(line: BaseGeometry, point: tuple[float, float]) -> float:
    if line.geom_type != "LineString" or len(line.coords) != 2:
        raise GeometryEngineError("line predicate requires two endpoints")
    (ax, ay), (bx, by) = line.coords
    px, py = point
    length = math.hypot(bx - ax, by - ay)
    if length <= 0:
        raise GeometryEngineError("line predicate cannot use a zero-length line")
    return ((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / length
