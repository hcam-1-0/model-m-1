import type { EvidenceHandoff, EvidenceReference } from "../../investigation-contracts/src";

export interface EvidenceAccessContext {
  readonly departmentRef: string;
  readonly purposeCode: string;
  readonly capabilities: readonly string[];
  readonly investigationRef: string;
}
export function authorizeEvidenceReference(
  reference: EvidenceReference,
  handoff: EvidenceHandoff,
  context: EvidenceAccessContext,
): boolean {
  const runtimeHandoff = handoff as unknown as Readonly<Record<string, unknown>>;
  return (
    reference.investigationRef === handoff.investigationRef &&
    reference.ref === handoff.evidenceRef &&
    handoff.departmentRef === context.departmentRef &&
    handoff.purposeCode === context.purposeCode &&
    context.investigationRef === reference.investigationRef &&
    context.capabilities.includes(handoff.capability) &&
    runtimeHandoff.sourceOperationAuthorized === false
  );
}
