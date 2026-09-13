import type { SupplyChainRecord } from "../../security-contracts/src";
export function supplyChainAttention(record: SupplyChainRecord): readonly string[] {
  const reasons: string[] = [];
  if (record.licenseState !== "recorded") reasons.push("license_review");
  if (record.vulnerabilityState !== "current") reasons.push("vulnerability_evidence_not_current");
  if (record.provenanceState !== "verified_reference") reasons.push("provenance_not_verified");
  return reasons;
}
export const supplyChainBoundary = Object.freeze({
  scannerExecution: false,
  artifactAcquisition: false,
  attestationSigning: false,
  mutation: false,
} as const);
