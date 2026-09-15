import type { ResourceId } from "@hcam/contracts";
import type { GisFeatureSummary } from "@hcam/gis-contracts";
export function AccessibleFeatureTable({
  features,
  selected,
  onSelect,
}: {
  readonly features: readonly GisFeatureSummary[];
  readonly selected: ResourceId | null;
  readonly onSelect: (id: ResourceId) => void;
}) {
  return (
    <section className="feature-table">
      <header>
        <div>
          <small>AUTHORITATIVE MAP ALTERNATIVE</small>
          <h2>Generated spatial records</h2>
        </div>
        <span>{features.length} records</span>
      </header>
      <div>
        <table>
          <thead>
            <tr>
              <th>Record</th>
              <th>Kind</th>
              <th>Status</th>
              <th>Completeness</th>
              <th>Revision</th>
            </tr>
          </thead>
          <tbody>
            {features.map((feature) => (
              <tr key={feature.id} className={selected === feature.id ? "selected" : undefined}>
                <td>
                  <button type="button" onClick={() => onSelect(feature.id)}>
                    {feature.label}
                  </button>
                </td>
                <td>{feature.kind}</td>
                <td>
                  <span className={`record-status ${feature.status}`}>{feature.status}</span>
                </td>
                <td>{feature.freshness.completeness}</td>
                <td>{feature.sourceRevision}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
