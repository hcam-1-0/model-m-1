import type { UiState } from "@hcam/contracts";
import type {
  EvidenceReference,
  InvestigationQueue,
  TimelinePage,
} from "../../investigation-contracts/src";

export function investigationQueueState(queue: InvestigationQueue | null, now: Date): UiState {
  if (!queue) return "loading";
  if (!queue.items.length) return "empty";
  if (queue.items.some((item) => item.correctionStatus === "pending")) return "correction";
  if (queue.items.every((item) => Date.parse(item.freshness.staleAt) <= now.getTime()))
    return "stale";
  if (queue.items.some((item) => item.freshness.completeness !== "complete")) return "partial";
  return "ready";
}
export function timelineState(page: TimelinePage | null): UiState {
  if (!page) return "loading";
  if (!page.items.length) return "empty";
  if (page.items.some((item) => item.kind === "retraction")) return "retracted";
  if (page.items.some((item) => item.limitations.length > 0)) return "partial";
  return "ready";
}
export function evidenceReferenceState(reference: EvidenceReference | null): UiState {
  if (!reference) return "loading";
  if (reference.access === "denied") return "denied";
  if (reference.availability === "unavailable") return "degraded";
  if (reference.integrity === "digest_mismatch") return "conflict";
  if (reference.freshness.completeness !== "complete") return "partial";
  return "ready";
}
