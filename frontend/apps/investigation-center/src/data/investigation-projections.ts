import {
  compareRevisions,
  eventContextChronology,
  recordChronology,
  summarizeImpactClosure,
} from "../../../../packages/investigation-domain/src";
import {
  generatedCorrection,
  generatedEvidenceReferences,
  generatedInvestigationHealth,
  generatedInvestigationQueue,
  generatedPolicyPreview,
  generatedProvenance,
  generatedReconstruction,
  generatedTimelinePage,
  investigationWorkloads,
  p55Threats,
  p55UnavailableProducers,
} from "../../../../packages/investigation-fixtures/src";

export const generatedNow = new Date("2026-09-09T11:00:00.000Z");
export const investigationQueue = generatedInvestigationQueue(10);
export const selectedInvestigation = investigationQueue.items[0];
export const timelinePage = generatedTimelinePage(25);
export const recordTimeline = recordChronology(timelinePage.items);
export const eventContextTimeline = eventContextChronology(timelinePage.items);
export const reconstructionBefore = generatedReconstruction(7, "partial");
export const reconstructionAfter = generatedReconstruction(8, "complete");
export const revisionComparison = compareRevisions(reconstructionBefore, reconstructionAfter);
export const correction = generatedCorrection(1);
export const impactClosure = summarizeImpactClosure(correction.impactTargets);
export const evidenceReferences = generatedEvidenceReferences(8);
export const investigationRelationships = generatedProvenance(10);
export const policyPreview = generatedPolicyPreview(1);
export const investigationHealth = generatedInvestigationHealth;
export const workloads = investigationWorkloads;
export const producerGaps = p55UnavailableProducers;
export const threats = p55Threats;
