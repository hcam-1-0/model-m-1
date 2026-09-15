import type { CameraProjection, CameraReason, StreamProjection } from "./contracts";

export type LiveUiState =
  | "loading"
  | "empty"
  | "ready"
  | "partial"
  | "stale"
  | "degraded"
  | "denied"
  | "failure"
  | "unknown";
export function cameraListState(
  cameras: readonly CameraProjection[] | null,
  now: Date,
): LiveUiState {
  if (cameras === null) return "loading";
  if (cameras.length === 0) return "empty";
  if (cameras.every((camera) => camera.state === "unknown")) return "unknown";
  if (cameras.every((camera) => Date.parse(camera.freshness.staleAt) <= now.getTime()))
    return "stale";
  if (cameras.every((camera) => camera.state === "offline")) return "failure";
  if (cameras.some((camera) => camera.state !== "online")) return "partial";
  return "ready";
}
export function streamState(stream: StreamProjection, reason: CameraReason | null): LiveUiState {
  if (reason === "department_denied") return "denied";
  if (reason === "producer_unavailable" || stream.state === "blocked") return "degraded";
  if (stream.state === "stale") return "stale";
  if (stream.state === "unavailable") return "failure";
  if (stream.health === "unknown") return "unknown";
  return stream.health === "healthy" ? "ready" : "partial";
}
