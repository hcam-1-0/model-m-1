export const intelligenceProfiles = [
  "low_resource",
  "enhanced_workstation",
  "control_room",
  "owned_gpu_lab",
  "future_server",
] as const;
export type IntelligenceProfile = (typeof intelligenceProfiles)[number];
export interface IntelligenceProfileLimits {
  readonly queuePageSize: 10 | 25 | 50;
  readonly graphNodes: 12 | 50 | 100;
  readonly graphEdges: 24 | 100 | 200;
  readonly motion: "reduced" | "standard";
  readonly authorityChanged: false;
}
export const intelligenceProfileLimits: Readonly<
  Record<IntelligenceProfile, IntelligenceProfileLimits>
> = {
  low_resource: {
    queuePageSize: 10,
    graphNodes: 12,
    graphEdges: 24,
    motion: "reduced",
    authorityChanged: false,
  },
  enhanced_workstation: {
    queuePageSize: 25,
    graphNodes: 50,
    graphEdges: 100,
    motion: "standard",
    authorityChanged: false,
  },
  control_room: {
    queuePageSize: 50,
    graphNodes: 100,
    graphEdges: 200,
    motion: "standard",
    authorityChanged: false,
  },
  owned_gpu_lab: {
    queuePageSize: 50,
    graphNodes: 100,
    graphEdges: 200,
    motion: "standard",
    authorityChanged: false,
  },
  future_server: {
    queuePageSize: 50,
    graphNodes: 100,
    graphEdges: 200,
    motion: "standard",
    authorityChanged: false,
  },
};
export function limitsForIntelligenceProfile(profile: IntelligenceProfile) {
  return intelligenceProfileLimits[profile];
}
