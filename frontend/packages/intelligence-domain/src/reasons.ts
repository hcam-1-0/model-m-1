export const reviewReasonCodes = [
  "evidence_sufficient",
  "evidence_insufficient",
  "contradiction_unresolved",
  "context_requested",
  "operator_abstained",
] as const;
export function assertSafeReasonCode(value: string): string {
  if (!reviewReasonCodes.includes(value as (typeof reviewReasonCodes)[number]))
    throw new Error("invalid_reason_code");
  return value;
}
export function reviewReasonLabel(value: string): string {
  return (
    (
      {
        evidence_sufficient: "Evidence sufficient for record",
        evidence_insufficient: "Evidence insufficient",
        contradiction_unresolved: "Contradiction unresolved",
        context_requested: "More context requested",
        operator_abstained: "Reviewer abstained",
      } as Record<string, string>
    )[value] ?? "Reason unavailable"
  );
}
