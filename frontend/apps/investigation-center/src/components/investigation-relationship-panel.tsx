import type { ProvenanceProjection } from "../../../../packages/investigation-contracts/src";
export function InvestigationRelationshipPanel({
  projection,
}: {
  readonly projection: ProvenanceProjection;
}) {
  return (
    <section className="panel relationship-panel">
      <header>
        <div>
          <span className="eyebrow">BOUNDED VISUAL ENHANCEMENT</span>
          <h2>Relationship projection</h2>
        </div>
        <span>
          {projection.nodes.length} nodes / {projection.edges.length} edges
        </span>
      </header>
      <div className="relationship-canvas" aria-label="Bounded relationship visual">
        <span className="relationship-line line-a" />
        <span className="relationship-line line-b" />
        {projection.nodes.slice(0, 8).map((node, index) => (
          <button
            key={node.ref}
            type="button"
            style={{ left: `${8 + (index % 4) * 24}%`, top: `${16 + Math.floor(index / 4) * 48}%` }}
            title={node.ref}
          >
            <strong>{node.kind}</strong>
            <small>{node.label.replace("Generated ", "")}</small>
          </button>
        ))}
      </div>
      <footer>Authoritative node and edge tables remain available below.</footer>
    </section>
  );
}
