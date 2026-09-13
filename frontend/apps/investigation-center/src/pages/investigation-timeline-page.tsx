import { useState } from "react";
import { Clock3 } from "lucide-react";
import { timelineState } from "../../../../packages/investigation-domain/src";
import { ChronologySwitcher } from "../components/chronology-switcher";
import { InvestigationStateBoundary } from "../components/investigation-state-boundary";
import { TimelineTable } from "../components/timeline-table";
import { TimelineVisualLane } from "../components/timeline-visual-lane";
import {
  eventContextTimeline,
  recordTimeline,
  timelinePage,
} from "../data/investigation-projections";
export function InvestigationTimelinePage() {
  const [mode, setMode] = useState<"record" | "event_context">("record");
  const projection = mode === "record" ? recordTimeline : eventContextTimeline;
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATION / TIMELINE</p>
          <h1>Typed investigation timeline</h1>
          <p>
            Record sequence is authoritative. Event-time mode is a qualified analytical context and
            never rewrites order.
          </p>
        </div>
        <ChronologySwitcher mode={mode} onChange={setMode} />
      </header>
      {projection.warning ? (
        <div className="context-warning">
          <Clock3 size={16} /> {projection.warning}
        </div>
      ) : null}
      <InvestigationStateBoundary state={timelineState(timelinePage)}>
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">BOUNDED PAGE</span>
              <h2>Visual chronology</h2>
            </div>
            <code>{timelinePage.stableAnchor}</code>
          </header>
          <TimelineVisualLane entries={projection.entries} />
        </section>
        <section className="panel table-panel">
          <header>
            <div>
              <span className="eyebrow">AUTHORITATIVE REPRESENTATION</span>
              <h2>Semantic record table</h2>
            </div>
            <span>through seq {timelinePage.completeThroughSequence}</span>
          </header>
          <TimelineTable entries={projection.entries} />
        </section>
      </InvestigationStateBoundary>
    </>
  );
}
