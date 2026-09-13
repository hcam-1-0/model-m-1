import type { ImpactClosure } from "../../../../packages/investigation-domain/src";
import type { ImpactTarget } from "../../../../packages/investigation-contracts/src";
export function ImpactClosureTable({
  targets,
  summary,
}: {
  readonly targets: readonly ImpactTarget[];
  readonly summary: ImpactClosure;
}) {
  return (
    <section className="panel">
      <header>
        <div>
          <span className="eyebrow">PER-TARGET CLOSURE</span>
          <h2>Correction impact</h2>
        </div>
        <span
          className={
            summary.complete ? "status-chip status-complete" : "status-chip status-partial"
          }
        >
          {summary.complete
            ? "complete"
            : `${summary.pending + summary.blocked + summary.failed} unresolved`}
        </span>
      </header>
      <div className="impact-summary">
        <span>
          Applied <strong>{summary.applied}</strong>
        </span>
        <span>
          Pending <strong>{summary.pending}</strong>
        </span>
        <span>
          Blocked <strong>{summary.blocked}</strong>
        </span>
        <span>
          Failed <strong>{summary.failed}</strong>
        </span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Target</th>
            <th>Kind</th>
            <th>Status</th>
            <th>Revision</th>
            <th>Limitation</th>
          </tr>
        </thead>
        <tbody>
          {targets.map((target) => (
            <tr key={target.targetRef}>
              <td>
                <code>{target.targetRef}</code>
              </td>
              <td>{target.targetKind}</td>
              <td>
                <span className={`status-chip status-${target.status}`}>{target.status}</span>
              </td>
              <td>{target.revision}</td>
              <td>{target.limitation ?? "None declared"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
