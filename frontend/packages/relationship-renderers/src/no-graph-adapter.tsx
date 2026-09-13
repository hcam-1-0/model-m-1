import type { RelationshipProjection } from "../../intelligence-contracts/src";
import type { RelationshipRendererAdapter } from "./adapter";
export const noGraphAdapter: RelationshipRendererAdapter = Object.freeze({
  id: "no_graph",
  interactive: false,
  dependency: "none",
  project(value: RelationshipProjection) {
    return value;
  },
});
export function NoGraphAdapterNotice() {
  return (
    <p role="note">
      Graph canvas is unavailable. Complete relationship tables remain authoritative.
    </p>
  );
}
