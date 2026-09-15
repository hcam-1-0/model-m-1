import { DatabaseBackup } from "lucide-react";
import { recoveryPreviews } from "../data/platform-operations-projections";
export function RecoveryPreviewPanel() {
  return (
    <section className="panel platform-panel">
      <header>
        <div>
          <span className="eyebrow">NON-OPERATIVE PREVIEW</span>
          <h2>Continuity and recovery</h2>
        </div>
        <DatabaseBackup size={20} />
      </header>
      <div className="recovery-grid">
        {recoveryPreviews.map((item) => (
          <article key={item.ref}>
            <strong>{item.class.replaceAll("_", " ")}</strong>
            <span>RPO: {item.rpo}</span>
            <span>RTO: {item.rto}</span>
            <small>{item.lastEvidenceRef ?? "No evidence reference"}</small>
            <button type="button" disabled>
              Unavailable
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
