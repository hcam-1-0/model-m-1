import { Ban, ClipboardList } from "lucide-react";
import type { NonoperativePolicyPreview } from "../../../../packages/investigation-contracts/src";
export function PolicyPreviewSummary({ preview }: { readonly preview: NonoperativePolicyPreview }) {
  return (
    <section className="panel policy-preview">
      <header>
        <div>
          <span className="eyebrow">GENERATED / NON-OPERATIVE</span>
          <h2>{preview.policyClass} preview</h2>
        </div>
        <ClipboardList size={19} />
      </header>
      <div className="policy-identity">
        <code>{preview.policyReference}</code>
        <span className="status-chip status-partial">preview only</span>
      </div>
      <dl className="definition-grid">
        <div>
          <dt>Targets</dt>
          <dd>{preview.targets.length}</dd>
        </div>
        <div>
          <dt>Residuals</dt>
          <dd>{preview.residualCount}</dd>
        </div>
        <div>
          <dt>Completeness</dt>
          <dd>{preview.completeness}</dd>
        </div>
        <div>
          <dt>Executable</dt>
          <dd>No</dd>
        </div>
      </dl>
      <ul>
        {preview.targets.map((target) => (
          <li key={target.ref}>
            <code>{target.ref}</code>
            <span>{target.included ? "Included" : "Excluded"}</span>
            <small>{target.reasonCode}</small>
          </li>
        ))}
      </ul>
      <footer>
        <Ban size={15} /> No approve, execute, export, delete, hold, release, or retention control
        exists.
      </footer>
    </section>
  );
}
