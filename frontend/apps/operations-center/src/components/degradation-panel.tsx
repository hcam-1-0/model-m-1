import { ShieldAlert } from "lucide-react";
import { platformDegradation } from "../data/platform-operations-projections";
export function DegradationPanel() {
  return (
    <section className="panel platform-panel">
      <header>
        <div>
          <span className="eyebrow">DEGRADATION STATE</span>
          <h2>{platformDegradation.state.replaceAll("_", " ")}</h2>
        </div>
        <ShieldAlert size={20} />
      </header>
      <ul className="platform-list">
        {platformDegradation.affectedDomains.map((item) => (
          <li key={item}>
            <strong>{item.replaceAll("_", " ")}</strong>
            <span>Generated limitation active</span>
          </li>
        ))}
      </ul>
      <footer>Kill-switch control is unavailable.</footer>
    </section>
  );
}
