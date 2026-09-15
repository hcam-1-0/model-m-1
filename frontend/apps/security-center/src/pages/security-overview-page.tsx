import { ArrowRight } from "lucide-react";
import { Link } from "react-router";
import { ComplianceEvidencePanel } from "../components/compliance-evidence-panel";
import { DenialActivityTable } from "../components/denial-activity-table";
import { PostureSummary } from "../components/posture-summary";
import { SecurityLimitations } from "../components/security-limitations";
import { SecurityPageFrame } from "../components/security-state-boundary";
export function SecurityOverviewPage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / ASSURANCE"
      title="Security overview"
      description="Generated, source-qualified access, audit, compliance, provider, and supply-chain assurance without live telemetry or operational conclusions."
    >
      <PostureSummary />
      <SecurityLimitations />
      <div className="two-column">
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">DENIAL ACTIVITY</span>
              <h2>Latest generated decisions</h2>
            </div>
            <Link to="/security/denials">
              Open explorer <ArrowRight size={15} />
            </Link>
          </header>
          <DenialActivityTable limit={6} />
        </section>
        <ComplianceEvidencePanel />
      </div>
    </SecurityPageFrame>
  );
}
