import type { ReconstructionProjection } from "../../investigation-contracts/src";

export function validateReconstruction(projection: ReconstructionProjection): readonly string[] {
  const failures: string[] = [];
  const runtimeProjection = projection as unknown as Readonly<Record<string, unknown>>;
  if (!/^SYN-REV-[0-9]{4}$/u.test(projection.requestedRevision))
    failures.push("invalid_requested_revision");
  if (projection.requestedRevision !== projection.resolvedRevision)
    failures.push("revision_not_exact");
  if (!/^sha256:[A-F0-9]{64}$/u.test(projection.digest)) failures.push("invalid_digest");
  if (projection.completeness !== "complete" && projection.limitations.length === 0)
    failures.push("missing_incompleteness_limitation");
  if (projection.omittedComponents.length > 0 && projection.limitations.length === 0)
    failures.push("omission_without_limitation");
  if (runtimeProjection.generated !== true) failures.push("not_generated");
  return failures;
}
export function reconstructionSequenceIsBounded(projection: ReconstructionProjection): boolean {
  return (
    projection.timeline.length <= 200 &&
    projection.timeline.every((entry) => entry.revisionRef === projection.resolvedRevision)
  );
}
