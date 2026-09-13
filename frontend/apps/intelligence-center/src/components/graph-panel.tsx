import { Network } from "lucide-react";
import type { RelationshipProjection } from "../../../../packages/intelligence-contracts/src";
export function GraphPanel({ projection }: { readonly projection: RelationshipProjection }) {
  const positions = projection.nodes
    .slice(0, 10)
    .map((node, index) => ({ node, x: 13 + (index % 4) * 25, y: 18 + Math.floor(index / 4) * 34 }));
  return (
    <section className="panel graph-panel" aria-label="Bounded relationship visual">
      <header>
        <div>
          <span className="eyebrow">BOUNDED VISUAL AID</span>
          <h2>Relationship projection</h2>
        </div>
        <span>
          <Network size={16} /> {projection.nodes.length} nodes
        </span>
      </header>
      <div
        className="graph-canvas"
        role="group"
        aria-label={`${projection.nodes.length} generated nodes and ${projection.edges.length} generated relationships. Tables below are authoritative.`}
      >
        {positions.map(({ node, x, y }) => (
          <button
            key={node.ref}
            type="button"
            style={{ left: `${x}%`, top: `${y}%` }}
            title={`${node.label}: ${node.kind}`}
          >
            <span />
            <small>{node.label}</small>
          </button>
        ))}
        <div className="graph-lines" aria-hidden="true" />
      </div>
      <footer>Visual selection never replaces the complete node and edge tables.</footer>
    </section>
  );
}
