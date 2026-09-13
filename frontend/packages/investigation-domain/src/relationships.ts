import type { ProvenanceEdge, ProvenanceNode } from "../../investigation-contracts/src";

export interface BoundedRelationshipProjection {
  readonly nodes: readonly ProvenanceNode[];
  readonly edges: readonly ProvenanceEdge[];
  readonly truncated: boolean;
  readonly authoritativeRepresentation: "node_edge_tables";
}
export function boundRelationships(
  nodes: readonly ProvenanceNode[],
  edges: readonly ProvenanceEdge[],
  nodeLimit: 12 | 50 | 100,
  edgeLimit: 24 | 100 | 200,
): BoundedRelationshipProjection {
  const boundedNodes = nodes.slice(0, nodeLimit);
  const allowed = new Set(boundedNodes.map((node) => node.ref));
  const boundedEdges = edges
    .filter((edge) => allowed.has(edge.fromRef) && allowed.has(edge.toRef))
    .slice(0, edgeLimit);
  return {
    nodes: boundedNodes,
    edges: boundedEdges,
    truncated: nodes.length > boundedNodes.length || edges.length > boundedEdges.length,
    authoritativeRepresentation: "node_edge_tables",
  };
}
