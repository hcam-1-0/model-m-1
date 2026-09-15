import { ListChecks } from "lucide-react";
import { AuditReferenceTable } from "../components/audit-reference-table";
import { SecurityPageFrame } from "../components/security-state-boundary";
export function AuditReferenceExplorerPage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / AUDIT"
      title="Audit reference explorer"
      description="Sequence-ordered immutable references remain distinct from operational logs, security signals, administrative events, and evidence records."
    >
      <section className="panel">
        <header>
          <div>
            <span className="eyebrow">AUDIT LANE</span>
            <h2>Generated audit references</h2>
          </div>
          <ListChecks size={20} />
        </header>
        <AuditReferenceTable />
      </section>
    </SecurityPageFrame>
  );
}
