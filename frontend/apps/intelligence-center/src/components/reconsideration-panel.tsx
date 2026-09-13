import { RefreshCcw } from "lucide-react";
import type { Reconsideration } from "../../../../packages/review-workflows/src";
export function ReconsiderationPanel({
  value,
  onConfirm,
}: {
  readonly value: Reconsideration;
  readonly onConfirm: () => void;
}) {
  return (
    <section className="reconsideration" role="alert">
      <RefreshCcw size={20} />
      <div>
        <strong>Authoritative state changed</strong>
        <p>
          Revision {value.priorRevision} is now {value.currentRevision}. Review changed fields
          before creating a new decision.
        </p>
        <ul>
          {value.changedFields.map((field) => (
            <li key={field}>{field}</li>
          ))}
        </ul>
      </div>
      <button type="button" onClick={onConfirm}>
        Acknowledge and reconsider
      </button>
    </section>
  );
}
