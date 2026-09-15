import { RotateCcw } from "lucide-react";
import { CorrectionRetractionPanel } from "../components/correction-retraction-panel";
import { ImpactClosureTable } from "../components/impact-closure-table";
import { correction, impactClosure } from "../data/investigation-projections";
export function CorrectionsRetractionsPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATION / HISTORY</p>
          <h1>Corrections and retractions</h1>
          <p>
            Append-only predecessor and successor records with explicit per-target impact closure.
            Historical states remain visible.
          </p>
        </div>
        <span className="page-icon">
          <RotateCcw size={19} /> no rewrite
        </span>
      </header>
      <div className="detail-grid">
        <CorrectionRetractionPanel record={correction} />
        <section className="panel">
          <header>
            <div>
              <span className="eyebrow">CHANGE CONTROL</span>
              <h2>Propagation rules</h2>
            </div>
          </header>
          <ul className="rule-list">
            <li>Original record remains visible</li>
            <li>Successor links to predecessor</li>
            <li>Each accepted target reports closure</li>
            <li>Blocked and failed impacts remain prominent</li>
            <li>No automatic downstream reversal</li>
          </ul>
        </section>
      </div>
      <ImpactClosureTable targets={correction.impactTargets} summary={impactClosure} />
    </>
  );
}
