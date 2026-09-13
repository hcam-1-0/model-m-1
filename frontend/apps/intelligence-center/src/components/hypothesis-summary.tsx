import { FlaskConical } from "lucide-react";
import type { QueueItem } from "../../../../packages/intelligence-contracts/src";
import { PriorityBadge } from "./priority-badge";
import { TypedConceptLabel } from "./typed-concept-label";
export function HypothesisSummary({ item }: { readonly item: QueueItem }) {
  return (
    <section className="identity-band">
      <FlaskConical size={22} />
      <div>
        <span className="eyebrow">WORKING ANALYTICAL PROPOSITION</span>
        <h1>{item.title}</h1>
        <p>{item.summary}</p>
      </div>
      <div>
        <TypedConceptLabel kind="hypothesis" />
        <PriorityBadge priority={item.priority} />
      </div>
    </section>
  );
}
