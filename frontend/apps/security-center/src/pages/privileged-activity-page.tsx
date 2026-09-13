import { UserRoundCheck } from "lucide-react";
import { AuditReferenceTable } from "../components/audit-reference-table";
import { SecurityPageFrame } from "../components/security-state-boundary";
export function PrivilegedActivityPage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / PRIVILEGED ACTIVITY"
      title="Privileged activity"
      description="Append-only generated references for administrative review; no break-glass path and no direct control surface."
    >
      <section className="panel">
        <header>
          <div>
            <span className="eyebrow">ATTRIBUTABLE HISTORY</span>
            <h2>Privileged review references</h2>
          </div>
          <UserRoundCheck size={20} />
        </header>
        <AuditReferenceTable />
      </section>
    </SecurityPageFrame>
  );
}
