import type { ResourceId } from "@hcam/contracts";
import {
  investigationGeneratedMarker,
  timelineKinds,
  type CorrectionRetractionRecord,
  type CustodyEvent,
  type EvidenceHandoff,
  type EvidenceReference,
  type EvidenceVerificationEvent,
  type InvestigationHealth,
  type InvestigationQueue,
  type InvestigationSummary,
  type NonoperativePolicyPreview,
  type ProvenanceProjection,
  type ReconstructionProjection,
  type TimelineEntry,
  type TimelinePage,
} from "../../investigation-contracts/src";

const generatedAt = "2026-09-09T11:00:00.000Z";
const ref = (prefix: string, value: number) =>
  `SYN-${prefix}-${String(value).padStart(4, "0")}` as ResourceId;
const hexDigest = (value: number) =>
  `sha256:${value.toString(16).toUpperCase().padStart(64, "0").slice(-64)}`;

export function generatedInvestigations(count = 10): readonly InvestigationSummary[] {
  return Array.from({ length: Math.max(0, Math.min(count, 50)) }, (_, index) => ({
    ref: ref("INVESTIGATION", index + 1),
    title: `Generated investigation ${String(index + 1).padStart(2, "0")}`,
    state:
      index % 11 === 0
        ? "correction_pending"
        : index % 7 === 0
          ? "under_review"
          : index % 13 === 0
            ? "closed"
            : "open",
    priority:
      index % 4 === 0
        ? "urgent_review"
        : index % 4 === 1
          ? "elevated_review"
          : index % 4 === 2
            ? "standard_review"
            : "unknown",
    departmentRef: "SYN-DEPT-01",
    purposeCode: "SYN-PURPOSE-REVIEW",
    latestRecordSequence: 20 + index,
    timelineEntries: 20 + index * 4,
    evidenceReferences: 4 + (index % 6),
    correctionStatus: index % 11 === 0 ? "pending" : index % 17 === 0 ? "incomplete" : "clear",
    freshness: {
      observedAt: generatedAt,
      staleAt: index % 9 === 0 ? "2026-09-09T10:45:00.000Z" : "2026-09-09T12:00:00.000Z",
      completeness: index % 8 === 0 ? "partial" : "complete",
    },
    etag: `"SYN-P55-ETAG-${index + 1}"`,
    revision: index + 1,
    generated: true,
  }));
}

export function generatedInvestigationQueue(count = 10): InvestigationQueue {
  const items = generatedInvestigations(count);
  return {
    contractVersion: "1.0.0",
    marker: investigationGeneratedMarker,
    departmentRef: "SYN-DEPT-01",
    orderedBy: "server_priority_then_record_sequence_then_ref",
    stableAnchor: "SYN-P55-ANCHOR-0001",
    items,
    nextCursor: items.length < count ? `SYN-P55-CURSOR-${items.length}` : null,
    totalApproximate: items.length,
  };
}

export function generatedTimeline(
  investigationIndex = 1,
  count = 20,
  revision = 7,
): readonly TimelineEntry[] {
  const investigationRef = ref("INVESTIGATION", investigationIndex);
  const bounded = Math.max(0, Math.min(count, 200));
  return Array.from({ length: bounded }, (_, index) => {
    const kind = timelineKinds[index % timelineKinds.length] ?? "system_record";
    const analytical = ["inference", "hypothesis", "candidate", "proposed_alert"].includes(kind);
    const human = kind === "review";
    const historical = kind === "correction" || kind === "retraction" || kind === "action_record";
    const hasUnknownTime = index % 9 === 0;
    const itemRef = ref("TIMELINE", investigationIndex * 1000 + index + 1);
    return {
      ref: itemRef,
      investigationRef,
      recordSequence: index + 1,
      recordedAt: `2026-09-09T09:${String(index % 60).padStart(2, "0")}:00.000Z`,
      eventTime: {
        value: hasUnknownTime
          ? null
          : `2026-09-09T08:${String((index * 3) % 60).padStart(2, "0")}:00.000Z`,
        rangeStart: index % 7 === 0 ? "2026-09-09T08:00:00.000Z" : null,
        rangeEnd: index % 7 === 0 ? "2026-09-09T08:05:00.000Z" : null,
        precision: hasUnknownTime ? "unknown" : index % 7 === 0 ? "range" : "minute",
        source: hasUnknownTime ? "generated_unknown_clock" : "generated_source_clock",
        clockCondition: hasUnknownTime ? "unknown" : index % 5 === 0 ? "estimated" : "synchronized",
        changesRecordOrder: false,
      },
      kind,
      label: `${kind.replaceAll("_", " ")} record ${index + 1}`,
      summary: analytical
        ? "Generated analytical record; not an established fact."
        : human
          ? "Generated human-review record for chronology only."
          : "Generated append-only chronology record.",
      authority: analytical
        ? "analytical_only"
        : human
          ? "human_record"
          : historical
            ? "historical_record"
            : kind === "observation"
              ? "source_report"
              : "system_record",
      revisionRef: `SYN-REV-${String(revision).padStart(4, "0")}`,
      predecessorRef: index > 0 ? ref("TIMELINE", investigationIndex * 1000 + index) : null,
      supersedesRef:
        kind === "correction" || kind === "retraction"
          ? ref("TIMELINE", investigationIndex * 1000 + Math.max(1, index - 2))
          : null,
      sourceRef:
        kind === "observation" ? `SYN-SOURCE-REF-${String(index + 1).padStart(4, "0")}` : null,
      limitations:
        hasUnknownTime || analytical ? ["Generated projection with qualified authority."] : [],
      generated: true,
    };
  });
}

export function generatedTimelinePage(count = 20): TimelinePage {
  const items = generatedTimeline(1, count);
  return {
    contractVersion: "1.0.0",
    marker: investigationGeneratedMarker,
    investigationRef: ref("INVESTIGATION", 1),
    authority: "record_sequence",
    stableAnchor: "SYN-P55-ANCHOR-0001",
    revisionRef: "SYN-REV-0007",
    completeThroughSequence: items.length,
    items,
    nextCursor: count > items.length ? `SYN-P55-CURSOR-${items.length}` : null,
    totalApproximate: items.length,
  };
}

export function generatedReconstruction(
  revision = 7,
  completeness: ReconstructionProjection["completeness"] = "complete",
): ReconstructionProjection {
  const revisionRef = `SYN-REV-${String(revision).padStart(4, "0")}`;
  return {
    investigationRef: ref("INVESTIGATION", 1),
    requestedRevision: revisionRef,
    resolvedRevision: revisionRef,
    digest: hexDigest(revision),
    completeness,
    includedComponents: ["summary", "timeline", "relationships", "evidence_references"],
    omittedComponents: completeness === "complete" ? [] : ["generated_provider_context"],
    limitations:
      completeness === "complete"
        ? ["Generated reconstruction only."]
        : ["Generated provider context is unavailable."],
    laterChangesExist: revision < 8,
    timeline: generatedTimeline(1, Math.min(20 + revision, 40), revision),
    generated: true,
  };
}

export function generatedCorrection(index = 1): CorrectionRetractionRecord {
  const status = ["applied", "pending", "blocked", "failed", "superseded"] as const;
  return {
    ref: ref("CORRECTION", index),
    investigationRef: ref("INVESTIGATION", 1),
    kind: index % 3 === 0 ? "retraction" : "correction",
    predecessorRef: ref("TIMELINE", 1002),
    successorRef: ref("TIMELINE", 1021 + index),
    reasonCode: index % 3 === 0 ? "SYN-RETRACT-SOURCE" : "SYN-CORRECT-CONTEXT",
    recordedAt: "2026-09-09T10:15:00.000Z",
    actorClass: "generated_reviewer",
    impactTargets: status.map((item, targetIndex) => ({
      targetRef: ref("IMPACT", index * 10 + targetIndex + 1),
      targetKind:
        ["timeline", "relationship", "evidence", "review", "preview"][targetIndex] ?? "unknown",
      status: item,
      revision: targetIndex + 1,
      limitation:
        item === "blocked" || item === "failed" ? "Generated target requires review." : null,
    })),
    rewritesHistory: false,
    generated: true,
  };
}

export function generatedEvidenceReferences(count = 8): readonly EvidenceReference[] {
  const availability = ["referenced", "unavailable", "unknown"] as const;
  const integrity = ["digest_observed", "not_checked", "digest_mismatch", "unknown"] as const;
  const provenance = ["complete", "partial", "unknown"] as const;
  const custody = ["recorded", "partial", "not_provided", "unknown"] as const;
  return Array.from({ length: Math.max(0, Math.min(count, 50)) }, (_, index) => ({
    ref: ref("EVIDENCE", index + 1),
    investigationRef: ref("INVESTIGATION", 1),
    label: `Generated evidence reference ${String(index + 1).padStart(2, "0")}`,
    category: ["document_reference", "event_reference", "media_reference", "derived_reference"][
      index % 4
    ] as EvidenceReference["category"],
    availability: availability[index % availability.length] ?? "unknown",
    integrity: integrity[index % integrity.length] ?? "unknown",
    provenance: provenance[index % provenance.length] ?? "unknown",
    custody: custody[index % custody.length] ?? "unknown",
    signature: index % 3 === 0 ? "observed" : index % 3 === 1 ? "not_observed" : "unknown",
    access: index % 7 === 0 ? "denied" : "allowed",
    legalAssessment: index % 4 === 0 ? "review_required" : "not_assessed",
    digestObservation: index % 4 === 0 ? hexDigest(index + 10) : null,
    source: {
      referenceId: `SYN-SOURCE-REF-${String(index + 1).padStart(4, "0")}`,
      sourceClass: "generated_reference",
      resolved: false,
      renderable: false,
      downloadable: false,
      locatorExposed: false,
    },
    freshness: {
      observedAt: generatedAt,
      staleAt: "2026-09-09T12:00:00.000Z",
      completeness: index % 3 === 0 ? "partial" : "complete",
    },
    limitations: ["Generated reference only; source content is not resolved."],
    etag: `"SYN-EVIDENCE-ETAG-${index + 1}"`,
    revision: index + 1,
    generated: true,
  }));
}

export function generatedVerificationHistory(
  evidenceIndex = 1,
): readonly EvidenceVerificationEvent[] {
  return ["not_checked", "digest_observed", "digest_mismatch"].map((outcome, index) => ({
    ref: ref("VERIFY", evidenceIndex * 10 + index + 1),
    evidenceRef: ref("EVIDENCE", evidenceIndex),
    sequence: index + 1,
    observedAt: `2026-09-09T10:${String(index * 10).padStart(2, "0")}:00.000Z`,
    outcome: outcome as EvidenceVerificationEvent["outcome"],
    digestObservation: index === 0 ? null : hexDigest(evidenceIndex + index),
    truthEstablished: false,
    generated: true,
  }));
}

export function generatedProvenance(scale: 1 | 10 | 50 = 10): ProvenanceProjection {
  const limits =
    scale === 1 ? ([12, 24] as const) : scale === 10 ? ([50, 100] as const) : ([100, 200] as const);
  const count = Math.min(scale + 4, limits[0]);
  const nodes = Array.from({ length: count }, (_, index) => ({
    ref: ref("PROV-NODE", index + 1),
    label: `Generated provenance node ${index + 1}`,
    kind:
      index % 3 === 0
        ? ("entity" as const)
        : index % 3 === 1
          ? ("activity" as const)
          : ("agent" as const),
    generated: true as const,
  }));
  const edges = nodes.slice(1).map((node, index) => ({
    ref: ref("PROV-EDGE", index + 1),
    fromRef: nodes[index]?.ref ?? node.ref,
    toRef: node.ref,
    relation: index % 2 === 0 ? ("derived_from" as const) : ("generated_by" as const),
  }));
  return {
    evidenceRef: ref("EVIDENCE", 1),
    nodes,
    edges,
    nodeCeiling: limits[0],
    edgeCeiling: limits[1],
    truncated: false,
    authoritativeRepresentation: "node_edge_tables",
    externalProvImport: false,
    provConformanceClaim: false,
    generated: true,
  };
}

export function generatedCustodyEvents(evidenceIndex = 1): readonly CustodyEvent[] {
  const actions = [
    "referenced",
    "access_recorded",
    "transfer_recorded",
    "status_corrected",
  ] as const;
  return actions.map((action, index) => ({
    ref: ref("CUSTODY", evidenceIndex * 10 + index + 1),
    evidenceRef: ref("EVIDENCE", evidenceIndex),
    sequence: index + 1,
    action,
    actorClass: index % 2 === 0 ? "generated_system" : "generated_reviewer",
    recordedAt: `2026-09-09T10:${String(index * 8).padStart(2, "0")}:00.000Z`,
    source: "generated_custody_record",
    inferredFromProvenance: false,
    generated: true,
  }));
}

export function generatedPolicyPreview(index = 1): NonoperativePolicyPreview {
  const kinds = ["retention", "hold", "deletion", "disposition", "export"] as const;
  return {
    ref: ref("POLICY-PREVIEW", index),
    policyClass: kinds[(index - 1) % kinds.length] ?? "retention",
    policyReference: `SYN-POLICY-${String(index).padStart(4, "0")}`,
    targets: generatedEvidenceReferences(6).map((item, targetIndex) => ({
      ref: item.ref,
      included: targetIndex % 3 !== 0,
      reasonCode: targetIndex % 3 === 0 ? "SYN-EXCLUDED-CONFLICT" : "SYN-INCLUDED-SCOPE",
      conflict: targetIndex % 3 === 0 ? "Generated policy overlap" : null,
    })),
    completeness: index % 3 === 0 ? "partial" : "complete",
    limitations: ["Generated preview only. No policy action is available."],
    residualCount: 2,
    executable: false,
    generated: true,
  };
}

export function generatedEvidenceHandoff(evidenceIndex = 1): EvidenceHandoff {
  return {
    investigationRef: ref("INVESTIGATION", 1),
    evidenceRef: ref("EVIDENCE", evidenceIndex),
    purposeCode: "SYN-PURPOSE-REVIEW",
    departmentRef: "SYN-DEPT-01",
    capability: "evidence.viewer",
    sourceOperationAuthorized: false,
    generated: true,
  };
}

export const generatedInvestigationHealth: InvestigationHealth = Object.freeze({
  projection: "ready",
  timeline: "partial",
  reconstruction: "ready",
  evidence: "degraded",
  producerGapCount: 36,
  generated: true,
});
