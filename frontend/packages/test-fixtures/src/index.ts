import type { SessionProjection, UiState, VersionedEvent } from "@hcam/contracts";
export const generatedMarker = "HCAM-GENERATED-NON-OPERATIONAL" as const;
export const generatedStates: readonly UiState[] = [
  "loading",
  "empty",
  "ready",
  "partial",
  "stale",
  "degraded",
  "denied",
  "conflict",
  "failure",
  "recovery",
  "correction",
  "success",
];
export * from "./p5-2-fixtures";
export * from "./p5-3-fixtures";
export * from "./p5-4-fixtures";
export * from "../../investigation-fixtures/src";
export * from "../../admin-security-operations-fixtures/src";
export function generatedSession(now = new Date("2026-09-06T10:00:00.000Z")): SessionProjection {
  const future = new Date(now.getTime() + 3_600_000).toISOString();
  return {
    contractVersion: "1.0.0",
    operatorRef: "SYN-OPERATOR-0001",
    sessionRef: "SYN-SESSION-0001",
    department: { id: "SYN-DEPT-01", label: "Generated Department" },
    departments: [{ id: "SYN-DEPT-01", label: "Generated Department" }],
    capabilities: ["administrator"],
    policyRevision: "SYN-POLICY-1",
    serverTime: now.toISOString(),
    staleAt: future,
    expiresAt: future,
    reauthenticationRequired: false,
    csrfToken: "SYN-CSRF-NON-ISSUABLE-0001",
    locale: "en",
    timezone: "Asia/Kolkata",
  };
}
export function generatedEvent(
  sequence: number,
): VersionedEvent<{ readonly marker: typeof generatedMarker }> {
  return {
    eventType: "hcam.generated.changed.v1",
    version: "1.0.0",
    departmentRef: "SYN-DEPT-01",
    sequence,
    occurredAt: "2026-09-06T10:00:00.000Z",
    payload: { marker: generatedMarker },
  };
}
