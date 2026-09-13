export const operationsProfiles = [
  "low_resource",
  "enhanced_workstation",
  "control_room",
  "owned_GPU_lab",
  "future_server",
  "future_Kubernetes",
] as const;
export type OperationsProfile = (typeof operationsProfiles)[number];
export function operationsProfilePresentation(profile: OperationsProfile) {
  const dense = profile === "control_room" || profile.startsWith("future_");
  return {
    profile,
    visibleRows: profile === "low_resource" ? 10 : dense ? 50 : 25,
    panels: profile === "low_resource" ? 1 : dense ? 4 : 2,
    chartDetail: profile === "low_resource" ? "summary" : "bounded_detail",
    authorityInvariant: true,
    truthInvariant: true,
    accessibilityInvariant: true,
  } as const;
}
