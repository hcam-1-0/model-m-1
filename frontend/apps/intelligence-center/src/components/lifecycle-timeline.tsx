import { CheckCircle2, CircleDot, RotateCcw, ShieldQuestion } from "lucide-react";
export interface TimelineEntry {
  readonly ref: string;
  readonly at: string;
  readonly label: string;
  readonly detail: string;
  readonly kind: "created" | "review" | "correction" | "reconsideration";
}
const icons = {
  created: CircleDot,
  review: CheckCircle2,
  correction: RotateCcw,
  reconsideration: ShieldQuestion,
} as const;
export function LifecycleTimeline({ entries }: { readonly entries: readonly TimelineEntry[] }) {
  return (
    <ol className="lifecycle-timeline">
      {entries.map((entry) => {
        const Icon = icons[entry.kind];
        return (
          <li key={entry.ref}>
            <Icon size={17} />
            <time>{entry.at}</time>
            <div>
              <strong>{entry.label}</strong>
              <p>{entry.detail}</p>
              <small>{entry.ref}</small>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
