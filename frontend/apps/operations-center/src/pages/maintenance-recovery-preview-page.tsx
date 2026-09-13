import { PlatformOperationsPageFrame } from "../components/platform-operations-state-boundary";
import { RecoveryPreviewPanel } from "../components/recovery-preview-panel";
export function MaintenanceRecoveryPreviewPage() {
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / CONTINUITY"
      title="Maintenance and recovery previews"
      description="Generated backup, restore, failover, maintenance, and disaster-recovery previews with explicit evidence gaps and no executable procedures."
    >
      <RecoveryPreviewPanel />
    </PlatformOperationsPageFrame>
  );
}
