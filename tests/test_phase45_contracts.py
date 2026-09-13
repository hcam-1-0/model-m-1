from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from hcam.intelligence.investigations.bounds import (
    BoundsError,
    bounded_page_size,
    bounded_reason,
    validate_generated_document,
)
from hcam.intelligence.investigations.contracts import TemporalAssertionV1


def test_temporal_contract_preserves_dual_chronology(p45_context: dict) -> None:
    now = p45_context["now"]
    assertion = TemporalAssertionV1(
        occurred_at=now,
        observed_at=now,
        received_at=now + timedelta(seconds=1),
        recorded_at=now + timedelta(seconds=2),
        occurrence_precision="second",
        clock_trust="bounded_skew",
        clock_skew_ms=25,
    )
    assert assertion.recorded_at > assertion.occurred_at


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"occurred_at": None}, "known occurrence"),
        ({"occurrence_precision": "unknown"}, "unknown occurrence"),
        ({"clock_trust": "bounded_skew"}, "measured skew"),
    ],
)
def test_temporal_contract_fails_closed(p45_context: dict, updates: dict, message: str) -> None:
    now = p45_context["now"]
    values = {
        "occurred_at": now,
        "observed_at": now,
        "received_at": now,
        "recorded_at": now,
        "occurrence_precision": "second",
        "clock_trust": "trusted",
    }
    values.update(updates)
    with pytest.raises(ValidationError, match=message):
        TemporalAssertionV1.model_validate(values)


def test_entry_payload_rejects_locator_and_unknown_fields(p45_context: dict) -> None:
    entry = p45_context["entry"]()
    with_locator = entry.model_dump()
    with_locator["payload"] = {"source_url": "https://example.invalid"}
    with pytest.raises(ValidationError):
        type(entry).model_validate(with_locator)
    with pytest.raises(ValidationError, match="Extra inputs"):
        type(entry).model_validate({**entry.model_dump(), "private_note": "generated"})


@pytest.mark.parametrize(
    "value",
    [
        {"password": "generated"},
        {"value": "rtsp://example.invalid/generated"},
        {"value": float("inf")},
        {1: "generated"},
        b"generated",
    ],
)
def test_generated_documents_reject_prohibited_material(value: object) -> None:
    with pytest.raises(BoundsError):
        validate_generated_document(value)


def test_basic_bounds_are_explicit() -> None:
    assert bounded_page_size(200) == 200
    assert bounded_reason("generated reason") == "generated reason"
    with pytest.raises(BoundsError):
        bounded_page_size(0)
    with pytest.raises(BoundsError):
        bounded_reason(" short ")


@pytest.mark.parametrize(
    "value",
    [
        {"value": "x" * 4097},
        {"value": "generated\x00value"},
        {"value": "C:\\generated\\private"},
        {"value": "Bearer abcdefghijklmnopqrstuvwxyz"},
        list(range(2049)),
        {f"field_{index}": index for index in range(129)},
    ],
)
def test_generated_document_size_and_value_limits(value: object) -> None:
    with pytest.raises(BoundsError):
        validate_generated_document(value)


def test_generated_document_depth_is_bounded() -> None:
    value: object = "generated"
    for _ in range(18):
        value = [value]
    with pytest.raises(BoundsError, match="nesting depth"):
        validate_generated_document(value)
