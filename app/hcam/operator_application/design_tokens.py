from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from .contracts import OperatorContractModel, SchemaVersion, StableId


_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _linear_channel(value: int) -> float:
    channel = value / 255
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def contrast_ratio(foreground: str, background: str) -> float:
    if not _HEX_COLOR.fullmatch(foreground) or not _HEX_COLOR.fullmatch(background):
        raise ValueError("contrast colors must use six-digit hexadecimal notation")

    def luminance(color: str) -> float:
        red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
        return (
            0.2126 * _linear_channel(red)
            + 0.7152 * _linear_channel(green)
            + 0.0722 * _linear_channel(blue)
        )

    lighter, darker = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class ColorPairV1(OperatorContractModel):
    pair_id: StableId
    foreground: str
    background: str
    minimum_ratio: Annotated[float, Field(ge=3, le=21)]

    @field_validator("foreground", "background")
    @classmethod
    def color_is_hex(cls, value: str) -> str:
        if not _HEX_COLOR.fullmatch(value):
            raise ValueError("color must use six-digit hexadecimal notation")
        return value.upper()

    @model_validator(mode="after")
    def contrast_is_sufficient(self) -> ColorPairV1:
        if contrast_ratio(self.foreground, self.background) < self.minimum_ratio:
            raise ValueError("color pair does not meet its declared contrast target")
        return self


class DesignTokenSetV1(OperatorContractModel):
    contract_type: Literal["hcam.operator.design-tokens.v1"] = (
        "hcam.operator.design-tokens.v1"
    )
    version: SchemaVersion
    theme_id: Literal["neutral_grid", "high_contrast"]
    color_pairs: Annotated[list[ColorPairV1], Field(min_length=2, max_length=32)]
    spacing_steps_px: Annotated[list[int], Field(min_length=4, max_length=16)]
    control_minimum_px: Annotated[int, Field(ge=24, le=64)] = 44
    border_radius_maximum_px: Annotated[int, Field(ge=0, le=8)] = 8
    letter_spacing_px: Literal[0] = 0
    reduced_motion_supported: Literal[True] = True

    @model_validator(mode="after")
    def tokens_are_ordered_and_unique(self) -> DesignTokenSetV1:
        ids = [item.pair_id for item in self.color_pairs]
        if len(ids) != len(set(ids)):
            raise ValueError("color-pair identifiers must be unique")
        if self.spacing_steps_px != sorted(set(self.spacing_steps_px)):
            raise ValueError("spacing steps must be sorted and unique")
        return self
