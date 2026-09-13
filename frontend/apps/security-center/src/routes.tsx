import { Route, Routes } from "react-router";
import { AccessAssurancePage } from "./pages/access-assurance-page";
import { AuditReferenceExplorerPage } from "./pages/audit-reference-explorer-page";
import { DeniedAnomalousActivityPage } from "./pages/denied-anomalous-activity-page";
import { PoliciesExceptionsAttestationsPage } from "./pages/policies-exceptions-attestations-page";
import { PrivilegedActivityPage } from "./pages/privileged-activity-page";
import { ProviderDestinationSecretPosturePage } from "./pages/provider-destination-secret-posture-page";
import { SecurityOverviewPage } from "./pages/security-overview-page";
import { SessionAuthenticationPage } from "./pages/session-authentication-page";
import { SocHandoffUnavailablePage } from "./pages/soc-handoff-unavailable-page";
import { SupplyChainAssurancePage } from "./pages/supply-chain-assurance-page";
export const securityRoutes = [
  ["/security", "Overview"],
  ["/security/access", "Access assurance"],
  ["/security/denials", "Denied activity"],
  ["/security/privileged", "Privileged activity"],
  ["/security/sessions", "Sessions"],
  ["/security/audit", "Audit references"],
  ["/security/compliance", "Policies and attestations"],
  ["/security/supply-chain", "Supply chain"],
  ["/security/providers", "Provider posture"],
  ["/security/soc", "SOC handoff"],
] as const;
export function SecurityRoutes() {
  return (
    <Routes>
      <Route path="/" element={<SecurityOverviewPage />} />
      <Route path="/security" element={<SecurityOverviewPage />} />
      <Route path="/security/access" element={<AccessAssurancePage />} />
      <Route path="/security/denials" element={<DeniedAnomalousActivityPage />} />
      <Route path="/security/privileged" element={<PrivilegedActivityPage />} />
      <Route path="/security/sessions" element={<SessionAuthenticationPage />} />
      <Route path="/security/audit" element={<AuditReferenceExplorerPage />} />
      <Route path="/security/compliance" element={<PoliciesExceptionsAttestationsPage />} />
      <Route path="/security/supply-chain" element={<SupplyChainAssurancePage />} />
      <Route path="/security/providers" element={<ProviderDestinationSecretPosturePage />} />
      <Route path="/security/soc" element={<SocHandoffUnavailablePage />} />
      <Route path="*" element={<SecurityOverviewPage />} />
    </Routes>
  );
}
