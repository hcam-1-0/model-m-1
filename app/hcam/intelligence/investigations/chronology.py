from __future__ import annotations

from datetime import datetime
from typing import Literal

from hcam.intelligence.investigations.canonical import digest
from hcam.intelligence.investigations.contracts import ReconstructionV1, TimelineEntryV2


def order_entries(
    entries: list[TimelineEntryV2],
    *,
    view: Literal["record_sequence", "event_time"] = "record_sequence",
) -> list[TimelineEntryV2]:
    if view == "record_sequence":
        return sorted(entries, key=lambda entry: (entry.sequence, entry.entry_id))

    def event_key(entry: TimelineEntryV2) -> tuple[datetime, int, str]:
        occurred = entry.temporal.occurred_at or entry.temporal.observed_at
        return occurred, entry.sequence, entry.entry_id

    return sorted(entries, key=event_key)


def reconstruct(
    entries: list[TimelineEntryV2],
    *,
    through_revision: int,
    view: Literal["record_sequence", "event_time"] = "record_sequence",
    recorded_at_cutoff: datetime | None = None,
) -> ReconstructionV1:
    if through_revision < 1:
        raise ValueError("through_revision must be positive")
    if not entries:
        raise ValueError("at least one timeline entry is required")
    timeline_ids = {entry.timeline_id for entry in entries}
    departments = {entry.department for entry in entries}
    if len(timeline_ids) != 1 or len(departments) != 1:
        raise ValueError("reconstruction entries must share timeline and department")
    selected = [
        entry
        for entry in entries
        if entry.aggregate_revision <= through_revision
        and (
            recorded_at_cutoff is None
            or entry.temporal.recorded_at <= recorded_at_cutoff
        )
    ]
    later = [
        entry.entry_id
        for entry in entries
        if entry.aggregate_revision > through_revision
        and entry.family in {"correction", "retraction"}
    ]
    ordered = order_entries(selected, view=view)
    sequence_values = [entry.sequence for entry in order_entries(selected)]
    completeness = "complete"
    if sequence_values and sequence_values != list(
        range(sequence_values[0], sequence_values[0] + len(sequence_values))
    ):
        completeness = "partial"
    material = {
        "timeline_id": next(iter(timeline_ids)),
        "view": view,
        "through_revision": through_revision,
        "entry_ids": [entry.entry_id for entry in ordered],
        "later_correction_entry_ids": later,
        "completeness": completeness,
    }
    return ReconstructionV1(
        timeline_id=next(iter(timeline_ids)),
        department=next(iter(departments)),
        view=view,
        through_revision=through_revision,
        entries=ordered,
        later_correction_entry_ids=later,
        completeness=completeness,
        reconstruction_digest=digest(material),
    )
