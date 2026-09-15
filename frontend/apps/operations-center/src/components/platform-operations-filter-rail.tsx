import { Filter, Search } from "lucide-react";
export interface PlatformOperationsFilters {
  readonly query: string;
  readonly state: string;
  readonly domain: string;
}
export function PlatformOperationsFilterRail({
  filters,
  onChange,
}: {
  readonly filters: PlatformOperationsFilters;
  readonly onChange: (value: PlatformOperationsFilters) => void;
}) {
  return (
    <aside className="platform-filter-rail" aria-label="Platform operations filters">
      <h2>
        <Filter size={16} /> Filters
      </h2>
      <label>
        <span>Search</span>
        <div>
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
          <option value="healthy">Healthy</option>
          <option value="degraded">Degraded</option>
          <option value="stale">Stale</option>
          <option value="unknown">Unknown</option>
        </select>
      </label>
      <label>
        <span>Domain</span>
        <select
          value={filters.domain}
          onChange={(event) => onChange({ ...filters, domain: event.target.value })}
        >
          <option value="all">All domains</option>
          <option value="camera">Camera</option>
          <option value="intelligence">Intelligence</option>
          <option value="evidence">Evidence</option>
          <option value="platform">Platform</option>
        </select>
      </label>
    </aside>
  );
}
