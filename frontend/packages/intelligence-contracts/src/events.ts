import type { ResourceId, VersionedEvent } from "@hcam/contracts";

export type IntelligenceEventType =
  | "hcam.intelligence.queue.changed.v1"
  | "hcam.intelligence.alert.changed.v1"
  | "hcam.intelligence.review.recorded.v1"
  | "hcam.intelligence.correction.recorded.v1";
export interface IntelligenceEventPayload {
  readonly resourceRef: ResourceId;
  readonly queryScopes: readonly string[];
}
export type IntelligenceEvent = VersionedEvent<IntelligenceEventPayload> & {
  readonly eventType: IntelligenceEventType;
};

export function isIntelligenceEvent(value: unknown): value is IntelligenceEvent {
  if (!value || typeof value !== "object") return false;
  const event = value as Partial<IntelligenceEvent>;
  return (
    typeof event.eventType === "string" &&
    event.eventType.startsWith("hcam.intelligence.") &&
    event.eventType.endsWith(".v1") &&
    event.version === "1.0.0" &&
    typeof event.departmentRef === "string" &&
    Number.isSafeInteger(event.sequence) &&
    !!event.payload &&
    typeof event.payload.resourceRef === "string" &&
    Array.isArray(event.payload.queryScopes) &&
    event.payload.queryScopes.length <= 8
  );
}
