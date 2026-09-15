from __future__ import annotations

import pytest

from hcam.intelligence.investigations.canonical import stable_id
from hcam.intelligence.investigations.contracts import (
    ProvenanceBundleV1,
    ProvenanceEdgeV1,
    ProvenanceNodeV1,
)
from hcam.intelligence.investigations.provenance import closure, validate_graph


def _bundle(p45_context: dict) -> ProvenanceBundleV1:
    entity = ProvenanceNodeV1(
        node_id=stable_id("ipnd", "entity"),
        kind="entity",
        reference_id=stable_id("ref", "entity"),
        version=1,
        attributes={"generated_value": "entity"},
    )
    activity = ProvenanceNodeV1(
        node_id=stable_id("ipnd", "activity"),
        kind="activity",
        reference_id=stable_id("ref", "activity"),
        version=1,
        attributes={},
    )
    edge = ProvenanceEdgeV1(
        edge_id=stable_id("iped", "edge"),
        relation="was_generated_by",
        source_node_id=entity.node_id,
        target_node_id=activity.node_id,
        recorded_at=p45_context["now"],
    )
    candidate = ProvenanceBundleV1(
        bundle_id=stable_id("iprv", "bundle"),
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        nodes=[entity, activity],
        edges=[edge],
        bundle_digest="sha256:" + "0" * 64,
        completeness="complete",
    )
    return candidate.model_copy(update={"bundle_digest": validate_graph(candidate)})


def test_provenance_graph_is_closed_and_deterministic(p45_context: dict) -> None:
    bundle = _bundle(p45_context)
    assert validate_graph(bundle) == bundle.bundle_digest
    assert closure(bundle, bundle.nodes[0].node_id) == sorted(
        [bundle.nodes[0].node_id, bundle.nodes[1].node_id]
    )
    with pytest.raises(KeyError):
        closure(bundle, stable_id("ipnd", "missing"))


def test_provenance_cycle_is_rejected(p45_context: dict) -> None:
    bundle = _bundle(p45_context)
    reverse = ProvenanceEdgeV1(
        edge_id=stable_id("iped", "reverse"),
        relation="used",
        source_node_id=bundle.nodes[1].node_id,
        target_node_id=bundle.nodes[0].node_id,
        recorded_at=p45_context["now"],
    )
    with pytest.raises(ValueError, match="cycles"):
        validate_graph(bundle.model_copy(update={"edges": [*bundle.edges, reverse]}))
