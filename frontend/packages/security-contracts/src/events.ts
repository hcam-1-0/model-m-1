import { signalLanes, type SignalLane } from "./contracts";
export interface SecurityInvalidationEvent {
  readonly eventType: "hcam.security.projection.changed.v1";
  readonly version: "1.0.0";
  readonly departmentRef: string;
  readonly sequence: number;
  readonly lane: SignalLane;
  readonly queryScopes: readonly string[];
  readonly generated: true;
}
export function isSecurityInvalidationEvent(value: unknown): value is SecurityInvalidationEvent {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const event = value as Partial<SecurityInvalidationEvent>;
  return (
    event.eventType === "hcam.security.projection.changed.v1" &&
    event.version === "1.0.0" &&
    typeof event.departmentRef === "string" &&
    Number.isSafeInteger(event.sequence) &&
    signalLanes.some((lane: SignalLane) => lane === event.lane) &&
    Array.isArray(event.queryScopes) &&
    event.queryScopes.length <= 16 &&
    event.generated === true
  );
}
