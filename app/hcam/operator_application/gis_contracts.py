from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import Field, field_validator, model_validator

from .bounds import MAX_GIS_FEATURES, MAX_GIS_PARITY_REQUIREMENTS
from .contracts import (
    OperatorContractModel,
    ResourceProfile,
    SafeCode,
    SchemaVersion,
    StableId,
    SurfaceState,
)


Longitude = Annotated[float, Field(ge=-180, le=180)]
Latitude = Annotated[float, Field(ge=-90, le=90)]
Position = tuple[Longitude, Latitude]
LinearRing = Annotated[list[Position], Field(min_length=4, max_length=512)]


class GisPointV1(OperatorContractModel):
    type: Literal["Point"] = "Point"
    coordinates: Position


class GisLineStringV1(OperatorContractModel):
    type: Literal["LineString"] = "LineString"
    coordinates: Annotated[list[Position], Field(min_length=2, max_length=4_096)]


class GisPolygonV1(OperatorContractModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: Annotated[list[LinearRing], Field(min_length=1, max_length=16)]

    @field_validator("coordinates")
    @classmethod
    def rings_are_valid(cls, value: list[list[Position]]) -> list[list[Position]]:
        _validate_rings(value)
        return value


class GisMultiPolygonV1(OperatorContractModel):
    type: Literal["MultiPolygon"] = "MultiPolygon"
    coordinates: Annotated[
        list[Annotated[list[LinearRing], Field(min_length=1, max_length=16)]],
        Field(min_length=1, max_length=64),
    ]

    @field_validator("coordinates")
    @classmethod
    def polygons_are_valid(
        cls, value: list[list[list[Position]]]
    ) -> list[list[list[Position]]]:
        for polygon in value:
            _validate_rings(polygon)
        return value


def _validate_rings(rings: list[list[Position]]) -> None:
    for ring in rings:
        if ring[0] != ring[-1]:
            raise ValueError("GIS polygon rings must be closed")
        if len(set(ring[:-1])) < 3:
            raise ValueError("GIS polygon rings require three unique positions")


GisGeometryV1: TypeAlias = Annotated[
    GisPointV1 | GisLineStringV1 | GisPolygonV1 | GisMultiPolygonV1,
    Field(discriminator="type"),
]


class GisViewportV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.gis-viewport.v1"] = (
        "hcam.operator.gis-viewport.v1"
    )
    west: Longitude
    south: Latitude
    east: Longitude
    north: Latitude
    zoom: Annotated[float, Field(ge=0, le=24)]
    maximum_features: Annotated[int, Field(ge=1, le=MAX_GIS_FEATURES)]
    viewport_query_only: Literal[True] = True

    @model_validator(mode="after")
    def bounds_are_ordered(self) -> GisViewportV1:
        if self.west >= self.east or self.south >= self.north:
            raise ValueError("GIS viewport bounds must be ordered")
        return self


class GisFeatureV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.gis-feature.v1"] = (
        "hcam.operator.gis-feature.v1"
    )
    feature_id: Annotated[str, Field(pattern=r"^syn_gis_[0-9a-f]{20}$")]
    layer: Literal["camera", "incident", "patrol", "zone", "route", "coverage"]
    geometry: GisGeometryV1
    state: SurfaceState
    summary_code: SafeCode
    confidence: Annotated[float, Field(ge=0, le=1)] | None = None
    uncertainty: Annotated[float, Field(ge=0, le=1)] | None = None
    freshness: Literal["fresh", "stale", "unknown"]
    correction_state: Literal["current", "corrected", "retracted"]
    generated_only: Literal[True] = True
    operational: Literal[False] = False

    @model_validator(mode="after")
    def confidence_is_consistent(self) -> GisFeatureV1:
        if (self.confidence is None) != (self.uncertainty is None):
            raise ValueError("confidence and uncertainty must be present together")
        return self


class GisLayerContractV1(OperatorContractModel):
    layer_id: Literal["camera", "incident", "patrol", "zone", "route", "coverage"]
    producer_operation: StableId
    schema_version: SchemaVersion
    maximum_features: Annotated[int, Field(ge=1, le=MAX_GIS_FEATURES)]
    clustering: Literal["required", "allowed", "forbidden"]
    accessible_alternative: Literal["list", "table"]
    authoritative: bool


class GisParityRequirementV1(OperatorContractModel):
    requirement_id: StableId
    category: Literal[
        "composition",
        "filter",
        "layer",
        "selection",
        "focus",
        "responsive",
        "safety",
        "localization",
        "accessibility",
        "degradation",
        "performance",
        "preview_gate",
    ]
    source_control: StableId
    required_behavior: SafeCode
    visual_evidence_required: bool
    interaction_evidence_required: bool
    may_downgrade: Literal[False] = False


class GisParityMatrixV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.gis-parity-matrix.v1"] = (
        "hcam.operator.gis-parity-matrix.v1"
    )
    source_repository: Literal["hcam-1-0/final-ui"]
    source_commit: Literal["cd21af3bef132b211bfe2860d25eaf38a94253df"]
    source_component: Literal["src/components/GisWorkspace.tsx"]
    requirements: Annotated[
        list[GisParityRequirementV1],
        Field(min_length=12, max_length=MAX_GIS_PARITY_REQUIREMENTS),
    ]
    authoritative_2d: Literal[True] = True
    accessible_list_equivalent: Literal[True] = True
    optional_3d_default_enabled: Literal[False] = False
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def requirements_are_complete(self) -> GisParityMatrixV1:
        ids = [item.requirement_id for item in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("GIS parity requirement identifiers must be unique")
        categories = {item.category for item in self.requirements}
        if len(categories) != 12:
            raise ValueError("all GIS parity categories are required")
        return self


class GisParityCaseV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.gis-parity-case.v1"] = (
        "hcam.operator.gis-parity-case.v1"
    )
    case_id: Annotated[str, Field(pattern=r"^syn_gis_case_[0-9a-f]{20}$")]
    requirement_id: StableId
    geometry_type: Literal["Point", "LineString", "Polygon", "MultiPolygon"]
    resource_profile: ResourceProfile
    expected_state: Literal["parity_required"] = "parity_required"
    generated_only: Literal[True] = True
    operational: Literal[False] = False


class GisRendererPolicyV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.gis-renderer-policy.v1"] = (
        "hcam.operator.gis-renderer-policy.v1"
    )
    primary_renderer: Literal["MapLibre_2D"] = "MapLibre_2D"
    authoritative_path: Literal["2D_and_accessible_list"] = "2D_and_accessible_list"
    optional_3d: Literal["guarded_default_off"] = "guarded_default_off"
    renderer_runtime_enabled: Literal[False] = False
    provider_network_enabled: Literal[False] = False


def feature_intersects_viewport(feature: GisFeatureV1, viewport: GisViewportV1) -> bool:
    positions = tuple(_positions(feature.geometry))
    return any(
        viewport.west <= longitude <= viewport.east
        and viewport.south <= latitude <= viewport.north
        for longitude, latitude in positions
    )


def _positions(geometry: GisGeometryV1) -> list[Position]:
    if isinstance(geometry, GisPointV1):
        return [geometry.coordinates]
    if isinstance(geometry, GisLineStringV1):
        return geometry.coordinates
    if isinstance(geometry, GisPolygonV1):
        return [position for ring in geometry.coordinates for position in ring]
    return [
        position
        for polygon in geometry.coordinates
        for ring in polygon
        for position in ring
    ]
