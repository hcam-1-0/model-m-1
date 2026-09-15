import { Route, Routes } from "react-router";
import { CameraCataloguePage } from "./pages/camera-catalogue-page";
import { CameraDetailPage } from "./pages/camera-detail-page";
import { LiveWorkspacePage } from "./pages/live-workspace-page";
import { MonitorWallPage } from "./pages/monitor-wall-page";
import { StreamDiagnosticsPage } from "./pages/stream-diagnostics-page";
import { WorkspaceManagerPage } from "./pages/workspace-manager-page";
import { AiRuntimeSchedulerPage } from "./pages/ai-runtime-scheduler-page";
import { CapacityEvidencePage } from "./pages/capacity-evidence-page";
import { DataInfrastructurePage } from "./pages/data-infrastructure-page";
import { DegradationKillSwitchPage } from "./pages/degradation-kill-switch-page";
import { MaintenanceRecoveryPreviewPage } from "./pages/maintenance-recovery-preview-page";
import { PlatformOperationsOverviewPage } from "./pages/platform-operations-overview-page";
import { QueuesWorkersCircuitsPage } from "./pages/queues-workers-circuits-page";
import { ServicesDependenciesPage } from "./pages/services-dependencies-page";
import { SloErrorBudgetPage } from "./pages/slo-error-budget-page";
import { TopologyProjectionsPage } from "./pages/topology-projections-page";

export const operationsRoutes = [
  ["/operations", "Camera catalogue"],
  ["/operations/live", "Live workspace"],
  ["/operations/wall", "Monitor wall"],
  ["/operations/workspaces", "Workspaces"],
  ["/operations/platform", "Platform overview"],
  ["/operations/platform/services", "Services"],
  ["/operations/platform/queues", "Queues and workers"],
  ["/operations/platform/data", "Data infrastructure"],
  ["/operations/platform/ai-runtime", "AI runtime"],
  ["/operations/platform/slo", "SLO and budgets"],
  ["/operations/platform/degradation", "Degradation"],
  ["/operations/platform/recovery", "Recovery previews"],
  ["/operations/platform/capacity", "Capacity evidence"],
  ["/operations/platform/topology", "Topology projections"],
] as const;

export function OperationsRoutes() {
  return (
    <Routes>
      <Route path="/" element={<CameraCataloguePage />} />
      <Route path="/operations" element={<CameraCataloguePage />} />
      <Route path="/operations/cameras" element={<CameraCataloguePage />} />
      <Route path="/operations/cameras/:cameraId" element={<CameraDetailPage />} />
      <Route path="/operations/diagnostics/:streamId" element={<StreamDiagnosticsPage />} />
      <Route path="/operations/live" element={<LiveWorkspacePage />} />
      <Route path="/operations/wall" element={<MonitorWallPage />} />
      <Route path="/operations/workspaces" element={<WorkspaceManagerPage />} />
      <Route path="/operations/platform" element={<PlatformOperationsOverviewPage />} />
      <Route path="/operations/platform/services" element={<ServicesDependenciesPage />} />
      <Route path="/operations/platform/queues" element={<QueuesWorkersCircuitsPage />} />
      <Route path="/operations/platform/data" element={<DataInfrastructurePage />} />
      <Route path="/operations/platform/ai-runtime" element={<AiRuntimeSchedulerPage />} />
      <Route path="/operations/platform/slo" element={<SloErrorBudgetPage />} />
      <Route path="/operations/platform/degradation" element={<DegradationKillSwitchPage />} />
      <Route path="/operations/platform/recovery" element={<MaintenanceRecoveryPreviewPage />} />
      <Route path="/operations/platform/capacity" element={<CapacityEvidencePage />} />
      <Route path="/operations/platform/topology" element={<TopologyProjectionsPage />} />
      <Route path="*" element={<CameraCataloguePage />} />
    </Routes>
  );
}
