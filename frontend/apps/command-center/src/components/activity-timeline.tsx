import type { CommandActivity } from "@hcam/command-domain";
export function ActivityTimeline({ activity }: { readonly activity: readonly CommandActivity[] }) {
  return (
    <section className="panel timeline">
      <header>
        <div>
          <p className="eyebrow">CHRONOLOGY</p>
          <h2>Generated activity</h2>
        </div>
        <span className="panel-meta">Append-only view</span>
      </header>
      <ol>
        {activity.slice(0, 6).map((item) => (
          <li key={item.id}>
            <time>{item.at.slice(11, 16)}</time>
            <span aria-hidden="true" />
            <div>
              <strong>{item.title}</strong>
              <p>{item.detail}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
