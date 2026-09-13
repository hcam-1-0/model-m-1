import type { HealthBand } from "@hcam/camera-live-domain";

export function CameraHealthBadge({ health }: { readonly health: HealthBand }) {
  return <span className={`health-badge ${health}`}>{health}</span>;
}
