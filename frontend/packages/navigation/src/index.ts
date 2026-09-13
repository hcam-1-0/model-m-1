import type { Capability, PortalId, RouteManifest, SessionProjection } from "@hcam/contracts";
import { resolveRouteAccess } from "@hcam/capabilities";

export interface PortalManifest {
  readonly id: PortalId;
  readonly titleKey: `portal.${PortalId}`;
  readonly routeBase: `/${string}`;
  readonly icon: "shield" | "radio" | "brain" | "search" | "file" | "settings" | "lock";
}
export const portals: readonly PortalManifest[] = [
  { id: "command", titleKey: "portal.command", routeBase: "/command", icon: "shield" },
  { id: "operations", titleKey: "portal.operations", routeBase: "/operations", icon: "radio" },
  {
    id: "intelligence",
    titleKey: "portal.intelligence",
    routeBase: "/intelligence",
    icon: "brain",
  },
  {
    id: "investigations",
    titleKey: "portal.investigations",
    routeBase: "/investigations",
    icon: "search",
  },
  { id: "evidence", titleKey: "portal.evidence", routeBase: "/evidence", icon: "file" },
  { id: "admin", titleKey: "portal.admin", routeBase: "/admin", icon: "settings" },
  { id: "security", titleKey: "portal.security", routeBase: "/security", icon: "lock" },
] as const;

export const routes: readonly RouteManifest[] = portals.map((portal) => ({
  routeId: `${portal.id}.overview`,
  portalId: portal.id,
  path: portal.routeBase,
  titleKey: portal.titleKey,
  requiredCapabilities: [`${portal.id}.viewer`],
  allowedQueryKeys: ["window"],
  operationIds: [],
  focusTarget: "#main-content",
  allowMultiWindow: portal.id !== "admin",
  persistence: "harmless-display-only",
}));

export function routeByPath(path: string): RouteManifest | undefined {
  return routes.find((route) => route.path === path);
}
export function visiblePortals(
  session: SessionProjection | null,
  now = new Date(),
): readonly PortalManifest[] {
  return portals.filter(
    (portal) =>
      resolveRouteAccess(
        routes.find((route) => route.portalId === portal.id),
        session,
        now,
      ).allowed,
  );
}
export function safeRouteHref(
  route: RouteManifest,
  values: Readonly<Record<string, string>> = {},
): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(values))
    if (route.allowedQueryKeys.includes(key) && /^[A-Za-z0-9_-]{1,64}$/.test(value))
      query.set(key, value);
  const suffix = query.toString();
  return suffix ? `${route.path}?${suffix}` : route.path;
}

export const operationsCameraRoutes: readonly RouteManifest[] = [
  {
    routeId: "operations.cameras",
    portalId: "operations",
    path: "/operations/cameras",
    titleKey: "camera.catalogue",
    requiredCapabilities: ["operations.viewer"],
    allowedQueryKeys: ["state", "zone", "cursor"],
    operationIds: ["listCameras"],
    focusTarget: "#main-content",
    allowMultiWindow: true,
    persistence: "none",
  },
  {
    routeId: "operations.live",
    portalId: "operations",
    path: "/operations/live",
    titleKey: "camera.live",
    requiredCapabilities: ["operations.viewer"],
    allowedQueryKeys: [],
    operationIds: ["requestGeneratedPlayback"],
    focusTarget: "#main-content",
    allowMultiWindow: true,
    persistence: "none",
  },
  {
    routeId: "operations.wall",
    portalId: "operations",
    path: "/operations/wall",
    titleKey: "camera.wall",
    requiredCapabilities: ["operations.viewer"],
    allowedQueryKeys: [],
    operationIds: ["requestGeneratedPlayback"],
    focusTarget: "#main-content",
    allowMultiWindow: true,
    persistence: "none",
  },
  {
    routeId: "operations.workspaces",
    portalId: "operations",
    path: "/operations/workspaces",
    titleKey: "camera.workspaces",
    requiredCapabilities: ["operations.viewer"],
    allowedQueryKeys: [],
    operationIds: ["listGeneratedLayouts"],
    focusTarget: "#main-content",
    allowMultiWindow: true,
    persistence: "harmless-display-only",
  },
];

export const intelligenceCenterRoutes: readonly RouteManifest[] = [
  ["overview", "/intelligence", ["listGeneratedHypotheses"]],
  ["hypotheses", "/intelligence/hypotheses", ["listGeneratedHypotheses"]],
  ["runs", "/intelligence/runs", ["listGeneratedCorrelationRuns"]],
  ["relationships", "/intelligence/relationships", ["getGeneratedRelationships"]],
  ["spatial", "/intelligence/spatial", ["getGeneratedSpatialIntelligence"]],
  ["rules", "/intelligence/rules", ["getGeneratedRuleTrace"]],
  ["alerts", "/intelligence/alerts", ["listGeneratedProposedAlerts"]],
  ["review", "/intelligence/review", ["getGeneratedReviewPolicy", "recordGeneratedReview"]],
  ["corrections", "/intelligence/corrections", ["listGeneratedCorrections"]],
  ["health", "/intelligence/health", ["getGeneratedIntelligenceHealth"]],
].map(([name, path, operationIds]) => ({
  routeId: `intelligence.${name as string}`,
  portalId: "intelligence" as const,
  path: path as `/${string}`,
  titleKey: `intelligence.${name as string}`,
  requiredCapabilities: [
    (name === "review" ? "intelligence.reviewer" : "intelligence.viewer") as Capability,
  ],
  allowedQueryKeys: ["cursor", "state", "priority"],
  operationIds: operationIds as readonly string[],
  focusTarget: "#main-content" as const,
  allowMultiWindow: true,
  persistence: "none" as const,
}));

const p55Route = (
  portalId: "investigations" | "evidence",
  name: string,
  path: `/${string}`,
  capability: Capability,
  operationIds: readonly string[],
): RouteManifest => ({
  routeId: `${portalId}.${name}`,
  portalId,
  path,
  titleKey: `${portalId}.${name}`,
  requiredCapabilities: [capability],
  allowedQueryKeys: ["cursor", "state", "revision"],
  operationIds,
  focusTarget: "#main-content",
  allowMultiWindow: true,
  persistence: "none",
});
export const investigationCenterRoutes: readonly RouteManifest[] = [
  p55Route("investigations", "overview", "/investigations", "investigations.viewer", [
    "generatedInvestigationSummary",
  ]),
  p55Route("investigations", "queue", "/investigations/queue", "investigations.viewer", [
    "generatedInvestigationQueue",
  ]),
  p55Route("investigations", "timeline", "/investigations/timeline", "investigations.viewer", [
    "generatedInvestigationTimeline",
  ]),
  p55Route(
    "investigations",
    "reconstruction",
    "/investigations/reconstruction",
    "investigations.viewer",
    ["generatedInvestigationReconstruction"],
  ),
  p55Route(
    "investigations",
    "corrections",
    "/investigations/corrections",
    "investigations.viewer",
    ["generatedInvestigationCorrections"],
  ),
];
export const evidenceCenterRoutes: readonly RouteManifest[] = [
  p55Route("evidence", "overview", "/evidence", "evidence.viewer", ["generatedEvidenceSummary"]),
  p55Route("evidence", "queue", "/evidence/queue", "evidence.viewer", ["generatedEvidenceQueue"]),
  p55Route("evidence", "integrity", "/evidence/integrity", "evidence.viewer", [
    "generatedEvidenceIntegrity",
  ]),
  p55Route("evidence", "provenance", "/evidence/provenance", "evidence.viewer", [
    "generatedEvidenceProvenance",
    "generatedEvidenceCustody",
  ]),
];

const p56Route = (
  portalId: "admin" | "security" | "operations",
  name: string,
  path: `/${string}`,
  capability: Capability,
): RouteManifest => ({
  routeId: `${portalId}.${name}`,
  portalId,
  path,
  titleKey: `${portalId}.${name}`,
  requiredCapabilities: [capability],
  allowedQueryKeys: ["cursor", "state", "domain", "lane"],
  operationIds: [`generated${portalId}${name}`],
  focusTarget: "#main-content",
  allowMultiWindow: portalId !== "admin",
  persistence: "none",
});
export const p56AdministrationRoutes = [
  "organizations",
  "identities",
  "roles",
  "changes",
  "cameras",
  "providers",
  "configuration",
  "profiles",
  "retention",
].map((name) => p56Route("admin", name, `/admin/${name}`, "admin.viewer"));
export const p56SecurityRoutes = [
  "access",
  "denials",
  "privileged",
  "sessions",
  "audit",
  "compliance",
  "supply-chain",
  "providers",
  "soc",
].map((name) => p56Route("security", name, `/security/${name}`, "security.viewer"));
export const p56PlatformOperationsRoutes = [
  "services",
  "queues",
  "data",
  "ai-runtime",
  "slo",
  "degradation",
  "recovery",
  "capacity",
  "topology",
].map((name) =>
  p56Route("operations", `platform-${name}`, `/operations/platform/${name}`, "operations.viewer"),
);
