import { limitWorkItems, type CommandWorkItem } from "@hcam/command-domain";
export function WorkloadRail({ items }: { readonly items: readonly CommandWorkItem[] }) {
  return (
    <section className="panel workload">
      <header>
        <div>
          <p className="eyebrow">HUMAN REVIEW</p>
          <h2>Workload</h2>
        </div>
        <span className="panel-meta">Bounded list</span>
      </header>
      <ol>
        {limitWorkItems(items, 6).map((item) => (
          <li key={item.id}>
            <span className={`band ${item.band}`}>{item.band}</span>
            <div>
              <strong>{item.label}</strong>
              <small>
                {item.category} · {item.occurredAt.slice(11, 16)} UTC
              </small>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
