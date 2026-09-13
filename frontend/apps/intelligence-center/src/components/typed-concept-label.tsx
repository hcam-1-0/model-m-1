import { presentationFor } from "../../../../packages/intelligence-domain/src";
import type { AnalyticalConceptKind } from "../../../../packages/intelligence-contracts/src";
export function TypedConceptLabel({ kind }: { readonly kind: AnalyticalConceptKind }) {
  const item = presentationFor(kind);
  return (
    <span className={`concept concept-${kind}`} title={item.caution}>
      <strong>{item.label}</strong>
      <small>{item.authority.replaceAll("_", " ")}</small>
    </span>
  );
}
