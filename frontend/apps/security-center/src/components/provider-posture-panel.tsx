import { KeyRound, Network } from "lucide-react";
import { providerPosture } from "../data/security-projections";
export function ProviderPosturePanel() {
  return (
    <section className="panel">
      <header>
        <div>
          <span className="eyebrow">PROVIDER POSTURE</span>
          <h2>Destination and secret references</h2>
        </div>
        <Network size={20} />
      </header>
      <ul className="evidence-list">
        {providerPosture.map((item) => (
          <li key={item.ref}>
            <KeyRound size={16} />
            <div>
              <strong>{item.ref}</strong>
              <small>
                {item.destinationRuleRef} · certificate {item.certificateState}
              </small>
            </div>
            <span className="status blocked">offline</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
