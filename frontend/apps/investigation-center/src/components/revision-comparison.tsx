import type { RevisionComparison as Comparison } from "../../../../packages/investigation-contracts/src";
export function RevisionComparison({ value }: { readonly value: Comparison }) {
  return (
    <section className="panel comparison-panel">
      <header>
        <div>
          <span className="eyebrow">SERVER-PROJECTED DIFFERENCE</span>
          <h2>
            {value.fromRevision} to {value.toRevision}
          </h2>
        </div>
        <span
          className={value.complete ? "status-chip status-complete" : "status-chip status-partial"}
        >
          {value.complete ? "complete" : "partial"}
        </span>
      </header>
      <div className="comparison-columns">
        <div>
          <span>Before digest</span>
          <code>{value.fromDigest.slice(-18)}</code>
        </div>
        <div>
          <span>After digest</span>
          <code>{value.toDigest.slice(-18)}</code>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Field</th>
            <th>Before</th>
            <th>After</th>
            <th>Meaning</th>
          </tr>
        </thead>
        <tbody>
          {value.changes.map((item) => (
            <tr key={item.field}>
              <td>{item.field.replaceAll("_", " ")}</td>
              <td>{item.before}</td>
              <td>{item.after}</td>
              <td>{item.meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
