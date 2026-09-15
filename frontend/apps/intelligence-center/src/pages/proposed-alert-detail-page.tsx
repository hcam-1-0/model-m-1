import { ArrowLeft, ShieldAlert } from "lucide-react";
import { Link, useParams } from "react-router";
import { AuthorityBadge } from "../components/authority-badge";
import { CandidateMatrix } from "../components/candidate-matrix";
import { LifecycleTimeline } from "../components/lifecycle-timeline";
import { PriorityBadge } from "../components/priority-badge";
import { alert, candidate } from "../data/intelligence-projections";
export function ProposedAlertDetailPage() {
  const { alertId } = useParams();
  const entries = [
    {
      ref: "SYN-LIFE-0001",
      at: "09:31",
      label: "Proposal created",
      detail: "Generated rule result created an analytical proposal.",
      kind: "created" as const,
    },
    {
      ref: "SYN-LIFE-0002",
      at: "09:36",
      label: "Review requested",
      detail: "Mandatory independent quorum is incomplete.",
      kind: "review" as const,
    },
  ];
  return (
    <>
      <Link className="back-link" to="/intelligence/alerts">
        <ArrowLeft size={15} /> Proposed alerts
      </Link>
      <section className="alert-heading">
        <div>
          <span className="eyebrow">PROPOSED ALERT / GENERATED</span>
          <h1>{alert.title}</h1>
          <p>
            {alertId ?? alert.ref} · semantic identity {alert.semanticIdentity}
          </p>
        </div>
        <PriorityBadge priority={alert.priority} />
        <AuthorityBadge authority="analytical_only" />
      </section>
      <section className="identity-block">
        <ShieldAlert size={21} />
        <div>
          <strong>Identity not established. No operational authority.</strong>
          <p>
            Human review can only create an append-only generated record; it cannot trigger an
            external action.
          </p>
        </div>
      </section>
      <div className="detail-grid">
        <section className="panel">
          <header>
            <h2>Lifecycle chronology</h2>
          </header>
          <LifecycleTimeline entries={entries} />
        </section>
        <section className="panel definition-panel">
          <header>
            <h2>Concurrency contract</h2>
          </header>
          <dl>
            <div>
              <dt>Revision</dt>
              <dd>{alert.revision}</dd>
            </div>
            <div>
              <dt>Strong ETag</dt>
              <dd>{alert.etag}</dd>
            </div>
            <div>
              <dt>Review policy</dt>
              <dd>SYN-POLICY-007</dd>
            </div>
            <div>
              <dt>Mutation retry</dt>
              <dd>disabled</dd>
            </div>
          </dl>
          <Link className="primary-link" to="/intelligence/review">
            Open mandatory review
          </Link>
        </section>
      </div>
      <CandidateMatrix candidate={candidate} />
    </>
  );
}
