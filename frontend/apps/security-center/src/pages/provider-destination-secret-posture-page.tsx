import { EyeOff } from "lucide-react";
import { ProviderPosturePanel } from "../components/provider-posture-panel";
import { SecurityPageFrame } from "../components/security-state-boundary";
export function ProviderDestinationSecretPosturePage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / PROVIDER POSTURE"
      title="Provider, destination, and secret posture"
      description="Field-minimized exact-rule and certificate evidence with opaque references; no secret value, locator, network, or authentication operation."
    >
      <div className="two-column">
        <ProviderPosturePanel />
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">SECRET BOUNDARY</span>
              <h2>Values never projected</h2>
            </div>
            <EyeOff size={20} />
          </header>
          <ul className="plain-list">
            <li>Reference identifiers only</li>
            <li>No reveal, copy, test, rotate, transmit, or export</li>
            <li>No raw provider errors</li>
            <li>No provider network contact</li>
          </ul>
        </section>
      </div>
    </SecurityPageFrame>
  );
}
