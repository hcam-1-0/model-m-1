import type { ResourceId } from "@hcam/contracts";

export interface ProvenanceNode {
  readonly ref: ResourceId;
  readonly label: string;
  readonly kind: "entity" | "activity" | "agent";
  readonly generated: true;
}
export interface ProvenanceEdge {
  readonly ref: ResourceId;
  readonly fromRef: ResourceId;
  readonly toRef: ResourceId;
  readonly relation: "derived_from" | "generated_by" | "attributed_to" | "used";
}
export interface ProvenanceProjection {
  readonly evidenceRef: ResourceId;
  readonly nodes: readonly ProvenanceNode[];
  readonly edges: readonly ProvenanceEdge[];
  readonly nodeCeiling: 12 | 50 | 100;
  readonly edgeCeiling: 24 | 100 | 200;
  readonly truncated: boolean;
  readonly authoritativeRepresentation: "node_edge_tables";
  readonly externalProvImport: false;
  readonly provConformanceClaim: false;
  readonly generated: true;
}
export interface CustodyEvent {
  readonly ref: ResourceId;
  readonly evidenceRef: ResourceId;
  readonly sequence: number;
  readonly action: "referenced" | "access_recorded" | "transfer_recorded" | "status_corrected";
  readonly actorClass: string;
  readonly recordedAt: string;
  readonly source: "generated_custody_record";
  readonly inferredFromProvenance: false;
  readonly generated: true;
}
