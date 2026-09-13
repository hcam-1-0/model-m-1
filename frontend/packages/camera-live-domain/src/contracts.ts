export const cameraStates = ["online", "degraded", "offline", "unknown"] as const;
export const streamStates = ["available", "stale", "unavailable", "blocked"] as const;
export const healthBands = ["healthy", "attention", "critical", "unknown"] as const;
export const transports = ["hls", "native_hls", "whep", "none"] as const;
export const renditionBands = ["low", "medium", "high"] as const;
export const resourceProfiles = [
  "low_resource",
  "enhanced_workstation",
  "control_room",
  "owned_gpu_lab",
  "future_server",
] as const;
export type CameraState = (typeof cameraStates)[number];
export type StreamState = (typeof streamStates)[number];
export type HealthBand = (typeof healthBands)[number];
export type MediaTransport = (typeof transports)[number];
export type RenditionBand = (typeof renditionBands)[number];
export type ResourceProfileId = (typeof resourceProfiles)[number];

export interface FreshnessProjection {
  readonly observedAt: string;
  readonly staleAt: string;
  readonly completeness: "complete" | "partial" | "unknown";
}
export interface CapabilityProjection {
  readonly status: "fresh" | "stale" | "unavailable" | "unknown";
  readonly observedAt: string | null;
  readonly profileCount: number | null;
  readonly transports: readonly MediaTransport[];
  readonly codecs: readonly string[];
  readonly mediaOnly: boolean;
}
export interface ProbeProjection {
  readonly state: "succeeded" | "failed" | "pending" | "unavailable";
  readonly checkedAt: string | null;
  readonly safeReason: CameraReason | null;
  readonly latencyMs: number | null;
}
export interface StreamProjection {
  readonly id: string;
  readonly label: string;
  readonly state: StreamState;
  readonly health: HealthBand;
  readonly freshness: FreshnessProjection;
  readonly preferredTransport: MediaTransport;
  readonly availableRenditions: readonly RenditionBand[];
  readonly capabilities: CapabilityProjection;
  readonly probe: ProbeProjection;
  readonly generated: true;
}
export interface CameraProjection {
  readonly id: string;
  readonly label: string;
  readonly shortLocation: string;
  readonly zone: string;
  readonly departmentRef: string;
  readonly state: CameraState;
  readonly health: HealthBand;
  readonly configured: boolean;
  readonly freshness: FreshnessProjection;
  readonly streams: readonly StreamProjection[];
  readonly tags: readonly string[];
  readonly generated: true;
}
export interface BrowserMediaCapabilities {
  readonly mse: boolean;
  readonly nativeHls: boolean;
  readonly webrtc: boolean;
  readonly codecs: readonly string[];
}
export interface AdmissionRequest {
  readonly streamId: string;
  readonly priority: number;
  readonly intent?: "single" | "incident" | "pinned" | "selected" | "visible" | "near" | "hidden";
  readonly pinned?: boolean;
  readonly health?: HealthBand;
  readonly decodeUnits?: number;
  readonly networkUnits?: number;
  readonly serverUnits?: number;
  readonly requestedTransport: MediaTransport;
  readonly requestedRendition: RenditionBand;
  readonly visible: boolean;
  readonly focused: boolean;
}
export interface AdmissionBudget {
  readonly decodeUnits: number;
  readonly networkUnits: number;
  readonly serverUnits: number;
}
export interface AdmissionDecision {
  readonly streamId: string;
  readonly admitted: boolean;
  readonly transport: MediaTransport;
  readonly rendition: RenditionBand | null;
  readonly rank: number;
  readonly reason: CameraReason;
}
export type CameraReason =
  | "ready"
  | "generated_only"
  | "producer_unavailable"
  | "department_denied"
  | "capability_unknown"
  | "browser_unsupported"
  | "profile_budget_exceeded"
  | "grant_expired"
  | "grant_revoked"
  | "manifest_invalid"
  | "stream_stalled"
  | "cooldown_active"
  | "circuit_open"
  | "fallback_to_hls"
  | "teardown_complete"
  | "layout_conflict";

const safeId = /^SYN-[A-Z0-9-]{3,48}$/u;
function includesValue<T extends string>(values: readonly T[], value: unknown): value is T {
  return typeof value === "string" && values.some((candidate) => candidate === value);
}
export function isGeneratedCameraProjection(value: unknown): value is CameraProjection {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<CameraProjection>;
  return (
    item.generated === true &&
    typeof item.id === "string" &&
    safeId.test(item.id) &&
    typeof item.label === "string" &&
    item.label.length > 0 &&
    item.label.length <= 120 &&
    typeof item.departmentRef === "string" &&
    safeId.test(item.departmentRef) &&
    Array.isArray(item.streams) &&
    item.streams.length <= 4 &&
    includesValue(cameraStates, item.state) &&
    includesValue(healthBands, item.health)
  );
}
