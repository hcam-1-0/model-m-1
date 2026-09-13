import { evidenceStateMatrix } from "../../../../packages/evidence-domain/src";
import type { EvidenceReference } from "../../../../packages/investigation-contracts/src";

export function EvidenceStateMatrix({ reference }: { readonly reference: EvidenceReference }) {
  return (
    <section className="panel">
      <header>
        <div>
          <span className="eyebrow">ORTHOGONAL STATES</span>
          <h2>Evidence state matrix</h2>
        </div>
        <small>No combined verification conclusion</small>
      </header>
      <dl className="state-matrix">
        {evidenceStateMatrix(reference).map((item) => (
          <div key={item.axis}>
            <dt>{item.axis.replaceAll("_", " ")}</dt>
            <dd className={`status-value status-${item.value}`}>
              {item.value.replaceAll("_", " ")}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
