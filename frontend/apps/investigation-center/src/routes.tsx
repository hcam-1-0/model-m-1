import { Route, Routes } from "react-router";
import { CorrectionsRetractionsPage } from "./pages/corrections-retractions-page";
import { EvidenceReferencesPage } from "./pages/evidence-references-page";
import { InvestigationDetailPage } from "./pages/investigation-detail-page";
import { InvestigationHealthPage } from "./pages/investigation-health-page";
import { InvestigationOverviewPage } from "./pages/investigation-overview-page";
import { InvestigationQueuePage } from "./pages/investigation-queue-page";
import { InvestigationRelationshipsPage } from "./pages/investigation-relationships-page";
import { InvestigationTimelinePage } from "./pages/investigation-timeline-page";
import { PolicyPreviewsPage } from "./pages/policy-previews-page";
import { ReconstructionPage } from "./pages/reconstruction-page";
import { RevisionComparisonPage } from "./pages/revision-comparison-page";

export const investigationRoutes = [
  ["/investigations", "Overview"],
  ["/investigations/queue", "Investigation queue"],
  ["/investigations/timeline", "Timeline"],
  ["/investigations/reconstruction", "Reconstruction"],
  ["/investigations/comparison", "Revision comparison"],
  ["/investigations/corrections", "Corrections & retractions"],
  ["/investigations/relationships", "Relationships"],
  ["/investigations/evidence", "Evidence references"],
  ["/investigations/policy", "Policy previews"],
  ["/investigations/health", "Investigation health"],
] as const;
export function InvestigationRoutes() {
  return (
    <Routes>
      <Route path="/" element={<InvestigationOverviewPage />} />
      <Route path="/investigations" element={<InvestigationOverviewPage />} />
      <Route path="/investigations/queue" element={<InvestigationQueuePage />} />
      <Route path="/investigations/:investigationId" element={<InvestigationDetailPage />} />
      <Route path="/investigations/timeline" element={<InvestigationTimelinePage />} />
      <Route path="/investigations/reconstruction" element={<ReconstructionPage />} />
      <Route path="/investigations/comparison" element={<RevisionComparisonPage />} />
      <Route path="/investigations/corrections" element={<CorrectionsRetractionsPage />} />
      <Route path="/investigations/relationships" element={<InvestigationRelationshipsPage />} />
      <Route path="/investigations/evidence" element={<EvidenceReferencesPage />} />
      <Route path="/investigations/policy" element={<PolicyPreviewsPage />} />
      <Route path="/investigations/health" element={<InvestigationHealthPage />} />
      <Route path="*" element={<InvestigationOverviewPage />} />
    </Routes>
  );
}
