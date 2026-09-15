import { ExternalLink, ShieldOff } from "lucide-react";
import { SecurityPageFrame } from "../components/security-state-boundary";
export function SocHandoffUnavailablePage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / HANDOFF"
      title="SOC handoff unavailable"
      description="The external security operations workflow is intentionally defined but unavailable until a separately authorized producer and receiving system exist."
    >
      <section className="unavailable-panel">
        <ShieldOff size={34} />
        <h2>No external SOC connection</h2>
        <p>Generated references cannot be sent, escalated, notified, dispatched, or exported.</p>
        <button type="button" disabled>
          <ExternalLink size={16} /> Open external SOC
        </button>
      </section>
    </SecurityPageFrame>
  );
}
