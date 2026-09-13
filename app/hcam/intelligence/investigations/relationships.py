from __future__ import annotations

from datetime import datetime

from hcam.intelligence.investigations.canonical import stable_id
from hcam.intelligence.investigations.contracts import (
    InvestigationTimelineV2,
    RelationshipRevisionV1,
)


def create_relationship(
    *,
    department: str,
    source_timeline_id: str,
    target_timeline_id: str,
    kind: str,
    revision: int,
    active: bool,
    actor_id: str,
    reason: str,
    recorded_at: datetime,
) -> RelationshipRevisionV1:
    return RelationshipRevisionV1(
        relationship_id=stable_id(
            "irel", source_timeline_id, target_timeline_id, kind, revision
        ),
        department=department,
        source_timeline_id=source_timeline_id,
        target_timeline_id=target_timeline_id,
        kind=kind,
        revision=revision,
        active=active,
        actor_id=actor_id,
        reason=reason,
        recorded_at=recorded_at,
    )


def validate_merge_graph(relations: list[RelationshipRevisionV1]) -> None:
    latest: dict[tuple[str, str], RelationshipRevisionV1] = {}
    for relation in relations:
        if relation.kind != "merged_into":
            continue
        key = (relation.source_timeline_id, relation.target_timeline_id)
        current = latest.get(key)
        if current is None or relation.revision > current.revision:
            latest[key] = relation
    adjacency: dict[str, str] = {}
    for relation in latest.values():
        if not relation.active:
            continue
        existing_target = adjacency.get(relation.source_timeline_id)
        if existing_target is not None and existing_target != relation.target_timeline_id:
            raise ValueError("a timeline cannot have multiple active merge targets")
        adjacency[relation.source_timeline_id] = relation.target_timeline_id
    for source in adjacency:
        seen: set[str] = set()
        node = source
        while node in adjacency:
            if node in seen:
                raise ValueError("timeline merge cycles are forbidden")
            seen.add(node)
            node = adjacency[node]


def reopen_timeline(
    timeline: InvestigationTimelineV2,
    *,
    updated_at: datetime,
    content_digest: str,
) -> InvestigationTimelineV2:
    if timeline.lifecycle != "closed":
        raise ValueError("only closed timelines can be reopened")
    return timeline.model_copy(
        update={
            "lifecycle": "reopened",
            "revision": timeline.revision + 1,
            "updated_at": updated_at,
            "content_digest": content_digest,
        }
    )
