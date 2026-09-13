from __future__ import annotations

import pytest

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.case_bridge import execute_bridge, validate_disabled_bridge
from hcam.intelligence.investigations.contracts import (
    CaseManagementBridgeContractV1,
    ProvenanceBundleV1,
    ProvenanceEdgeV1,
    ProvenanceNodeV1,
)
from hcam.intelligence.investigations.prov_projection import (
    import_projection,
    project_generated_bundle,
)
from hcam.intelligence.investigations.provenance import validate_graph


def test_case_bridge_is_contract_only_and_disabled(p45_context: dict) -> None:
    bridge = CaseManagementBridgeContractV1(
        bridge_id="generated.case.bridge.v1",
        timeline_id=p45_context["timeline_id"],
        external_case_ref=stable_id("ref", "case"),
        mapping_profile="generated.case.mapping.v1",
        mapping_profile_digest=digest({"mapping": 1}),
        direction="projection_only",
    )
    validate_disabled_bridge(bridge)
    with pytest.raises(RuntimeError, match="not authorized"):
        execute_bridge(bridge)
    with pytest.raises(ValueError, match="must remain disabled"):
        validate_disabled_bridge(bridge.model_construct(**{**bridge.__dict__, "enabled": True}))


def test_generated_prov_projection_is_lossy_and_import_disabled(p45_context: dict) -> None:
    entity = ProvenanceNodeV1(
        node_id=stable_id("ipnd", "bridge-entity"),
        kind="entity",
        reference_id=stable_id("ref", "bridge-entity"),
        version=1,
        attributes={},
    )
    agent = ProvenanceNodeV1(
        node_id=stable_id("ipnd", "bridge-agent"),
        kind="agent",
        reference_id=stable_id("ref", "bridge-agent"),
        version=1,
        attributes={},
    )
    edge = ProvenanceEdgeV1(
        edge_id=stable_id("iped", "bridge-edge"),
        relation="was_attributed_to",
        source_node_id=entity.node_id,
        target_node_id=agent.node_id,
        recorded_at=p45_context["now"],
    )
    candidate = ProvenanceBundleV1(
        bundle_id=stable_id("iprv", "bridge-bundle"),
        timeline_id=p45_context["timeline_id"],
        department=p45_context["department"],
        nodes=[entity, agent],
        edges=[edge],
        bundle_digest="sha256:" + "0" * 64,
        completeness="partial",
    )
    bundle = candidate.model_copy(update={"bundle_digest": validate_graph(candidate)})
    projection = project_generated_bundle(bundle)
    assert projection.import_enabled is False
    assert projection.conformance_state == "not_claimed"
    with pytest.raises(RuntimeError, match="not authorized"):
        import_projection(projection.model_dump())
    with pytest.raises(ValueError, match="digest does not match"):
        project_generated_bundle(
            bundle.model_copy(update={"bundle_digest": "sha256:" + "f" * 64})
        )
