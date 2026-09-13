import { ArrowRight, Building2, GitPullRequest, ShieldCheck, Users } from "lucide-react";
import { Link } from "react-router";
import { ApprovalTimeline } from "../components/approval-timeline";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { adminSummary, changeRequests } from "../data/admin-projections";
export function AdminOverviewPage() {
  const current = changeRequests.at(2);
  if (!current) return null;
  return (
    <AdminPageFrame
      eyebrow="ADMINISTRATION / GOVERNANCE"
      title="Administration overview"
      description="Generated organization, authorization, configuration, and approval projections with no effective mutation path."
    >
      <section className="summary-band" aria-label="Administration summary">
        <article>
          <Building2 size={18} />
          <span>Organizations</span>
          <strong>{adminSummary.organizations}</strong>
          <small>Generated tenants</small>
        </article>
        <article>
          <Users size={18} />
          <span>Identities</span>
          <strong>{adminSummary.identities}</strong>
          <small>Scoped projections</small>
        </article>
        <article>
          <GitPullRequest size={18} />
          <span>Open changes</span>
          <strong>{adminSummary.openChanges}</strong>
          <small>Independent review</small>
        </article>
        <article>
          <ShieldCheck size={18} />
          <span>Producer gaps</span>
          <strong>{adminSummary.producerGaps}</strong>
          <small>Remain explicit</small>
        </article>
      </section>
      <div className="two-column">
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">APPROVAL WORK</span>
              <h2>{current.ref}</h2>
            </div>
            <Link to="/admin/changes">
              Open queue <ArrowRight size={15} />
            </Link>
          </header>
          <ApprovalTimeline request={current} />
        </section>
        <section className="panel authority-panel">
          <header>
            <div>
              <span className="eyebrow">AUTHORITY</span>
              <h2>Server decisions only</h2>
            </div>
            <ShieldCheck size={20} />
          </header>
          <ul>
            <li>Default deny</li>
            <li>Department and purpose scope</li>
            <li>Independent PostgreSQL RLS equivalence</li>
            <li>Break-glass unavailable</li>
          </ul>
        </section>
      </div>
    </AdminPageFrame>
  );
}
