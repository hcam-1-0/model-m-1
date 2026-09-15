import { useMemo, useState } from "react";
import { FlaskConical } from "lucide-react";
import { filterQueue, intelligenceQueueState } from "../../../../packages/intelligence-domain/src";
import {
  IntelligenceFilterRail,
  type IntelligenceFilters,
} from "../components/intelligence-filter-rail";
import { IntelligenceStateBoundary } from "../components/intelligence-state-boundary";
import { QueueTable } from "../components/queue-table";
import { generatedNow, queues } from "../data/intelligence-projections";
export function HypothesisQueuePage() {
  const [filters, setFilters] = useState<IntelligenceFilters>({
    query: "",
    state: "all",
    priority: "all",
  });
  const items = useMemo(
    () =>
      filterQueue(queues.hypotheses.items, filters.state, filters.priority).filter((item) =>
        `${item.title} ${item.ref}`.toLowerCase().includes(filters.query.toLowerCase()),
      ),
    [filters],
  );
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS / HYPOTHESES</p>
          <h1>Hypothesis queue</h1>
          <p>
            Unconfirmed analytical propositions, kept distinct from observations, candidates,
            alerts, and review decisions.
          </p>
        </div>
        <span className="page-icon">
          <FlaskConical size={20} /> {items.length} generated
        </span>
      </header>
      <div className="queue-layout">
        <IntelligenceFilterRail value={filters} onChange={setFilters} />
        <section className="panel table-panel">
          <header>
            <div>
              <span className="eyebrow">AUTHORITATIVE QUEUE</span>
              <h2>Server priority order</h2>
            </div>
            <span>cursor page 1</span>
          </header>
          <IntelligenceStateBoundary
            state={intelligenceQueueState(queues.hypotheses, generatedNow)}
          >
            <QueueTable items={items} detailBase="/intelligence/hypotheses" />
          </IntelligenceStateBoundary>
        </section>
      </div>
    </>
  );
}
