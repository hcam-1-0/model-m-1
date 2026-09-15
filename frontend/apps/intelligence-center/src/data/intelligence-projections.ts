import { correctionImpact } from "../../../../packages/intelligence-domain/src";
import {
  generatedAlert,
  generatedCandidate,
  generatedQueue,
  generatedRelationship,
  generatedReviewPolicy,
  generatedReviews,
  generatedRuleTrace,
  generatedSpatial,
  p54UnavailableProducers,
} from "../../../../packages/intelligence-fixtures/src";
import type { ResourceId } from "@hcam/contracts";

export const generatedNow = new Date("2026-09-09T09:45:00.000Z");
export const queues = Object.freeze({
  hypotheses: generatedQueue("hypothesis", 10),
  runs: generatedQueue("correlation_run", 10),
  alerts: generatedQueue("proposed_alert", 10),
  reviews: generatedQueue("mandatory_review", 10),
  corrections: generatedQueue("correction", 6),
});
export const candidate = generatedCandidate();
export const alert = generatedAlert();
export const ruleTrace = generatedRuleTrace();
export const relationships = generatedRelationship(10);
export const spatial = generatedSpatial(10);
export const reviewPolicy = generatedReviewPolicy;
export const reviews = generatedReviews(alert.ref);
export const correction = correctionImpact("SYN-CORRECTION-0001" as ResourceId, alert.ref, [
  alert.ref,
  candidate.candidateRef,
  candidate.hypothesisRef,
]);
export const producerGaps = p54UnavailableProducers;
