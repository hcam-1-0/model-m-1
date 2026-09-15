import type { SloProjection } from "../../operations-contracts/src";
export function sloAttention(slo: SloProjection): "none" | "watch" | "stop" | "unknown" {
  if (slo.budgetState === "healthy") return "none";
  if (slo.budgetState === "watch") return "watch";
  if (slo.budgetState === "exhausted") return "stop";
  return "unknown";
}
export const generatedSloBoundary = Object.freeze({
  productionTarget: false,
  capacityClaim: false,
  hardwareBenchmark: false,
  generatedEvidenceOnly: true,
} as const);
