import { Activity } from "lucide-react";
import { capacityEvidence, p56Workloads } from "../data/platform-operations-projections";
export function CapacityEvidencePanel() {
  return (
    <section className="panel platform-panel">
      <header>
        <div>
          <span className="eyebrow">FUNCTIONAL WORKLOADS</span>
          <h2>C1 / C10 / C50 evidence</h2>
        </div>
        <Activity size={20} />
      </header>
      <div className="capacity-grid">
        {capacityEvidence.map((item) => (
          <article key={item.workload}>
            <strong>{item.workload}</strong>
            <span>{item.totalSubjects} subjects</span>
            <span>{item.totalOperationalRecords} records</span>
            <small>{p56Workloads[item.workload].services} services · generated</small>
            <em>No hardware or production claim</em>
          </article>
        ))}
      </div>
    </section>
  );
}
