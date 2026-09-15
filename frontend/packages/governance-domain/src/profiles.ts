export const governanceProfiles = [
  "low_resource",
  "enhanced_workstation",
  "control_room",
  "owned_GPU_lab",
  "future_server",
  "future_Kubernetes",
] as const;
export type GovernanceProfile = (typeof governanceProfiles)[number];
export interface GovernanceProfileProjection {
  readonly profile: GovernanceProfile;
  readonly rowLimit: 25 | 50 | 100 | 250;
  readonly refreshSeconds: 15 | 30 | 60;
  readonly visualization: "table_only" | "table_and_summary" | "multi_panel";
  readonly authorityInvariant: true;
  readonly scopeInvariant: true;
  readonly actionEligibilityInvariant: true;
}
export function governanceProfile(profile: GovernanceProfile): GovernanceProfileProjection {
  const enhanced = ["control_room", "owned_GPU_lab", "future_server", "future_Kubernetes"].includes(
    profile,
  );
  return {
    profile,
    rowLimit: profile === "low_resource" ? 25 : enhanced ? 250 : 100,
    refreshSeconds: profile === "low_resource" ? 60 : enhanced ? 15 : 30,
    visualization:
      profile === "low_resource" ? "table_only" : enhanced ? "multi_panel" : "table_and_summary",
    authorityInvariant: true,
    scopeInvariant: true,
    actionEligibilityInvariant: true,
  };
}
