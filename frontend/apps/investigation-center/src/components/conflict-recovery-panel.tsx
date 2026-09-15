import { AlertCircle, RefreshCw } from "lucide-react";
export function ConflictRecoveryPanel() {
  return (
    <section className="panel conflict-panel">
      <header>
        <div>
          <span className="eyebrow">STALE MUTATION SAFETY</span>
          <h2>Conflict recovery</h2>
        </div>
        <AlertCircle size={19} />
      </header>
      <ol>
        <li>
          <strong>1</strong>
          <span>Discard the stale draft mutation</span>
        </li>
        <li>
          <strong>2</strong>
          <span>Refetch the authoritative HTTP projection</span>
        </li>
        <li>
          <strong>3</strong>
          <span>Compare revisions and visible changes</span>
        </li>
        <li>
          <strong>4</strong>
          <span>Require deliberate reconsideration</span>
        </li>
      </ol>
      <button type="button">
        <RefreshCw size={15} /> Refetch generated projection
      </button>
      <p>No automatic retry or last-write-wins behavior.</p>
    </section>
  );
}
