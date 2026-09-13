import { Cpu, Workflow } from "lucide-react";
import { PlatformOperationsPageFrame } from "../components/platform-operations-state-boundary";
export function AiRuntimeSchedulerPage() {
  return (
    <PlatformOperationsPageFrame
      eyebrow="OPERATIONS / AI RUNTIME"
      title="AI runtime and scheduler"
      description="Generated compatibility and scheduling projections only; no model, artifact, inference, accelerator, container, or Kubernetes runtime is active."
    >
      <div className="platform-two-column">
        <section className="panel platform-panel">
          <header>
            <div>
              <span className="eyebrow">DYNAMIC PROFILE</span>
              <h2>Portable scheduler projection</h2>
            </div>
            <Cpu size={20} />
          </header>
          <dl className="platform-details">
            <div>
              <dt>Current profile</dt>
              <dd>low resource</dd>
            </div>
            <div>
              <dt>Optional capability</dt>
              <dd>owned GPU lab</dd>
            </div>
            <div>
              <dt>Future target</dt>
              <dd>server / Kubernetes</dd>
            </div>
            <div>
              <dt>Runtime state</dt>
              <dd>not executed</dd>
            </div>
          </dl>
        </section>
        <section className="panel platform-panel">
          <header>
            <div>
              <span className="eyebrow">LAYER GRAPH</span>
              <h2>Bypass-safe plan</h2>
            </div>
            <Workflow size={20} />
          </header>
          <ol className="scheduler-flow">
            <li>Capability inventory</li>
            <li>Policy selection</li>
            <li>Compatible lane projection</li>
            <li>Generated fallback</li>
          </ol>
          <button type="button" disabled>
            Activate runtime
          </button>
        </section>
      </div>
    </PlatformOperationsPageFrame>
  );
}
