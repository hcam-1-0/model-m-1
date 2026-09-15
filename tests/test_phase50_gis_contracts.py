from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.operator_application import (
    GisFeatureV1,
    GisParityMatrixV1,
    GisRendererPolicyV1,
    GisViewportV1,
    generated_gis_parity_cases,
)
from hcam.operator_application.gis_contracts import (
    GisLineStringV1,
    GisMultiPolygonV1,
    GisPointV1,
    GisPolygonV1,
    feature_intersects_viewport,
)


ROOT = Path(__file__).resolve().parents[1]


def _matrix() -> GisParityMatrixV1:
    return GisParityMatrixV1.model_validate_json(
        (ROOT / "contracts/phase-5/operator-ui-gis-parity.v1.json").read_text(
            encoding="utf-8"
        )
    )


def _feature(geometry: object) -> GisFeatureV1:
    return GisFeatureV1(
        feature_id="syn_gis_0123456789abcdef0123",
        layer="camera",
        geometry=geometry,
        state="ready",
        summary_code="generated_camera",
        confidence=0.75,
        uncertainty=0.25,
        freshness="fresh",
        correction_state="current",
    )


def test_gis_parity_matrix_is_complete_and_no_downgrade() -> None:
    matrix = _matrix()
    assert len(matrix.requirements) == 12
    assert len({item.category for item in matrix.requirements}) == 12
    assert all(not item.may_downgrade for item in matrix.requirements)
    assert len(generated_gis_parity_cases(matrix)) == 96
    assert GisRendererPolicyV1().model_dump() == {
        "contract_type": "hcam.operator.gis-renderer-policy.v1",
        "primary_renderer": "MapLibre_2D",
        "authoritative_path": "2D_and_accessible_list",
        "optional_3d": "guarded_default_off",
        "renderer_runtime_enabled": False,
        "provider_network_enabled": False,
    }


def test_all_supported_geometries_intersect_generated_viewport() -> None:
    viewport = GisViewportV1(
        west=-1,
        south=-1,
        east=1,
        north=1,
        zoom=8,
        maximum_features=100,
    )
    ring = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, -0.5)]
    geometries = (
        GisPointV1(coordinates=(0.0, 0.0)),
        GisLineStringV1(coordinates=[(-2.0, -2.0), (0.0, 0.0)]),
        GisPolygonV1(coordinates=[ring]),
        GisMultiPolygonV1(coordinates=[[[*ring]]]),
    )
    assert all(feature_intersects_viewport(_feature(item), viewport) for item in geometries)
    outside = _feature(GisPointV1(coordinates=(10.0, 10.0)))
    assert feature_intersects_viewport(outside, viewport) is False


def test_gis_geometry_and_viewport_reject_invalid_bounds() -> None:
    with pytest.raises(ValidationError, match="closed"):
        GisPolygonV1(
            coordinates=[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]]
        )
    with pytest.raises(ValidationError, match="three unique"):
        GisPolygonV1(
            coordinates=[[(0.0, 0.0), (1.0, 0.0), (0.0, 0.0), (0.0, 0.0)]]
        )
    with pytest.raises(ValidationError, match="ordered"):
        GisViewportV1(
            west=1,
            south=-1,
            east=-1,
            north=1,
            zoom=8,
            maximum_features=100,
        )


def test_feature_requires_confidence_and_uncertainty_together() -> None:
    feature = _feature(GisPointV1(coordinates=(0.0, 0.0)))
    data = feature.model_dump()
    with pytest.raises(ValidationError, match="present together"):
        GisFeatureV1.model_validate({**data, "uncertainty": None})
    without_scores = {**data, "confidence": None, "uncertainty": None}
    assert GisFeatureV1.model_validate(without_scores).confidence is None


def test_gis_matrix_rejects_duplicate_or_missing_categories() -> None:
    data = _matrix().model_dump()
    duplicate = [*data["requirements"]]
    duplicate[-1] = duplicate[0]
    with pytest.raises(ValidationError):
        GisParityMatrixV1.model_validate({**data, "requirements": duplicate})
