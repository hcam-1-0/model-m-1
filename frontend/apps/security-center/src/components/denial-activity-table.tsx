import { denialActivity } from "../data/security-projections";
export function DenialActivityTable({ limit = 18 }: { readonly limit?: number }) {
  return (
    <div className="table-scroll" tabIndex={0}>
      <table>
        <thead>
          <tr>
            <th>Reference</th>
            <th>Category</th>
            <th>Reason</th>
            <th>Actor class</th>
            <th>Raw payload</th>
          </tr>
        </thead>
        <tbody>
          {denialActivity.slice(0, limit).map((item) => (
            <tr key={item.ref}>
              <td>
                <strong>{item.ref}</strong>
                <small>{item.recordedAt}</small>
              </td>
              <td>{item.category}</td>
              <td>{item.reasonCode}</td>
              <td>{item.actorClass}</td>
              <td>
                <span className="status blocked">Not retained</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
