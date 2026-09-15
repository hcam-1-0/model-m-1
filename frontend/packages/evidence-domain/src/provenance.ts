import type { ProvenanceProjection } from "../../investigation-contracts/src";

export function validateProvenanceProjection(projection: ProvenanceProjection): readonly string[] {
  const failures: string[] = [];
  const runtimeProjection = projection as unknown as Readonly<Record<string, unknown>>;
  const refs = new Set(projection.nodes.map((node) => node.ref));
  if (projection.nodes.length > projection.nodeCeiling) failures.push("node_ceiling_exceeded");
  if (projection.edges.length > projection.edgeCeiling) failures.push("edge_ceiling_exceeded");
  if (projection.edges.some((edge) => !refs.has(edge.fromRef) || !refs.has(edge.toRef)))
    failures.push("dangling_edge");
  if (runtimeProjection.authoritativeRepresentation !== "node_edge_tables")
    failures.push("table_authority_missing");
  if (
    runtimeProjection.externalProvImport !== false ||
    runtimeProjection.provConformanceClaim !== false
  )
    failures.push("external_prov_boundary_violation");
  return failures;
}
