import { History, Lock } from "lucide-react";
import type { CorrectionImpact as CorrectionImpactValue } from "../../../../packages/intelligence-contracts/src";
export function CorrectionImpact({ impact }: { readonly impact: CorrectionImpactValue }) {
  return (
    <section className="panel correction-impact">
      <header>
        <div>
          <span className="eyebrow">APPEND-ONLY CORRECTION</span>
          <h2>Impact projection</h2>
        </div>
        <History size={19} />
      </header>
      <div className="correction-summary">
        <span>
          <strong>{impact.impactedRefs.length}</strong> impacted records
        </span>
        <span>
          <strong>{impact.viewsMarkedStale.length}</strong> views marked stale
        </span>
        <span>
          <Lock size={15} />
          <strong>Mutations disabled</strong>
        </span>
      </div>
      <ul>
        {impact.impactedRefs.map((ref) => (
          <li key={ref}>{ref}</li>
        ))}
      </ul>
      <footer>
        History rewritten: <strong>no</strong>. Authoritative refetch required.
      </footer>
    </section>
  );
}
