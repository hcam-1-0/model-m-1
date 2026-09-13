import { ShieldX } from "lucide-react";
import { useState } from "react";
import { DenialActivityTable } from "../components/denial-activity-table";
import { SecurityFilterRail, type SecurityFilters } from "../components/security-filter-rail";
import { SecurityPageFrame } from "../components/security-state-boundary";
export function DeniedAnomalousActivityPage() {
  const [filters, setFilters] = useState<SecurityFilters>({
    query: "",
    state: "all",
    lane: "security",
  });
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / DENIALS"
      title="Denied and anomalous activity"
      description="Sanitized denial categories and bounded actor classes; raw payloads, identities, locators, and security material are not retained."
    >
      <div className="workspace-grid">
        <SecurityFilterRail filters={filters} onChange={setFilters} />
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">SECURITY LANE</span>
              <h2>Generated denials</h2>
            </div>
            <ShieldX size={20} />
          </header>
          <DenialActivityTable />
        </section>
      </div>
    </SecurityPageFrame>
  );
}
