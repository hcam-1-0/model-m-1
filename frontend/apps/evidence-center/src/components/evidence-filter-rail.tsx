import { Filter, Search } from "lucide-react";

export function EvidenceFilterRail() {
  return (
    <form className="filter-rail" onSubmit={(event) => event.preventDefault()}>
      <label>
        Search references
        <span className="search-field">
          <Search size={15} />
          <input type="search" placeholder="Generated reference" />
        </span>
      </label>
      <label>
        Integrity
        <select defaultValue="all">
          <option value="all">All states</option>
          <option>Digest observed</option>
          <option>Digest mismatch</option>
          <option>Not checked</option>
        </select>
      </label>
      <label>
        Access
        <select defaultValue="all">
          <option value="all">All access states</option>
          <option>Allowed</option>
          <option>Denied</option>
          <option>Unknown</option>
        </select>
      </label>
      <span className="filter-summary">
        <Filter size={15} /> Server-side projection, generated locally
      </span>
    </form>
  );
}
