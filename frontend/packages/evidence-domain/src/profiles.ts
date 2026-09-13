export const evidenceProfiles = [
  "low_resource",
  "enhanced_workstation",
  "control_room",
  "owned_gpu_lab",
  "future_server",
] as const;
export type EvidenceProfile = (typeof evidenceProfiles)[number];
export interface EvidenceProfileLimits {
  readonly pageSize: 10 | 25 | 50;
  readonly graphNodes: 12 | 50 | 100;
  readonly graphEdges: 24 | 100 | 200;
  readonly visualDetail: "minimal" | "standard" | "enhanced";
  readonly sourceAccessChanged: false;
  readonly authorityChanged: false;
}
export const evidenceProfileLimits: Readonly<Record<EvidenceProfile, EvidenceProfileLimits>> = {
  low_resource: {
    pageSize: 10,
    graphNodes: 12,
    graphEdges: 24,
    visualDetail: "minimal",
    sourceAccessChanged: false,
    authorityChanged: false,
  },
  enhanced_workstation: {
    pageSize: 25,
    graphNodes: 50,
    graphEdges: 100,
    visualDetail: "standard",
    sourceAccessChanged: false,
    authorityChanged: false,
  },
  control_room: {
    pageSize: 50,
    graphNodes: 100,
    graphEdges: 200,
    visualDetail: "enhanced",
    sourceAccessChanged: false,
    authorityChanged: false,
  },
  owned_gpu_lab: {
    pageSize: 50,
    graphNodes: 100,
    graphEdges: 200,
    visualDetail: "enhanced",
    sourceAccessChanged: false,
    authorityChanged: false,
  },
  future_server: {
    pageSize: 50,
    graphNodes: 100,
    graphEdges: 200,
    visualDetail: "enhanced",
    sourceAccessChanged: false,
    authorityChanged: false,
  },
};
export function limitsForEvidenceProfile(profile: EvidenceProfile) {
  return evidenceProfileLimits[profile];
}
