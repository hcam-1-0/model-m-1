import { Link, useParams } from "react-router";
import { ArrowLeft, ArrowRight, Clock3, Database } from "lucide-react";
import { HypothesisSummary } from "../components/hypothesis-summary";
import { EvidenceRoleList } from "../components/evidence-role-list";
import { queues, candidate } from "../data/intelligence-projections";
export function HypothesisDetailPage() {
  const { hypothesisId } = useParams();
  const item =
    queues.hypotheses.items.find((entry) => entry.ref === hypothesisId) ??
    queues.hypotheses.items.at(0);
  if (!item) return <p>No generated hypothesis is available.</p>;
  return (
    <>
      <Link className="back-link" to="/intelligence/hypotheses">
        <ArrowLeft size={15} /> Hypothesis queue
      </Link>
      <HypothesisSummary item={item} />
      <div className="detail-grid">
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">SOURCE ROLES</span>
              <h2>Evidence composition</h2>
            </div>
            <Database size={19} />
          </header>
          <EvidenceRoleList fields={candidate.fields} />
        </section>
        <section className="panel definition-panel">
          <header>
            <div>
              <span className="eyebrow">PROJECTION STATE</span>
              <h2>Bounded detail</h2>
            </div>
            <Clock3 size={19} />
          </header>
          <dl>
            <div>
              <dt>Revision</dt>
              <dd>{item.revision}</dd>
            </div>
            <div>
              <dt>Freshness</dt>
              <dd>{item.freshness.completeness}</dd>
            </div>
            <div>
              <dt>Identity</dt>
              <dd>not established</dd>
            </div>
            <div>
              <dt>Authority</dt>
              <dd>analytical only</dd>
            </div>
          </dl>
          <Link className="primary-link" to={`/intelligence/candidates/${candidate.candidateRef}`}>
            Open candidate evidence <ArrowRight size={15} />
          </Link>
        </section>
      </div>
    </>
  );
}
