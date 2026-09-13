from __future__ import annotations

import hashlib
from collections.abc import Iterable

from .contracts import (
    GeneratedContractCaseV1,
    LocaleName,
    ResourceProfile,
    SurfaceState,
)
from .gis_contracts import GisParityCaseV1, GisParityMatrixV1


GENERATED_VIEW_IDS = (
    "command.overview",
    "operations.camera_catalogue",
    "operations.live_workspace",
    "operations.gis_workspace",
    "intelligence.hypotheses",
    "intelligence.alert_review",
    "investigations.timeline",
    "evidence.references",
    "admin.platform",
    "security.audit",
)
GENERATED_STATES: tuple[SurfaceState, ...] = (
    "loading",
    "empty",
    "ready",
    "partial",
    "stale",
    "degraded",
    "denied",
    "correction",
)
GENERATED_PROFILES: tuple[ResourceProfile, ...] = (
    "low_resource",
    "enhanced",
    "control_room",
)
GENERATED_LOCALES: tuple[LocaleName, ...] = ("en-IN", "gu-IN", "hi-IN")
GIS_GEOMETRY_TYPES = ("Point", "LineString", "Polygon", "MultiPolygon")
GIS_CASE_PROFILES: tuple[ResourceProfile, ...] = ("low_resource", "control_room")


def _digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]


def generated_contract_cases() -> tuple[GeneratedContractCaseV1, ...]:
    cases: list[GeneratedContractCaseV1] = []
    for view_index, view_id in enumerate(GENERATED_VIEW_IDS):
        for state in GENERATED_STATES:
            for profile in GENERATED_PROFILES:
                for locale in GENERATED_LOCALES:
                    discriminator = f"{view_index}:{state}:{profile}:{locale}"
                    expected = "denied" if state == "denied" else "accepted"
                    cases.append(
                        GeneratedContractCaseV1(
                            case_id=f"syn_case_{_digest(view_id, discriminator)}",
                            view_id=view_id,
                            state=state,
                            resource_profile=profile,
                            locale=locale,
                            expected_outcome=expected,
                            reason_code=(
                                "access_denied" if expected == "denied" else "valid"
                            ),
                        )
                    )
    return tuple(cases)


def generated_gis_parity_cases(
    matrix: GisParityMatrixV1,
) -> tuple[GisParityCaseV1, ...]:
    cases: list[GisParityCaseV1] = []
    for requirement in matrix.requirements:
        for geometry_type in GIS_GEOMETRY_TYPES:
            for profile in GIS_CASE_PROFILES:
                cases.append(
                    GisParityCaseV1(
                        case_id=(
                            "syn_gis_case_"
                            + _digest(requirement.requirement_id, geometry_type, profile)
                        ),
                        requirement_id=requirement.requirement_id,
                        geometry_type=geometry_type,
                        resource_profile=profile,
                    )
                )
    return tuple(cases)


def unique_case_ids(cases: Iterable[GeneratedContractCaseV1 | GisParityCaseV1]) -> bool:
    identifiers = [case.case_id for case in cases]
    return len(identifiers) == len(set(identifiers))
