import { GitCompareArrows } from "lucide-react";
import { AuthorityLimit } from "../components/authority-limit";
import { ReconstructionPanel } from "../components/reconstruction-panel";
import { RevisionComparison } from "../components/revision-comparison";
import {
  reconstructionAfter,
  reconstructionBefore,
  revisionComparison,
} from "../data/investigation-projections";
export function RevisionComparisonPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATION / COMPARISON</p>
          <h1>Revision comparison</h1>
          <p>
            Before-and-after generated state uses exact server revisions and never infers a missing
            historical state in the browser.
          </p>
        </div>
        <span className="page-icon">
          <GitCompareArrows size={19} /> two revisions
        </span>
      </header>
      <AuthorityLimit compact />
      <div className="comparison-grid">
        <ReconstructionPanel value={reconstructionBefore} />
        <ReconstructionPanel value={reconstructionAfter} />
      </div>
      <RevisionComparison value={revisionComparison} />
    </>
  );
}
