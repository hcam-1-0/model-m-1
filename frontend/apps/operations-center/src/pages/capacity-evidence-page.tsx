import { CapacityEvidencePanel } from "../components/capacity-evidence-panel";
import { PlatformOperationsPageFrame } from "../components/platform-operations-state-boundary";
export function CapacityEvidencePage() {
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / CAPACITY"
      title="Capacity evidence"
      description="Deterministic C1, C10, and C50 functional workloads validate bounded rendering and contracts, not performance, hardware, thermal, or production capacity."
    >
      <CapacityEvidencePanel />
    </PlatformOperationsPageFrame>
  );
}
