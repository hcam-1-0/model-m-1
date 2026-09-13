import { AlertTriangle } from "lucide-react";
import { CorrectionImpact } from "../components/correction-impact";
import { LifecycleTimeline } from "../components/lifecycle-timeline";
import { correction } from "../data/intelligence-projections";
export function CorrectionsPage() {
  const entries = [
    {
      ref: "SYN-LIFE-0001",
      at: "09:31",
      label: "Original proposal retained",
      detail: "Historical record remains byte-for-byte attributable.",
      kind: "created" as const,
    },
    {
      ref: "SYN-CORRECTION-0001",
      at: "09:44",
      label: "Correction appended",
      detail: "Impacted views marked stale and mutation disabled.",
      kind: "correction" as const,
    },
    {
      ref: "SYN-RECONSIDER-0001",
      at: "09:45",
      label: "Reconsideration required",
      detail: "A new review may follow authoritative refetch.",
      kind: "reconsideration" as const,
    },
  ];
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INTELLIGENCE / CORRECTIONS</p>
          <h1>Corrections and reconsideration</h1>
          <p>
            Append-only correction records propagate staleness without rewriting prior decisions.
          </p>
        </div>
        <span className="page-icon">
          <AlertTriangle size={19} /> mutations held
        </span>
      </header>
      <div className="detail-grid">
        <CorrectionImpact impact={correction} />
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">CHRONOLOGY</span>
              <h2>Attributable history</h2>
            </div>
          </header>
          <LifecycleTimeline entries={entries} />
        </section>
      </div>
    </>
  );
}
