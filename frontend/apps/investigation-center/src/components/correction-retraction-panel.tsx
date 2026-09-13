import { GitCommitHorizontal, RotateCcw } from "lucide-react";
import type { CorrectionRetractionRecord } from "../../../../packages/investigation-contracts/src";
export function CorrectionRetractionPanel({
  record,
}: {
  readonly record: CorrectionRetractionRecord;
}) {
  return (
    <section className="panel correction-panel">
      <header>
        <div>
          <span className="eyebrow">APPEND-ONLY CHANGE</span>
          <h2>{record.kind === "correction" ? "Correction" : "Retraction"}</h2>
        </div>
        <RotateCcw size={19} />
      </header>
      <div className="lineage">
        <div>
          <span>Predecessor retained</span>
          <code>{record.predecessorRef}</code>
        </div>
        <GitCommitHorizontal size={28} />
        <div>
          <span>Successor appended</span>
          <code>{record.successorRef}</code>
        </div>
      </div>
      <dl className="definition-grid">
        <div>
          <dt>Reason</dt>
          <dd>{record.reasonCode}</dd>
        </div>
        <div>
          <dt>Recorded</dt>
          <dd>{record.recordedAt}</dd>
        </div>
        <div>
          <dt>History rewritten</dt>
          <dd>No</dd>
        </div>
        <div>
          <dt>Impact targets</dt>
          <dd>{record.impactTargets.length}</dd>
        </div>
      </dl>
    </section>
  );
}
