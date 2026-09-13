export interface DegradationProjection {
  readonly ref: string;
  readonly state: "normal" | "constrained" | "fail_closed" | "recovering" | "unknown";
  readonly affectedDomains: readonly string[];
  readonly limitations: readonly string[];
  readonly killSwitchAvailable: false;
  readonly generated: true;
}
export interface RecoveryPreview {
  readonly ref: string;
  readonly class: "backup" | "restore" | "failover" | "maintenance" | "disaster_recovery";
  readonly state: "preview_only";
  readonly lastEvidenceRef: string | null;
  readonly rpo: string;
  readonly rto: string;
  readonly executable: false;
  readonly generated: true;
}
export interface TopologyProjection {
  readonly ref: string;
  readonly profile:
    | "low_resource"
    | "enhanced_workstation"
    | "control_room"
    | "owned_GPU_lab"
    | "future_server"
    | "future_Kubernetes";
  readonly nodes: readonly {
    readonly ref: string;
    readonly role: string;
    readonly state: string;
  }[];
  readonly deploymentActive: false;
  readonly generated: true;
}
