import { useMemo, useState } from "react";
import { AdminFilterRail, type AdminFilters } from "../components/admin-filter-rail";
import { AdminPageFrame, AdminStateBoundary } from "../components/admin-state-boundary";
import { adminResources } from "../data/admin-projections";
export function OrganizationsDepartmentsPage() {
  const [filters, setFilters] = useState<AdminFilters>({ query: "", state: "all" });
  const rows = useMemo(
    () =>
      adminResources
        .filter((item) => ["organization", "department"].includes(item.kind))
        .filter(
          (item) =>
            (filters.state === "all" || item.state === filters.state) &&
            (!filters.query || item.label.toLowerCase().includes(filters.query.toLowerCase())),
        ),
    [filters],
  );
  return (
    <AdminPageFrame
      eyebrow="ADMIN / ORGANIZATION"
      title="Organizations and departments"
      description="Authoritative generated hierarchy with department isolation, revision, freshness, and completeness."
    >
      <div className="workspace-grid">
        <AdminFilterRail filters={filters} onChange={setFilters} />
        <section className="panel table-panel">
          <header>
            <div>
              <span className="eyebrow">SERVER-ORDERED</span>
              <h2>{rows.length} scoped records</h2>
            </div>
            <span className="status current">generated</span>
          </header>
          <AdminStateBoundary
            state={rows.some((item) => item.state === "partial") ? "partial" : "ready"}
          >
            <div className="table-scroll" tabIndex={0}>
              <table>
                <thead>
                  <tr>
                    <th>Resource</th>
                    <th>Kind</th>
                    <th>Department</th>
                    <th>State</th>
                    <th>Revision</th>
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
                      <td>
                        <span className={`status ${item.state}`}>{item.state}</span>
                      </td>
                      <td>{item.revision}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AdminStateBoundary>
        </section>
      </div>
    </AdminPageFrame>
  );
}
