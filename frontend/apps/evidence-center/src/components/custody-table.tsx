import { orderCustodyEvents } from "../../../../packages/evidence-domain/src";
import type { CustodyEvent } from "../../../../packages/investigation-contracts/src";

export function CustodyTable({ events }: { readonly events: readonly CustodyEvent[] }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Sequence</th>
            <th>Action</th>
            <th>Actor class</th>
            <th>Recorded at</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {orderCustodyEvents(events).map((event) => (
            <tr key={event.ref}>
              <td>{event.sequence}</td>
              <td>{event.action.replaceAll("_", " ")}</td>
              <td>{event.actorClass.replaceAll("_", " ")}</td>
              <td>
                <time>{event.recordedAt}</time>
              </td>
              <td>{event.source.replaceAll("_", " ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
