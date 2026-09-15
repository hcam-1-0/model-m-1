import { Filter, Search } from "lucide-react";
export interface AdminFilters {
  readonly query: string;
  readonly state: string;
}
export function AdminFilterRail({
  filters,
  onChange,
}: {
  readonly filters: AdminFilters;
  readonly onChange: (filters: AdminFilters) => void;
}) {
  return (
    <aside className="filter-rail" aria-label="Governance filters">
      <h2>
        <Filter size={16} /> Filters
      </h2>
      <label>
        <span>Search</span>
        <div className="input-with-icon">
          <Search size={15} />
          <input
            value={filters.query}
            onChange={(event) => onChange({ ...filters, query: event.target.value })}
          />
        </div>
      </label>
      <label>
        <span>State</span>
        <select
          value={filters.state}
          onChange={(event) => onChange({ ...filters, state: event.target.value })}
        >
          <option value="all">All states</option>
          <option value="current">Current</option>
          <option value="partial">Partial</option>
          <option value="stale">Stale</option>
        </select>
      </label>
      <button type="button" onClick={() => onChange({ query: "", state: "all" })}>
        Reset filters
      </button>
    </aside>
  );
}
