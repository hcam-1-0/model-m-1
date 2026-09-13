export const administrationGeneratedMarker = "HCAM-GENERATED-NON-OPERATIONAL" as const;
export type AdminResourceKind =
  | "organization"
  | "department"
  | "user"
  | "membership"
  | "role"
  | "permission"
  | "policy"
  | "camera"
  | "stream"
  | "provider"
  | "configuration"
  | "resource_profile"
  | "retention_policy";
export type ProjectionState = "current" | "partial" | "stale" | "unknown" | "unavailable";
export interface ProjectionTruth {
  readonly source: "generated_fixture";
  readonly observedAt: string;
  readonly staleAt: string;
  readonly completeness: "complete" | "partial" | "unknown";
  readonly limitations: readonly string[];
}
export interface AdminResource {
  readonly ref: string;
  readonly kind: AdminResourceKind;
  readonly label: string;
  readonly departmentRef: string;
  readonly state: ProjectionState;
  readonly revision: number;
  readonly etag: string;
  readonly effective: false;
  readonly truth: ProjectionTruth;
  readonly generated: true;
}
export interface AdminCatalogue {
  readonly contractVersion: "1.0.0";
  readonly marker: typeof administrationGeneratedMarker;
  readonly items: readonly AdminResource[];
  readonly nextCursor: string | null;
  readonly authoritativeOrder: "server_sequence_then_ref";
}
const adminCatalogueKeys = new Set([
  "contractVersion",
  "marker",
  "items",
  "nextCursor",
  "authoritativeOrder",
]);
const adminResourceKeys = new Set([
  "ref",
  "kind",
  "label",
  "departmentRef",
  "state",
  "revision",
  "etag",
  "effective",
  "truth",
  "generated",
]);
function hasOnlyKeys(value: object, allowed: ReadonlySet<string>): boolean {
  return Object.keys(value).every((key) => allowed.has(key));
}
export function isAdminCatalogue(value: unknown): value is AdminCatalogue {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const item = value as Partial<AdminCatalogue>;
  return (
    hasOnlyKeys(value, adminCatalogueKeys) &&
    item.contractVersion === "1.0.0" &&
    item.marker === administrationGeneratedMarker &&
    (item.nextCursor === null || typeof item.nextCursor === "string") &&
    item.authoritativeOrder === "server_sequence_then_ref" &&
    Array.isArray(item.items) &&
    item.items.length <= 500 &&
    item.items.every((resource: unknown) => {
      if (!resource || typeof resource !== "object" || Array.isArray(resource)) return false;
      if (!hasOnlyKeys(resource, adminResourceKeys)) return false;
      const candidate = resource as Partial<AdminResource>;
      return (
        candidate.generated === true &&
        candidate.effective === false &&
        typeof candidate.ref === "string" &&
        candidate.ref.startsWith("SYN-")
      );
    })
  );
}
