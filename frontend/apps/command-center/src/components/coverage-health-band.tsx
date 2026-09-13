import type { GisFeatureSummary } from "@hcam/gis-contracts";
export function CoverageHealthBand({
  features,
}: {
  readonly features: readonly GisFeatureSummary[];
}) {
  const available = features.filter((item) => item.status === "available").length;
  const unknown = features.filter((item) => item.status === "unknown").length;
  return (
    <section className="panel">
      <header>
        <div>
          <p className="eyebrow">SOURCE COVERAGE</p>
          <h2>Coverage and health</h2>
        </div>
        <span className="panel-meta">Generated projection</span>
      </header>
      <div className="bar-row">
        <span>Available</span>
        <div>
          <i style={{ width: `${available * 10}%` }} />
        </div>
        <strong>{available}</strong>
      </div>
      <div className="bar-row warning">
        <span>Unknown</span>
        <div>
          <i style={{ width: `${unknown * 10}%` }} />
        </div>
        <strong>{unknown}</strong>
      </div>
      <p className="quiet">
        No client-side coverage percentage or blind-spot conclusion is calculated.
      </p>
    </section>
  );
}
