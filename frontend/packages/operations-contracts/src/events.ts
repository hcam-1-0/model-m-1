export interface OperationsInvalidationEvent {
  readonly eventType: "hcam.operations.projection.changed.v1";
  readonly version: "1.0.0";
  readonly departmentRef: string;
  readonly sequence: number;
  readonly queryScopes: readonly string[];
  readonly generated: true;
}
export function isOperationsInvalidationEvent(
  value: unknown,
): value is OperationsInvalidationEvent {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const event = value as Partial<OperationsInvalidationEvent>;
  return (
    event.eventType === "hcam.operations.projection.changed.v1" &&
    event.version === "1.0.0" &&
    typeof event.departmentRef === "string" &&
    Number.isSafeInteger(event.sequence) &&
    Array.isArray(event.queryScopes) &&
    event.queryScopes.length <= 16 &&
    event.generated === true
  );
}
