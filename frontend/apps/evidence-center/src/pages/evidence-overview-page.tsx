import { ArrowRight, FileLock2, Fingerprint, Network } from "lucide-react";
import { Link } from "react-router";
import { EvidenceLimitations } from "../components/evidence-limitations";
import { EvidenceReferenceTable } from "../components/evidence-reference-table";
import { evidenceReferences, producerGaps } from "../data/evidence-projections";

export function EvidenceOverviewPage() {
  const observed = evidenceReferences.filter((item) => item.integrity === "digest_observed").length;
  const denied = evidenceReferences.filter((item) => item.access === "denied").length;
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INDEPENDENTLY AUTHORIZED WORKSPACE</p>
          <h1>Evidence reference overview</h1>
          <p>
            Review generated identities, integrity observations, provenance, custody, access, and
            limitations without resolving source content.
          </p>
        </div>
        <Link className="primary-link" to="/evidence/queue">
          <FileLock2 size={16} /> Open reference queue
        </Link>
      </header>
      <section className="metric-strip" aria-label="Evidence overview metrics">
        <div>
          <span>References</span>
          <strong>{evidenceReferences.length}</strong>
          <small>generated only</small>
        </div>
        <div>
          <span>Digest observed</span>
          <strong>{observed}</strong>
          <small>not truth</small>
        </div>
        <div>
          <span>Access denied</span>
          <strong>{denied}</strong>
          <small>fail closed</small>
        </div>
        <div>
          <span>Producer gaps</span>
          <strong>{producerGaps.length}</strong>
          <small>preserved</small>
        </div>
      </section>
      <div className="overview-grid">
        <section className="panel table-panel">
          <header>
            <div>
              <span className="eyebrow">AUTHORITATIVE LIST</span>
              <h2>Generated evidence references</h2>
            </div>
            <Link to="/evidence/queue">
              View all <ArrowRight size={15} />
            </Link>
          </header>
          <EvidenceReferenceTable items={evidenceReferences.slice(0, 7)} />
        </section>
        <section className="panel workspace-principles">
          <header>
            <div>
              <span className="eyebrow">SEPARATE AXES</span>
              <h2>Evidence controls</h2>
            </div>
            <Fingerprint size={19} />
          </header>
          <ul>
            <li>
              <Fingerprint size={16} />
              <div>
                <strong>Integrity</strong>
                <span>Observed independently from truth</span>
              </div>
            </li>
            <li>
              <Network size={16} />
              <div>
                <strong>Provenance</strong>
                <span>Bounded graph with authoritative tables</span>
              </div>
            </li>
            <li>
              <FileLock2 size={16} />
              <div>
                <strong>Source</strong>
                <span>Opaque and unresolved by default</span>
              </div>
            </li>
          </ul>
        </section>
      </div>
      <EvidenceLimitations
        limitations={[
          "No source, media, export, print, deletion, hold, or release operation is available.",
        ]}
      />
    </>
  );
}
