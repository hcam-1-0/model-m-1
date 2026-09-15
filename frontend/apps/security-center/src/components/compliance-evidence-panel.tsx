import { FileCheck2 } from "lucide-react";
import { complianceControls } from "../data/security-projections";
export function ComplianceEvidencePanel() {
  return (
    <section className="panel">
      <header>
        <div>
          <span className="eyebrow">COMPLIANCE EVIDENCE</span>
          <h2>Control projections</h2>
        </div>
        <FileCheck2 size={20} />
      </header>
      <ul className="evidence-list">
        {complianceControls.slice(0, 6).map((item) => (
          <li key={item.ref}>
            <div>
              <strong>{item.title}</strong>
              <small>
                {item.framework} · {item.ref}
              </small>
            </div>
            <span className={`status ${item.state}`}>{item.state}</span>
          </li>
        ))}
      </ul>
      <footer>No attestation is signed or activated.</footer>
    </section>
  );
}
