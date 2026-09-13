import type { TimelineEntry } from "../../../../packages/investigation-contracts/src";
export function TimelineVisualLane({ entries }: { readonly entries: readonly TimelineEntry[] }) {
  return (
    <div className="timeline-lane" aria-label="Bounded visual timeline enhancement">
      {entries.slice(0, 12).map((entry) => (
        <div key={entry.ref}>
          <span className={`lane-dot kind-${entry.kind}`} aria-hidden="true" />
          <strong>{entry.recordSequence}</strong>
          <span>{entry.label}</span>
          <small>{entry.recordedAt.slice(11, 16)}</small>
        </div>
      ))}
      <p>Visual lane is limited to this page. The table is authoritative.</p>
    </div>
  );
}
