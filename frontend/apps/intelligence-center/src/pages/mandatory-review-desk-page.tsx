import { useState } from "react";
import { CheckCircle2, ClipboardCheck, ShieldCheck } from "lucide-react";
import type { ReviewOutcome } from "../../../../packages/intelligence-contracts/src";
import { ReviewPolicyPanel } from "../components/review-policy-panel";
import { ReviewConfirmationDialog } from "../components/review-confirmation-dialog";
import { CandidateMatrix } from "../components/candidate-matrix";
import { alert, candidate, reviewPolicy, reviews } from "../data/intelligence-projections";
export function MandatoryReviewDeskPage() {
  const [dialog, setDialog] = useState(false);
  const [receipt, setReceipt] = useState<string | null>(null);
  const confirm = (outcome: ReviewOutcome, reason: string) => {
    setReceipt(`SYN-RECEIPT-${outcome.toUpperCase()}-${reason.toUpperCase()}`);
    setDialog(false);
  };
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INTELLIGENCE / HUMAN REVIEW</p>
          <h1>Mandatory review desk</h1>
          <p>
            Independent, server-authoritative review with explicit confirmation and conflict-safe
            reconsideration.
          </p>
        </div>
        <span className="page-icon">
          <ClipboardCheck size={19} /> 1 selected
        </span>
      </header>
      {receipt ? (
        <section className="receipt-banner" role="status">
          <CheckCircle2 size={20} />
          <div>
            <strong>Generated review receipt recorded</strong>
            <span>{receipt}</span>
          </div>
          <small>No external side effects</small>
        </section>
      ) : null}
      <div className="review-layout">
        <section className="review-workspace">
          <section className="selected-record">
            <div>
              <span className="eyebrow">SELECTED PROPOSAL</span>
              <h2>{alert.title}</h2>
              <p>
                {alert.ref} · revision {alert.revision} · {alert.etag}
              </p>
            </div>
            <span className="identity-warning">Identity not established</span>
          </section>
          <CandidateMatrix candidate={candidate} />
          <section className="review-actions">
            <div>
              <ShieldCheck size={19} />
              <span>
                <strong>Ready for explicit review</strong>
                <small>Draft remains memory-only and is purged on authority transitions.</small>
              </span>
            </div>
            <button className="primary-action" type="button" onClick={() => setDialog(true)}>
              Review generated proposal
            </button>
          </section>
        </section>
        <ReviewPolicyPanel policy={reviewPolicy} reviews={reviews} />
      </div>
      {dialog ? (
        <ReviewConfirmationDialog
          alertRef={alert.ref}
          onClose={() => setDialog(false)}
          onConfirm={confirm}
        />
      ) : null}
    </>
  );
}
