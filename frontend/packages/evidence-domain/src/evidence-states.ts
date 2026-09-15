import type { EvidenceReference } from "../../investigation-contracts/src";

export const evidenceStateAxes = [
  "availability",
  "integrity",
  "provenance",
  "custody",
  "signature",
  "access",
  "legalAssessment",
] as const;
export type EvidenceStateAxis = (typeof evidenceStateAxes)[number];
export function evidenceStateMatrix(reference: EvidenceReference) {
  return evidenceStateAxes.map((axis) => ({ axis, value: reference[axis] }));
}
export function hasSingleVerificationConclusion(reference: EvidenceReference): boolean {
  const runtimeReference = reference as unknown as Readonly<Record<string, unknown>>;
  return runtimeReference.singleVerificationConclusion === true;
}
