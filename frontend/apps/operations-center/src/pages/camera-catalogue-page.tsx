import { Camera, CircleDot, RadioTower, TriangleAlert } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { CameraFilterRail, type CameraFilters } from "../components/camera-filter-rail";
import { StateBoundary } from "../components/state-boundary";
import { SynchronizedCameraTable } from "../components/synchronized-camera-table";
import { cameras, catalogueSummary } from "../data/camera-live-projections";

export function CameraCataloguePage() {
  const [filters, setFilters] = useState<CameraFilters>({ query: "", state: "all", zone: "all" });
  const zones = [...new Set(cameras.map((camera) => camera.zone))].sort();
  const visible = useMemo(
    () =>
      cameras.filter((camera) => {
        const query = filters.query.trim().toLowerCase();
        return (
          (filters.state === "all" || camera.state === filters.state) &&
          (filters.zone === "all" || camera.zone === filters.zone) &&
          (!query ||
            `${camera.id} ${camera.label} ${camera.shortLocation}`.toLowerCase().includes(query))
        );
      }),
    [filters],
  );
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">OPERATIONS / CAMERA NETWORK</p>
          <h1>Camera catalogue</h1>
          <p>
            Authoritative generated inventory, health, capability freshness, and diagnostics entry
            points.
          </p>
        </div>
        <Link className="primary-link" to="/operations/live">
          <RadioTower size={16} /> Open live workspace
        </Link>
      </header>
      <section className="summary-band" aria-label="Camera catalogue summary">
        <article>
          <Camera size={18} />
          <span>Configured</span>
          <strong>{catalogueSummary.total}</strong>
          <small>Generated sources</small>
        </article>
        <article>
          <CircleDot size={18} />
          <span>Online</span>
          <strong>{catalogueSummary.online}</strong>
          <small>Current projections</small>
        </article>
        <article>
          <TriangleAlert size={18} />
          <span>Attention</span>
          <strong>{catalogueSummary.attention}</strong>
          <small>Degraded sources</small>
        </article>
        <article>
          <RadioTower size={18} />
          <span>Unavailable</span>
          <strong>{catalogueSummary.unavailable}</strong>
          <small>No connection attempted</small>
        </article>
      </section>
      <div className="catalogue-layout">
        <CameraFilterRail filters={filters} zones={zones} onChange={setFilters} />
        <section className="table-panel">
          <header>
            <div>
              <span className="eyebrow">SYNCHRONIZED LIST</span>
              <h2>{visible.length} cameras</h2>
            </div>
            <span className="truth current">generated</span>
          </header>
          <StateBoundary state={catalogueSummary.viewState}>
            <SynchronizedCameraTable cameras={visible} />
          </StateBoundary>
        </section>
      </div>
    </>
  );
}
