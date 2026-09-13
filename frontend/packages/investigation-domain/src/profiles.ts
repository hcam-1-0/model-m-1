export const investigationProfiles = [
  "low_resource",
  "enhanced_workstation",
  "control_room",
  "owned_gpu_lab",
  "future_server",
] as const;
export type InvestigationProfile = (typeof investigationProfiles)[number];
export interface InvestigationProfileLimits {
  readonly timelinePageSize: 10 | 25 | 50;
  readonly prefetchPages: 0 | 1 | 2;
  readonly graphNodes: 12 | 50 | 100;
  readonly graphEdges: 24 | 100 | 200;
  readonly visualDensity: "compact" | "comfortable" | "expanded";
  readonly authorityChanged: false;
  readonly semanticsChanged: false;
}
export const investigationProfileLimits: Readonly<
  Record<InvestigationProfile, InvestigationProfileLimits>
> = {
  low_resource: {
    timelinePageSize: 10,
    prefetchPages: 0,
    graphNodes: 12,
    graphEdges: 24,
    visualDensity: "compact",
    authorityChanged: false,
    semanticsChanged: false,
  },
  enhanced_workstation: {
    timelinePageSize: 25,
    prefetchPages: 1,
    graphNodes: 50,
    graphEdges: 100,
    visualDensity: "comfortable",
    authorityChanged: false,
    semanticsChanged: false,
  },
  control_room: {
    timelinePageSize: 50,
    prefetchPages: 2,
    graphNodes: 100,
    graphEdges: 200,
    visualDensity: "expanded",
    authorityChanged: false,
    semanticsChanged: false,
  },
  owned_gpu_lab: {
    timelinePageSize: 50,
    prefetchPages: 2,
    graphNodes: 100,
    graphEdges: 200,
    visualDensity: "expanded",
    authorityChanged: false,
    semanticsChanged: false,
  },
  future_server: {
    timelinePageSize: 50,
    prefetchPages: 2,
    graphNodes: 100,
    graphEdges: 200,
    visualDensity: "expanded",
    authorityChanged: false,
    semanticsChanged: false,
  },
};
export function limitsForInvestigationProfile(profile: InvestigationProfile) {
  return investigationProfileLimits[profile];
}
