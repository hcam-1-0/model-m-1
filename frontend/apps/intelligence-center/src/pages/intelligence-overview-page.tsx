import {
  ArrowRight,
  BrainCircuit,
  CircleAlert,
  GitPullRequestArrow,
  ShieldCheck,
} from "lucide-react";
import { Link } from "react-router";
import { WorkloadStrip } from "../components/workload-strip";
import { QueueTable } from "../components/queue-table";
import { queues, producerGaps } from "../data/intelligence-projections";
export function IntelligenceOverviewPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INTELLIGENCE / SITUATIONAL ANALYSIS</p>
          <h1>Intelligence overview</h1>
          <p>
            Generated analytical workload with explicit truth boundaries, mandatory review, and no
            operational side effects.
          </p>
        </div>
        <Link className="primary-link" to="/intelligence/review">
          <ShieldCheck size={16} /> Open review desk
        </Link>
      </header>
      <WorkloadStrip />
      <div className="overview-grid">
        <section className="panel overview-queues">
          <header>
            <div>
              <span className="eyebrow">SERVER-ORDERED WORK</span>
              <h2>Priority intelligence queue</h2>
            </div>
            <Link to="/intelligence/hypotheses">
              All hypotheses <ArrowRight size={15} />
            </Link>
          </header>
          <QueueTable
            items={queues.hypotheses.items.slice(0, 5)}
            detailBase="/intelligence/hypotheses"
          />
        </section>
        <section className="panel truth-ladder">
          <header>
            <div>
              <span className="eyebrow">ANALYTICAL TRUTH</span>
              <h2>Authority boundary</h2>
            </div>
            <BrainCircuit size={19} />
          </header>
          <ol>
            <li>
              <CircleAlert size={15} />
              <div>
                <strong>Observation</strong>
                <span>Generated source report</span>
              </div>
            </li>
            <li>
              <GitPullRequestArrow size={15} />
              <div>
                <strong>Inference and hypothesis</strong>
                <span>Analytical only</span>
              </div>
            </li>
            <li>
              <ShieldCheck size={15} />
              <div>
                <strong>Independent human review</strong>
                <span>For record, never enforcement</span>
              </div>
            </li>
          </ol>
          <footer>Identity not established across all generated candidates.</footer>
        </section>
      </div>
      <section className="producer-gap">
        <strong>{producerGaps.length} producer integrations remain blocked</strong>
        <span>
          The UI uses deterministic generated projections; no API, provider, camera, or model
          connection is implied.
        </span>
      </section>
    </>
  );
}
