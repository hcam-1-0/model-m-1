import {
  generatedCustodyEvents,
  generatedEvidenceHandoff,
  generatedEvidenceReferences,
  generatedInvestigationHealth,
  generatedPolicyPreview,
  generatedProvenance,
  generatedVerificationHistory,
  p55Threats,
  p55UnavailableProducers,
} from "../../../../packages/investigation-fixtures/src";

export const evidenceReferences = generatedEvidenceReferences(18);
export const selectedEvidence = evidenceReferences[0];
export const verificationHistory = generatedVerificationHistory(1);
export const provenanceProjection = generatedProvenance(10);
export const custodyEvents = generatedCustodyEvents(1);
export const policyPreviews = Array.from({ length: 5 }, (_, index) =>
  generatedPolicyPreview(index + 1),
);
export const evidenceHandoff = generatedEvidenceHandoff(1);
export const evidenceHealth = generatedInvestigationHealth;
export const producerGaps = p55UnavailableProducers;
export const threats = p55Threats;
