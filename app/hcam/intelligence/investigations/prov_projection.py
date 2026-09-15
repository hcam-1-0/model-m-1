from __future__ import annotations

from hcam.intelligence.investigations.canonical import stable_id
from hcam.intelligence.investigations.contracts import (
    ProvInterchangeProjectionV1,
    ProvenanceBundleV1,
    ProvProjectionStatementV1,
)
from hcam.intelligence.investigations.provenance import validate_graph


_RELATION_MAP = {
    "used": "used",
    "was_generated_by": "wasGeneratedBy",
    "was_derived_from": "wasDerivedFrom",
    "was_attributed_to": "wasAttributedTo",
    "was_associated_with": "wasAssociatedWith",
    "acted_on_behalf_of": "actedOnBehalfOf",
    "was_informed_by": "wasInformedBy",
    "was_revision_of": "wasRevisionOf",
    "had_primary_source": "hadPrimarySource",
    "was_invalidated_by": "wasInvalidatedBy",
    "was_quoted_from": "wasQuotedFrom",
}


def project_generated_bundle(bundle: ProvenanceBundleV1) -> ProvInterchangeProjectionV1:
    calculated = validate_graph(bundle)
    if calculated != bundle.bundle_digest:
        raise ValueError("provenance bundle digest does not match")
    statements = [
        ProvProjectionStatementV1(
            subject=edge.source_node_id,
            relation=_RELATION_MAP[edge.relation],
            object=edge.target_node_id,
        )
        for edge in bundle.edges
        if edge.relation in _RELATION_MAP
    ]
    unmapped = [
        edge.edge_id for edge in bundle.edges if edge.relation not in _RELATION_MAP
    ]
    return ProvInterchangeProjectionV1(
        projection_id=stable_id("iprx", bundle.bundle_id, bundle.bundle_digest),
        bundle_id=bundle.bundle_id,
        bundle_digest=bundle.bundle_digest,
        statements=statements,
        unmapped_edge_ids=unmapped,
    )


def import_projection(_payload: object) -> ProvenanceBundleV1:
    raise RuntimeError("PROV import is disabled and not authorized")
