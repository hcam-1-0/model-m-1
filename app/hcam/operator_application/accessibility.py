from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .contracts import OperatorContractModel, StableId


class AccessibilityRequirementV1(OperatorContractModel):
    requirement_id: StableId
    category: Literal[
        "keyboard",
        "focus",
        "name_role_value",
        "contrast",
        "zoom_reflow",
        "localization",
        "reduced_motion",
        "alternative_view",
        "status_announcement",
    ]
    target: Literal["WCAG_2_2_AA", "APG_pattern", "HCAM_safety"]
    automated_check: bool
    manual_evidence_required: bool


class AlternativeViewV1(OperatorContractModel):
    source_view: Literal["map", "graph", "timeline", "data_grid", "media"]
    alternative_view: Literal["list", "table", "transcript", "summary"]
    preserves_selection: Literal[True] = True
    preserves_order: Literal[True] = True
    preserves_freshness: Literal[True] = True
    preserves_corrections: Literal[True] = True
    preserves_actions: Literal[True] = True


class AccessibilityMatrixV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.accessibility-matrix.v1"] = (
        "hcam.operator.accessibility-matrix.v1"
    )
    requirements: Annotated[
        list[AccessibilityRequirementV1], Field(min_length=9, max_length=64)
    ]
    alternatives: Annotated[list[AlternativeViewV1], Field(min_length=5, max_length=8)]
    generated_only: Literal[True] = True

    @model_validator(mode="after")
    def matrix_is_complete(self) -> AccessibilityMatrixV1:
        ids = [item.requirement_id for item in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("accessibility requirement identifiers must be unique")
        categories = {item.category for item in self.requirements}
        if len(categories) != 9:
            raise ValueError("all accessibility categories are required")
        source_views = [item.source_view for item in self.alternatives]
        if set(source_views) != {"map", "graph", "timeline", "data_grid", "media"}:
            raise ValueError("all complex views require an accessible alternative")
        if len(source_views) != len(set(source_views)):
            raise ValueError("complex-view alternatives must be unique")
        return self
