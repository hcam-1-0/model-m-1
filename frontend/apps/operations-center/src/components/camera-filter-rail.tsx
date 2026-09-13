import { Filter, Search } from "lucide-react";

export interface CameraFilters {
  readonly query: string;
  readonly state: string;
  readonly zone: string;
}
export function CameraFilterRail({
  filters,
  zones,
  onChange,
}: {
  readonly filters: CameraFilters;
  readonly zones: readonly string[];
  readonly onChange: (next: CameraFilters) => void;
}) {
  return (
    <form
      className="filter-rail"
      onSubmit={(event) => event.preventDefault()}
      aria-label="Camera filters"
    >
      <strong>
        <Filter size={15} /> Filters
      </strong>
      <label>
        <span>Find camera</span>
        <span className="search-field">
          <Search size={15} />
          <input
            value={filters.query}
            onChange={(event) => onChange({ ...filters, query: event.target.value })}
            placeholder="ID or location"
          />
        </span>
      </label>
      <label>
        <span>State</span>
        <select
          value={filters.state}
          onChange={(event) => onChange({ ...filters, state: event.target.value })}
        >
          <option value="all">All states</option>
          <option value="online">Online</option>
          <option value="degraded">Degraded</option>
          <option value="offline">Offline</option>
          <option value="unknown">Unknown</option>
        </select>
      </label>
      <label>
        <span>Zone</span>
        <select
          value={filters.zone}
          onChange={(event) => onChange({ ...filters, zone: event.target.value })}
        >
          <option value="all">All zones</option>
          {zones.map((zone) => (
            <option key={zone}>{zone}</option>
          ))}
        </select>
      </label>
      <button
        type="button"
        className="quiet-button"
        onClick={() => onChange({ query: "", state: "all", zone: "all" })}
      >
        Clear filters
      </button>
    </form>
  );
}
