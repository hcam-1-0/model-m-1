import type { CommandMetric } from "@hcam/command-domain";

export function SummaryBand({ metrics }: { readonly metrics: readonly CommandMetric[] }) {
  return (
    <section className="summary-band" aria-label="Situation summary">
      {metrics.map((metric) => (
        <article key={metric.id}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <small className={`truth ${metric.truth}`}>{metric.truth}</small>
          <p>{metric.detail}</p>
        </article>
      ))}
    </section>
  );
}
