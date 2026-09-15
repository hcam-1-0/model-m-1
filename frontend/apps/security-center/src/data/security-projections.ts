import {
  generatedAuditReferences,
  generatedComplianceControls,
  generatedDenials,
  generatedProviderPosture,
  generatedSupplyChain,
} from "../../../../packages/admin-security-operations-fixtures/src";
export const denialActivity = generatedDenials(18);
export const auditReferences = generatedAuditReferences(16);
export const complianceControls = generatedComplianceControls(12);
export const supplyChainRecords = generatedSupplyChain(14);
export const providerPosture = generatedProviderPosture(8);
export const securitySummary = Object.freeze({
  posture: "partial",
  accessDecisions: 1240,
  denials: denialActivity.length,
  privilegedReviews: 7,
  staleEvidence: supplyChainRecords.filter((item) => item.vulnerabilityState === "stale").length,
  threatsCovered: 72,
  generated: true,
} as const);
