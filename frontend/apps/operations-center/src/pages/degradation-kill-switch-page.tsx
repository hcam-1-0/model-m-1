import { Power } from "lucide-react";
import { DegradationPanel } from "../components/degradation-panel";
import { PlatformOperationsPageFrame } from "../components/platform-operations-state-boundary";
export function DegradationKillSwitchPage() {
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / DEGRADATION"
      title="Degradation and kill-switch governance"
      description="Generated degradation states and proposed controls remain separate from active configuration. No direct toggle or automatic activation exists."
    >
      <div className="platform-two-column">
        <DegradationPanel />
        <section className="panel platform-panel">
          <header>
            <div>
              <span className="eyebrow">CONTROL PROPOSAL</span>
              <h2>Kill switch</h2>
            </div>
            <Power size={20} />
          </header>
          <dl className="platform-details">
            <div>
              <dt>Declared</dt>
              <dd>Yes</dd>
            </div>
            <div>
              <dt>Current source</dt>
              <dd>Required</dd>
            </div>
            <div>
              <dt>Direct toggle</dt>
              <dd>Unavailable</dd>
            </div>
            <div>
              <dt>Automatic activation</dt>
              <dd>Disabled</dd>
            </div>
          </dl>
          <button type="button" disabled>
            Change state
          </button>
        </section>
      </div>
    </PlatformOperationsPageFrame>
  );
}
