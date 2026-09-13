import type { CustodyEvent } from "../../../../packages/investigation-contracts/src";

export function CustodyTimeline({ events }: { readonly events: readonly CustodyEvent[] }) {
  return (
    <ol className="custody-timeline" aria-label="Generated custody chronology">
      {events.map((event) => (
        <li key={event.ref}>
          <span>{event.sequence}</span>
          <div>
            <strong>{event.action.replaceAll("_", " ")}</strong>
            <small>{event.recordedAt}</small>
          </div>
        </li>
      ))}
    </ol>
  );
}
