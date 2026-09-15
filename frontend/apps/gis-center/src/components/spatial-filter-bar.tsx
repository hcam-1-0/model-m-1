import { Filter, LocateFixed, Search } from "lucide-react";
export function SpatialFilterBar({
  query,
  onQuery,
  sourceState,
  onSourceState,
  onFit,
}: {
  readonly query: string;
  readonly onQuery: (value: string) => void;
  readonly sourceState: "all" | "available" | "unavailable" | "unknown";
  readonly onSourceState: (value: "all" | "available" | "unavailable" | "unknown") => void;
  readonly onFit: () => void;
}) {
  return (
    <div className="filter-bar">
      <label>
        <Search size={16} />
        <span className="sr-only">Filter generated map records</span>
        <input
          value={query}
          onChange={(event) => onQuery(event.currentTarget.value)}
          placeholder="Filter generated records"
        />
      </label>
      <label className="source-filter">
        <Filter size={16} />
        <span className="sr-only">Filter source state</span>
        <select
          value={sourceState}
          aria-label="Filter source state"
          onChange={(event) =>
            onSourceState(
              event.currentTarget.value as "all" | "available" | "unavailable" | "unknown",
            )
          }
        >
          <option value="all">All source states</option>
          <option value="available">Available</option>
          <option value="unavailable">Unavailable</option>
          <option value="unknown">Unknown</option>
        </select>
      </label>
      <button type="button" onClick={onFit}>
        <LocateFixed size={16} />
        Fit generated extent
      </button>
    </div>
  );
}
