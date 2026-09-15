import { FileClock, FileLock2, GitCompareArrows, Network } from "lucide-react";
import { Link, useParams } from "react-router";
import { AuthorityLimit } from "../components/authority-limit";
import { TimelineTable } from "../components/timeline-table";
import { selectedInvestigation, timelinePage } from "../data/investigation-projections";
export function InvestigationDetailPage() {
  const { investigationId } = useParams();
  return (
    <>
      <header className="identity-band">
        <div className="identity-icon">
          <FileClock size={22} />
        </div>
        <div>
          <p className="eyebrow">GENERATED INVESTIGATION</p>
          <h1>{selectedInvestigation?.title ?? "Generated investigation"}</h1>
          <code>{investigationId ?? selectedInvestigation?.ref}</code>
        </div>
        <div>
          <span className="status-chip status-open">{selectedInvestigation?.state ?? "open"}</span>
          <small>rev {selectedInvestigation?.revision ?? 1}</small>
        </div>
      </header>
      <AuthorityLimit compact />
      <nav className="detail-actions" aria-label="Investigation detail sections">
        <Link to="/investigations/timeline">
          <FileClock size={16} /> Timeline
        </Link>
        <Link to="/investigations/comparison">
          <GitCompareArrows size={16} /> Compare
        </Link>
        <Link to="/investigations/relationships">
          <Network size={16} /> Relationships
        </Link>
        <Link to="/investigations/evidence">
          <FileLock2 size={16} /> Evidence references
        </Link>
      </nav>
      <section className="panel table-panel">
        <header>
          <div>
            <span className="eyebrow">LATEST RECORDS</span>
            <h2>Authoritative chronology</h2>
          </div>
          <span>rev {selectedInvestigation?.revision ?? 1}</span>
        </header>
        <TimelineTable entries={timelinePage.items.slice(0, 8)} />
      </section>
    </>
  );
}
