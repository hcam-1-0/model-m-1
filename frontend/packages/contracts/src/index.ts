export const contractManifestDigest = "p5.0.accepted.generated-only" as const;
export const supportedContractRange = ">=phase4.7.handoff.v1 <phase6" as const;

export const uiStates = [
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
  "unknown",
  "retracted",
  "unsupported",
  "success",
] as const;
export type UiState = (typeof uiStates)[number];

export const portalIds = [
  "command",
  "operations",
  "intelligence",
  "investigations",
  "evidence",
  "admin",
  "security",
] as const;
export type PortalId = (typeof portalIds)[number];
export type Capability = `${string}.${string}` | "administrator";
export type ResourceId = string & { readonly __resourceId: unique symbol };
export const signalAuthorityLanes = [
  "operational",
  "security",
  "audit",
  "evidence",
  "administrative",
] as const;
export type SignalAuthorityLane = (typeof signalAuthorityLanes)[number];
export const p56ResourceProfiles = [
  "low_resource",
  "enhanced_workstation",
  "control_room",
  "owned_GPU_lab",
  "future_server",
  "future_Kubernetes",
] as const;
export type P56ResourceProfile = (typeof p56ResourceProfiles)[number];

export interface RouteManifest {
  readonly routeId: string;
  readonly portalId: PortalId;
  readonly path: `/${string}`;
  readonly titleKey: string;
  readonly requiredCapabilities: readonly Capability[];
  readonly allowedQueryKeys: readonly string[];
  readonly operationIds: readonly string[];
  readonly focusTarget: `#${string}`;
  readonly allowMultiWindow: boolean;
  readonly persistence: "none" | "harmless-display-only";
}

export interface DepartmentChoice {
  readonly id: string;
  readonly label: string;
}
export interface SessionProjection {
  readonly contractVersion: "1.0.0";
  readonly operatorRef: string;
  readonly sessionRef: string;
  readonly department: DepartmentChoice;
  readonly departments: readonly DepartmentChoice[];
  readonly capabilities: readonly Capability[];
  readonly policyRevision: string;
  readonly serverTime: string;
  readonly staleAt: string;
  readonly expiresAt: string;
  readonly reauthenticationRequired: boolean;
  readonly csrfToken: string;
  readonly locale: "en" | "gu" | "hi";
  readonly timezone: string;
}

export interface ProblemDetails {
  readonly type: string;
  readonly title: string;
  readonly status: number;
  readonly code: ProblemCode;
  readonly correlationRef?: string;
}
export type ProblemCode =
  | "denied"
  | "conflict"
  | "incompatible"
  | "invalid"
  | "timeout"
  | "offline"
  | "unavailable"
  | "safe_failure";

export interface Page<T> {
  readonly items: readonly T[];
  readonly nextCursor: string | null;
  readonly totalApproximate: number | null;
}
export interface Freshness {
  readonly observedAt: string;
  readonly staleAt: string;
  readonly completeness: "complete" | "partial" | "unknown";
}
export interface QualifiedChronology {
  readonly authority: "record_sequence";
  readonly eventTimeChangesOrder: false;
  readonly exactRevisionRequired: true;
}
export interface EvidenceTruthBoundary {
  readonly integrityEstablishesTruth: false;
  readonly integrityEstablishesIdentity: false;
  readonly integrityEstablishesGuilt: false;
  readonly integrityEstablishesAdmissibility: false;
  readonly sourceResolutionAuthorized: false;
}
export interface VersionedEvent<T = unknown> {
  readonly eventType: string;
  readonly version: "1.0.0";
  readonly departmentRef: string;
  readonly sequence: number;
  readonly occurredAt: string;
  readonly payload: T;
}
export interface DisplayPreferences {
  readonly version: 1;
  readonly theme: "light" | "dark" | "system";
  readonly density: "compact" | "comfortable" | "spacious";
  readonly locale: "en" | "gu" | "hi";
  readonly reducedMotion: boolean;
  readonly expiresAt: string;
}
export interface WorkspaceWindowIntent {
  readonly version: 1;
  readonly portal: PortalId;
  readonly view: "list" | "detail" | "map_alternative" | "monitoring";
  readonly opaqueResourceRef?: ResourceId;
}
export function parseWorkspaceWindowIntent(value: unknown): WorkspaceWindowIntent | null {
  if (!value || typeof value !== "object") return null;
  const item = value as Record<string, unknown>;
  if (
    item.version !== 1 ||
    !portalIds.includes(item.portal as PortalId) ||
    !["list", "detail", "map_alternative", "monitoring"].includes(String(item.view))
  )
    return null;
  if (
    "opaqueResourceRef" in item &&
    (typeof item.opaqueResourceRef !== "string" || asResourceId(item.opaqueResourceRef) === null)
  )
    return null;
  return item as unknown as WorkspaceWindowIntent;
}

const sessionKeys = [
  "contractVersion",
  "operatorRef",
  "sessionRef",
  "department",
  "departments",
  "capabilities",
  "policyRevision",
  "serverTime",
  "staleAt",
  "expiresAt",
  "reauthenticationRequired",
  "csrfToken",
  "locale",
  "timezone",
] as const;
const isBoundedString = (value: unknown, minimum: number, maximum: number): value is string =>
  typeof value === "string" && value.length >= minimum && value.length <= maximum;
const isTimestamp = (value: unknown): value is string =>
  typeof value === "string" && /^\d{4}-\d{2}-\d{2}T/.test(value);
const isDepartment = (value: unknown): value is DepartmentChoice => {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const keys = Object.keys(value);
  if (keys.length !== 2 || !keys.every((key) => key === "id" || key === "label")) return false;
  const department = value as Partial<DepartmentChoice>;
  return isBoundedString(department.id, 3, 64) && isBoundedString(department.label, 1, 80);
};
const isCapabilityList = (value: unknown): value is readonly Capability[] =>
  Array.isArray(value) &&
  value.length <= 256 &&
  value.every((item) => isBoundedString(item, 3, 96)) &&
  new Set(value).size === value.length;

export function parseSessionProjection(value: unknown): SessionProjection | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const item = value as Partial<SessionProjection>;
  const keys = Object.keys(value);
  const valid =
    keys.length === sessionKeys.length &&
    keys.every((key) => sessionKeys.includes(key as (typeof sessionKeys)[number])) &&
    item.contractVersion === "1.0.0" &&
    isBoundedString(item.operatorRef, 8, 96) &&
    isBoundedString(item.sessionRef, 8, 96) &&
    isDepartment(item.department) &&
    Array.isArray(item.departments) &&
    item.departments.length >= 1 &&
    item.departments.length <= 32 &&
    item.departments.every(isDepartment) &&
    isCapabilityList(item.capabilities) &&
    isBoundedString(item.policyRevision, 1, 64) &&
    isTimestamp(item.serverTime) &&
    isTimestamp(item.staleAt) &&
    isTimestamp(item.expiresAt) &&
    typeof item.reauthenticationRequired === "boolean" &&
    isBoundedString(item.csrfToken, 16, 256) &&
    ["en", "gu", "hi"].includes(String(item.locale)) &&
    isBoundedString(item.timezone, 1, 64);
  return valid ? (value as SessionProjection) : null;
}

export function toSafeProblem(status: number, value: unknown): ProblemDetails {
  const fallback: ProblemDetails = {
    type: "about:blank",
    title: "Request could not be completed",
    status,
    code: status === 403 ? "denied" : status === 409 ? "conflict" : "safe_failure",
  };
  if (!value || typeof value !== "object") return fallback;
  const item = value as Record<string, unknown>;
  const allowed = new Set<ProblemCode>([
    "denied",
    "conflict",
    "incompatible",
    "invalid",
    "timeout",
    "offline",
    "unavailable",
    "safe_failure",
  ]);
  const code =
    typeof item.code === "string" && allowed.has(item.code as ProblemCode)
      ? (item.code as ProblemCode)
      : fallback.code;
  const correlationRef =
    typeof item.correlation_ref === "string" && /^[A-Za-z0-9_-]{8,64}$/.test(item.correlation_ref)
      ? item.correlation_ref
      : undefined;
  return { ...fallback, code, ...(correlationRef ? { correlationRef } : {}) };
}

export function asResourceId(value: string): ResourceId | null {
  return /^[A-Za-z0-9_-]{8,96}$/.test(value) ? (value as ResourceId) : null;
}
