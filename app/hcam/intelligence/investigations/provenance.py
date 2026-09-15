from __future__ import annotations

from collections import defaultdict, deque

from hcam.intelligence.investigations.bounds import (
    MAX_PROVENANCE_DEPTH,
    MAX_PROVENANCE_FANOUT,
)
from hcam.intelligence.investigations.canonical import digest
from hcam.intelligence.investigations.contracts import ProvenanceBundleV1


_CAUSAL_RELATIONS = frozenset(
    {
        "used",
        "was_generated_by",
        "was_derived_from",
        "was_revision_of",
        "had_primary_source",
        "was_invalidated_by",
        "was_quoted_from",
        "was_informed_by",
    }
)


def validate_graph(bundle: ProvenanceBundleV1) -> str:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in bundle.edges:
        if edge.relation in _CAUSAL_RELATIONS:
            adjacency[edge.source_node_id].append(edge.target_node_id)
    if any(len(targets) > MAX_PROVENANCE_FANOUT for targets in adjacency.values()):
        raise ValueError("provenance fanout exceeds the bound")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, depth: int) -> None:
        if depth > MAX_PROVENANCE_DEPTH:
            raise ValueError("provenance depth exceeds the bound")
        if node in visiting:
            raise ValueError("causal provenance cycles are forbidden")
        if node in visited:
            return
        visiting.add(node)
        for target in adjacency.get(node, []):
            visit(target, depth + 1)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node, 0)
    material = {
        "timeline_id": bundle.timeline_id,
        "department": bundle.department,
        "nodes": [node.model_dump(mode="json") for node in bundle.nodes],
        "edges": [edge.model_dump(mode="json") for edge in bundle.edges],
        "completeness": bundle.completeness,
    }
    return digest(material)


def closure(bundle: ProvenanceBundleV1, start_node_id: str) -> list[str]:
    known = {node.node_id for node in bundle.nodes}
    if start_node_id not in known:
        raise KeyError("provenance node was not found")
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in bundle.edges:
        adjacency[edge.source_node_id].append(edge.target_node_id)
    queue = deque([(start_node_id, 0)])
    seen: set[str] = set()
    while queue:
        node, depth = queue.popleft()
        if depth > MAX_PROVENANCE_DEPTH:
            raise ValueError("provenance closure exceeds the depth bound")
        if node in seen:
            continue
        seen.add(node)
        queue.extend((target, depth + 1) for target in adjacency.get(node, []))
    return sorted(seen)
