import { useMemo, useState } from "react";
import { DependencyHealthPanel } from "../components/dependency-health-panel";
import {
  PlatformOperationsFilterRail,
  type PlatformOperationsFilters,
} from "../components/platform-operations-filter-rail";
import { PlatformOperationsPageFrame } from "../components/platform-operations-state-boundary";
import { ServiceHealthTable } from "../components/service-health-table";
import { platformServices } from "../data/platform-operations-projections";
export function ServicesDependenciesPage() {
  const [filters, setFilters] = useState<PlatformOperationsFilters>({
    query: "",
    state: "all",
    domain: "all",
  });
  const rows = useMemo(
    () =>
      platformServices.filter(
        (item) =>
          (filters.state === "all" || item.state === filters.state) &&
          (filters.domain === "all" || item.domain === filters.domain) &&
          (!filters.query || item.label.toLowerCase().includes(filters.query.toLowerCase())),
      ),
    [filters],
  );
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / SERVICES"
      title="Services and dependencies"
      description="Bounded generated service inventory with explicit state, freshness, completeness, latency, saturation, and dependency references."
    >
      <div className="platform-workspace-grid">
        <PlatformOperationsFilterRail filters={filters} onChange={setFilters} />
        <div className="platform-stack">
          <section className="panel platform-panel">
            <header>
              <div>
                <span className="eyebrow">SERVICE INVENTORY</span>
                <h2>{rows.length} generated services</h2>
              </div>
              <span className="truth partial">qualified</span>
            </header>
            <ServiceHealthTable services={rows} />
          </section>
          <DependencyHealthPanel />
        </div>
      </div>
    </PlatformOperationsPageFrame>
  );
}
