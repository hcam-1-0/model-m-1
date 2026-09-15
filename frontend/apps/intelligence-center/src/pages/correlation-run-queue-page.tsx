import { Workflow } from "lucide-react";
import { QueueTable } from "../components/queue-table";
import { queues } from "../data/intelligence-projections";
export function CorrelationRunQueuePage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS / CORRELATION</p>
          <h1>Correlation run queue</h1>
          <p>
            Bounded generated runs with explicit source revision, freshness, and completion state.
          </p>
        </div>
        <span className="page-icon">
          <Workflow size={20} /> deterministic
        </span>
      </header>
      <section className="panel table-panel">
        <header>
          <div>
            <span className="eyebrow">SEPARATE TYPED QUEUE</span>
            <h2>Correlation runs</h2>
          </div>
          <span>server ordered</span>
        </header>
        <QueueTable items={queues.runs.items} detailBase="/intelligence/runs" />
      </section>
    </>
  );
}
