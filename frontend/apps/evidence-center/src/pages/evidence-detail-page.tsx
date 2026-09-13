import { Fingerprint, Network, Scale, ShieldAlert } from "lucide-react";
import { Link, useParams } from "react-router";
import { EvidenceIdentityPanel } from "../components/evidence-identity-panel";
import { EvidenceLimitations } from "../components/evidence-limitations";
import { EvidenceStateMatrix } from "../components/evidence-state-matrix";
import { SourceBoundaryPanel } from "../components/source-boundary-panel";
import { evidenceReferences, selectedEvidence } from "../data/evidence-projections";

export function EvidenceDetailPage() {
  const { evidenceId } = useParams();
  const reference = evidenceReferences.find((item) => item.ref === evidenceId) ?? selectedEvidence;
  if (!reference) return <EvidenceStateBoundaryFallback />;
  return (
    <>
      <EvidenceIdentityPanel reference={reference} />
      <nav className="detail-actions" aria-label="Evidence detail sections">
        <Link to="/evidence/integrity">
          <Fingerprint size={16} /> Integrity
        </Link>
        <Link to="/evidence/provenance">
          <Network size={16} /> Provenance & custody
        </Link>
        <Link to="/evidence/policy">
          <Scale size={16} /> Policy previews
        </Link>
      </nav>
      <div className="split-layout">
        <EvidenceStateMatrix reference={reference} />
        <SourceBoundaryPanel reference={reference} />
      </div>
      <EvidenceLimitations limitations={reference.limitations} />
    </>
  );
}
function EvidenceStateBoundaryFallback() {
  return (
    <section className="state-boundary state-degraded">
      <ShieldAlert size={18} />
      <div>
        <strong>Unavailable</strong>
        <p>The generated evidence fixture is unavailable.</p>
      </div>
    </section>
  );
}
