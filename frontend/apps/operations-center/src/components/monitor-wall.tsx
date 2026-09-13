import type { AdmissionDecision, CameraProjection } from "@hcam/camera-live-domain";
import { LiveWorkspaceGrid } from "./live-workspace-grid";

export function MonitorWall({
  cameras,
  decisions,
}: {
  readonly cameras: readonly CameraProjection[];
  readonly decisions: readonly AdmissionDecision[];
}) {
  const columns = cameras.length <= 1 ? 1 : cameras.length <= 4 ? 2 : cameras.length <= 9 ? 3 : 4;
  return (
    <div className="monitor-wall">
      <header>
        <span>WALL 01</span>
        <strong>{cameras.length} generated sources</strong>
        <small>View only · automatic admission</small>
      </header>
      <LiveWorkspaceGrid cameras={cameras} decisions={decisions} columns={columns} compact />
    </div>
  );
}
