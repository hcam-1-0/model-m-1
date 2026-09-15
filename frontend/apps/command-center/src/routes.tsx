import { Route, Routes } from "react-router";
import { AlertsReviewPage } from "./pages/alerts-review-page";
import { BriefingPage } from "./pages/briefing-page";
import { CameraNetworkPage } from "./pages/camera-network-page";
import { CoveragePage } from "./pages/coverage-page";
import { InvestigationWorkloadPage } from "./pages/investigation-workload-page";
import { LiveSituationPage } from "./pages/live-situation-page";
import { OperationalWorkloadPage } from "./pages/operational-workload-page";
import { OverviewPage } from "./pages/overview-page";
import { PlatformHealthPage } from "./pages/platform-health-page";
import { WorkspacesPage } from "./pages/workspaces-page";
export const commandRoutes = [
  ["/command", "Overview"],
  ["/command/live", "Live situation"],
  ["/command/coverage", "Coverage"],
  ["/command/cameras", "Camera network"],
  ["/command/review", "Alerts & review"],
  ["/command/investigations", "Investigations"],
  ["/command/workload", "Workload"],
  ["/command/health", "Platform health"],
  ["/command/briefing", "Briefing"],
  ["/command/workspaces", "Workspaces"],
] as const;
export function CommandRoutes() {
  return (
    <Routes>
      <Route path="/" element={<OverviewPage />} />
      <Route path="/command" element={<OverviewPage />} />
      <Route path="/command/live" element={<LiveSituationPage />} />
      <Route path="/command/coverage" element={<CoveragePage />} />
      <Route path="/command/cameras" element={<CameraNetworkPage />} />
      <Route path="/command/review" element={<AlertsReviewPage />} />
      <Route path="/command/investigations" element={<InvestigationWorkloadPage />} />
      <Route path="/command/workload" element={<OperationalWorkloadPage />} />
      <Route path="/command/health" element={<PlatformHealthPage />} />
      <Route path="/command/briefing" element={<BriefingPage />} />
      <Route path="/command/workspaces" element={<WorkspacesPage />} />
      <Route path="*" element={<OverviewPage />} />
    </Routes>
  );
}
