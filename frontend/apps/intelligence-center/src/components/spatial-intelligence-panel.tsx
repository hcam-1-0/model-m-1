import { MapPin } from "lucide-react";
import type { SpatialProjection } from "../../../../packages/intelligence-contracts/src";
export function SpatialIntelligencePanel({
  projection,
  selected,
  onSelect,
}: {
  readonly projection: SpatialProjection;
  readonly selected: string | null;
  readonly onSelect: (ref: string) => void;
}) {
  return (
    <section className="panel spatial-panel">
      <header>
        <div>
          <span className="eyebrow">GENERATED SPATIAL PROJECTION</span>
          <h2>Zone intelligence</h2>
        </div>
        <span>
          <MapPin size={16} /> no tile network
        </span>
      </header>
      <div
        className="spatial-grid"
        role="img"
        aria-label={`${projection.records.length} generated spatial records. The synchronized table is authoritative.`}
      >
        {projection.records.map((record, index) => (
          <button
            type="button"
            key={record.ref}
            aria-pressed={selected === record.ref}
            onClick={() => onSelect(record.ref)}
            style={{
              left: `${12 + (index % 5) * 18}%`,
              top: `${18 + Math.floor(index / 5) * 46}%`,
            }}
          >
            <MapPin size={20} />
            <span>{index + 1}</span>
          </button>
        ))}
        <i aria-hidden="true" />
        <b aria-hidden="true" />
      </div>
      <div className="table-scroll">
        <table>
          <caption>Authoritative generated spatial records</caption>
          <thead>
            <tr>
              <th>Record</th>
              <th>Zone</th>
              <th>Concept</th>
              <th>State</th>
            </tr>
          </thead>
          <tbody>
            {projection.records.map((record) => (
              <tr
                key={record.ref}
                className={selected === record.ref ? "selected" : undefined}
                onClick={() => onSelect(record.ref)}
              >
                <td>
                  {record.label}
                  <small>{record.ref}</small>
                </td>
                <td>{record.zoneRef}</td>
                <td>{record.concept}</td>
                <td>{record.state}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
