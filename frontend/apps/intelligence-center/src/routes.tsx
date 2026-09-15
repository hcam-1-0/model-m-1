import { Route, Routes } from "react-router";
import { CandidateEvidencePage } from "./pages/candidate-evidence-page";
import { CorrectionsPage } from "./pages/corrections-page";
import { CorrelationRunDetailPage } from "./pages/correlation-run-detail-page";
import { CorrelationRunQueuePage } from "./pages/correlation-run-queue-page";
import { HypothesisDetailPage } from "./pages/hypothesis-detail-page";
import { HypothesisQueuePage } from "./pages/hypothesis-queue-page";
import { IntelligenceHealthPage } from "./pages/intelligence-health-page";
import { IntelligenceOverviewPage } from "./pages/intelligence-overview-page";
import { MandatoryReviewDeskPage } from "./pages/mandatory-review-desk-page";
import { ProposedAlertDetailPage } from "./pages/proposed-alert-detail-page";
import { ProposedAlertQueuePage } from "./pages/proposed-alert-queue-page";
import { RelationshipExplorerPage } from "./pages/relationship-explorer-page";
import { RuleEvaluationsPage } from "./pages/rule-evaluations-page";
import { SpatialIntelligencePage } from "./pages/spatial-intelligence-page";

export const intelligenceRoutes = [
  ["/intelligence", "Overview"],
  ["/intelligence/hypotheses", "Hypotheses"],
  ["/intelligence/runs", "Correlation runs"],
  ["/intelligence/relationships", "Relationships"],
  ["/intelligence/spatial", "Spatial intelligence"],
  ["/intelligence/rules", "Rule evaluations"],
  ["/intelligence/alerts", "Proposed alerts"],
  ["/intelligence/review", "Mandatory review"],
  ["/intelligence/corrections", "Corrections"],
  ["/intelligence/health", "Intelligence health"],
] as const;
export function IntelligenceRoutes() {
  return (
    <Routes>
      <Route path="/" element={<IntelligenceOverviewPage />} />
      <Route path="/intelligence" element={<IntelligenceOverviewPage />} />
      <Route path="/intelligence/hypotheses" element={<HypothesisQueuePage />} />
      <Route path="/intelligence/hypotheses/:hypothesisId" element={<HypothesisDetailPage />} />
      <Route path="/intelligence/runs" element={<CorrelationRunQueuePage />} />
      <Route path="/intelligence/runs/:runId" element={<CorrelationRunDetailPage />} />
      <Route path="/intelligence/relationships" element={<RelationshipExplorerPage />} />
      <Route path="/intelligence/spatial" element={<SpatialIntelligencePage />} />
      <Route path="/intelligence/rules" element={<RuleEvaluationsPage />} />
      <Route path="/intelligence/candidates/:candidateId" element={<CandidateEvidencePage />} />
      <Route path="/intelligence/alerts" element={<ProposedAlertQueuePage />} />
      <Route path="/intelligence/alerts/:alertId" element={<ProposedAlertDetailPage />} />
      <Route path="/intelligence/review" element={<MandatoryReviewDeskPage />} />
      <Route path="/intelligence/corrections" element={<CorrectionsPage />} />
      <Route path="/intelligence/health" element={<IntelligenceHealthPage />} />
      <Route path="*" element={<IntelligenceOverviewPage />} />
    </Routes>
  );
}
