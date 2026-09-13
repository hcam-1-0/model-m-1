import type { PriorityBand } from "../../../../packages/intelligence-contracts/src";
export function PriorityBadge({ priority }: { readonly priority: PriorityBand }) {
  return <span className={`priority priority-${priority}`}>{priority.replaceAll("_", " ")}</span>;
}
