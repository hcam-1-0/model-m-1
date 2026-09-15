import { RelationshipTableRenderer } from "../../../../packages/relationship-renderers/src";
import type { RelationshipProjection } from "../../../../packages/intelligence-contracts/src";
export function GraphTable({ projection }: { readonly projection: RelationshipProjection }) {
  return <RelationshipTableRenderer projection={projection} />;
}
