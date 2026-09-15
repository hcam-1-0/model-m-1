import { ShieldX } from "lucide-react";
import { PolicyPreviewSummary } from "../components/policy-preview-summary";
import { policyPreview } from "../data/investigation-projections";
export function PolicyPreviewsPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATION / POLICY PREVIEW</p>
          <h1>Non-operative policy preview</h1>
          <p>
            Generated inclusion, exclusion, conflicts, residuals, completeness, and limitations
            without any policy execution control.
          </p>
        </div>
        <span className="page-icon">
          <ShieldX size={19} /> actions disabled
        </span>
      </header>
      <PolicyPreviewSummary preview={policyPreview} />
      <section className="panel disabled-bridges">
        <header>
          <h2>Disabled bridges</h2>
        </header>
        <div>
          <strong>Case-management bridge</strong>
          <span>Disabled; no real case-system operation.</span>
        </div>
        <div>
          <strong>External PROV interchange</strong>
          <span>Generated lossy projection only; no import or conformance claim.</span>
        </div>
      </section>
    </>
  );
}
