import type { ResourceId } from "@hcam/contracts";
import type { CorrectionImpact } from "../../intelligence-contracts/src";

export function correctionImpact(
  correctionRef: ResourceId,
  correctedRef: ResourceId,
  impactedRefs: readonly ResourceId[],
): CorrectionImpact {
  return Object.freeze({
    correctionRef,
    correctedRef,
    impactedRefs: [...new Set(impactedRefs)].slice(0, 100),
    viewsMarkedStale: ["overview", "queue", "detail", "relationship", "spatial"],
    mutationDisabled: true,
    requiresRefetch: true,
    historyRewritten: false,
  });
}
