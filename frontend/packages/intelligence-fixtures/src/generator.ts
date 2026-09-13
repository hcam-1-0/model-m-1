import type { ResourceId } from "@hcam/contracts";
import {
  generatedMarker,
  type CandidateEvidence,
  type IntelligenceQueue,
  type ProposedAlert,
  type QueueKind,
  type RelationshipProjection,
  type ReviewPolicy,
  type ReviewRecord,
  type RuleTrace,
  type SpatialProjection,
} from "../../intelligence-contracts/src";

const ref = (prefix: string, value: number) =>
  `SYN-${prefix}-${String(value).padStart(4, "0")}` as ResourceId;
const priorities = ["urgent_review", "elevated_review", "standard_review", "unknown"] as const;
const queueConcept = {
  hypothesis: "hypothesis",
  correlation_run: "inference",
  proposed_alert: "proposed_alert",
  mandatory_review: "review",
  correction: "correction",
} as const;

export function generatedQueue(queue: QueueKind, count = 10): IntelligenceQueue {
  const bounded = Math.max(0, Math.min(count, 50));
  return {
    contractVersion: "1.0.0",
    marker: generatedMarker,
    queue,
    departmentRef: "SYN-DEPT-01",
    orderedBy: "server_priority_then_age_then_ref",
    nextCursor: bounded < count ? `SYN-CURSOR-${bounded}` : null,
    totalApproximate: bounded,
    items: Array.from({ length: bounded }, (_, index) => ({
      ref: ref(queue.replace("_", "-").toUpperCase(), index + 1),
      queue,
      title: `${queue.replaceAll("_", " ")} ${String(index + 1).padStart(2, "0")}`,
      summary:
        index % 4 === 0
          ? "Generated evidence has unresolved contradiction."
          : "Generated analytical item awaiting bounded operator assessment.",
      concept: queueConcept[queue],
      priority: priorities[index % priorities.length] ?? "unknown",
      state:
        index % 7 === 0 ? "correction_pending" : index % 5 === 0 ? "partial" : "awaiting_review",
      ageMinutes: 4 + index * 7,
      revision: index + 1,
      etag: `"SYN-ETAG-${index + 1}"`,
      freshness: {
        observedAt: `2026-09-09T09:${String(index % 60).padStart(2, "0")}:00.000Z`,
        staleAt: `2026-09-09T10:${String(index % 60).padStart(2, "0")}:00.000Z`,
        completeness: index % 5 === 0 ? "partial" : "complete",
      },
      generated: true,
    })),
  };
}

export function generatedCandidate(index = 1): CandidateEvidence {
  const roles = ["supports", "contradicts", "ambiguous", "missing"] as const;
  return {
    candidateRef: ref("CANDIDATE", index),
    hypothesisRef: ref("HYPOTHESIS", index),
    fields: ["appearance class", "movement window", "zone sequence", "source quality"].map(
      (field, fieldIndex) => ({
        field,
        displayValue:
          fieldIndex === 3 ? "Partial source quality" : `Generated attribute ${fieldIndex + 1}`,
        role: roles[fieldIndex] ?? "missing",
        confidenceBand: fieldIndex === 3 ? "not_scored" : fieldIndex === 0 ? "high" : "medium",
        calibrated: fieldIndex !== 3,
        stale: fieldIndex === 2,
        provenanceRef: ref("OBS", index * 10 + fieldIndex),
        limitation:
          fieldIndex === 0 ? "Appearance may not be unique." : "Generated comparison only.",
      }),
    ),
    abstained: true,
    identityEstablished: false,
    generated: true,
  };
}

export function generatedAlert(index = 1): ProposedAlert {
  return {
    ref: ref("ALERT", index),
    semanticIdentity: `SYN-SEM-${index}`,
    title: `Proposed zone-transition alert ${String(index).padStart(2, "0")}`,
    priority: priorities[(index - 1) % priorities.length] ?? "unknown",
    lifecycle: index % 3 === 0 ? "in_review" : "proposed",
    hypothesisRef: ref("HYPOTHESIS", index),
    candidateRefs: [ref("CANDIDATE", index)],
    identityEstablished: false,
    operationalAuthority: false,
    etag: `"SYN-ETAG-${index}"`,
    revision: index,
    generated: true,
  };
}

export function generatedRuleTrace(index = 1): RuleTrace {
  const nodeTypes = ["input", "predicate", "temporal", "geometry", "result", "abstention"] as const;
  return {
    evaluationRef: ref("EVAL", index),
    ruleRef: ref("RULE", 1),
    ruleRevision: 7,
    normalizedAt: "2026-09-09T09:30:00.000Z",
    timerWindow: "PT5M",
    result: "abstained",
    exactSteps: nodeTypes.map((nodeType, step) => ({
      sequence: step + 1,
      nodeType,
      label: `${nodeType} step`,
      result: step === 5 ? "abstain" : step === 3 ? "unknown" : "pass",
      normalizedInput: `SYN-IN-${step + 1}`,
      limitation: step === 3 ? "Generated geometry source is partial." : null,
    })),
    generated: true,
  };
}

export function generatedRelationship(scale: 1 | 10 | 50 = 10): RelationshipProjection {
  const ceiling =
    scale === 1 ? ([12, 24] as const) : scale === 10 ? ([50, 100] as const) : ([100, 200] as const);
  const nodeCount = Math.min(scale + 3, ceiling[0]);
  const nodes = Array.from({ length: nodeCount }, (_, index) => ({
    ref: ref("NODE", index + 1),
    label: `Generated node ${index + 1}`,
    kind:
      index % 3 === 0
        ? ("observation" as const)
        : index % 3 === 1
          ? ("inference" as const)
          : ("hypothesis" as const),
    state: index % 4 === 0 ? "partial" : "current",
  }));
  const edges = nodes.slice(1).flatMap((node, index) => {
    const previous = nodes[index];
    return previous
      ? [
          {
            ref: ref("EDGE", index + 1),
            fromRef: previous.ref,
            toRef: node.ref,
            relationship: index % 3 === 0 ? ("contradicts" as const) : ("supports" as const),
            confidenceBand: index % 3 === 0 ? ("low" as const) : ("medium" as const),
          },
        ]
      : [];
  });
  return {
    nodes,
    edges,
    nodeCeiling: ceiling[0],
    edgeCeiling: ceiling[1],
    truncated: false,
    authoritativeRepresentation: "tables",
  };
}

export function generatedSpatial(count = 10): SpatialProjection {
  return {
    records: Array.from({ length: Math.min(count, 50) }, (_, index) => ({
      ref: ref("SPATIAL", index + 1),
      label: `Generated zone signal ${index + 1}`,
      zoneRef: `SYN-ZONE-${(index % 4) + 1}`,
      longitude: 72.51 + index * 0.012,
      latitude: 23.01 + index * 0.009,
      concept: index % 2 ? "hypothesis" : "observation",
      state: index % 5 === 0 ? "partial" : "current",
    })),
    generated: true,
    tileNetworkUsed: false,
    authoritativeRepresentation: "table",
  };
}

export const generatedReviewPolicy: ReviewPolicy = Object.freeze({
  policyRevision: "SYN-POLICY-007",
  requiredApprovals: 2,
  requiredCapabilities: ["intelligence.reviewer"],
  requireIndependentActors: true,
  allowedOutcomes: ["confirm_for_record", "reject", "abstain", "request_more_context"] as const,
});
export function generatedReviews(alertRef = ref("ALERT", 1)): readonly ReviewRecord[] {
  return [
    {
      reviewRef: ref("REVIEW", 1),
      alertRef,
      actorRef: "SYN-ACTOR-ALPHA",
      outcome: "confirm_for_record",
      reasonCode: "evidence_sufficient",
      policyRevision: generatedReviewPolicy.policyRevision,
      decidedAt: "2026-09-09T09:40:00.000Z",
      revision: 1,
      generated: true,
    },
  ];
}
