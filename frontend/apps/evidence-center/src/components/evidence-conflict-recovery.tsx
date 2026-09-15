import { AlertTriangle, RefreshCw } from "lucide-react";

export function EvidenceConflictRecovery() {
  return (
    <section className="panel conflict-panel">
      <header>
        <div>
          <span className="eyebrow">ETAG CONFLICT</span>
          <h2>Reconsider current state</h2>
        </div>
        <AlertTriangle size={19} />
      </header>
      <div>
        <p>
          This generated revision changed after the view was opened. Automatic retry and
          last-write-wins are disabled.
        </p>
        <button type="button">
          <RefreshCw size={15} /> Refresh authoritative projection
        </button>
      </div>
    </section>
  );
}
