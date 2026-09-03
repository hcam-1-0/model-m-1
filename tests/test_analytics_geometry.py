from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.analytics.contracts import canonical_contract_json
from hcam.analytics.geometry import (
    GeometryDefinitionV1,
    GeometryScheduleV1,
    LineGeometryV1,
    WeeklyWindowV1,
    ZoneGeometryV1,
)
from hcam.analytics.spatial.sql_types import PostGISImageGeometry


FIXTURE_ROOT = Path(__file__).parents[1] / "contracts" / "phase-3" / "fixtures"


def _document(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "name,kind",
    [
        ("geometry-line-draft-v1.json", "line"),
        ("geometry-zone-draft-v1.json", "zone"),
    ],
)
def test_draft_geometry_fixtures_are_deterministic(name: str, kind: str) -> None:
    geometry = GeometryDefinitionV1.model_validate(_document(name))

    assert geometry.status == "draft"
    assert geometry.shape.kind == kind
    assert canonical_contract_json(geometry) == (FIXTURE_ROOT / name).read_text(
        encoding="utf-8"
    )


def test_line_endpoints_must_be_distinct() -> None:
    with pytest.raises(ValidationError, match="endpoints must be distinct"):
        LineGeometryV1.model_validate(
            {
                "start": {"x": 0.5, "y": 0.5},
                "end": {"x": 0.5, "y": 0.5},
            }
        )


@pytest.mark.parametrize(
    "vertices,message",
    [
        (
            [
                {"x": 0.1, "y": 0.1},
                {"x": 0.9, "y": 0.1},
                {"x": 0.1, "y": 0.1},
            ],
            "vertices must be unique",
        ),
        (
            [
                {"x": 0.1, "y": 0.1},
                {"x": 0.5, "y": 0.5},
                {"x": 0.9, "y": 0.9},
            ],
            "non-zero area",
        ),
        (
            [
                {"x": 0.1, "y": 0.1},
                {"x": 0.9, "y": 0.1},
                {"x": 0.3, "y": 0.8},
                {"x": 0.5, "y": 0.0},
                {"x": 0.7, "y": 0.8},
            ],
            "must not self-intersect",
        ),
    ],
)
def test_zone_rejects_invalid_polygons(
    vertices: list[dict[str, float]],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        ZoneGeometryV1.model_validate({"vertices": vertices})


def test_schedule_requires_bounded_non_overlapping_day_window_shape() -> None:
    with pytest.raises(ValidationError, match="requires at least one window"):
        GeometryScheduleV1(mode="weekly", timezone="UTC", windows=[])
    with pytest.raises(ValidationError, match="days must be unique"):
        WeeklyWindowV1(days=["monday", "monday"], start_minute=10, end_minute=20)
    with pytest.raises(ValidationError, match="split at midnight"):
        WeeklyWindowV1(days=["monday"], start_minute=1_200, end_minute=60)
    with pytest.raises(ValidationError, match="must not overlap"):
        GeometryScheduleV1(
            mode="weekly",
            timezone="Asia/India/Kolkata",
            windows=[
                WeeklyWindowV1(days=["monday"], start_minute=60, end_minute=120),
                WeeklyWindowV1(days=["monday"], start_minute=90, end_minute=180),
            ],
        )


def test_approved_geometry_requires_owner_approval_record() -> None:
    document = _document("geometry-line-draft-v1.json")
    document["status"] = "approved"

    with pytest.raises(ValidationError, match="requires approval record"):
        GeometryDefinitionV1.model_validate(document)

    document["approval_record_id"] = "DR-GEOMETRY-001"
    approved = GeometryDefinitionV1.model_validate(document)
    assert approved.status == "approved"
    assert approved.independent_reviewer_id is None

    document["independent_reviewer_id"] = "phase3-owner"
    owner_reviewed = GeometryDefinitionV1.model_validate(document)
    assert owner_reviewed.independent_reviewer_id == owner_reviewed.owner_id


def test_postgis_geometry_type_supports_reflected_type_arguments() -> None:
    reflected = PostGISImageGeometry("Geometry", "0")

    assert reflected.geometry_type == "Geometry"
    assert reflected.srid == 0
    assert reflected.get_col_spec() == "geometry(Geometry,0)"
