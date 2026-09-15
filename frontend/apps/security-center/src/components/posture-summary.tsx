import { CircleAlert, LockKeyhole, ShieldCheck, TriangleAlert } from "lucide-react";
import { securitySummary } from "../data/security-projections";
export function PostureSummary() {
  return (
    <section className="summary-band" aria-label="Security posture summary">
      <article>
        <ShieldCheck size={18} />
        <span>Posture</span>
        <strong>{securitySummary.posture}</strong>
        <small>Generated evidence</small>
      </article>
      <article>
        <LockKeyhole size={18} />
        <span>Access decisions</span>
        <strong>{securitySummary.accessDecisions}</strong>
        <small>Bounded projection</small>
      </article>
      <article>
        <CircleAlert size={18} />
        <span>Denials</span>
        <strong>{securitySummary.denials}</strong>
        <small>No raw payloads</small>
      </article>
      <article>
        <TriangleAlert size={18} />
        <span>Stale evidence</span>
        <strong>{securitySummary.staleEvidence}</strong>
        <small>Review required</small>
      </article>
    </section>
  );
}
