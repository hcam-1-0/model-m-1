import { BellRing } from "lucide-react";
import { QueueTable } from "../components/queue-table";
import { queues } from "../data/intelligence-projections";
export function ProposedAlertQueuePage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INTELLIGENCE / PROPOSED ALERTS</p>
          <h1>Proposed alert queue</h1>
          <p>
            Analytical proposals awaiting mandatory human review. Priority means review order, not
            criminal severity.
          </p>
        </div>
        <span className="page-icon">
          <BellRing size={19} /> no delivery
        </span>
      </header>
      <section className="semantic-warning">
        <strong>Proposed alerts are not operational alerts.</strong>
        <span>No notification, dispatch, enforcement, or external workflow is connected.</span>
      </section>
      <section className="panel table-panel">
        <header>
          <div>
            <span className="eyebrow">SERVER-ORDERED REVIEW PRIORITY</span>
            <h2>Generated proposals</h2>
          </div>
          <span>delivery identity: none</span>
        </header>
        <QueueTable items={queues.alerts.items} detailBase="/intelligence/alerts" />
      </section>
    </>
  );
}
