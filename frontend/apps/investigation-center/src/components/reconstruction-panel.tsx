import { Box, CircleAlert, History } from "lucide-react";
import type { ReconstructionProjection } from "../../../../packages/investigation-contracts/src";
export function ReconstructionPanel({ value }: { readonly value: ReconstructionProjection }) {
  return (
    <section className="panel reconstruction-panel">
      <header>
        <div>
          <span className="eyebrow">EXACT SERVER REVISION</span>
          <h2>Reconstruction {value.resolvedRevision}</h2>
        </div>
        <History size={19} />
      </header>
      <div className="revision-identity">
        <span>
          <Box size={15} /> Digest
        </span>
        <code>{value.digest.slice(0, 26)}...</code>
        <span className={`status-chip status-${value.completeness}`}>{value.completeness}</span>
      </div>
      {value.laterChangesExist ? (
        <p className="warning-line">
          <CircleAlert size={15} /> Later records exist and are not included in this revision.
        </p>
      ) : null}
      <dl className="definition-grid">
        <div>
          <dt>Included</dt>
          <dd>{value.includedComponents.join(", ")}</dd>
        </div>
        <div>
          <dt>Omitted</dt>
          <dd>
            {value.omittedComponents.length ? value.omittedComponents.join(", ") : "None declared"}
          </dd>
        </div>
        <div>
          <dt>Limitations</dt>
          <dd>{value.limitations.join(" ")}</dd>
        </div>
        <div>
          <dt>Timeline records</dt>
          <dd>{value.timeline.length}</dd>
        </div>
      </dl>
    </section>
  );
}
