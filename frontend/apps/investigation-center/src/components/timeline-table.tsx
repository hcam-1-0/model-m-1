import { AlertTriangle, ArrowDown } from "lucide-react";
import type { TimelineEntry } from "../../../../packages/investigation-contracts/src";
export function TimelineTable({ entries }: { readonly entries: readonly TimelineEntry[] }) {
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      aria-label="Scrollable authoritative investigation timeline"
    >
      <table className="timeline-table">
        <caption className="sr-only">Record-sequence authoritative generated timeline</caption>
        <thead>
          <tr>
            <th>Seq</th>
            <th>Record</th>
            <th>Authority</th>
            <th>Recorded</th>
            <th>Event-time context</th>
            <th>Revision</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.ref}>
              <td>
                <span className="sequence">{entry.recordSequence}</span>
                <ArrowDown size={12} />
              </td>
              <td>
                <strong>{entry.label}</strong>
                <small>{entry.summary}</small>
                {entry.limitations.length ? (
                  <span className="limitation">
                    <AlertTriangle size={12} /> {entry.limitations[0]}
                  </span>
                ) : null}
              </td>
              <td>
                <span className={`kind kind-${entry.kind}`}>{entry.kind.replaceAll("_", " ")}</span>
                <small>{entry.authority.replaceAll("_", " ")}</small>
              </td>
              <td>
                <time>{entry.recordedAt.slice(11, 16)}</time>
                <small>record authority</small>
              </td>
              <td>
                {entry.eventTime.value ? (
                  <time>{entry.eventTime.value.slice(11, 16)}</time>
                ) : (
                  "Unknown"
                )}
                <small>
                  {entry.eventTime.precision} / {entry.eventTime.clockCondition}
                </small>
              </td>
              <td>
                <code>{entry.revisionRef}</code>
                <small>
                  {entry.supersedesRef ? `supersedes ${entry.supersedesRef}` : "append-only"}
                </small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
