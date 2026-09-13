import { CircleSlash2 } from "lucide-react";
import type { CandidateEvidence } from "../../../../packages/intelligence-contracts/src";
export function ContradictionPanel({ candidate }: { readonly candidate: CandidateEvidence }) {
  const conflicts = candidate.fields.filter(
    (field) => field.role === "contradicts" || field.role === "ambiguous",
  );
  return (
    <section className="panel contradiction-panel">
      <header>
        <div>
          <span className="eyebrow">VISIBLE LIMITATIONS</span>
          <h2>Contradiction and ambiguity</h2>
        </div>
        <CircleSlash2 size={19} />
      </header>
      <ul>
        {conflicts.map((item) => (
          <li key={item.field}>
            <strong>{item.field}</strong>
            <span>{item.role}</span>
            <p>{item.limitation}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
