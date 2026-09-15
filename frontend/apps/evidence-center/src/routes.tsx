import { Route, Routes } from "react-router";
import { EvidenceDetailPage } from "./pages/evidence-detail-page";
import { EvidenceHealthPage } from "./pages/evidence-health-page";
import { EvidenceOverviewPage } from "./pages/evidence-overview-page";
import { EvidencePolicyPreviewPage } from "./pages/evidence-policy-preview-page";
import { EvidenceQueuePage } from "./pages/evidence-queue-page";
import { IntegrityHistoryPage } from "./pages/integrity-history-page";
import { ProvenanceCustodyPage } from "./pages/provenance-custody-page";

export const evidenceRoutes = [
  ["/evidence", "Overview"],
  ["/evidence/queue", "Reference queue"],
  ["/evidence/integrity", "Integrity history"],
  ["/evidence/provenance", "Provenance & custody"],
  ["/evidence/policy", "Policy previews"],
  ["/evidence/health", "Evidence health"],
] as const;
export function EvidenceRoutes() {
  return (
    <Routes>
      <Route path="/" element={<EvidenceOverviewPage />} />
      <Route path="/evidence" element={<EvidenceOverviewPage />} />
      <Route path="/evidence/queue" element={<EvidenceQueuePage />} />
      <Route path="/evidence/:evidenceId" element={<EvidenceDetailPage />} />
      <Route path="/evidence/integrity" element={<IntegrityHistoryPage />} />
      <Route path="/evidence/provenance" element={<ProvenanceCustodyPage />} />
      <Route path="/evidence/policy" element={<EvidencePolicyPreviewPage />} />
      <Route path="/evidence/health" element={<EvidenceHealthPage />} />
      <Route path="*" element={<EvidenceOverviewPage />} />
    </Routes>
  );
}
