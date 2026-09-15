import type { Freshness, ResourceId } from "@hcam/contracts";

export const gisFeatureKinds = [
  "camera",
  "coverage",
  "blind_spot",
  "alert",
  "investigation",
  "movement",
  "resource",
] as const;
export type GisFeatureKind = (typeof gisFeatureKinds)[number];
export type GisGeometry =
  | { readonly type: "Point"; readonly coordinates: readonly [number, number] }
  | { readonly type: "LineString"; readonly coordinates: readonly (readonly [number, number])[] }
  | {
      readonly type: "Polygon";
      readonly coordinates: readonly (readonly (readonly [number, number])[])[];
    };
export interface GisFeatureSummary {
  readonly id: ResourceId;
  readonly kind: GisFeatureKind;
  readonly label: string;
  readonly status: "available" | "unavailable" | "unknown";
  readonly severity: "none" | "information" | "attention" | "critical";
  readonly geometry: GisGeometry;
  readonly freshness: Freshness;
  readonly sourceRevision: string;
  readonly generated: true;
}
export interface GisViewport {
  readonly west: number;
  readonly south: number;
  readonly east: number;
  readonly north: number;
  readonly zoom: number;
}
export type GisRendererMode = "maplibre" | "deck_overlaid" | "deck_interleaved" | "list_only";
export type GisDowngradeReason =
  | "requested"
  | "webgl_unavailable"
  | "webgl2_unavailable"
  | "policy_denied"
  | "health_downgrade"
  | "profile_limit"
  | "renderer_failed";
export interface GisAdmission {
  readonly admitted: boolean;
  readonly mode: GisRendererMode;
  readonly reason: GisDowngradeReason;
  readonly listFallback: true;
}
export interface GisLayerDefinition {
  readonly id: string;
  readonly label: string;
  readonly kinds: readonly GisFeatureKind[];
  readonly defaultVisible: boolean;
  readonly minZoom: number;
  readonly maxFeatures: number;
  readonly requires: readonly string[];
}
export interface GisTimeWindow {
  readonly from: string;
  readonly to: string;
  readonly serverNow: string;
}
export interface GisSelection {
  readonly selected: readonly ResourceId[];
  readonly focused: ResourceId | null;
  readonly revision: number;
}
export interface GisProviderDefinition {
  readonly id: string;
  readonly enabled: false;
  readonly destination: string;
  readonly purpose: string;
}
export interface GisAdapter {
  readonly kind: GisRendererMode;
  admit(): GisAdmission;
  list(viewport: GisViewport): Promise<readonly GisFeatureSummary[]>;
  focus(id: ResourceId): Promise<boolean>;
  dispose(): void;
}

export function validateViewport(value: unknown): value is GisViewport {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const keys = Object.keys(value);
  if (
    keys.length !== 5 ||
    !keys.every((key) => ["west", "south", "east", "north", "zoom"].includes(key))
  )
    return false;
  const viewport = value as Partial<GisViewport>;
  const within = (candidate: unknown, minimum: number, maximum: number): candidate is number =>
    typeof candidate === "number" &&
    Number.isFinite(candidate) &&
    candidate >= minimum &&
    candidate <= maximum;
  return (
    within(viewport.west, -180, 180) &&
    within(viewport.south, -90, 90) &&
    within(viewport.east, -180, 180) &&
    within(viewport.north, -90, 90) &&
    within(viewport.zoom, 0, 24) &&
    viewport.west < viewport.east &&
    viewport.south < viewport.north
  );
}
export function geometryIsBounded(geometry: GisGeometry): boolean {
  const points: readonly (readonly [number, number])[] =
    geometry.type === "Point"
      ? [geometry.coordinates]
      : geometry.type === "LineString"
        ? geometry.coordinates
        : geometry.coordinates.flat();
  return (
    points.length > 0 &&
    points.length <= 10_000 &&
    points.every(([x, y]) => x >= -180 && x <= 180 && y >= -90 && y <= 90)
  );
}
