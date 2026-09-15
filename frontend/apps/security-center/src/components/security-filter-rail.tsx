import { Filter, Search } from "lucide-react";
export interface SecurityFilters {
  readonly query: string;
  readonly state: string;
  readonly lane: string;
}
export function SecurityFilterRail({
  filters,
  onChange,
}: {
  readonly filters: SecurityFilters;
  readonly onChange: (value: SecurityFilters) => void;
}) {
  return (
    <aside className="filter-rail">
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
        <span>Lane</span>
        <select
          value={filters.lane}
          onChange={(event) => onChange({ ...filters, lane: event.target.value })}
        >
          <option value="all">All lanes</option>
          <option value="security">Security</option>
          <option value="audit">Audit</option>
          <option value="administrative">Administrative</option>
        </select>
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
    </aside>
  );
}
