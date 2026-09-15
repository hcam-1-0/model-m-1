from __future__ import annotations

import pytest

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.relationships import (
    create_relationship,
    reopen_timeline,
    validate_merge_graph,
)


def test_merge_graph_rejects_cycles(p45_context: dict) -> None:
    second = stable_id("inv", "second")
    forward = create_relationship(
        department=p45_context["department"],
        source_timeline_id=p45_context["timeline_id"],
        target_timeline_id=second,
        kind="merged_into",
        revision=1,
        active=True,
        actor_id=p45_context["actor"],
        reason=p45_context["reason"],
        recorded_at=p45_context["now"],
    )
    reverse = create_relationship(
        department=p45_context["department"],
        source_timeline_id=second,
        target_timeline_id=p45_context["timeline_id"],
        kind="merged_into",
        revision=1,
        active=True,
        actor_id=p45_context["actor"],
        reason=p45_context["reason"],
        recorded_at=p45_context["now"],
    )
    with pytest.raises(ValueError, match="cycles"):
        validate_merge_graph([forward, reverse])


def test_merge_graph_rejects_multiple_active_targets(p45_context: dict) -> None:
    second = stable_id("inv", "second")
    third = stable_id("inv", "third")
    relations = [
        create_relationship(
            department=p45_context["department"],
            source_timeline_id=p45_context["timeline_id"],
            target_timeline_id=target,
            kind="merged_into",
            revision=1,
            active=True,
            actor_id=p45_context["actor"],
            reason=p45_context["reason"],
            recorded_at=p45_context["now"],
        )
        for target in (second, third)
    ]
    with pytest.raises(ValueError, match="multiple active merge targets"):
        validate_merge_graph(relations)


def test_closed_timeline_can_be_reopened_without_erasing_history(p45_context: dict) -> None:
    timeline = p45_context["command"]
    from hcam.intelligence.investigations.contracts import InvestigationTimelineV2

    current = InvestigationTimelineV2(
        timeline_id=timeline.timeline_id,
        department=timeline.department,
        title=timeline.title,
        purpose_code=timeline.purpose_code,
        lifecycle="closed",
        disposition="reviewed",
        revision=2,
        entry_count=1,
        canonical_timeline_id=timeline.timeline_id,
        content_digest=digest({"timeline": "closed"}),
        created_at=timeline.requested_at,
        updated_at=timeline.requested_at,
    )
    reopened = reopen_timeline(
        current,
        updated_at=p45_context["now"],
        content_digest=digest({"timeline": "reopened"}),
    )
    assert reopened.lifecycle == "reopened"
    assert reopened.revision == 3
    with pytest.raises(ValueError, match="only closed"):
        reopen_timeline(
            reopened,
            updated_at=p45_context["now"],
            content_digest=digest({"timeline": "invalid"}),
        )
