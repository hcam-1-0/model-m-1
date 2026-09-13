import { Ban, FileWarning } from "lucide-react";
import { EvidenceLimitations } from "../components/evidence-limitations";
import { policyPreviews } from "../data/evidence-projections";

export function EvidencePolicyPreviewPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">NON-OPERATIVE POLICY PROJECTIONS</p>
          <h1>Evidence policy previews</h1>
          <p>
            Generated previews expose scope, conflicts, residual counts, and limitations without
            selecting or executing legal or retention policy.
          </p>
        </div>
      </header>
      <section className="policy-grid">
        {policyPreviews.map((preview) => (
          <article className="panel policy-preview" key={preview.ref}>
            <header>
              <div>
                <span className="eyebrow">{preview.policyClass.replaceAll("_", " ")}</span>
                <h2>{preview.policyReference}</h2>
              </div>
              <Ban size={18} />
            </header>
            <dl>
              <div>
                <dt>Completeness</dt>
                <dd>{preview.completeness}</dd>
              </div>
              <div>
                <dt>Targets</dt>
                <dd>{preview.targets.length}</dd>
              </div>
              <div>
                <dt>Residual</dt>
                <dd>{preview.residualCount}</dd>
              </div>
              <div>
                <dt>Execution</dt>
                <dd>Disabled</dd>
              </div>
            </dl>
            <footer>
              <FileWarning size={14} /> {preview.limitations.join(" ")}
            </footer>
          </article>
        ))}
      </section>
      <EvidenceLimitations
        limitations={[
          "No retention, hold, deletion, disposition, or export operation is available.",
        ]}
      />
    </>
  );
}
