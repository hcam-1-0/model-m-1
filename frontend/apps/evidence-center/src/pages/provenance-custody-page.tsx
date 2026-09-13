import { CustodyTable } from "../components/custody-table";
import { CustodyTimeline } from "../components/custody-timeline";
import { EvidenceLimitations } from "../components/evidence-limitations";
import { ProvenancePanel } from "../components/provenance-panel";
import { ProvenanceTable } from "../components/provenance-table";
import { custodyEvents, provenanceProjection } from "../data/evidence-projections";

export function ProvenanceCustodyPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">BOUNDED RELATIONSHIP PROJECTIONS</p>
          <h1>Provenance and custody</h1>
          <p>
            Separate generated provenance and custody records with authoritative table equivalents
            and explicit ceilings.
          </p>
        </div>
      </header>
      <div className="split-layout">
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">VISUAL AID</span>
              <h2>Provenance projection</h2>
            </div>
            <small>
              {provenanceProjection.nodes.length}/{provenanceProjection.nodeCeiling} nodes
            </small>
          </header>
          <ProvenancePanel projection={provenanceProjection} />
        </section>
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">SEQUENCE ORDER</span>
              <h2>Custody chronology</h2>
            </div>
            <small>Not inferred from provenance</small>
          </header>
          <CustodyTimeline events={custodyEvents} />
        </section>
      </div>
      <section className="panel table-panel section-gap">
        <header>
          <div>
            <span className="eyebrow">AUTHORITATIVE PROVENANCE</span>
            <h2>Node-edge table</h2>
          </div>
        </header>
        <ProvenanceTable projection={provenanceProjection} />
      </section>
      <section className="panel table-panel section-gap">
        <header>
          <div>
            <span className="eyebrow">AUTHORITATIVE CUSTODY</span>
            <h2>Custody event table</h2>
          </div>
        </header>
        <CustodyTable events={custodyEvents} />
      </section>
      <EvidenceLimitations
        limitations={["External PROV import and conformance claims remain disabled."]}
      />
    </>
  );
}
