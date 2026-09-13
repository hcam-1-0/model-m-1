import { useMemo, useState } from "react";
import { ArrowUpRight, ListFilter } from "lucide-react";
import { Link } from "react-router";
import { investigationQueueState } from "../../../../packages/investigation-domain/src";
import {
  InvestigationFilterRail,
  type InvestigationFilters,
} from "../components/investigation-filter-rail";
import { InvestigationStateBoundary } from "../components/investigation-state-boundary";
import { generatedNow, investigationQueue } from "../data/investigation-projections";
export function InvestigationQueuePage() {
  const [filters, setFilters] = useState<InvestigationFilters>({
    query: "",
    state: "all",
    kind: "all",
  });
  const items = useMemo(
    () =>
      investigationQueue.items.filter(
        (item) =>
          (filters.state === "all" || item.state === filters.state) &&
          `${item.title} ${item.ref}`.toLowerCase().includes(filters.query.toLowerCase()),
      ),
    [filters],
  );
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATIONS / QUEUE</p>
          <h1>Investigation queue</h1>
          <p>
            Bounded department and purpose-scoped work in server priority and record-sequence order.
          </p>
        </div>
        <span className="page-icon">
          <ListFilter size={19} /> {items.length} generated
        </span>
      </header>
      <div className="queue-layout">
        <InvestigationFilterRail value={filters} onChange={setFilters} />
        <section className="panel table-panel">
          <header>
            <div>
              <span className="eyebrow">AUTHORITATIVE QUEUE</span>
              <h2>Stable page anchor</h2>
            </div>
            <code>{investigationQueue.stableAnchor}</code>
          </header>
          <InvestigationStateBoundary
            state={investigationQueueState(investigationQueue, generatedNow)}
          >
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Investigation</th>
                    <th>Priority</th>
                    <th>State</th>
                    <th>Timeline</th>
                    <th>Corrections</th>
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
                        <code>{item.ref}</code>
                      </td>
                      <td>{item.priority.replaceAll("_", " ")}</td>
                      <td>
                        <span className={`status-chip status-${item.state}`}>
                          {item.state.replaceAll("_", " ")}
                        </span>
                      </td>
                      <td>
                        {item.timelineEntries}
                        <small>latest seq {item.latestRecordSequence}</small>
                      </td>
                      <td>{item.correctionStatus}</td>
                      <td>
                        <Link
                          className="row-link"
                          to={`/investigations/${item.ref}`}
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
          </InvestigationStateBoundary>
        </section>
      </div>
    </>
  );
}
