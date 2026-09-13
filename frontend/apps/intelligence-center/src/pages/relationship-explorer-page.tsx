import { GraphPanel } from "../components/graph-panel";
import { GraphTable } from "../components/graph-table";
import { relationships } from "../data/intelligence-projections";
export function RelationshipExplorerPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS / RELATIONSHIPS</p>
          <h1>Relationship explorer</h1>
          <p>
            A bounded read-only visual projection with complete node and edge tables as the
            authority.
          </p>
        </div>
        <span className="page-icon">No graph dependency</span>
      </header>
      <GraphPanel projection={relationships} />
      <section className="panel relationship-authority">
        <header>
          <div>
            <span className="eyebrow">AUTHORITATIVE REPRESENTATION</span>
            <h2>Complete relationship tables</h2>
          </div>
          <span>{relationships.edges.length} edges</span>
        </header>
        <GraphTable projection={relationships} />
      </section>
    </>
  );
}
