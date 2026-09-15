import { LockKeyhole } from "lucide-react";
import type { ReviewPolicy, ReviewRecord } from "../../../../packages/intelligence-contracts/src";
import { projectQuorum } from "../../../../packages/review-workflows/src";
export function ReviewPolicyPanel({
  policy,
  reviews,
}: {
  readonly policy: ReviewPolicy;
  readonly reviews: readonly ReviewRecord[];
}) {
  const quorum = projectQuorum(policy, reviews);
  return (
    <section className="panel review-policy">
      <header>
        <div>
          <span className="eyebrow">SERVER-AUTHORITATIVE POLICY</span>
          <h2>Independent review quorum</h2>
        </div>
        <LockKeyhole size={19} />
      </header>
      <div className="quorum-meter">
        <strong>
          {quorum.approvals} / {quorum.required}
        </strong>
        <span>confirmations recorded</span>
        <progress value={quorum.approvals} max={quorum.required} />
      </div>
      <dl>
        <div>
          <dt>Policy revision</dt>
          <dd>{policy.policyRevision}</dd>
        </div>
        <div>
          <dt>Independent actors</dt>
          <dd>{quorum.independentActors}</dd>
        </div>
        <div>
          <dt>Client override</dt>
          <dd>denied</dd>
        </div>
        <div>
          <dt>Operational side effect</dt>
          <dd>none</dd>
        </div>
      </dl>
    </section>
  );
}
