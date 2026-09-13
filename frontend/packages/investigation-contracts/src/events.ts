import type { ResourceId, VersionedEvent } from "@hcam/contracts";

export type InvestigationEventType =
  | "hcam.investigation.timeline.changed.v1"
  | "hcam.investigation.correction.recorded.v1"
  | "hcam.investigation.retraction.recorded.v1"
  | "hcam.evidence.reference.changed.v1"
  | "hcam.evidence.custody.recorded.v1";
export interface InvestigationEventPayload {
  readonly resourceRef: ResourceId;
  readonly investigationRef: ResourceId;
  readonly queryScopes: readonly string[];
  readonly requiresHttpConfirmation: true;
}
export type InvestigationEvent = VersionedEvent<InvestigationEventPayload> & {
  readonly eventType: InvestigationEventType;
};
export function isInvestigationEvent(value: unknown): value is InvestigationEvent {
  if (!value || typeof value !== "object") return false;
  const event = value as Partial<InvestigationEvent>;
  const runtimePayload = event.payload as unknown as Readonly<Record<string, unknown>>;
  return (
    typeof event.eventType === "string" &&
    /^hcam\.(?:investigation|evidence)\.[a-z_.]+\.v1$/u.test(event.eventType) &&
    event.version === "1.0.0" &&
    typeof event.departmentRef === "string" &&
    Number.isSafeInteger(event.sequence) &&
    !!event.payload &&
    typeof event.payload.resourceRef === "string" &&
    typeof event.payload.investigationRef === "string" &&
    runtimePayload.requiresHttpConfirmation === true &&
    Array.isArray(event.payload.queryScopes) &&
    event.payload.queryScopes.length <= 8
  );
}
