import { ArchiveRestore, LockKeyhole } from "lucide-react";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { retentionProjections } from "../data/admin-projections";
export function RetentionPolicyProjectionsPage() {
  return (
    <AdminPageFrame
      eyebrow="ADMIN / RECORDS POLICY"
      title="Retention policy projections"
      description="Generated retention, hold, deletion, disposition, and export impact previews remain non-operative and are not legal-policy decisions."
    >
      <section className="panel table-panel">
        <header>
          <div>
            <span className="eyebrow">IMPACT PREVIEW</span>
            <h2>Generated policy projections</h2>
          </div>
          <ArchiveRestore size={20} />
        </header>
        <div className="table-scroll" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th>Preview</th>
                <th>Target class</th>
                <th>Affected</th>
                <th>Hold overlay</th>
                <th>Residual</th>
                <th>Execution</th>
              </tr>
            </thead>
            <tbody>
              {retentionProjections.map((item) => (
                <tr key={item.ref}>
                  <td>
                    <strong>{item.ref}</strong>
                    <small>{item.policyRef}</small>
                  </td>
                  <td>{item.targetClass}</td>
                  <td>{item.affectedCount}</td>
                  <td>{item.holdOverlay}</td>
                  <td>{item.residualCount}</td>
                  <td>
                    <span className="status blocked">
                      <LockKeyhole size={13} /> Unavailable
                    </span>
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
