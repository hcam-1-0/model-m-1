import { ServerCog } from "lucide-react";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { ResourceProfilePanel } from "../components/resource-profile-panel";
export function ResourceModelDeploymentProfilesPage() {
  return (
    <AdminPageFrame
      eyebrow="ADMIN / RESOURCE GOVERNANCE"
      title="Resource, model, and deployment profiles"
      description="Portable presentation profiles are visible without model loading, hardware inspection, Kubernetes execution, or deployment."
    >
      <ResourceProfilePanel />
      <section className="panel">
        <header>
          <div>
            <span className="eyebrow">FUTURE TOPOLOGY</span>
            <h2>Activation boundary</h2>
          </div>
          <ServerCog size={20} />
        </header>
        <p>
          Standalone, GPU-lab, server, and Kubernetes profiles remain generated projections.
          Authority and security policy never vary by hardware.
        </p>
        <button type="button" disabled>
          Activate deployment profile
        </button>
      </section>
    </AdminPageFrame>
  );
}
