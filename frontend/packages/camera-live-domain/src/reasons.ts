import type { CameraReason } from "./contracts";

export const safeReasonLabels: Readonly<Record<CameraReason, string>> = Object.freeze({
  ready: "Ready",
  generated_only: "Generated source",
  producer_unavailable: "Source unavailable",
  department_denied: "Department access denied",
  capability_unknown: "Capabilities unknown",
  browser_unsupported: "Browser transport unsupported",
  profile_budget_exceeded: "Resource profile limit reached",
  grant_expired: "Playback grant expired",
  grant_revoked: "Playback grant revoked",
  manifest_invalid: "Media manifest rejected",
  stream_stalled: "Playback stalled",
  cooldown_active: "Recovery cooldown active",
  circuit_open: "Recovery circuit open",
  fallback_to_hls: "Using HLS fallback",
  teardown_complete: "Playback closed",
  layout_conflict: "Layout revision conflict",
});
export function safeReason(value: string): CameraReason {
  return Object.hasOwn(safeReasonLabels, value) ? (value as CameraReason) : "producer_unavailable";
}
