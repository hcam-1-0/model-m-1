import { Activity, ShieldCheck } from "lucide-react";
import { EvidenceConflictRecovery } from "../components/evidence-conflict-recovery";
import { EvidenceLimitations } from "../components/evidence-limitations";
import { evidenceHealth, producerGaps, threats } from "../data/evidence-projections";

export function EvidenceHealthPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">GENERATED CONTRACT HEALTH</p>
          <h1>Evidence workspace health</h1>
          <p>
            Static projection health, preserved producer gaps, and bounded threat inventory. This is
            not operational telemetry.
          </p>
        </div>
      </header>
      <section className="health-grid">
        {Object.entries(evidenceHealth)
          .filter(([key]) => key !== "generated")
          .map(([key, value]) => (
            <article key={key}>
              <span>{key.replaceAll("_", " ")}</span>
              <strong>{String(value).replaceAll("_", " ")}</strong>
              <small>
                {key === "producerGapCount" ? "unavailable producers" : "generated projection"}
              </small>
            </article>
          ))}
        <article>
          <span>Threat cases</span>
          <strong>{threats.length}</strong>
          <small>documented and generated</small>
        </article>
      </section>
      <section className="panel section-gap">
        <header>
          <div>
            <span className="eyebrow">PRODUCER BOUNDARY</span>
            <h2>Unavailable producer contracts</h2>
          </div>
          <Activity size={18} />
        </header>
        <div className="gap-list">
          {producerGaps.map((gap) => (
            <span key={gap}>
              <ShieldCheck size={13} /> {gap.replaceAll("_", " ")}
            </span>
          ))}
        </div>
      </section>
      <EvidenceConflictRecovery />
      <EvidenceLimitations
        limitations={[
          "Health values are generated validation projections, not production SLO measurements.",
        ]}
      />
    </>
  );
}
