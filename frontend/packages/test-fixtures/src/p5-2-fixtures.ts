import { asResourceId, type ResourceId } from "@hcam/contracts";

const observedAt = "2026-09-08T00:00:00.000Z";
const staleAt = "2026-09-08T01:00:00.000Z";
interface GeneratedGisFeature {
  readonly id: ResourceId;
  readonly kind: "camera" | "coverage" | "blind_spot" | "investigation";
  readonly label: string;
  readonly status: "available" | "unavailable" | "unknown";
  readonly severity: "information" | "attention" | "critical";
  readonly geometry: { readonly type: "Point"; readonly coordinates: readonly [number, number] };
  readonly freshness: {
    readonly observedAt: string;
    readonly staleAt: string;
    readonly completeness: "complete" | "unknown";
  };
  readonly sourceRevision: string;
  readonly generated: true;
}
function syntheticId(prefix: string, index: number): ResourceId {
  const value = asResourceId(`SYN-${prefix}-${String(index).padStart(4, "0")}`);
  if (!value) throw new Error("invalid_generated_identifier");
  return value;
}
export const unavailableProducers = [
  "camera_live_media",
  "camera_ptz_control",
  "dispatch_actions",
  "government_identity",
  "vehicle_owner_records",
  "biometric_matching",
  "watchlist_matching",
  "operational_risk_score",
  "real_tile_provider",
  "geocoding_provider",
  "routing_provider",
  "weather_provider",
  "field_resource_gps",
  "notification_delivery",
] as const;
export const generatedLayers = [
  {
    id: "camera_status",
    label: "Camera status",
    kinds: ["camera"],
    defaultVisible: true,
    minZoom: 0,
    maxFeatures: 50,
    requires: ["gis.viewer"],
  },
  {
    id: "coverage",
    label: "Coverage",
    kinds: ["coverage", "blind_spot"],
    defaultVisible: true,
    minZoom: 0,
    maxFeatures: 50,
    requires: ["gis.viewer"],
  },
  {
    id: "review_work",
    label: "Review work",
    kinds: ["alert", "investigation"],
    defaultVisible: true,
    minZoom: 0,
    maxFeatures: 50,
    requires: ["command.viewer"],
  },
  {
    id: "movement",
    label: "Movement",
    kinds: ["movement"],
    defaultVisible: false,
    minZoom: 1,
    maxFeatures: 50,
    requires: ["gis.viewer"],
  },
] as const;
export function generatedGisFeatures(count = 10): readonly GeneratedGisFeature[] {
  if (!Number.isInteger(count) || count < 1 || count > 50)
    throw new Error("invalid_generated_feature_count");
  return Array.from({ length: count }, (_, index) => ({
    id: syntheticId("GEO", index + 1),
    kind:
      index % 7 === 0
        ? "blind_spot"
        : index % 5 === 0
          ? "investigation"
          : index % 4 === 0
            ? "coverage"
            : "camera",
    label: `Generated sector ${String.fromCharCode(65 + (index % 6))}-${index + 1}`,
    status: index % 9 === 0 ? "unknown" : index % 6 === 0 ? "unavailable" : "available",
    severity: index % 11 === 0 ? "critical" : index % 4 === 0 ? "attention" : "information",
    geometry: {
      type: "Point" as const,
      coordinates: [((index % 10) - 4.5) * 0.08, (Math.floor(index / 10) - 2) * 0.08] as const,
    },
    freshness: { observedAt, staleAt, completeness: index % 9 === 0 ? "unknown" : "complete" },
    sourceRevision: "SYN-REV-P5-2-001",
    generated: true as const,
  }));
}
export function generatedSituationSnapshot(size = 10) {
  const workCount = Math.min(size, 50);
  return {
    contractVersion: "1.0.0",
    marker: "HCAM-GENERATED-NON-OPERATIONAL",
    departmentRef: "SYN-DEPT-01",
    revision: "SYN-REV-P5-2-001",
    freshness: { observedAt, staleAt, completeness: "partial" },
    metrics: [
      {
        id: "sources",
        label: "Source projections",
        value: String(size),
        detail: "Generated summaries",
        truth: "current",
      },
      {
        id: "review",
        label: "Awaiting review",
        value: String(Math.ceil(size / 4)),
        detail: "Mandatory human review",
        truth: "current",
      },
      {
        id: "coverage",
        label: "Coverage state",
        value: "Partial",
        detail: "No live producer",
        truth: "partial",
      },
      {
        id: "platform",
        label: "Platform state",
        value: "Generated",
        detail: "Local fixture mode",
        truth: "current",
      },
    ],
    workItems: Array.from({ length: workCount }, (_, index) => ({
      id: syntheticId("WORK", index + 1),
      label: `Generated review item ${index + 1}`,
      category: index % 3 === 0 ? "investigation" : "review",
      band: index % 9 === 0 ? "critical" : index % 3 === 0 ? "attention" : "routine",
      occurredAt: new Date(Date.parse(observedAt) - index * 60_000).toISOString(),
      sourceRevision: "SYN-REV-P5-2-001",
      generated: true,
    })),
    activity: Array.from({ length: Math.min(workCount, 12) }, (_, index) => ({
      id: syntheticId("ACT", index + 1),
      at: new Date(Date.parse(observedAt) - index * 120_000).toISOString(),
      title: `Generated timeline entry ${index + 1}`,
      detail: "No operational action was executed.",
      kind: index === 4 ? "correction" : index % 3 === 0 ? "review" : "observation",
      generated: true,
    })),
    unavailableProducers,
  };
}
