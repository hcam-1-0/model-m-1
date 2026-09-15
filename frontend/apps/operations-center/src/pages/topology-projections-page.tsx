import { PlatformOperationsPageFrame } from "../components/platform-operations-state-boundary";
import { TopologyProjection } from "../components/topology-projection";
export function TopologyProjectionsPage() {
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / TOPOLOGY"
      title="Topology projections"
      description="Portable standalone, workstation, control-room, GPU-lab, server, and Kubernetes layouts without container, cluster, deployment, or profile activation."
    >
      <TopologyProjection />
    </PlatformOperationsPageFrame>
  );
}
