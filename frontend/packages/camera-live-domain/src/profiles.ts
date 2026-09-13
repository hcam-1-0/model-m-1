import type { RenditionBand, ResourceProfileId } from "./contracts";

export interface ResourceProfile {
  readonly id: ResourceProfileId;
  readonly maxStreams: number;
  readonly preferredRendition: RenditionBand;
  readonly maxFps: number;
  readonly recoveryConcurrency: number;
  readonly animations: boolean;
}
export const profileRegistry: Readonly<Record<ResourceProfileId, ResourceProfile>> = Object.freeze({
  low_resource: {
    id: "low_resource",
    maxStreams: 1,
    preferredRendition: "low",
    maxFps: 10,
    recoveryConcurrency: 1,
    animations: false,
  },
  enhanced_workstation: {
    id: "enhanced_workstation",
    maxStreams: 4,
    preferredRendition: "medium",
    maxFps: 20,
    recoveryConcurrency: 2,
    animations: true,
  },
  control_room: {
    id: "control_room",
    maxStreams: 10,
    preferredRendition: "high",
    maxFps: 25,
    recoveryConcurrency: 3,
    animations: true,
  },
  owned_gpu_lab: {
    id: "owned_gpu_lab",
    maxStreams: 10,
    preferredRendition: "high",
    maxFps: 25,
    recoveryConcurrency: 4,
    animations: true,
  },
  future_server: {
    id: "future_server",
    maxStreams: 10,
    preferredRendition: "high",
    maxFps: 25,
    recoveryConcurrency: 4,
    animations: true,
  },
});
export function getResourceProfile(id: ResourceProfileId): ResourceProfile {
  return profileRegistry[id];
}
export function clampRequestedStreams(id: ResourceProfileId, requested: number): number {
  if (!Number.isInteger(requested) || requested < 0) return 0;
  return Math.min(requested, profileRegistry[id].maxStreams);
}
