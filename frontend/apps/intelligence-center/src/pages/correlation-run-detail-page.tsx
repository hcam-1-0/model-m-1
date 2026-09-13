import { ArrowLeft, CheckCircle2, CircleDashed, Database, GitBranch } from "lucide-react";
import { Link, useParams } from "react-router";
import { queues } from "../data/intelligence-projections";
export function CorrelationRunDetailPage() {
  const { runId } = useParams();
  const item = queues.runs.items.find((entry) => entry.ref === runId) ?? queues.runs.items.at(0);
  if (!item) return <p>No generated correlation run is available.</p>;
  return (
    <>
      <Link className="back-link" to="/intelligence/runs">
        <ArrowLeft size={15} /> Correlation runs
      </Link>
      <header className="page-heading">
        <div>
          <p className="eyebrow">GENERATED CORRELATION RUN</p>
          <h1>{item.title}</h1>
          <p>{item.summary}</p>
        </div>
        <span className="priority priority-standard_review">analytical only</span>
      </header>
      <section className="run-pipeline" aria-label="Correlation stages">
        <div>
          <Database size={18} />
          <strong>Inputs normalized</strong>
          <span>generated revision 7</span>
        </div>
        <i />
        <div>
          <GitBranch size={18} />
          <strong>Relationships projected</strong>
          <span>bounded graph</span>
        </div>
        <i />
        <div>
          <CircleDashed size={18} />
          <strong>Rule abstained</strong>
          <span>partial geometry</span>
        </div>
        <i />
        <div>
          <CheckCircle2 size={18} />
          <strong>Record sealed</strong>
          <span>no side effect</span>
        </div>
      </section>
      <section className="panel definition-panel">
        <header>
          <h2>Run contract</h2>
        </header>
        <dl>
          <div>
            <dt>Run reference</dt>
            <dd>{item.ref}</dd>
          </div>
          <div>
            <dt>ETag</dt>
            <dd>{item.etag}</dd>
          </div>
          <div>
            <dt>Completeness</dt>
            <dd>{item.freshness.completeness}</dd>
          </div>
          <div>
            <dt>Operational authority</dt>
            <dd>none</dd>
          </div>
        </dl>
      </section>
    </>
  );
}
