from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar


MAX_ACTIONS = 32
MAX_CAPABILITIES = 64
MAX_CONTRACT_CASES = 2_048
MAX_FILTERS = 32
MAX_GIS_FEATURES = 5_000
MAX_GIS_PARITY_REQUIREMENTS = 128
MAX_JOURNEY_STEPS = 64
MAX_LOCALE_KEY_LENGTH = 160
MAX_PAGE_SIZE = 200
MAX_PORTALS = 16
MAX_REASON_LENGTH = 256
MAX_ROLES = 16
MAX_ROUTE_STATE_KEYS = 24
MAX_SAFE_TEXT_LENGTH = 512
MAX_SORT_FIELDS = 8
MAX_VIEWS = 256


T = TypeVar("T")


def require_unique(values: Iterable[T], *, label: str) -> tuple[T, ...]:
    result = tuple(values)
    if len(result) != len(set(result)):
        raise ValueError(f"{label} must be unique")
    return result


def require_bounded_text(
    value: str,
    *,
    label: str,
    minimum: int = 1,
    maximum: int = MAX_SAFE_TEXT_LENGTH,
) -> str:
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    if not minimum <= len(value) <= maximum:
        raise ValueError(f"{label} length is outside its allowed bounds")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{label} contains a control character")
    return value
