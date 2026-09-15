import { Gauge } from "lucide-react";
import { platformSlos } from "../data/platform-operations-projections";
export function SloBudgetPanel() {
  return (
    <section className="panel platform-panel">
      <header>
        <div>
          <span className="eyebrow">GENERATED OBJECTIVES</span>
          <h2>SLO and error budgets</h2>
        </div>
        <Gauge size={20} />
      </header>
      <div className="slo-grid">
        {platformSlos.map((item) => (
          <article key={item.ref}>
            <span>{item.indicator}</span>
            <strong>{item.budgetState}</strong>
            <small>{item.window}</small>
            <em>Not a production target</em>
          </article>
        ))}
      </div>
    </section>
  );
}
