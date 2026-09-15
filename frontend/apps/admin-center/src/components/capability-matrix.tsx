const roles = [
  { role: "Department administrator", view: true, propose: true, approve: false },
  { role: "Independent approver", view: true, propose: false, approve: true },
  { role: "Auditor", view: true, propose: false, approve: false },
  { role: "Operator", view: false, propose: false, approve: false },
];
export function CapabilityMatrix() {
  return (
    <div className="table-scroll" tabIndex={0} aria-label="Scrollable capability matrix">
      <table>
        <caption className="sr-only">Generated role capability projection</caption>
        <thead>
          <tr>
            <th>Role</th>
            <th>View</th>
            <th>Propose</th>
            <th>Approve</th>
            <th>Effective mutation</th>
          </tr>
        </thead>
        <tbody>
          {roles.map((item) => (
            <tr key={item.role}>
              <td>
                <strong>{item.role}</strong>
              </td>
              <td>{item.view ? "Allowed" : "Denied"}</td>
              <td>{item.propose ? "Allowed" : "Denied"}</td>
              <td>{item.approve ? "Independent only" : "Denied"}</td>
              <td>
                <span className="status blocked">Unavailable</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
