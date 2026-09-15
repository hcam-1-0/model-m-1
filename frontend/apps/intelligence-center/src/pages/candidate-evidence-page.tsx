import { ArrowLeft, ShieldQuestion } from "lucide-react";
import { Link, useParams } from "react-router";
import { CandidateMatrix } from "../components/candidate-matrix";
import { ContradictionPanel } from "../components/contradiction-panel";
import { candidate } from "../data/intelligence-projections";
export function CandidateEvidencePage() {
  const { candidateId } = useParams();
  return (
    <>
      <Link className="back-link" to="/intelligence/hypotheses">
        <ArrowLeft size={15} /> Hypotheses
      </Link>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS / CANDIDATE EVIDENCE</p>
          <h1>Candidate comparison</h1>
          <p>
            {candidateId ?? candidate.candidateRef} is an analytical comparison, not a confirmed
            identity.
          </p>
        </div>
        <span className="identity-warning">
          <ShieldQuestion size={17} /> Identity not established
        </span>
      </header>
      <CandidateMatrix candidate={candidate} />
      <div className="detail-grid">
        <ContradictionPanel candidate={candidate} />
        <section className="panel definition-panel">
          <header>
            <h2>Decision boundary</h2>
          </header>
          <dl>
            <div>
              <dt>Abstention</dt>
              <dd>mandatory</dd>
            </div>
            <div>
              <dt>Missing fields</dt>
              <dd>visible</dd>
            </div>
            <div>
              <dt>Calibration</dt>
              <dd>field-level</dd>
            </div>
            <div>
              <dt>Operational action</dt>
              <dd>prohibited</dd>
            </div>
          </dl>
        </section>
      </div>
    </>
  );
}
