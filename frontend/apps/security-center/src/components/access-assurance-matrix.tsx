const checks = [
  { boundary: "Application RBAC", result: "projected equivalent", source: "SYN-POLICY-R7" },
  { boundary: "Constrained ABAC", result: "department + purpose", source: "SYN-ABAC-R3" },
  { boundary: "PostgreSQL RLS", result: "independent equivalent", source: "SYN-RLS-R4" },
  { boundary: "Break-glass", result: "unavailable", source: "SYN-BREAK-GLASS-OFF" },
];
export function AccessAssuranceMatrix() {
  return (
    <div className="table-scroll" tabIndex={0}>
      <table>
        <thead>
          <tr>
            <th>Boundary</th>
            <th>Result</th>
            <th>Source reference</th>
            <th>Authority</th>
          </tr>
        </thead>
        <tbody>
          {checks.map((item) => (
            <tr key={item.boundary}>
              <td>
                <strong>{item.boundary}</strong>
              </td>
              <td>{item.result}</td>
              <td>{item.source}</td>
              <td>
                <span className="status current">server</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
