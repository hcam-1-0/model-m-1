import { ShieldCheck } from "lucide-react";
import { AccessAssuranceMatrix } from "../components/access-assurance-matrix";
import { SecurityPageFrame, SecurityStateBoundary } from "../components/security-state-boundary";
export function AccessAssurancePage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / ACCESS"
      title="Access assurance"
      description="Application authorization and PostgreSQL row-security equivalence are independently projected with default-deny outcomes."
    >
      <SecurityStateBoundary state="ready">
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">EQUIVALENCE MATRIX</span>
              <h2>Authorization boundaries</h2>
            </div>
            <ShieldCheck size={20} />
          </header>
          <AccessAssuranceMatrix />
        </section>
      </SecurityStateBoundary>
    </SecurityPageFrame>
  );
}
