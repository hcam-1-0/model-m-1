import { useState } from "react";
import { Check, X } from "lucide-react";
import { Button, IconButton, ModalDialog } from "@hcam/ui";
import type { ReviewOutcome } from "../../../../packages/intelligence-contracts/src";
import { reviewReasonCodes, reviewReasonLabel } from "../../../../packages/intelligence-domain/src";
export function ReviewConfirmationDialog({
  alertRef,
  onClose,
  onConfirm,
}: {
  readonly alertRef: string;
  readonly onClose: () => void;
  readonly onConfirm: (outcome: ReviewOutcome, reason: string) => void;
}) {
  const [outcome, setOutcome] = useState<ReviewOutcome>("abstain");
  const [reason, setReason] = useState<string>("operator_abstained");
  return (
    <ModalDialog title="Confirm review record" onClose={onClose}>
      <form
        className="review-dialog"
        onSubmit={(event) => {
          event.preventDefault();
          onConfirm(outcome, reason);
        }}
      >
        <header>
          <div>
            <span className="eyebrow">GENERATED RECORD ONLY</span>
            <h2>Confirm review decision</h2>
          </div>
          <IconButton label="Close review confirmation" onClick={onClose}>
            <X size={18} />
          </IconButton>
        </header>
        <p>
          This append-only decision cannot trigger notification, dispatch, enforcement, or another
          external action.
        </p>
        <dl>
          <div>
            <dt>Proposed alert</dt>
            <dd>{alertRef}</dd>
          </div>
          <div>
            <dt>Concurrency</dt>
            <dd>ETag + revision + idempotency</dd>
          </div>
        </dl>
        <label>
          Outcome
          <select
            value={outcome}
            onChange={(event) => setOutcome(event.target.value as ReviewOutcome)}
          >
            <option value="confirm_for_record">Confirm for generated record</option>
            <option value="reject">Reject proposal</option>
            <option value="abstain">Abstain</option>
            <option value="request_more_context">Request more context</option>
          </select>
        </label>
        <label>
          Reason
          <select value={reason} onChange={(event) => setReason(event.target.value)}>
            {reviewReasonCodes.map((code) => (
              <option key={code} value={code}>
                {reviewReasonLabel(code)}
              </option>
            ))}
          </select>
        </label>
        <footer>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" type="submit">
            <Check size={16} /> Record generated review
          </Button>
        </footer>
      </form>
    </ModalDialog>
  );
}
