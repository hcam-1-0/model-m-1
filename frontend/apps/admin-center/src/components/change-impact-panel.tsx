import { GitCompareArrows, TriangleAlert } from "lucide-react";
export function ChangeImpactPanel({
  title = "Generated change impact",
  impacts = [
    "Department-scoped projection refresh",
    "Independent review required",
    "No runtime activation path",
  ],
}: {
  readonly title?: string;
  readonly impacts?: readonly string[];
}) {
  return (
    <section className="panel impact-panel">
      <header>
        <div>
          <span className="eyebrow">IMPACT PREVIEW</span>
          <h2>{title}</h2>
        </div>
        <GitCompareArrows size={20} />
      </header>
      <ul>
        {impacts.map((impact) => (
          <li key={impact}>
            <TriangleAlert size={15} />
            {impact}
          </li>
        ))}
      </ul>
    </section>
  );
}
