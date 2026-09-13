import { Clock3, UserCheck, Users } from "lucide-react";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { adminResources } from "../data/admin-projections";
export function UsersMembershipsSessionsPage() {
  const rows = adminResources
    .filter((item) => ["user", "membership"].includes(item.kind))
    .slice(0, 12);
  return (
    <AdminPageFrame
      eyebrow="ADMIN / IDENTITY"
      title="Users, memberships, and sessions"
      description="Generated identity references only; role, department, policy revision, and session freshness are independently visible."
    >
      <section className="summary-band">
        <article>
          <Users size={18} />
          <span>Visible identities</span>
          <strong>{rows.length}</strong>
          <small>Department scoped</small>
        </article>
        <article>
          <UserCheck size={18} />
          <span>Policy revision</span>
          <strong>R7</strong>
          <small>Server authoritative</small>
        </article>
        <article>
          <Clock3 size={18} />
          <span>Session state</span>
          <strong>Current</strong>
          <small>Generated clock</small>
        </article>
      </section>
      <section className="panel table-panel">
        <header>
          <div>
            <span className="eyebrow">IDENTITY PROJECTION</span>
            <h2>Membership inventory</h2>
          </div>
          <span className="status current">current</span>
        </header>
        <div className="table-scroll" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Resource</th>
                <th>Department</th>
                <th>Policy</th>
                <th>Effective action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => (
                <tr key={item.ref}>
                  <td>
                    <strong>{item.label}</strong>
                    <small>{item.ref}</small>
                  </td>
                  <td>{item.kind}</td>
                  <td>{item.departmentRef}</td>
                  <td>SYN-POLICY-R7</td>
                  <td>
                    <span className="status blocked">Unavailable</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AdminPageFrame>
  );
}
