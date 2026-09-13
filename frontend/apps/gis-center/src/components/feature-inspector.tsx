import { Info, X } from "lucide-react";
import type { GisFeatureSummary } from "@hcam/gis-contracts";
export function FeatureInspector({
  feature,
  onClose,
}: {
  readonly feature: GisFeatureSummary | null;
  readonly onClose: () => void;
}) {
  if (!feature)
    return (
      <aside aria-label="Generated record inspector" className="inspector empty-inspector">
        <Info size={20} />
        <h2>No generated record selected</h2>
        <p>Select a map marker or a row in the authoritative table.</p>
      </aside>
    );
  return (
    <aside aria-label="Generated record inspector" className="inspector">
      <header>
        <div>
          <small>GENERATED RECORD</small>
          <h2>{feature.label}</h2>
        </div>
        <button type="button" aria-label="Close feature details" onClick={onClose}>
          <X size={17} />
        </button>
      </header>
      <dl>
        <div>
          <dt>Kind</dt>
          <dd>{feature.kind}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{feature.status}</dd>
        </div>
        <div>
          <dt>Severity</dt>
          <dd>{feature.severity}</dd>
        </div>
        <div>
          <dt>Observed</dt>
          <dd>{feature.freshness.observedAt}</dd>
        </div>
        <div>
          <dt>Completeness</dt>
          <dd>{feature.freshness.completeness}</dd>
        </div>
        <div>
          <dt>Revision</dt>
          <dd>{feature.sourceRevision}</dd>
        </div>
      </dl>
      <p className="boundary-note">
        This detail is a generated read model. No identity, media, owner record, score, or
        operational action exists.
      </p>
    </aside>
  );
}
