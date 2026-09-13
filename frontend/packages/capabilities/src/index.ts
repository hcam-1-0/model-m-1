import type { Capability, RouteManifest, SessionProjection } from "@hcam/contracts";

export type AccessReason =
  | "allowed"
  | "session_missing"
  | "session_stale"
  | "reauthentication_required"
  | "department_mismatch"
  | "capability_missing"
  | "route_unknown";
export interface AccessDecision {
  readonly allowed: boolean;
  readonly reason: AccessReason;
}

export function resolveRouteAccess(
  route: RouteManifest | undefined,
  session: SessionProjection | null,
  now = new Date(),
): AccessDecision {
  if (!route) return { allowed: false, reason: "route_unknown" };
  if (!session) return { allowed: false, reason: "session_missing" };
  if (session.reauthenticationRequired)
    return { allowed: false, reason: "reauthentication_required" };
  if (
    Date.parse(session.staleAt) <= now.getTime() ||
    Date.parse(session.expiresAt) <= now.getTime()
  )
    return { allowed: false, reason: "session_stale" };
  const granted = new Set<Capability>(session.capabilities);
  if (
    !route.requiredCapabilities.some(
      (capability) => granted.has(capability) || granted.has("administrator"),
    )
  )
    return { allowed: false, reason: "capability_missing" };
  return { allowed: true, reason: "allowed" };
}

export function intersectCapabilities(
  server: readonly Capability[],
  build: readonly Capability[],
): readonly Capability[] {
  const supported = new Set(build);
  return server.filter((capability) => supported.has(capability));
}

export const resourceProfiles = [
  "low_resource",
  "enhanced",
  "control_room",
  "future_server",
] as const;
export type ResourceProfile = (typeof resourceProfiles)[number];
export interface ProfileInputs {
  readonly requested: ResourceProfile;
  readonly serverCeiling: ResourceProfile;
  readonly buildSupported: readonly ResourceProfile[];
  readonly coarseBrowserSupport: "basic" | "enhanced";
  readonly sessionHealth: "healthy" | "degraded";
}
export interface ProfileDecision {
  readonly profile: ResourceProfile;
  readonly degraded: boolean;
  readonly reason:
    "requested" | "build_limit" | "browser_limit" | "server_limit" | "session_health";
}
export interface ResourceProfileLimits {
  readonly featureCap: 10 | 50;
  readonly requestConcurrency: 1 | 2 | 4 | 8;
  readonly rendererCeiling: "maplibre" | "deck_overlaid" | "deck_interleaved";
  readonly multiMonitor: boolean;
}
export const resourceProfileLimits: Readonly<Record<ResourceProfile, ResourceProfileLimits>> = {
  low_resource: {
    featureCap: 10,
    requestConcurrency: 1,
    rendererCeiling: "maplibre",
    multiMonitor: false,
  },
  enhanced: {
    featureCap: 50,
    requestConcurrency: 2,
    rendererCeiling: "deck_overlaid",
    multiMonitor: true,
  },
  control_room: {
    featureCap: 50,
    requestConcurrency: 4,
    rendererCeiling: "deck_interleaved",
    multiMonitor: true,
  },
  future_server: {
    featureCap: 50,
    requestConcurrency: 8,
    rendererCeiling: "deck_interleaved",
    multiMonitor: true,
  },
};
export function limitsForProfile(profile: ResourceProfile): ResourceProfileLimits {
  return resourceProfileLimits[profile];
}
const profileRank: Record<ResourceProfile, number> = {
  low_resource: 0,
  enhanced: 1,
  control_room: 2,
  future_server: 3,
};
export function resolveResourceProfile(input: ProfileInputs): ProfileDecision {
  if (input.sessionHealth === "degraded")
    return {
      profile: "low_resource",
      degraded: input.requested !== "low_resource",
      reason: "session_health",
    };
  const supported = input.buildSupported.filter(
    (profile) => profileRank[profile] <= profileRank[input.serverCeiling],
  );
  const browserLimit = input.coarseBrowserSupport === "basic" ? 0 : 3;
  const candidates = supported.filter(
    (profile) =>
      profileRank[profile] <= browserLimit && profileRank[profile] <= profileRank[input.requested],
  );
  const profile = candidates.sort((a, b) => profileRank[b] - profileRank[a])[0] ?? "low_resource";
  if (profile === input.requested) return { profile, degraded: false, reason: "requested" };
  if (profileRank[input.serverCeiling] < profileRank[input.requested])
    return { profile, degraded: true, reason: "server_limit" };
  if (browserLimit < profileRank[input.requested])
    return { profile, degraded: true, reason: "browser_limit" };
  return { profile, degraded: true, reason: "build_limit" };
}

export type Phase3ExecutionClass =
  "portable_cpu" | "owned_gpu_lab" | "standalone_server" | "kubernetes_cluster";
export type CameraResourceProfile =
  "low_resource" | "enhanced_workstation" | "control_room" | "owned_gpu_lab" | "future_server";
export function mapExecutionClassToCameraProfile(
  executionClass: Phase3ExecutionClass,
  serverAuthorized: boolean,
): CameraResourceProfile {
  if (!serverAuthorized) return "low_resource";
  if (executionClass === "owned_gpu_lab") return "owned_gpu_lab";
  if (executionClass === "standalone_server" || executionClass === "kubernetes_cluster")
    return "future_server";
  return "enhanced_workstation";
}

export interface ReviewAuthorityInput {
  readonly departmentMatches: boolean;
  readonly policyCurrent: boolean;
  readonly capabilities: readonly Capability[];
  readonly priorActorRefs: readonly string[];
  readonly actorRef: string;
}
export function resolveReviewAuthority(input: ReviewAuthorityInput): AccessDecision {
  if (!input.departmentMatches) return { allowed: false, reason: "department_mismatch" };
  if (!input.policyCurrent) return { allowed: false, reason: "session_stale" };
  if (
    !input.capabilities.includes("intelligence.reviewer") &&
    !input.capabilities.includes("administrator")
  )
    return { allowed: false, reason: "capability_missing" };
  if (input.priorActorRefs.includes(input.actorRef))
    return { allowed: false, reason: "reauthentication_required" };
  return { allowed: true, reason: "allowed" };
}

export interface InvestigationEvidenceAuthorityInput {
  readonly departmentMatches: boolean;
  readonly purposeMatches: boolean;
  readonly policyCurrent: boolean;
  readonly capability: "investigations.viewer" | "evidence.viewer";
  readonly capabilities: readonly Capability[];
}
export function resolveInvestigationEvidenceAuthority(
  input: InvestigationEvidenceAuthorityInput,
): AccessDecision {
  if (!input.departmentMatches || !input.purposeMatches)
    return { allowed: false, reason: "department_mismatch" };
  if (!input.policyCurrent) return { allowed: false, reason: "session_stale" };
  if (
    !input.capabilities.includes(input.capability) &&
    !input.capabilities.includes("administrator")
  )
    return { allowed: false, reason: "capability_missing" };
  return { allowed: true, reason: "allowed" };
}

export interface GovernanceAuthorityInput {
  readonly sessionCurrent: boolean;
  readonly departmentMatches: boolean;
  readonly purposeMatches: boolean;
  readonly policyCurrent: boolean;
  readonly requiredCapability: Capability;
  readonly capabilities: readonly Capability[];
}
export function resolveGovernanceAuthority(input: GovernanceAuthorityInput): AccessDecision {
  if (!input.sessionCurrent || !input.policyCurrent)
    return { allowed: false, reason: "session_stale" };
  if (!input.departmentMatches || !input.purposeMatches)
    return { allowed: false, reason: "department_mismatch" };
  if (
    !input.capabilities.includes(input.requiredCapability) &&
    !input.capabilities.includes("administrator")
  )
    return { allowed: false, reason: "capability_missing" };
  return { allowed: true, reason: "allowed" };
}
