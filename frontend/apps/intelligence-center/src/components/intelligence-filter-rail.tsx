import { Filter, Search } from "lucide-react";
export interface IntelligenceFilters {
  readonly query: string;
  readonly state: string;
  readonly priority: string;
}
export function IntelligenceFilterRail({
  value,
  onChange,
}: {
  readonly value: IntelligenceFilters;
  readonly onChange: (value: IntelligenceFilters) => void;
}) {
  return (
    <aside className="filter-rail" aria-label="Queue filters">
      <strong>
        <Filter size={15} /> Filters
      </strong>
      <label>
        <span>Search</span>
        <div>
          <Search size={14} />
          <input
            value={value.query}
            onChange={(event) => onChange({ ...value, query: event.target.value })}
            placeholder="Generated reference"
          />
        </div>
      </label>
      <label>
        <span>State</span>
        <select
          value={value.state}
          onChange={(event) => onChange({ ...value, state: event.target.value })}
        >
          <option value="all">All states</option>
          <option value="awaiting_review">Awaiting review</option>
          <option value="partial">Partial</option>
          <option value="correction_pending">Correction pending</option>
        </select>
      </label>
      <label>
        <span>Priority</span>
        <select
          value={value.priority}
          onChange={(event) => onChange({ ...value, priority: event.target.value })}
        >
          <option value="all">All priorities</option>
          <option value="urgent_review">Urgent review</option>
          <option value="elevated_review">Elevated review</option>
          <option value="standard_review">Standard review</option>
          <option value="unknown">Unknown</option>
        </select>
      </label>
      <button
        className="quiet-button"
        type="button"
        onClick={() => onChange({ query: "", state: "all", priority: "all" })}
      >
        Clear filters
      </button>
    </aside>
  );
}
