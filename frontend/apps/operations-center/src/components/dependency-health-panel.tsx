import { Boxes } from "lucide-react";
import { platformServices } from "../data/platform-operations-projections";
export function DependencyHealthPanel() {
  return (
    <section className="panel platform-panel">
      <header>
        <div>
          <span className="eyebrow">BOUNDED DEPENDENCIES</span>
          <h2>Dependency chain</h2>
        </div>
        <Boxes size={20} />
      </header>
      <ol className="dependency-chain">
        {platformServices.slice(0, 6).map((item) => (
          <li key={item.ref}>
            <strong>{item.label}</strong>
            <span>{item.dependencyRefs[0] ?? "root projection"}</span>
            <em className={item.state}>{item.state}</em>
          </li>
        ))}
      </ol>
    </section>
  );
}
