import { situationState } from "@hcam/command-domain";
import { ActivityTimeline } from "../components/activity-timeline";
import { CommandGisPanel } from "../components/command-gis-panel";
import { CoverageHealthBand } from "../components/coverage-health-band";
import { SourceStatusStrip } from "../components/source-status-strip";
import { StateBoundary } from "../components/state-boundary";
import { SummaryBand } from "../components/summary-band";
import { WorkloadRail } from "../components/workload-rail";
import { commandFeatures, commandSnapshot, generatedClock } from "../data/command-projections";
export function OverviewPage() {
  const state = situationState(commandSnapshot, generatedClock);
  return (
    <StateBoundary state={state}>
      <div className="page-heading">
        <div>
          <p className="eyebrow">SITUATIONAL AWARENESS</p>
          <h1>Command overview</h1>
          <p>
            Authoritative generated projections for review, coverage, platform state, and
            chronology.
          </p>
        </div>
        <div className="time-window">
          <span>Window</span>
          <strong>Last 60 minutes</strong>
        </div>
      </div>
      <SourceStatusStrip />
      <SummaryBand metrics={commandSnapshot.metrics} />
      <div className="dashboard-grid">
        <CommandGisPanel features={commandFeatures} />
        <WorkloadRail items={commandSnapshot.workItems} />
        <CoverageHealthBand features={commandFeatures} />
        <ActivityTimeline activity={commandSnapshot.activity} />
      </div>
    </StateBoundary>
  );
}
