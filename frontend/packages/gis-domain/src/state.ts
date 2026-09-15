import type { UiState } from "@hcam/contracts";
import type { GisAdmission, GisFeatureSummary } from "@hcam/gis-contracts";

export function gisState(
  features: readonly GisFeatureSummary[] | null,
  admission: GisAdmission,
  now: Date,
): UiState {
  if (!features) return "loading";
  if (features.length === 0) return "empty";
  if (features.some((feature) => feature.status === "unknown")) return "unknown";
  if (features.some((feature) => Date.parse(feature.freshness.staleAt) <= now.getTime()))
    return "stale";
  if (admission.mode === "list_only" || !admission.admitted) return "degraded";
  return "ready";
}
