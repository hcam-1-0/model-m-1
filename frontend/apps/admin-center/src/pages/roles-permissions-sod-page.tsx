import { ShieldCheck } from "lucide-react";
import { CapabilityMatrix } from "../components/capability-matrix";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { PolicyPreviewPanel } from "../components/policy-preview-panel";
export function RolesPermissionsSodPage() {
  return (
    <AdminPageFrame
      eyebrow="ADMIN / AUTHORIZATION"
      title="Roles, permissions, and separation of duty"
      description="Server-authoritative RBAC, constrained ABAC, default deny, and independent database policy equivalence."
    >
      <div className="two-column">
        <section className="panel wide">
          <header>
            <div>
              <span className="eyebrow">CAPABILITY MATRIX</span>
              <h2>Generated role projection</h2>
            </div>
            <ShieldCheck size={20} />
          </header>
          <CapabilityMatrix />
        </section>
        <PolicyPreviewPanel />
      </div>
    </AdminPageFrame>
  );
}
