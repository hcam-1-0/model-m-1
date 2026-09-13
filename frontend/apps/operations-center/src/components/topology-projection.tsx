import { Network } from "lucide-react";
import { topologyProjections } from "../data/platform-operations-projections";
export function TopologyProjection() {
  return (
    <section className="panel platform-panel">
      <header>
        <div>
          <span className="eyebrow">PLATFORM-NEUTRAL</span>
          <h2>Topology projections</h2>
        </div>
        <Network size={20} />
      </header>
      <div className="topology-grid">
        {topologyProjections.map((item) => (
          <article key={item.ref}>
            <strong>{item.profile.replaceAll("_", " ")}</strong>
            <div>
              <span>UI</span>
              <i />
              <span>Policy</span>
              <i />
              <span>Service</span>
            </div>
            <small>Not deployed · authority invariant</small>
          </article>
        ))}
      </div>
    </section>
  );
}
