import type { NonoperativePolicyPreview } from "../../investigation-contracts/src";

export const forbiddenPolicyActions = [
  "execute",
  "approve",
  "sign",
  "activate",
  "release",
  "deliver",
  "download",
  "print",
  "delete",
  "hold",
  "change_retention",
  "dispose",
  "export",
] as const;
export function validatePolicyPreview(preview: NonoperativePolicyPreview): readonly string[] {
  const failures: string[] = [];
  const runtimePreview = preview as unknown as Readonly<Record<string, unknown>>;
  if (runtimePreview.executable !== false) failures.push("preview_is_executable");
  if (!preview.policyReference.startsWith("SYN-POLICY-")) failures.push("invalid_policy_reference");
  if (preview.targets.length > 100) failures.push("target_ceiling_exceeded");
  if (preview.completeness !== "complete" && preview.limitations.length === 0)
    failures.push("missing_limitation");
  return failures;
}
