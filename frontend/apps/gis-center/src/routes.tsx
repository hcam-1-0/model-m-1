import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router";
import { AlertsInvestigationsPage } from "./pages/alerts-investigations-page";
import { CameraGeographyPage } from "./pages/camera-geography-page";
import { CoveragePage } from "./pages/coverage-page";
import { DataRendererHealthPage } from "./pages/data-renderer-health-page";
import { LayerCataloguePage } from "./pages/layer-catalogue-page";
import { MovementTimePage } from "./pages/movement-time-page";
import { OverviewPage } from "./pages/overview-page";
import { SpatialWorkspacesPage } from "./pages/spatial-workspaces-page";

const OperationalMapPage = lazy(() =>
  import("./pages/operational-map-page").then((module) => ({
    default: module.OperationalMapPage,
  })),
);

function OperationalMapRoute() {
  return (
    <Suspense
      fallback={
        <div className="gis-route-loading" role="status" aria-live="polite">
          Loading operational map
        </div>
      }
    >
      <OperationalMapPage />
    </Suspense>
  );
}
export const gisRoutes = [
  ["/gis", "GIS overview"],
  ["/gis/map", "Operational map"],
  ["/gis/cameras", "Camera geography"],
  ["/gis/coverage", "Coverage"],
  ["/gis/layers", "Layer catalogue"],
  ["/gis/time", "Movement & time"],
  ["/gis/review", "Alerts & investigations"],
  ["/gis/workspaces", "Spatial workspaces"],
  ["/gis/health", "Data & renderer health"],
] as const;
export function GisRoutes() {
  return (
    <Routes>
      <Route path="/" element={<OverviewPage />} />
      <Route path="/gis" element={<OverviewPage />} />
      <Route path="/gis/map" element={<OperationalMapRoute />} />
      <Route path="/gis/cameras" element={<CameraGeographyPage />} />
      <Route path="/gis/coverage" element={<CoveragePage />} />
      <Route path="/gis/layers" element={<LayerCataloguePage />} />
      <Route path="/gis/time" element={<MovementTimePage />} />
      <Route path="/gis/review" element={<AlertsInvestigationsPage />} />
      <Route path="/gis/workspaces" element={<SpatialWorkspacesPage />} />
      <Route path="/gis/health" element={<DataRendererHealthPage />} />
      <Route path="*" element={<OverviewPage />} />
    </Routes>
  );
}
