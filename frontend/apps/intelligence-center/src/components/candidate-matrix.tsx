import { ShieldQuestion } from "lucide-react";
import type { CandidateEvidence } from "../../../../packages/intelligence-contracts/src";
export function CandidateMatrix({ candidate }: { readonly candidate: CandidateEvidence }) {
  return (
    <section className="panel candidate-panel">
      <header>
        <div>
          <span className="eyebrow">FIELD-LEVEL COMPARISON</span>
          <h2>Candidate evidence matrix</h2>
        </div>
        <span className="identity-warning">
          <ShieldQuestion size={15} /> Identity not established
        </span>
      </header>
      <div className="table-scroll" tabIndex={0} aria-label="Scrollable candidate evidence table">
        <table className="candidate-table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
              <th>Role</th>
              <th>Confidence</th>
              <th>Calibration</th>
              <th>Freshness</th>
            </tr>
          </thead>
          <tbody>
            {candidate.fields.map((field) => (
              <tr key={field.field}>
                <td>
                  <strong>{field.field}</strong>
                  <small>{field.provenanceRef}</small>
                </td>
                <td>
                  {field.displayValue}
                  <small>{field.limitation}</small>
                </td>
                <td>
                  <span className={`evidence-pill ${field.role}`}>{field.role}</span>
                </td>
                <td>{field.confidenceBand}</td>
                <td>{field.calibrated ? "calibrated" : "not calibrated"}</td>
                <td>{field.stale ? "stale" : "current"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <footer>
        Comparison abstained: <strong>{candidate.abstained ? "yes" : "no"}</strong>. No candidate
        establishes identity.
      </footer>
    </section>
  );
}
