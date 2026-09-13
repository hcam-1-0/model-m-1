from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.operator_application import (
    AccessibilityMatrixV1,
    ColorPairV1,
    DesignTokenSetV1,
    contrast_ratio,
)


ROOT = Path(__file__).resolve().parents[1]


def _accessibility_document() -> dict[str, object]:
    return json.loads(
        (ROOT / "contracts/phase-5/operator-ui-accessibility.v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_accessibility_matrix_covers_every_required_category_and_complex_view() -> None:
    matrix = AccessibilityMatrixV1.model_validate(_accessibility_document())
    assert {item.category for item in matrix.requirements} == {
        "keyboard",
        "focus",
        "name_role_value",
        "contrast",
        "zoom_reflow",
        "localization",
        "reduced_motion",
        "alternative_view",
        "status_announcement",
    }
    assert {item.source_view for item in matrix.alternatives} == {
        "map",
        "graph",
        "timeline",
        "data_grid",
        "media",
    }
    assert all(
        alternative.preserves_selection
        and alternative.preserves_order
        and alternative.preserves_freshness
        and alternative.preserves_corrections
        and alternative.preserves_actions
        for alternative in matrix.alternatives
    )


def test_accessibility_matrix_rejects_a_missing_category() -> None:
    document = _accessibility_document()
    requirements = document["requirements"]  # type: ignore[assignment]
    requirements[-1] = {  # type: ignore[index]
        **requirements[-1],  # type: ignore[index]
        "category": "keyboard",
    }
    with pytest.raises(ValidationError, match="all accessibility categories"):
        AccessibilityMatrixV1.model_validate(document)


def test_accessibility_matrix_rejects_duplicate_alternative() -> None:
    document = _accessibility_document()
    alternatives = document["alternatives"]  # type: ignore[assignment]
    alternatives[-1] = alternatives[0]  # type: ignore[index]
    with pytest.raises(ValidationError, match="all complex views"):
        AccessibilityMatrixV1.model_validate(document)


def test_contrast_ratio_uses_wcag_relative_luminance() -> None:
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0)
    with pytest.raises(ValueError, match="six-digit hexadecimal"):
        contrast_ratio("black", "#FFFFFF")


def test_color_pair_fails_closed_below_declared_contrast() -> None:
    with pytest.raises(ValidationError, match="contrast target"):
        ColorPairV1(
            pair_id="color.low_contrast",
            foreground="#777777",
            background="#888888",
            minimum_ratio=4.5,
        )


def test_design_tokens_enforce_dense_enterprise_constraints() -> None:
    tokens = DesignTokenSetV1(
        version="phase5.0.v1",
        theme_id="neutral_grid",
        color_pairs=[
            ColorPairV1(
                pair_id="color.primary",
                foreground="#FFFFFF",
                background="#111111",
                minimum_ratio=4.5,
            ),
            ColorPairV1(
                pair_id="color.status",
                foreground="#000000",
                background="#FFFFFF",
                minimum_ratio=7.0,
            ),
        ],
        spacing_steps_px=[4, 8, 12, 16],
        control_minimum_px=44,
        border_radius_maximum_px=8,
    )
    assert tokens.letter_spacing_px == 0
    assert tokens.reduced_motion_supported is True
    assert tokens.color_pairs[0].foreground == "#FFFFFF"


@pytest.mark.parametrize("spacing", [[8, 4, 12, 16], [4, 8, 8, 16]])
def test_design_tokens_reject_unsorted_or_duplicate_spacing(spacing: list[int]) -> None:
    with pytest.raises(ValidationError, match="sorted and unique"):
        DesignTokenSetV1(
            version="phase5.0.v1",
            theme_id="high_contrast",
            color_pairs=[
                ColorPairV1(
                    pair_id="color.one",
                    foreground="#FFFFFF",
                    background="#000000",
                    minimum_ratio=7.0,
                ),
                ColorPairV1(
                    pair_id="color.two",
                    foreground="#000000",
                    background="#FFFFFF",
                    minimum_ratio=7.0,
                ),
            ],
            spacing_steps_px=spacing,
        )
