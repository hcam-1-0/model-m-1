import pytest

from hcam.operations.platform.bounds import BoundsError, bounded_text, validate_generated_document
from hcam.operations.platform.canonical import CanonicalizationError, canonical_bytes, digest, stable_id


def test_canonical_encoding_is_ascii_sorted_and_stable() -> None:
    assert canonical_bytes({"b": 2, "a": "value"}) == b'{"a":"value","b":2}'
    assert digest({"a": 1}) == digest({"a": 1})
    assert stable_id("ref", "a", 1) == stable_id("ref", "a", 1)


def test_canonical_encoding_rejects_nan_and_oversize() -> None:
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"value": float("nan")})
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"value": "x" * 100}, maximum_bytes=10)


@pytest.mark.parametrize(
    "value",
    [" padded", "padded ", "contains\x00null", "https://generated.invalid", "Bearer " + "x" * 20],
)
def test_bounded_text_rejects_ambiguous_or_sensitive_material(value: str) -> None:
    with pytest.raises(BoundsError):
        bounded_text(value)


def test_generated_document_accepts_bounded_primitives_and_containers() -> None:
    assert validate_generated_document(
        {"enabled": True, "count": 2, "ratio": 0.5, "state": None, "items": ["generated", 1]}
    ) == 8


@pytest.mark.parametrize(
    "value",
    [
        float("inf"),
        {1: "non-string-key"},
        {"credential_state": "unknown"},
        {f"field_{index}": index for index in range(129)},
        list(range(2049)),
        bytes(1),
    ],
)
def test_generated_document_rejects_unbounded_or_prohibited_values(value: object) -> None:
    with pytest.raises(BoundsError):
        validate_generated_document(value)


def test_generated_document_rejects_excessive_depth_and_aggregate_items() -> None:
    nested: object = "leaf"
    for _ in range(18):
        nested = [nested]
    with pytest.raises(BoundsError):
        validate_generated_document(nested)
    with pytest.raises(BoundsError):
        validate_generated_document([*range(2048)])
