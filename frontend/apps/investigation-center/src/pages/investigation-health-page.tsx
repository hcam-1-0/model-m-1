import { Activity, ServerOff } from "lucide-react";
import { ConflictRecoveryPanel } from "../components/conflict-recovery-panel";
import { investigationHealth, producerGaps, threats } from "../data/investigation-projections";
export function InvestigationHealthPage() {
  const health = Object.entries(investigationHealth).filter(
    ([key]) => !["generated", "producerGapCount"].includes(key),
  );
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATION / HEALTH</p>
          <h1>Projection health</h1>
          <p>
            Low-cardinality generated status for bounded consumers, with unavailable producers and
            recovery behavior made explicit.
          </p>
        </div>
        <span className="page-icon">
          <Activity size={19} /> generated signals
        </span>
      </header>
      <section className="health-grid">
        {health.map(([key, value]) => (
          <article key={key}>
            <span>{key.replaceAll("_", " ")}</span>
            <strong>{String(value)}</strong>
            <small>HTTP authority</small>
          </article>
        ))}
      </section>
      <div className="detail-grid">
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">BLOCKED PRODUCERS</span>
              <h2>{producerGaps.length} unavailable contracts</h2>
            </div>
            <ServerOff size={19} />
          </header>
          <ul className="compact-list">
            {producerGaps.slice(0, 12).map((gap) => (
              <li key={gap}>{gap.replaceAll("_", " ")}</li>
            ))}
          </ul>
          <footer>{threats.length} documented threats remain active.</footer>
        </section>
        <ConflictRecoveryPanel />
      </div>
    </>
  );
}
