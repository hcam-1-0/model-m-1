import { Filter, Search } from "lucide-react";
export interface InvestigationFilters {
  readonly query: string;
  readonly state: string;
  readonly kind: string;
}
export function InvestigationFilterRail({
  value,
  onChange,
}: {
  readonly value: InvestigationFilters;
  readonly onChange: (value: InvestigationFilters) => void;
}) {
  return (
    <aside className="filter-rail" aria-label="Investigation filters">
      <strong>
        <Filter size={15} /> Filters
      </strong>
      <label>
        <span>Search</span>
        <span className="filter-input">
          <Search size={14} />
          <input
            value={value.query}
            onChange={(event) => onChange({ ...value, query: event.target.value })}
            aria-label="Search investigations"
          />
        </span>
      </label>
      <label>
        <span>State</span>
        <select
          value={value.state}
          onChange={(event) => onChange({ ...value, state: event.target.value })}
        >
          <option value="all">All states</option>
          <option value="open">Open</option>
          <option value="under_review">Under review</option>
          <option value="correction_pending">Correction pending</option>
          <option value="closed">Closed</option>
        </select>
      </label>
      <label>
        <span>Record type</span>
        <select
          value={value.kind}
          onChange={(event) => onChange({ ...value, kind: event.target.value })}
        >
          <option value="all">All types</option>
          <option value="observation">Observation</option>
          <option value="hypothesis">Hypothesis</option>
          <option value="correction">Correction</option>
          <option value="retraction">Retraction</option>
        </select>
      </label>
      <button type="button" onClick={() => onChange({ query: "", state: "all", kind: "all" })}>
        Clear filters
      </button>
    </aside>
  );
}
