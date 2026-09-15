import { commandFeatures, commandSnapshot } from "../data/command-projections";
import { WorkloadRail } from "../components/workload-rail";
import { CoverageHealthBand } from "../components/coverage-health-band";
export function OperationalWorkloadPage({
  title = "Operational workload",
  description = "Bounded generated work queues with no operational execution.",
}: {
  readonly title?: string;
  readonly description?: string;
}) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">AUTHORITATIVE DETAIL</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <div className="time-window">
          <span>State</span>
          <strong>Read only</strong>
        </div>
      </div>
      <div className="dashboard-grid detail-grid">
        <WorkloadRail items={commandSnapshot.workItems} />
        <CoverageHealthBand features={commandFeatures} />
      </div>
    </>
  );
}
