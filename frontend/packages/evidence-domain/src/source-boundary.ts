import type { EvidenceReference, OpaqueSourceReference } from "../../investigation-contracts/src";

const forbiddenSourceKeys = new Set([
  "url",
  "uri",
  "path",
  "bucket",
  "objectKey",
  "token",
  "secret",
  "credential",
  "locator",
]);
export function validateOpaqueSource(source: OpaqueSourceReference): readonly string[] {
  const failures: string[] = [];
  const runtimeSource = source as unknown as Readonly<Record<string, unknown>>;
  if (
    runtimeSource.resolved !== false ||
    runtimeSource.renderable !== false ||
    runtimeSource.downloadable !== false ||
    runtimeSource.locatorExposed !== false
  )
    failures.push("source_operation_enabled");
  for (const key of Object.keys(source))
    if (forbiddenSourceKeys.has(key)) failures.push("forbidden_key");
  if (!/^SYN-SOURCE-REF-[0-9]{4}$/u.test(source.referenceId))
    failures.push("invalid_generated_reference");
  return [...new Set(failures)];
}
export function canResolveEvidenceSource(reference: EvidenceReference): boolean {
  const runtimeReference = reference as unknown as Readonly<Record<string, unknown>>;
  return runtimeReference.sourceResolutionAuthorized === true;
}
