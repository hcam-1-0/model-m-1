import { FileCheck2 } from "lucide-react";
import { ComplianceEvidencePanel } from "../components/compliance-evidence-panel";
import { SecurityLimitations } from "../components/security-limitations";
import { SecurityPageFrame } from "../components/security-state-boundary";
export function PoliciesExceptionsAttestationsPage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / COMPLIANCE"
      title="Policies, exceptions, and attestations"
      description="Revisioned generated policy evidence and exception references; attestation signing and compliance claims remain unavailable."
    >
      <SecurityLimitations />
      <div className="two-column">
        <ComplianceEvidencePanel />
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">ATTESTATION</span>
              <h2>Signing boundary</h2>
            </div>
            <FileCheck2 size={20} />
          </header>
          <dl className="detail-grid">
            <div>
              <dt>Evidence</dt>
              <dd>Generated references</dd>
            </div>
            <div>
              <dt>Policy revision</dt>
              <dd>SYN-POLICY-R7</dd>
            </div>
            <div>
              <dt>Legal decision</dt>
              <dd>Not made</dd>
            </div>
            <div>
              <dt>Signing</dt>
              <dd>Unavailable</dd>
            </div>
          </dl>
          <button type="button" disabled>
            Sign attestation
          </button>
        </section>
      </div>
    </SecurityPageFrame>
  );
}
