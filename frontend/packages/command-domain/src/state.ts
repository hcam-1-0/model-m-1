import type { UiState } from "@hcam/contracts";
import type { SituationSnapshot } from "./projections";

export function situationState(snapshot: SituationSnapshot | null, now: Date): UiState {
  if (!snapshot) return "loading";
  if (snapshot.metrics.length === 0 && snapshot.workItems.length === 0) return "empty";
  if (snapshot.activity.some((item) => item.kind === "correction")) return "correction";
  if (Date.parse(snapshot.freshness.staleAt) <= now.getTime()) return "stale";
  if (snapshot.freshness.completeness === "unknown") return "unknown";
  if (snapshot.freshness.completeness === "partial" || snapshot.unavailableProducers.length > 0)
    return "partial";
  return "ready";
}
export function boundedTimeWindow(hours: number): number {
  if (!Number.isFinite(hours)) return 1;
  return Math.min(24, Math.max(1, Math.round(hours)));
}
