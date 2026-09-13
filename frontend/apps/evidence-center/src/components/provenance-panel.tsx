import type { ProvenanceProjection } from "../../../../packages/investigation-contracts/src";

export function ProvenancePanel({ projection }: { readonly projection: ProvenanceProjection }) {
  return (
    <section className="provenance-visual" aria-label="Generated provenance visual projection">
      {projection.nodes.slice(0, 8).map((node) => (
        <article key={node.ref} className={`provenance-node node-${node.kind}`}>
          <strong>{node.label}</strong>
          <small>{node.kind}</small>
        </article>
      ))}
      <p>Visual aid only. The node and edge tables are authoritative.</p>
    </section>
  );
}
