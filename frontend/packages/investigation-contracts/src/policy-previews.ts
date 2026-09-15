import type { ResourceId } from "@hcam/contracts";

export interface PolicyPreviewTarget {
  readonly ref: ResourceId;
  readonly included: boolean;
  readonly reasonCode: string;
  readonly conflict: string | null;
}
export interface NonoperativePolicyPreview {
  readonly ref: ResourceId;
  readonly policyClass: "retention" | "hold" | "deletion" | "disposition" | "export";
  readonly policyReference: string;
  readonly targets: readonly PolicyPreviewTarget[];
  readonly completeness: "complete" | "partial" | "unknown";
  readonly limitations: readonly string[];
  readonly residualCount: number;
  readonly executable: false;
  readonly generated: true;
}
export interface DisabledBridge {
  readonly bridge: "case_management" | "external_prov";
  readonly state: "disabled";
  readonly reason: string;
  readonly externalOperationAuthorized: false;
}
