import { auditReferences } from "../data/security-projections";
export function AuditReferenceTable() {
  return (
    <div className="table-scroll" tabIndex={0}>
      <table>
        <thead>
          <tr>
            <th>Sequence</th>
            <th>Reference</th>
            <th>Action class</th>
            <th>Outcome</th>
            <th>Target</th>
          </tr>
        </thead>
        <tbody>
          {auditReferences.map((item) => (
            <tr key={item.ref}>
              <td>{item.sequence}</td>
              <td>
                <strong>{item.ref}</strong>
                <small>immutable reference</small>
              </td>
              <td>{item.actionClass}</td>
              <td>
                <span className={`status ${item.outcome === "allowed" ? "current" : "partial"}`}>
                  {item.outcome}
                </span>
              </td>
              <td>{item.targetRef}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
