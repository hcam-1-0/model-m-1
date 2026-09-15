import { EvidenceFilterRail } from "../components/evidence-filter-rail";
import { EvidenceReferenceTable } from "../components/evidence-reference-table";
import { EvidenceStateBoundary } from "../components/evidence-state-boundary";
import { evidenceReferences } from "../data/evidence-projections";

export function EvidenceQueuePage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">SERVER-PAGINATED CONTRACT</p>
          <h1>Evidence reference queue</h1>
          <p>
            Authoritative generated list with stable references, independent states, freshness, and
            access decisions.
          </p>
        </div>
      </header>
      <EvidenceFilterRail />
      <EvidenceStateBoundary
        state="partial"
        detail="Generated list is complete for its fixture page; thirty-six real producer contracts remain unavailable."
      />
      <section className="panel table-panel">
        <header>
          <div>
            <span className="eyebrow">18 GENERATED REFERENCES</span>
            <h2>Reference results</h2>
          </div>
          <small>Stable anchor SYN-P55-EVIDENCE-0001</small>
        </header>
        <EvidenceReferenceTable items={evidenceReferences} />
      </section>
    </>
  );
}
