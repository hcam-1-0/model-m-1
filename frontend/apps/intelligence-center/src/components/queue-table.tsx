import { ArrowUpRight, Inbox } from "lucide-react";
import { Link } from "react-router";
import type { QueueItem } from "../../../../packages/intelligence-contracts/src";
import { PriorityBadge } from "./priority-badge";
import { TypedConceptLabel } from "./typed-concept-label";
export function QueueTable({
  items,
  detailBase,
}: {
  readonly items: readonly QueueItem[];
  readonly detailBase: string;
}) {
  if (!items.length)
    return (
      <div className="empty-state">
        <Inbox size={25} />
        <strong>No generated items match</strong>
        <span>Change filters to restore the authoritative queue.</span>
      </div>
    );
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      aria-label="Scrollable authoritative intelligence queue"
    >
      <table className="queue-table">
        <caption className="sr-only">Server-ordered generated queue</caption>
        <thead>
          <tr>
            <th>Item</th>
            <th>Concept</th>
            <th>Priority</th>
            <th>State</th>
            <th>Age</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.ref}>
              <td>
                <strong>{item.title}</strong>
                <small>{item.ref}</small>
              </td>
              <td>
                <TypedConceptLabel kind={item.concept} />
              </td>
              <td>
                <PriorityBadge priority={item.priority} />
              </td>
              <td>
                {item.state.replaceAll("_", " ")}
                <small>rev {item.revision}</small>
              </td>
              <td>
                {item.ageMinutes} min<small>{item.freshness.completeness}</small>
              </td>
              <td>
                <Link
                  className="row-link"
                  to={`${detailBase}/${item.ref}`}
                  aria-label={`Open ${item.title}`}
                >
                  <ArrowUpRight size={16} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
