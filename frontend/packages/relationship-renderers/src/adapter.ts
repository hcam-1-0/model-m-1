import type { RelationshipProjection } from "../../intelligence-contracts/src";
export interface RelationshipRendererAdapter {
  readonly id: "no_graph";
  readonly interactive: false;
  readonly dependency: "none";
  project(value: RelationshipProjection): RelationshipProjection;
}
