import type { ReviewCommand } from "../../intelligence-domain/src";

export type ConcurrencyDecision =
  "current" | "etag_mismatch" | "stale_revision" | "fingerprint_mismatch";
export function checkConcurrency(
  command: ReviewCommand,
  currentRevision: number,
  currentEtag: string,
  expectedFingerprint: string,
): ConcurrencyDecision {
  if (command.ifMatch !== currentEtag) return "etag_mismatch";
  if (command.expectedRevision !== currentRevision) return "stale_revision";
  if (command.canonicalFingerprint !== expectedFingerprint) return "fingerprint_mismatch";
  return "current";
}
export function conflictRequiresReconsideration(decision: ConcurrencyDecision): boolean {
  return decision !== "current";
}
