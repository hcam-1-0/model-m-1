export interface RetentionProjection {
  readonly ref: string;
  readonly policyRef: string;
  readonly targetClass: string;
  readonly affectedCount: number;
  readonly conflicts: readonly string[];
  readonly residualCount: number;
  readonly holdOverlay: "none" | "declared" | "unknown";
  readonly executable: false;
  readonly generated: true;
}
export function retentionPreview(index = 1): RetentionProjection {
  return {
    ref: `SYN-RETENTION-PREVIEW-${String(index).padStart(4, "0")}`,
    policyRef: `SYN-POLICY-${String(index).padStart(4, "0")}`,
    targetClass: "generated_audit_reference",
    affectedCount: index * 12,
    conflicts: index % 2 ? ["Generated hold overlay requires independent review"] : [],
    residualCount: index % 3,
    holdOverlay: index % 2 ? "declared" : "none",
    executable: false,
    generated: true,
  };
}
