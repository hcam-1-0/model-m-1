import type {
  AdmissionRequest,
  CameraProjection,
  RenditionBand,
  ResourceProfileId,
  WorkspaceLayout,
} from "@hcam/camera-live-domain";
import type { PlaybackSessionGrant } from "@hcam/media-edge-contracts";

export const p53GeneratedMarker = "HCAM-GENERATED-NON-OPERATIONAL" as const;
const observedAt = "2026-09-08T09:00:00.000Z";
const staleAt = "2026-09-08T09:05:00.000Z";
const locations = [
  ["North gate", "Sector A"],
  ["Transit entry", "Sector B"],
  ["Service lane", "Sector C"],
  ["Public concourse", "Sector D"],
  ["Parking entry", "Sector E"],
  ["Loading area", "Sector F"],
  ["East gate", "Sector A"],
  ["West passage", "Sector B"],
  ["South gate", "Sector C"],
  ["Control perimeter", "Sector D"],
] as const;
const renditionSets: readonly (readonly RenditionBand[])[] = [
  ["low", "medium"],
  ["low", "medium", "high"],
  ["low"],
];
export function generatedCameras(count = 10): readonly CameraProjection[] {
  if (!Number.isInteger(count) || count < 1 || count > 10)
    throw new Error("invalid_generated_camera_count");
  return Array.from({ length: count }, (_, index) => {
    const number = String(index + 1).padStart(4, "0");
    const locationEntry = locations[index];
    const availableRenditions = renditionSets[index % renditionSets.length];
    if (!locationEntry || !availableRenditions)
      throw new Error("generated_camera_fixture_incomplete");
    const [location, zone] = locationEntry;
    const state =
      index === 7 ? "offline" : index === 5 ? "degraded" : index === 9 ? "unknown" : "online";
    const health =
      state === "online"
        ? "healthy"
        : state === "degraded"
          ? "attention"
          : state === "offline"
            ? "critical"
            : "unknown";
    return {
      id: `SYN-CAM-${number}`,
      label: `Generated camera ${number}`,
      shortLocation: location,
      zone,
      departmentRef: "SYN-DEPT-01",
      state,
      health,
      configured: true,
      freshness: {
        observedAt,
        staleAt: index === 6 ? observedAt : staleAt,
        completeness: index === 9 ? "unknown" : index === 5 ? "partial" : "complete",
      },
      streams: [
        {
          id: `SYN-STREAM-${number}`,
          label: "Primary generated stream",
          state:
            state === "online"
              ? "available"
              : state === "degraded"
                ? "stale"
                : state === "offline"
                  ? "unavailable"
                  : "blocked",
          health,
          freshness: {
            observedAt,
            staleAt: index === 6 ? observedAt : staleAt,
            completeness: index === 9 ? "unknown" : "complete",
          },
          preferredTransport: index % 4 === 0 ? "whep" : "hls",
          availableRenditions,
          capabilities: {
            status: index === 9 ? "unknown" : index === 6 ? "stale" : "fresh",
            observedAt: index === 9 ? null : observedAt,
            profileCount: index === 9 ? null : 2 + (index % 3),
            transports: index % 4 === 0 ? ["hls", "whep"] : ["hls"],
            codecs: index === 9 ? [] : ["H.264"],
            mediaOnly: index % 3 === 0,
          },
          probe: {
            state:
              state === "online" ? "succeeded" : state === "degraded" ? "failed" : "unavailable",
            checkedAt: state === "unknown" ? null : observedAt,
            safeReason: state === "online" ? "generated_only" : "producer_unavailable",
            latencyMs: state === "online" ? 34 + index * 7 : null,
          },
          generated: true,
        },
      ],
      tags: [zone.toLowerCase().replace(" ", "-"), index % 2 === 0 ? "entry" : "public-area"],
      generated: true,
    } satisfies CameraProjection;
  });
}
export function generatedAdmissionRequests(count = 10): readonly AdmissionRequest[] {
  return generatedCameras(count).map((camera, index) => {
    const stream = camera.streams[0];
    if (!stream) throw new Error("generated_camera_stream_missing");
    return {
      streamId: stream.id,
      priority: 100 - index,
      requestedTransport: stream.preferredTransport,
      requestedRendition: "high",
      visible: true,
      focused: index === 0,
      pinned: index === 1,
      intent: index === 0 ? "single" : index === 1 ? "pinned" : "visible",
      health: camera.health,
      decodeUnits: index % 3 === 0 ? 2 : 1,
      networkUnits: index % 2 === 0 ? 2 : 1,
      serverUnits: 1,
    };
  });
}
export function generatedLayout(count = 4, revision = 1): WorkspaceLayout {
  if (!Number.isInteger(count) || count < 1 || count > 10)
    throw new Error("invalid_generated_layout_count");
  return {
    id: "SYN-LAYOUT-0001",
    name: "Generated operations wall",
    revision,
    etag: `SYN-ETAG-${String(revision).padStart(4, "0")}`,
    columns: count === 1 ? 1 : count <= 4 ? 2 : count <= 9 ? 3 : 4,
    tiles: generatedCameras(count).map((camera, index) => {
      const stream = camera.streams[0];
      if (!stream) throw new Error("generated_camera_stream_missing");
      return {
        tileId: `SYN-TILE-${String(index + 1).padStart(4, "0")}`,
        streamId: stream.id,
        order: index,
      };
    }),
    generated: true,
  };
}
export function generatedPlaybackGrant(
  streamRef = "SYN-STREAM-0001",
  transport: "hls" | "native_hls" | "whep" = "hls",
): PlaybackSessionGrant {
  const suffix = streamRef.slice(-4);
  return {
    sessionRef: `SYN-SESSION-${suffix}`,
    streamRef,
    transport,
    rendition: "low",
    mediaPath: `/media-edge/sessions/SYN-SESSION-${suffix}/${transport === "whep" ? "whep" : "master.m3u8"}`,
    grant: `g1_GENERATED_NON_ISSUABLE_${suffix}_TOKEN`,
    issuedAt: "2026-09-08T09:00:00.000Z",
    expiresAt: "2026-09-08T09:01:30.000Z",
    sourceRevision: "SYN-REV-P5-3-001",
    generated: true,
  };
}
export const generatedProfiles: readonly ResourceProfileId[] = [
  "low_resource",
  "enhanced_workstation",
  "control_room",
  "owned_gpu_lab",
  "future_server",
];
export const p53UnavailableProducers = [
  "camera_catalogue_api",
  "camera_detail_api",
  "stream_diagnostics_api",
  "capability_snapshot_api",
  "probe_history_api",
  "playback_session_api",
  "media_edge_hls",
  "media_edge_whep",
  "admission_service",
  "profile_service",
  "layout_service",
  "layout_event_stream",
  "grant_revocation_stream",
  "camera_health_stream",
  "stream_health_stream",
  "browser_codec_policy",
  "investigation_handoff_api",
  "operational_metrics_backend",
  "audit_backend",
  "owned_lab_validation",
] as const;
