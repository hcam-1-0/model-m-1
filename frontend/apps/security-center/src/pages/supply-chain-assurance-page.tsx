import { PackageCheck } from "lucide-react";
import { SecurityPageFrame, SecurityStateBoundary } from "../components/security-state-boundary";
import { SupplyChainTable } from "../components/supply-chain-table";
export function SupplyChainAssurancePage() {
  return (
    <SecurityPageFrame
      eyebrow="SECURITY / SUPPLY CHAIN"
      title="Supply-chain assurance"
      description="Read-only SBOM, license, vulnerability, and provenance evidence without scanner execution, artifact acquisition, or attestation signing."
    >
      <SecurityStateBoundary state="stale">
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">DEPENDENCY EVIDENCE</span>
              <h2>Generated component inventory</h2>
            </div>
            <PackageCheck size={20} />
          </header>
          <SupplyChainTable />
        </section>
      </SecurityStateBoundary>
    </SecurityPageFrame>
  );
}
