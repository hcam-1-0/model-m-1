export interface AdminInvalidationEvent {
  readonly eventType: "hcam.admin.projection.changed.v1";
  readonly version: "1.0.0";
  readonly departmentRef: string;
  readonly sequence: number;
  readonly queryScopes: readonly string[];
  readonly generated: true;
}
export function isAdminInvalidationEvent(value: unknown): value is AdminInvalidationEvent {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const event = value as Partial<AdminInvalidationEvent>;
  return (
    event.eventType === "hcam.admin.projection.changed.v1" &&
    event.version === "1.0.0" &&
    typeof event.departmentRef === "string" &&
    Number.isSafeInteger(event.sequence) &&
    (event.sequence ?? 0) >= 0 &&
    Array.isArray(event.queryScopes) &&
    event.queryScopes.length <= 16 &&
    event.queryScopes.every(
      (scope: unknown) => typeof scope === "string" && /^[a-z0-9_.-]{1,64}$/u.test(scope),
    ) &&
    event.generated === true
  );
}
