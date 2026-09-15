import type { DegradationProjection } from "../../operations-contracts/src";
export function allowedDegradationActions(
  state: DegradationProjection["state"],
): readonly string[] {
  if (state === "normal") return ["inspect"];
  if (state === "constrained") return ["inspect", "open_generated_preview"];
  if (state === "recovering") return ["inspect", "review_generated_evidence"];
  return ["inspect"];
}
export const killSwitchBoundary = Object.freeze({
  proposedStateVisible: true,
  currentStateSourceRequired: true,
  directToggleAvailable: false,
  automaticActivation: false,
} as const);
