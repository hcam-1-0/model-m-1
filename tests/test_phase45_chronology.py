from __future__ import annotations

from datetime import timedelta

import pytest

from hcam.intelligence.investigations.chronology import order_entries, reconstruct


def test_reconstruction_supports_record_and_event_time_views(p45_context: dict) -> None:
    first = p45_context["entry"](1)
    second = p45_context["entry"](2, family="correction")
    second = second.model_copy(
        update={
            "temporal": second.temporal.model_copy(
                update={"occurred_at": p45_context["now"] - timedelta(seconds=1)}
            )
        }
    )
    assert [item.entry_id for item in order_entries([first, second])] == [
        first.entry_id,
        second.entry_id,
    ]
    assert order_entries([first, second], view="event_time")[0].entry_id == second.entry_id
    snapshot = reconstruct([first, second], through_revision=2)
    assert [item.entry_id for item in snapshot.entries] == [first.entry_id]
    assert snapshot.later_correction_entry_ids == [second.entry_id]


def test_reconstruction_detects_incomplete_sequence(p45_context: dict) -> None:
    first = p45_context["entry"](1)
    third = p45_context["entry"](3)
    result = reconstruct([first, third], through_revision=4)
    assert result.completeness == "partial"


def test_reconstruction_rejects_invalid_or_mixed_input(p45_context: dict) -> None:
    with pytest.raises(ValueError, match="positive"):
        reconstruct([p45_context["entry"]()], through_revision=0)
    with pytest.raises(ValueError, match="at least one"):
        reconstruct([], through_revision=1)
    mixed = p45_context["entry"]().model_copy(
        update={"timeline_id": "inv_" + "1" * 32}
    )
    with pytest.raises(ValueError, match="share timeline"):
        reconstruct([p45_context["entry"](), mixed], through_revision=2)
