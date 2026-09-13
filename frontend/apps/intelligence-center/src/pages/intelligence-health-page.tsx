import { Activity, CheckCircle2, CircleAlert, DatabaseZap, ShieldCheck } from "lucide-react";
import { producerGaps } from "../data/intelligence-projections";
export function IntelligenceHealthPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INTELLIGENCE / HEALTH</p>
          <h1>Intelligence health</h1>
          <p>
            Low-cardinality generated signals, blocked producer inventory, and explicit degradation.
          </p>
        </div>
        <span className="page-icon">
          <Activity size={19} /> generated only
        </span>
      </header>
      <section className="health-summary">
        <div>
          <CheckCircle2 size={18} />
          <span>Contract validation</span>
          <strong>current</strong>
        </div>
        <div>
          <CircleAlert size={18} />
          <span>Producer integrations</span>
          <strong>{producerGaps.length} blocked</strong>
        </div>
        <div>
          <DatabaseZap size={18} />
          <span>Authoritative HTTP</span>
          <strong>simulated</strong>
        </div>
        <div>
          <ShieldCheck size={18} />
          <span>Operational actions</span>
          <strong>disabled</strong>
        </div>
      </section>
      <section className="panel producer-table">
        <header>
          <div>
            <span className="eyebrow">PRESERVED PRODUCER GAPS</span>
            <h2>Integration readiness</h2>
          </div>
          <span>{producerGaps.length} contracts</span>
        </header>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Producer contract</th>
                <th>P5.4 status</th>
                <th>Runtime</th>
              </tr>
            </thead>
            <tbody>
              {producerGaps.map((gap) => (
                <tr key={gap}>
                  <td>{gap.replaceAll("_", " ")}</td>
                  <td>
                    <span className="evidence-pill missing">generated bridge</span>
                  </td>
                  <td>blocked</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
