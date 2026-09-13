import type { VersionedEvent } from "@hcam/contracts";

export type EventDisposition =
  "accepted" | "duplicate" | "gap" | "reordered" | "wrong_department" | "unknown_version";
export interface EventDecision {
  readonly disposition: EventDisposition;
  readonly revalidate: boolean;
  readonly nextSequence: number;
}
type InboundEvent = Omit<VersionedEvent, "version"> & { readonly version: string };
export function classifyEvent(
  event: InboundEvent,
  departmentRef: string,
  lastSequence: number,
): EventDecision {
  if (event.version !== "1.0.0")
    return { disposition: "unknown_version", revalidate: true, nextSequence: lastSequence };
  if (event.departmentRef !== departmentRef)
    return { disposition: "wrong_department", revalidate: false, nextSequence: lastSequence };
  if (event.sequence === lastSequence)
    return { disposition: "duplicate", revalidate: false, nextSequence: lastSequence };
  if (event.sequence < lastSequence)
    return { disposition: "reordered", revalidate: true, nextSequence: lastSequence };
  if (event.sequence > lastSequence + 1)
    return { disposition: "gap", revalidate: true, nextSequence: event.sequence };
  return { disposition: "accepted", revalidate: true, nextSequence: event.sequence };
}

export interface InvalidationBatch {
  readonly queryScopes: readonly string[];
  readonly highestSequence: number;
  readonly requiresHttpConfirmation: true;
}
export function coalesceInvalidations(
  events: readonly { readonly sequence: number; readonly queryScopes: readonly string[] }[],
  maximumScopes = 32,
): InvalidationBatch {
  const scopes = [...new Set(events.flatMap((event) => event.queryScopes))]
    .filter((scope) => /^[a-z0-9_.-]{1,64}$/u.test(scope))
    .sort()
    .slice(0, Math.max(0, maximumScopes));
  return {
    queryScopes: scopes,
    highestSequence: Math.max(0, ...events.map((event) => event.sequence)),
    requiresHttpConfirmation: true,
  };
}

export const p55InvalidationScopes = Object.freeze({
  investigationChanged: ["investigation.list", "investigation.detail", "investigation.timeline"],
  correctionRecorded: [
    "investigation.detail",
    "investigation.timeline",
    "investigation.reconstruction",
    "evidence.list",
  ],
  evidenceChanged: [
    "evidence.list",
    "evidence.detail",
    "evidence.integrity",
    "evidence.provenance",
    "evidence.custody",
  ],
} as const);
export function p55InvalidationBatch(
  event: keyof typeof p55InvalidationScopes,
  sequence: number,
): InvalidationBatch {
  return coalesceInvalidations([{ sequence, queryScopes: p55InvalidationScopes[event] }]);
}

export const p56InvalidationScopes = Object.freeze({
  administrationChanged: ["admin.changes", "admin.governance", "admin.configuration"],
  securityProjectionChanged: ["security.posture", "security.denials", "security.audit"],
  platformOperationsChanged: ["operations.services", "operations.queues", "operations.slo"],
} as const);
export function p56InvalidationBatch(
  event: keyof typeof p56InvalidationScopes,
  sequence: number,
): InvalidationBatch {
  return coalesceInvalidations([{ sequence, queryScopes: p56InvalidationScopes[event] }]);
}
