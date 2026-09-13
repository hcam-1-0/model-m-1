import { ArrowRight, Boxes, Gauge, ListRestart, ServerCog } from "lucide-react";
import { Link } from "react-router";
import { CapacityEvidencePanel } from "../components/capacity-evidence-panel";
import { DegradationPanel } from "../components/degradation-panel";
import {
  PlatformOperationsPageFrame,
  PlatformOperationsStateBoundary,
} from "../components/platform-operations-state-boundary";
import { platformSummary } from "../data/platform-operations-projections";
export function PlatformOperationsOverviewPage() {
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / PLATFORM"
      title="Platform operations"
      description="Generated service, queue, objective, degradation, recovery, capacity, and topology projections. Camera and live monitoring remain separate preserved workspaces."
    >
      <section className="platform-summary">
        <article>
          <ServerCog size={18} />
          <span>Platform state</span>
          <strong>{platformSummary.state}</strong>
          <small>Worst qualified state</small>
        </article>
        <article>
          <Boxes size={18} />
          <span>Services</span>
          <strong>{platformSummary.services}</strong>
          <small>Generated inventory</small>
        </article>
        <article>
          <ListRestart size={18} />
          <span>Queues needing review</span>
          <strong>{platformSummary.queuesNeedingAttention}</strong>
          <small>Bounded classifications</small>
        </article>
        <article>
          <Gauge size={18} />
          <span>Supply-chain attention</span>
          <strong>{platformSummary.supplyChainAttention}</strong>
          <small>Read-only evidence</small>
        </article>
      </section>
      <PlatformOperationsStateBoundary state="degraded">
        <div className="platform-two-column">
          <section className="panel platform-panel">
            <header>
              <div>
                <span className="eyebrow">WORKSPACE MAP</span>
                <h2>Operational domains</h2>
              </div>
            </header>
            <ul className="platform-links">
              <li>
                <Link to="/operations/platform/services">
                  Services and dependencies <ArrowRight size={15} />
                </Link>
              </li>
              <li>
                <Link to="/operations/platform/queues">
                  Queues and workers <ArrowRight size={15} />
                </Link>
              </li>
              <li>
                <Link to="/operations/platform/slo">
                  SLO and budgets <ArrowRight size={15} />
                </Link>
              </li>
              <li>
                <Link to="/operations/platform/recovery">
                  Recovery previews <ArrowRight size={15} />
                </Link>
              </li>
            </ul>
          </section>
          <DegradationPanel />
        </div>
      </PlatformOperationsStateBoundary>
      <CapacityEvidencePanel />
    </PlatformOperationsPageFrame>
  );
}
