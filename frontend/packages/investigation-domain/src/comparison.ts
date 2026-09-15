import type {
  ReconstructionProjection,
  RevisionComparison,
  RevisionFieldChange,
} from "../../investigation-contracts/src";

export function compareRevisions(
  before: ReconstructionProjection,
  after: ReconstructionProjection,
): RevisionComparison {
  if (before.investigationRef !== after.investigationRef)
    throw new Error("comparison_scope_mismatch");
  const fields: RevisionFieldChange[] = [
    {
      field: "timeline_entries",
      before: String(before.timeline.length),
      after: String(after.timeline.length),
      meaning:
        before.timeline.length === after.timeline.length
          ? "unchanged"
          : before.timeline.length < after.timeline.length
            ? "added"
            : "removed",
      source: "server_projection",
    },
    {
      field: "completeness",
      before: before.completeness,
      after: after.completeness,
      meaning: before.completeness === after.completeness ? "unchanged" : "changed",
      source: "server_projection",
    },
  ];
  return {
    investigationRef: before.investigationRef,
    fromRevision: before.resolvedRevision,
    toRevision: after.resolvedRevision,
    fromDigest: before.digest,
    toDigest: after.digest,
    changes: fields,
    complete: before.completeness === "complete" && after.completeness === "complete",
    limitations:
      before.completeness === "complete" && after.completeness === "complete"
        ? []
        : ["At least one generated revision is incomplete."],
    generated: true,
  };
}
