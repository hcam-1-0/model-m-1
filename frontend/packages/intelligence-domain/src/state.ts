import type { UiState } from "@hcam/contracts";
import type { IntelligenceQueue } from "../../intelligence-contracts/src";

export function intelligenceQueueState(queue: IntelligenceQueue | null, now: Date): UiState {
  if (!queue) return "loading";
  if (!queue.items.length) return "empty";
  if (queue.items.some((item) => item.state === "correction_pending")) return "correction";
  if (queue.items.every((item) => Date.parse(item.freshness.staleAt) <= now.getTime()))
    return "stale";
  if (queue.items.some((item) => item.freshness.completeness !== "complete")) return "partial";
  return "ready";
}
export function filterQueue<T extends { state: string; priority: string }>(
  items: readonly T[],
  state: string,
  priority: string,
): readonly T[] {
  return items.filter(
    (item) =>
      (state === "all" || item.state === state) &&
      (priority === "all" || item.priority === priority),
  );
}
