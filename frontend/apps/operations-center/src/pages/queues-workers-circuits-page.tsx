import { ListRestart } from "lucide-react";
import {
  PlatformOperationsPageFrame,
  PlatformOperationsStateBoundary,
} from "../components/platform-operations-state-boundary";
import { QueueWorkerTable } from "../components/queue-worker-table";
export function QueuesWorkersCircuitsPage() {
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / WORK COORDINATION"
      title="Queues, workers, and circuits"
      description="Generated queue depth, lease, retry, dead-letter, circuit, graceful-shutdown, and abandoned-work recovery projections."
    >
      <PlatformOperationsStateBoundary state="degraded">
        <section className="panel platform-panel">
          <header>
            <div>
              <span className="eyebrow">BOUNDED WORKERS</span>
              <h2>Queue and lease state</h2>
            </div>
            <ListRestart size={20} />
          </header>
          <QueueWorkerTable />
        </section>
      </PlatformOperationsStateBoundary>
    </PlatformOperationsPageFrame>
  );
}
