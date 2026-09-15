import type { AdmissionDecision, CameraProjection } from "@hcam/camera-live-domain";
import { playbackFor } from "../data/camera-live-projections";
import { LiveTile } from "./live-tile";

export function LiveWorkspaceGrid({
  cameras,
  decisions,
  columns,
  compact = false,
}: {
  readonly cameras: readonly CameraProjection[];
  readonly decisions: readonly AdmissionDecision[];
  readonly columns: 1 | 2 | 3 | 4;
  readonly compact?: boolean;
}) {
  return (
    <section
      className="live-grid"
      style={{ "--live-columns": columns } as React.CSSProperties}
      aria-label="Generated live camera workspace"
    >
      {cameras.map((camera) => {
        const stream = camera.streams[0];
        if (!stream) return null;
        const decision = decisions.find((item) => item.streamId === stream.id);
        if (!decision) return null;
        return (
          <LiveTile
            key={stream.id}
            stream={stream}
            decision={decision}
            grant={playbackFor(stream.id)}
            compact={compact}
          />
        );
      })}
    </section>
  );
}
